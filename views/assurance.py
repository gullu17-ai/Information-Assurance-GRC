"""Governance, audit and operational assurance views."""
import streamlit as st

from services.calculations import UNKNOWN, maturity, recovery_outcome, recovery_readiness, target_minutes
from services.database import query, recovery_services
from views.common import Field, flow, number, record_editor, show, table
from views.registers import ids
from views.theme import action_status, bar_rows, empty_state, kpi, kpis, section, status_badge


def governance():
    st.write(
        "PakArena Smart Stadium is a hypothetical multipurpose venue in Pakistan. It supports sports, concerts "
        "and other events for approximately 45,000 spectators, with around 350 permanent and 1,200 peak-event temporary staff."
    )
    st.subheader("Organization architecture")
    from views.program import architecture
    architecture()
    table([
        {"service": "Spectator services", "systems": "Cloud ticketing, mobile app, spectator database, QR entry and public Wi-Fi"},
        {"service": "Event operations", "systems": "Event control room, signage and scoreboard"},
        {"service": "Safety and security", "systems": "CCTV, access control, crowd sensors, AI crowd prediction and emergency coordination"},
        {"service": "Facilities and engineering", "systems": "BMS, lighting, power and facility sensors"},
        {"service": "Commercial and corporate", "systems": "POS, vendor services, finance, HR, IAM and corporate network"},
        {"service": "Security and resilience", "systems": "SOC/SIEM, segmentation, backup and DR"},
    ])
    st.subheader("Reporting and decision rights")
    flow("Board / Stadium Owners", "CEO / General Manager", "CIO, CISO, Operations, Facilities / OT, Physical Security and Risk & Compliance")
    st.write("Internal Audit has an independent reporting line to senior leadership / the Board.")
    show("SELECT * FROM governance_roles")
    st.caption("TODO · Document the approved risk appetite, escalation thresholds and versioned policy set.")


def iam():
    flow("User", "Identity", "Authentication", "Authorization", "Least Privilege", "Monitoring")
    rbac, abac, privileged, vendor, reviews, duties = st.tabs(
        ["RBAC", "ABAC", "Privileged Access", "Vendor Access", "Access Reviews", "Separation of Duties"]
    )
    with rbac:
        show("SELECT * FROM iam_roles")
    with abac:
        show("SELECT * FROM iam_permissions")
    with privileged:
        st.write(
            "Require MFA for remote employee access, cloud administration, email, IAM administration, VPN, "
            "vendor accounts and privileged access. Use separate named admin accounts. "
            "Restrict break-glass access and report every use."
        )
        show("SELECT * FROM iam_permissions WHERE policy = 'Privileged changes'")
    with vendor:
        show("SELECT * FROM iam_permissions WHERE policy = 'Vendor remote access'")
    with reviews:
        show("SELECT * FROM access_reviews")
    with duties:
        show("SELECT * FROM iam_permissions WHERE policy = 'Separation of duties'")
        st.caption("TODO · Formal incompatible-role matrix and operating access review evidence.")


def data_protection():
    st.caption("Assignment 3 handling rules and PASS examples. Dataset ownership and exact retention periods are TODO.")
    show("""
        SELECT d.name AS data_type, d.classification, d.owner, c.access AS access_requirement,
               c.encryption AS encryption_requirement, c.retention, c.handling AS handling_rule, d.source
        FROM data_items d JOIN data_inventory c ON c.classification = d.classification ORDER BY d.rowid
    """)
    record_editor("data_items", [Field("owner")], key="name", edit_only=True)
    st.subheader("Proposed asset-level classification and dependencies")
    show("SELECT a.id,a.name,r.data_classification,r.dependencies FROM assets a JOIN recovery_design r ON r.asset_id=a.id ORDER BY a.id")
    st.caption("Final-project proposed mapping for owner review; source dataset classes remain above.")
    st.subheader("Key data flows")
    flow("Ticketing website / app", "Spectator database", "Approved ticket validation at entry")
    flow("CCTV and crowd sensors", "Video analytics", "Physical Security human review")
    flow("Restricted / Critical systems", "Protected backups", "Approved recovery environment")
    st.caption("Proposed flow derived from A1–A3. A formal privacy assessment and complete transfer inventory are TODO.")


def bcdr():
    services = recovery_services()
    results = [{**service, "outcome": recovery_outcome(service)} for service in services]
    outcomes = [row["outcome"] for row in results]
    shortest = min((target for row in services if (target := target_minutes(row["rto"])) is not None), default=None)
    tested = sum(bool(row["test_id"]) for row in services)
    documented = sum(bool(row["backup_status"]) for row in services)
    kpis(("Critical services", sum(row["criticality"] == 5 for row in services), "Criticality 5"),
         ("Shortest RTO", f"{shortest} min" if shortest is not None else UNKNOWN),
         ("Backup status", f"{documented} / {len(services)} recorded" if documented else UNKNOWN),
         ("DR test status", f"{tested} / {len(services)} tested" if tested else UNKNOWN))
    section("Disaster recovery design")
    flow("Primary", "Replication", "Backup", "DR Site")
    st.subheader("Business impact and recovery targets")
    st.caption("Source A3 targets are preserved below. The proposed dependency-aware BIA is available under Program Completion > Audit and recovery.")
    show("SELECT * FROM bcdr_services ORDER BY priority IS NULL, priority, asset_id")
    st.caption("RTO and RPO are planning targets. Maximum tolerable downtime is Not Yet Assessed.")
    record_editor("bcdr_services", [Field("backup_status"), Field("restore_test", "Restore test notes", kind="area")],
                  key="asset_id", title_column="service", edit_only=True, label="Edit backup and restore notes")
    st.subheader("Measured recovery readiness")
    kpi("BC/DR readiness", number(recovery_readiness(outcomes), "%"))
    st.caption(
        f"{outcomes.count('Targets met')} of {len(services)} services met their applicable targets. "
        "Readiness uses the latest dated test per service. Untested services stay in the denominator."
    )
    columns = ("service", "rto", "rpo", "test_id", "tested_on", "restore_result", "actual_rto_minutes",
               "actual_rpo_minutes", "outcome", "reviewer", "evidence_id")
    table([{key: row[key] for key in columns} for row in results])
    record_editor("recovery_tests", [
        Field("asset_id", "Service asset ID", options=(None, *(row["asset_id"] for row in services)), required=True),
        Field("tested_on", "Test date", kind="date", required=True),
        Field("restore_result", "Restore result", options=(None, "Restored", "Failed"), required=True),
        Field("actual_rto_minutes", "Measured recovery time (minutes)", kind="minutes"),
        Field("actual_rpo_minutes", "Measured data loss (minutes)", kind="minutes"),
        Field("reviewer"), Field("evidence_id", "Evidence", options=(None, *ids("evidence"))),
        Field("notes", kind="area"),
    ], label="Add or edit recovery test", validate=validate_recovery_test)
    with st.expander("Recovery test history"):
        show("SELECT * FROM recovery_tests ORDER BY tested_on DESC, rowid DESC")
    section("Recovery priorities and exercises")
    st.write(
        "Replicate priority databases and virtual services. Keep a recovery copy protected from production accounts. "
        "Restore priority services at a backup site or cloud recovery environment."
    )
    st.write(
        "Restore the network and IAM first, then gates and ticket records, then CCTV/BMS, followed by ticketing/POS "
        "and finally AI and public Wi-Fi. The SIEM has a target but no explicit standalone priority in A3."
    )
    st.write("Test sample restores monthly and DR at least twice a year. Check backup status, contacts and recovery access before major events.")


def validate_recovery_test(values, _previous):
    if values["restore_result"] == "Failed":
        return
    if values["actual_rto_minutes"] is None:
        raise ValueError("Enter the measured recovery time for a restored service.")
    rpo = query("SELECT rpo FROM bcdr_services WHERE asset_id = ?", (values["asset_id"],))[0]["rpo"]
    if target_minutes(rpo) is not None and values["actual_rpo_minutes"] is None:
        raise ValueError("Enter measured data loss, including zero when the test found no loss.")


def incidents():
    stages = query("SELECT * FROM incident_stages ORDER BY rowid")
    section("Response lifecycle")
    flow(*(row["stage"] for row in stages))
    section("Ransomware scenario")
    show("SELECT * FROM incidents")
    table(stages)
    st.caption("Scenario evidence describes what analysts would collect. Exercise results and current response readiness are Not Yet Assessed.")
    st.subheader("Final program incident command and safety procedures")
    for row in query("SELECT title,content FROM program_sections WHERE id IN ('incident','recovery','exercise')"):
        with st.expander(row["title"]): st.write(row["content"])


def soc():
    st.caption("Proposed PASS monitoring architecture")
    flow("Log sources", "SIEM correlation and alert monitoring", "SOC analyst triage", "Incident escalation")
    show("SELECT * FROM soc_sources")
    st.write(
        "SOC correlates alerts and escalates confirmed critical incidents to the CISO and Stadium Operations. "
        "Coordinate with IT, Physical Security and Facilities when operational systems may be affected."
    )
    st.write("Proposed SOAR support covers alert grouping, enrichment and routing. Containment and changes require human authorization.")
    st.caption("TODO · Validate source coverage, retention, clock synchronization, alert tests and escalation times.")


def infrastructure():
    architecture, control_panel = st.columns([1, 2], gap="medium")
    with architecture:
        section("Proposed zones and conduits")
        flow("Internet / Public", "DMZ", "Corporate IT", "Security Boundary", "OT Zone", "BMS / Turnstiles / IoT",
             vertical=True, boundary="Security Boundary")
    with control_panel:
        section("IT, OT, IoT and vendor controls")
        table([
        {"area": "Network segmentation", "control": "Separate guest, staff and OT networks. Limit traffic to approved conduits.",
         "reference": "R04 / C04 · CIS Controls, IEC 62443"},
        {"area": "OT maintenance", "control": "Use approved gateway or jump host, MFA and allow-listing. Log authorized maintenance.",
         "reference": "R06 / C06 · IEC 62443, NIST SP 800-82"},
        {"area": "IoT lifecycle", "control": "Maintain inventory and firmware records. Authenticate devices and encrypt traffic.",
         "reference": "R07 / C07 · IEC 62443, NIST SP 800-82"},
        {"area": "Cloud", "control": "Use least privilege, configuration reviews and secure key handling.",
         "reference": "R09 / C09 · ISO/IEC 27001, CIS Controls"},
        {"area": "Supply chain", "control": "Review suppliers, use security clauses, scope access, log access and consider insurance where suitable.",
         "reference": "R13 / C13 · PISF 2026, ISO/IEC 27001"},
        ])
    st.write("PASS owns workload identities, data handling and configuration review. Provider responsibilities depend on the service contract.")
    st.subheader("Supply-chain assessment")
    st.write("PASS depends on providers for ticketing, payments, internet access, maintenance and event technology.")
    show("""
        SELECT r.id AS risk_id, r.treatment, r.treatment_action, r.residual_target AS expected_residual_target,
               c.status AS control_status, c.evidence_requirement
        FROM risks r JOIN risk_controls m ON m.risk_id = r.id
        JOIN controls c ON c.id = m.control_id WHERE r.id = 'R13'
    """)
    st.caption(
        "TODO · Confirm cloud responsibilities, supplier-specific assessments, device firmware and lifecycle status, "
        "formal Purdue-level mapping, and cryptographic dependencies for future PQC migration."
    )


def maturity_roadmap():
    rows = query("SELECT * FROM maturity_scores ORDER BY rowid")
    overall = maturity(row["score"] for row in rows)
    kpi("Overall maturity score", "Assessment Pending" if overall is None else number(overall, " / 5"))
    st.caption(f"{sum(row['score'] is not None for row in rows)} of {len(rows)} dimensions scored. Enter reviewed PASS scores with their assessment basis.")
    st.caption("Use one rubric across PASS dimensions. Suggested scale: 1 Initial · 2 Repeatable · 3 Defined · 4 Measured · 5 Optimized.")
    bar_rows([(row["dimension"], row["score"], number(row["score"], " / 5")) for row in rows], 5)
    with st.expander("Assessment details"):
        table(rows)
    record_editor("maturity_scores", [
        Field("score", options=(None, 1, 2, 3, 4, 5)), Field("rationale", "Assessment basis", kind="area"),
        Field("assessor"), Field("assessed_on", "Assessment date", kind="date"),
    ], key="dimension", edit_only=True, label="Assess maturity dimension", validate=validate_maturity)
    st.subheader("Three-year roadmap")
    st.write("Use the course plan's three phases to record PASS-approved activities and track their delivery.")
    phases = query("SELECT * FROM roadmap ORDER BY year")
    actions = query("SELECT * FROM roadmap_actions ORDER BY year, target_date IS NULL, target_date, id")
    for column, phase in zip(st.columns(3, gap="small"), phases):
        with column.container(border=True):
            st.html(f'<div class="pass-roadmap"><small>YEAR {phase["year"]}</small></div>')
            st.markdown(f"### {phase['phase']}")
            phase_actions = [row for row in actions if row["year"] == phase["year"]]
            if not phase["activities"] and not phase_actions:
                empty_state("Not Yet Assessed", "No activities recorded for this phase.")
            if phase["activities"]:
                st.text(phase["activities"])
            for action in phase_actions:
                st.text(action["action"])
                st.html(status_badge(action["status"] or UNKNOWN))
    record_editor("roadmap", [
        Field("activities", "Approved activities", kind="area"),
    ], key="year", title_column="phase", edit_only=True, label="Edit phase summary")
    st.subheader("Roadmap actions")
    if actions:
        table(actions)
    else:
        st.info("Not Yet Assessed · Add an approved PASS action to begin tracking progress.")
    years = tuple(row["year"] for row in phases)
    record_editor("roadmap_actions", [
        Field("year", "Roadmap year", options=(None, *years), required=True),
        Field("action", kind="area", required=True), Field("owner"),
        Field("target_date", kind="date"), Field("status", options=(None, "Planned", "In Progress", "Complete", "Deferred")),
        Field("success_criterion", kind="area"), Field("risk_id", "Related risk", options=(None, *ids("risks"))),
        Field("evidence_id", "Completion evidence", options=(None, *ids("evidence"))),
    ], title_column="action", label="Add or edit roadmap action")
    st.subheader("Documented PASS assurance priorities")
    show("SELECT * FROM assurance_priorities ORDER BY priority")


def validate_maturity(values, previous):
    if values["score"] is not None and values["score"] != previous.get("score") and not values["rationale"]:
        raise ValueError("Enter the assessment basis for the maturity score.")


def audit():
    from views.program import third_party_audit
    third_party_audit()
    with st.expander("Assignment 2 design observations and original action records"):
        show("SELECT * FROM audit_findings WHERE id NOT LIKE 'EXT-%' ORDER BY id")
        show("SELECT * FROM corrective_actions ORDER BY id")
