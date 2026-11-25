"""AI governance, review-only recommendations and measured evaluation."""
from time import perf_counter

import streamlit as st

from services.ai_service import provider_settings, recommend
from services.calculations import UNKNOWN, ai_accuracy, evaluation_gain, percentage
from services.database import query, save
from services.policy_engine import NOTICE, control_catalog
from views.common import Field, number, record_editor, table
from views.theme import empty_state, kpi, section, status_badge


def ai_governance():
    systems = query("SELECT * FROM ai_systems")
    for system in systems:
        with st.container(border=True):
            section(system["system"], f"{system['asset_id']} · {system['owner'] or UNKNOWN}")
            st.write(system["purpose"] or UNKNOWN)
            st.html(status_badge(system["governance_status"] or UNKNOWN))
        for fields in (
            (("AI Risk", "ai_risk"), ("Human Oversight", "oversight"), ("Data Privacy", "privacy")),
            (("Data Used", "data_used"), ("Model Monitoring", "monitoring"), ("Incident Handling", "incident_handling")),
        ):
            for column, (label, field) in zip(st.columns(3, gap="small"), fields):
                with column.container(border=True):
                    st.markdown(f"**{label}**")
                    st.write(system[field] or UNKNOWN)
    record_editor("ai_systems", [
        Field("owner"), Field("oversight", kind="area"), Field("privacy", kind="area"),
        Field("monitoring", kind="area"), Field("incident_handling", kind="area"), Field("governance_status"),
    ], key="asset_id", title_column="system", edit_only=True)
    st.subheader("AI risk assessment")
    risks = query("SELECT * FROM ai_risk_reviews ORDER BY rowid")
    for offset in range(0, len(risks), 3):
        for column, risk in zip(st.columns(3, gap="small"), risks[offset:offset + 3]):
            with column.container(border=True):
                st.markdown(f"**{risk['topic']}**")
                st.write(risk["crowd_prediction_review"])
                st.html(status_badge("Assessed" if risk["crowd_assessment"] else UNKNOWN))
    with st.expander("Review details for both AI systems"):
        table(risks)
    record_editor("ai_risk_reviews", [
        Field("crowd_assessment", kind="area"), Field("assistant_assessment", kind="area"),
    ], key="topic", edit_only=True)
    st.caption("Crowd-model inventory, incident procedure, measured performance and review approvals remain TODO.")


def automation_card():
    table([
        {"item": label, "design": value} for label, value in [
            ("IA phase", "Risk Assessment / Control Mapping"),
            ("Existing problem", "Manual risk, control and framework mapping takes analyst time."),
            ("Input", "Asset, threat, vulnerability, current controls, likelihood and impact."),
            ("AI method", "Local rule matching or optional LLM ranking with deterministic validation."),
            ("Processing", "Score the risk and map the scenario to existing PASS control packages and evidence needs."),
            ("Output", "Structured treatment, control, framework and evidence recommendations."),
            ("Human role", "A security analyst verifies recommendations. Authorized decision makers approve changes or risk decisions."),
            ("Security risks", "Hallucination, bias, data leakage, prompt injection, drift, over-reliance, explainability, availability and vendor risk."),
            ("Accuracy", "Compare the result against a human-reviewed reference for each test case."),
            ("Benefit", "Measure workload reduction through paired processing times."),
            ("Limitation", "The assistant provides advisory output. Approval and final assurance decisions belong to authorized humans."),
            ("Governance owner", "CISO / Risk & Compliance Committee"),
        ]
    ], height=470)


def assistant():
    analysis_tab, card_tab = st.tabs(["Risk & Control Analyzer", "AI Automation Card"])
    with analysis_tab:
        st.caption("Recommendations use the local PASS control catalog. Rule-based mode requires no external service.")
        assets = {row["id"]: row["name"] for row in query("SELECT id, name FROM assets ORDER BY id")}
        scopes = {
            f"scope:{row['scope']}": row["scope"]
            for row in query("SELECT DISTINCT scope FROM risks WHERE scope IS NOT NULL ORDER BY scope")
        }
        assets.update(scopes)
        controls = {row["id"]: row["name"] for row in query("SELECT id, name FROM controls ORDER BY id")}
        provider_ready = all(provider_settings())
        if not provider_ready:
            st.caption("External LLM is available after configuring its HTTPS endpoint, model and API key.")
        input_panel, output_panel = st.columns([1, 1.25], gap="medium")
        with input_panel:
            section("Risk Inputs")
        with input_panel.form("risk_analyzer"):
            mode = st.selectbox("Mode", ["Rule-based", "External LLM"] if provider_ready else ["Rule-based"])
            asset_id = st.selectbox("Asset or PASS scope", list(assets), format_func=assets.get)
            threat = st.text_input("Threat", max_chars=1500, placeholder="Example: privileged account theft")
            vulnerability = st.text_area("Vulnerability", max_chars=1500, placeholder="Example: weak MFA for administrators")
            existing = st.multiselect("Existing controls", list(controls), format_func=lambda key: f"{key} · {controls[key]}")
            left, right = st.columns(2)
            likelihood = left.select_slider("Likelihood", [1, 2, 3, 4, 5], value=3)
            impact = right.select_slider("Impact", [1, 2, 3, 4, 5], value=4)
            safe_input = st.checkbox("For external LLM mode, I confirm the input is synthetic or non-sensitive.") if provider_ready else False
            submitted = st.form_submit_button("Analyze risk", type="primary", width="stretch")
        if submitted:
            st.session_state.pop("last_analysis", None)
            if not threat.strip() or not vulnerability.strip():
                input_panel.error("Enter a threat and a vulnerability.")
            elif mode == "External LLM" and not safe_input:
                input_panel.error("Confirm that the input is safe to send to the configured external provider.")
            else:
                start = perf_counter()
                result = recommend(
                    asset_id, threat, vulnerability, existing, likelihood, impact, control_catalog(),
                    external=mode == "External LLM",
                )
                result["elapsed"] = perf_counter() - start
                result["asset"] = assets[asset_id]
                result["scenario"] = f"{assets[asset_id]}: {threat.strip()}"
                st.session_state["last_analysis"] = result
        with output_panel:
            section("AI Recommendation")
            result = st.session_state.get("last_analysis")
            st.warning(result["approval"] if result else NOTICE, icon=":material/verified_user:")
            if result:
                if result.get("provider_status"):
                    st.info(result["provider_status"])
                st.caption(f"{result['mode']} · {result['asset']} · {result['elapsed']:.3f} seconds analyzer processing time")
                a, b = st.columns(2, gap="small")
                with a:
                    kpi("Risk score", result["score"], "PASS 25-point scale")
                with b:
                    kpi("Risk level", result["level"], tone="critical" if result["level"] == "Critical" else "default")
                st.markdown(f"**Suggested treatment** — {result['treatment']}")
                st.write(result["explanation"])
                section("Recommended controls")
                if not result["controls"]:
                    empty_state("No matched controls", "Review the risk manually against the PASS catalog.")
                for row in result["controls"]:
                    with st.container(border=True):
                        st.markdown(f"**{row['control_id']} · {row['name']}**")
                        st.html(status_badge(row["status"] or UNKNOWN))
                        st.caption(f"Related risk {row['risk_id']} · {row['frameworks'] or UNKNOWN}")
                        st.write(f"Suggested evidence — {row['evidence_requirement'] or UNKNOWN}")
                st.caption("Authorized humans decide risk acceptance, compliance certification, critical control changes and final audit conclusions.")
            else:
                empty_state("Recommendation pending", "Enter a threat and vulnerability, then select Analyze risk.")
    with card_tab:
        st.subheader("AI Automation Card")
        automation_card()
        from services.project_exports import automation_pdf
        st.download_button("Download one-page Automation Card", automation_pdf(), "PASS_AI_Automation_Card.pdf", "application/pdf")


def ai_evaluation():
    st.caption("Save a draft, then reopen it to compare the result with the human reference and record a verdict.")
    rows = query("SELECT * FROM ai_evaluations ORDER BY id DESC")
    modes = ["Rule-based", "External LLM"]
    scope = st.selectbox("Results by mode", ["All modes", *modes])
    visible = rows if scope == "All modes" else [row for row in rows if row["mode"] == scope]
    verified = [row for row in visible if row["human_verified"]]
    a, b, c = st.columns(3)
    for column, label, value in (
        (a, "AI accuracy", ai_accuracy(visible)), (b, "Automation gain", evaluation_gain(visible)),
        (c, "Human verification rate", percentage(len(verified), len(visible))),
    ):
        with column:
            kpi(label, "Pending Evaluation" if value is None else number(value, "%"))
    st.write(
        f"{len(visible)} test cases recorded · {len(verified)} human verified · "
        f"{sum(row['false_positive'] for row in verified)} verified false positives · "
        f"{sum(row['false_negative'] for row in verified)} verified false negatives."
    )
    st.caption("Time both complete workflows using the same start and end points, including the assisted result's human review.")
    verdict_labels = {None: UNKNOWN, 1: "Correct", 0: "Incorrect"}
    table([
        {**row, "correct": verdict_labels[row["correct"]], "human_verified": bool(row["human_verified"])}
        for row in visible
    ], labels={"reference": "Human reference result", "correct": "Verdict"})
    if visible:
        st.caption(NOTICE)
    with st.expander("Add or edit a test result", expanded=True):
        index = {row["id"]: row for row in rows}
        if "saved_evaluation_id" in st.session_state:
            st.session_state["evaluation_record"] = st.session_state.pop("saved_evaluation_id")
        selected = st.selectbox("Evaluation record", [None, *index], key="evaluation_record", format_func=lambda value: (
            "New test case" if value is None else f"{value} · {index[value]['test_case']}"
        ))
        row = index.get(selected, {})
        key = f"evaluation_{selected}"
        last = st.session_state.get("last_analysis")
        if selected is None and last and st.button("Use last analyzer result"):
            references = ", ".join(row["control_id"] for row in last["controls"]) or "No matched control"
            st.session_state[f"{key}_case"] = last.get("scenario", last["asset"])
            st.session_state[f"{key}_result"] = (
                f'{last["score"]} ({last["level"]}). {last["treatment"]}. Controls: {references}. {last["explanation"]}'
            )
            st.session_state[f"{key}_mode"] = last["mode"]
        with st.form(key, clear_on_submit=False):
            case = st.text_input("Test case", value=row.get("test_case", ""), key=f"{key}_case")
            mode = st.selectbox("Mode", modes, index=modes.index(row.get("mode", modes[0])), key=f"{key}_mode")
            reference = st.text_area("Human reference result", value=row.get("reference", ""))
            ai_result = st.text_area("AI result", value=row.get("ai_result", ""), key=f"{key}_result")
            verdicts = list(verdict_labels.values())
            verdict = st.selectbox("Verdict", verdicts, index=verdicts.index(verdict_labels[row.get("correct")]))
            left, middle, right = st.columns(3)
            false_positive = left.checkbox("False positive", value=bool(row.get("false_positive")))
            false_negative = middle.checkbox("False negative", value=bool(row.get("false_negative")))
            human_verified = right.checkbox("Human verified", value=bool(row.get("human_verified")))
            reviewer = st.text_input("Reviewer", value=row.get("reviewer") or "")
            review_notes = st.text_area("Review notes", value=row.get("review_notes") or "")
            left, right = st.columns(2)
            manual = left.number_input("Manual processing time (seconds)", min_value=0.0, value=row.get("manual_seconds"))
            assisted = right.number_input("AI processing time (seconds)", min_value=0.0, value=row.get("ai_seconds"))
            submit = st.form_submit_button("Save test result", type="primary")
        if submit:
            if not case.strip():
                st.error("Enter the test case.")
            elif human_verified and (verdict == UNKNOWN or not reference.strip() or not ai_result.strip()):
                st.error("Verification needs a verdict, human reference and AI result.")
            elif human_verified and not reviewer.strip():
                st.error("Enter the human reviewer before marking this result verified.")
            elif (manual is None) != (assisted is None) or manual == 0:
                st.error("Enter both times with a positive manual time, or leave both blank.")
            elif verdict == "Correct" and (false_positive or false_negative):
                st.error("Use Incorrect if the result contains false positives or false negatives.")
            else:
                saved_id = save("ai_evaluations", {
                    "test_case": case.strip(), "mode": mode, "reference": reference.strip(), "ai_result": ai_result.strip(),
                    "correct": {"Correct": 1, "Incorrect": 0}.get(verdict), "false_positive": int(false_positive),
                    "false_negative": int(false_negative), "human_verified": int(human_verified),
                    "manual_seconds": manual, "ai_seconds": assisted, "reviewer": reviewer.strip() or None,
                    "review_notes": review_notes.strip() or None,
                }, existing=selected)
                st.session_state["saved_evaluation_id"] = saved_id
                st.session_state["saved_record"] = "Saved AI evaluation."
                st.rerun()

    from views.program import benchmark_view
    benchmark_view()
