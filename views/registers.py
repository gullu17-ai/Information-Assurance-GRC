"""The five master registers and their relationships."""
from collections import Counter

import streamlit as st

from services.calculations import UNKNOWN, compliance, control_effectiveness, pisf_clauses, risk_level, risk_score
from services.database import query
from views.common import Field, filter_rows, number, record_editor, table
from views.theme import bar_rows, empty_state, kpi, kpis, section, summary_table

SCALE = (None, 1, 2, 3, 4, 5)
COMPLIANCE_STATUSES = (None, "Compliant", "Partially Compliant", "Weak", "Non-Compliant")


def ids(table_name):
    return tuple(row["id"] for row in query(f"SELECT id FROM {table_name} ORDER BY id"))


def assets():
    rows = query("""
        SELECT a.*, (SELECT group_concat(r.id, ', ') FROM risks r WHERE r.asset_id = a.id) AS related_risks
        FROM assets a ORDER BY a.id
    """)
    kpis(("Registered assets", len(rows)), ("Criticality 5", sum(row["criticality"] == 5 for row in rows)),
         ("Linked to risks", sum(bool(row["related_risks"]) for row in rows)))
    table(filter_rows(rows, "type"), labels={"id": "Asset ID", "name": "Asset"})
    record_editor("assets", [
        Field("name", "Asset", required=True), Field("owner"), Field("type"),
        Field("criticality", options=SCALE), Field("environment"),
    ], title_column="name")


def risk_rows():
    rows = query("""
        SELECT r.id, COALESCE(a.name, r.scope) AS asset, a.type AS asset_category, r.event AS risk_event, r.threat, r.vulnerability,
               r.likelihood, r.impact, r.treatment, r.treatment_action, r.owner, r.residual_likelihood,
               r.residual_impact, r.residual_target AS expected_residual_target, r.status, r.source
        FROM risks r LEFT JOIN assets a ON a.id = r.asset_id ORDER BY r.id
    """)
    for row in rows:
        row["risk_score"] = risk_score(row["likelihood"], row["impact"])
        row["risk_level"] = risk_level(row["risk_score"])
        row["residual_risk"] = risk_score(row["residual_likelihood"], row["residual_impact"])
    return rows


def risks():
    rows = risk_rows()
    counts = Counter(row["risk_level"] for row in rows)
    kpis(("Total risks", len(rows)), ("Critical", counts["Critical"]), ("High", counts["High"]),
         ("Treatment recorded", sum(bool(row["treatment"]) for row in rows)),
         ("Open", sum((row["status"] or "").casefold() == "open" for row in rows)
          if any(row["status"] for row in rows) else UNKNOWN))
    severity, category = st.columns(2, gap="medium")
    with severity:
        section("Risk distribution")
        bar_rows([(level, counts[level], counts[level]) for level in ("Critical", "High", "Medium", "Low")],
                 len(rows), tone="severity")
    with category:
        categories = Counter(row["asset_category"] for row in rows if row["asset_category"])
        section("Risk by Asset Category")
        with st.expander(f"{sum(categories.values())} risks with a recorded asset category"):
            bar_rows([(name, count, count) for name, count in sorted(categories.items(), key=lambda item: (-item[1], item[0]))], len(rows))
    st.caption("Likelihood × impact · Low 1–4 · Medium 5–9 · High 10–16 · Critical 17–25")
    st.caption("Expected residual targets are Assignment 2 estimates. Assessed residual risk uses the entered residual likelihood and impact.")
    visible = filter_rows(rows, "risk_level", "asset", "treatment", "status", labels={"risk_level": "Severity"})
    order = "id risk_event asset risk_score risk_level treatment owner status threat vulnerability likelihood impact treatment_action residual_likelihood residual_impact residual_risk expected_residual_target source".split()
    table([{column: row[column] for column in order} for row in visible], labels={"id": "Risk ID"})
    with st.expander("PASS likelihood and impact scales"):
        table([
            {"score": i, "likelihood": likelihood, "impact": impact}
            for i, (likelihood, impact) in enumerate(zip(
                ["Rare", "Unlikely", "Possible", "Likely", "Almost Certain"],
                ["Insignificant", "Minor", "Moderate", "Major", "Severe"],
            ), 1)
        ])
        st.markdown("**Assignment 1 baseline rating rationale**")
        table(query("SELECT * FROM risk_rationales ORDER BY risk_id"))
    record_editor("risks", [
        Field("asset_id", options=(None, *ids("assets"))), Field("scope", "Cross-asset scope"),
        Field("event", "Risk event", required=True), Field("threat"), Field("vulnerability", kind="area"),
        Field("likelihood", options=SCALE, required=True), Field("impact", options=SCALE, required=True),
        Field("treatment"), Field("treatment_action", kind="area"), Field("owner"),
        Field("residual_target", "Expected residual target", options=(None, *range(1, 26))),
        Field("residual_likelihood", options=SCALE), Field("residual_impact", options=SCALE), Field("status"),
    ], title_column="event", links=[("risk_controls", "risk_id", "control_id", ids("controls"), "Related controls")])


def controls():
    rows = query("""
        SELECT c.*, e.status AS assessment_evidence_status,
               (SELECT group_concat(risk_id, ', ') FROM risk_controls m WHERE m.control_id = c.id) AS related_risks
        FROM controls c LEFT JOIN evidence e ON e.id = c.assessment_evidence_id ORDER BY c.id
    """)
    applicable = [row for row in rows if row["applicable"]]
    effective = sum(row["effectiveness"] == "Effective" for row in applicable)
    assessed = sum(row["effectiveness"] in ("Effective", "Ineffective") for row in applicable)
    kpis(("Controls", len(rows)), ("Applicable", len(applicable)), ("Design gaps", sum(row["status"] == "Gap" for row in rows)),
         ("Control effectiveness", number(control_effectiveness(rows), "%")))
    st.caption(
        f"{effective} effective · {assessed} assessed · {len(applicable)} applicable. "
        "Effectiveness uses all applicable controls as the denominator. Record the operating test or evidence behind each verdict."
    )
    table(filter_rows(rows, "status"), labels={"id": "Control ID", "name": "Control name"})
    record_editor("controls", [
        Field("name", "Control name", required=True), Field("type", "Control type"),
        Field("frameworks", "Frameworks (semicolon-separated)"), Field("owner"),
        Field("evidence_requirement", kind="area"),
        Field("status", options=(None, "Planned", "Partial", "Gap", "Implemented")),
        Field("effectiveness", options=(None, "Effective", "Ineffective")),
        Field("assessment_basis", "Assessment basis", kind="area"), Field("assessor"),
        Field("assessed_on", "Assessment date", kind="date"),
        Field("assessment_evidence_id", "Assessment evidence", options=(None, *ids("evidence"))),
        Field("applicable", kind="bool"),
    ], title_column="name", links=[("risk_controls", "control_id", "risk_id", ids("risks"), "Related risks")],
        validate=validate_control_assessment)


def validate_control_assessment(values, previous):
    verdict = values["effectiveness"]
    if verdict and verdict != previous.get("effectiveness") and not values["assessment_basis"]:
        raise ValueError("Enter the operating test or evidence reviewed for the effectiveness verdict.")


def compliance_register():
    rows = query("""
        SELECT q.*, linked.status AS assessment_evidence_status,
                    (SELECT group_concat(m.control_id, ', ') FROM compliance_controls m
                     WHERE m.requirement_id = q.id) AS mapped_controls,
                    (SELECT group_concat(e.id || ' (' || COALESCE(e.status, 'Not Yet Assessed') || ')', ', ')
                     FROM compliance_controls m JOIN evidence e ON e.control_id = m.control_id
                     WHERE m.requirement_id = q.id) AS evidence
        FROM compliance_requirements q LEFT JOIN evidence linked ON linked.id = q.assessment_evidence_id ORDER BY q.id
    """)
    areas = [row for row in rows if not row["clause_ref"]]
    overall = compliance(areas)
    kpis(("Overall compliance", number(overall, "%"), "Framework-area assessment"),
         ("Applicable areas", sum(row["applicable"] for row in areas)),
         ("Compliant areas", sum(row["applicable"] and row["status"] == "Compliant" for row in areas)))
    if overall is None:
        empty_state("No assessed requirements yet", "Enter a status for an applicable framework area to calculate compliance.")
    st.caption("Compliant ÷ applicable × 100. Clause-level assessments are reported separately.")
    with st.expander("Framework assessment overview"):
        summary_table(("Framework", "Requirement area", "Status"), [
            (row["framework"], row["requirement"], row["status"]) for row in areas
        ], badge_columns=(2,))
    table(filter_rows(rows, "framework", "status"), labels={"id": "Requirement ID"})
    record_editor("compliance_requirements", [
        Field("framework", required=True), Field("requirement", required=True), Field("purpose", kind="area"),
        Field("clause_ref", "Clause identifier"), Field("reference_source", "Source and version"),
        Field("assessment_evidence_id", "Assessment evidence", options=(None, *ids("evidence"))),
        Field("status", "Assessment status", options=COMPLIANCE_STATUSES), Field("gap", kind="area"),
        Field("recommendation", kind="area"), Field("applicable", kind="bool"),
    ], title_column="requirement", links=[
        ("compliance_controls", "requirement_id", "control_id", ids("controls"), "Mapped controls"),
    ], validate=validate_clause)
    st.subheader("PISF 2026 mapping")
    clauses = pisf_clauses(rows)
    kpi("PISF clause compliance", number(compliance(clauses), "%"))
    if clauses:
        keys = ("id", "clause_ref", "reference_source", "requirement", "applicable", "status",
                "mapped_controls", "assessment_evidence_id", "assessment_evidence_status", "gap")
        table([{key: row[key] for key in keys} for row in clauses])
    else:
        st.info(f"{UNKNOWN} · Add a requirement with framework PISF 2026, a clause identifier and its authoritative source.")
    st.caption("Coverage is limited to the applicable clauses entered here. It does not represent full-standard compliance.")
    with st.expander("Assignment 2 framework-level mapping"):
        table(query("""
            SELECT q.id AS requirement_id, c.id AS control_id, c.name AS control_name,
                   r.risk_id, c.evidence_requirement, c.status
            FROM compliance_requirements q JOIN compliance_controls m ON m.requirement_id = q.id
            JOIN controls c ON c.id = m.control_id LEFT JOIN risk_controls r ON r.control_id = c.id
            WHERE lower(trim(q.framework)) = 'pisf 2026' AND q.clause_ref IS NULL ORDER BY c.id, r.risk_id
        """))


def validate_clause(values, _previous):
    if values["clause_ref"] and not values["reference_source"]:
        raise ValueError("Enter the authoritative source and version for this clause.")


def evidence():
    rows = query("SELECT * FROM evidence ORDER BY id")
    kpis(("Evidence entries", len(rows)), ("Requested", sum(row["status"] == "Requested" for row in rows)),
         ("Verified", sum(row["status"] == "Verified" for row in rows)))
    st.caption("Seed entries are evidence requests. Mark demonstration artifacts as Simulated Evidence.")
    table(filter_rows(rows, "status"), labels={"id": "Evidence ID", "finding_id": "Related audit finding"})
    record_editor("evidence", [
        Field("control_id", "Related control", options=(None, *ids("controls"))), Field("type", "Evidence type"),
        Field("description", kind="area", required=True), Field("owner"), Field("last_reviewed", "Last reviewed (YYYY-MM-DD)"),
        Field("status", options=(None, "Requested", "Collected", "Verified", "Simulated Evidence")),
        Field("finding_id", "Related audit finding", options=(None, *ids("audit_findings"))),
    ], title_column="description")
