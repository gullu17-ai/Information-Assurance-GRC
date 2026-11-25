"""PASS Streamlit entry point."""
import streamlit as st

from services.database import default_path, initialize
from services.final_program import initialize_final
from views import program
from views import ai, assurance, registers
from views.dashboard import dashboard
from views.theme import apply_theme, page_header, sidebar_brand

PAGES = {
    "Executive Dashboard": dashboard,
    "Organization & Governance": assurance.governance,
    "Asset Register": registers.assets,
    "Risk Register": registers.risks,
    "Control Register": registers.controls,
    "Compliance Register": registers.compliance_register,
    "Evidence Register": registers.evidence,
    "Audit & Corrective Actions": assurance.audit,
    "IAM & Access Assurance": assurance.iam,
    "Data Protection": assurance.data_protection,
    "BC/DR": assurance.bcdr,
    "Incident Response": assurance.incidents,
    "SOC & Monitoring": assurance.soc,
    "Cloud / IoT / OT Security": assurance.infrastructure,
    "AI Governance": ai.ai_governance,
    "AI Risk & Control Assistant": ai.assistant,
    "Maturity & Roadmap": assurance.maturity_roadmap,
    "AI Evaluation": ai.ai_evaluation,
    "Submission & Coverage": program.completion,
}

GROUPS = {
    "Overview": ("Executive Dashboard", "Organization & Governance"),
    "GRC": ("Asset Register", "Risk Register", "Control Register", "Compliance Register", "Evidence Register", "Audit & Corrective Actions"),
    "Assurance": ("IAM & Access Assurance", "Data Protection", "BC/DR", "Incident Response", "SOC & Monitoring"),
    "Technology": ("Cloud / IoT / OT Security", "AI Governance"),
    "AI Automation": ("AI Risk & Control Assistant", "AI Evaluation"),
    "Strategy": ("Maturity & Roadmap",),
    "Supporting Material": ("Submission & Coverage",),
}
DESCRIPTIONS = {
    "Submission & Coverage": "Access submission exports, requirement coverage and supporting designs.",
    "Executive Dashboard": "CISO assurance overview · Enterprise Information Assurance, Risk & Compliance",
    "Organization & Governance": "Review PASS services, decision rights and assurance responsibilities.",
    "Asset Register": "Track PASS assets, their owners, criticality and linked risks.",
    "Risk Register": "Track identified risks, treatment decisions, residual exposure and ownership.",
    "Control Register": "Map controls to risks, frameworks and supporting evidence.",
    "Compliance Register": "Track framework requirements, assessment status and remediation gaps.",
    "Evidence Register": "Manage assurance evidence and trace it to controls and audit findings.",
    "Audit & Corrective Actions": "Review findings, corrective action owners and remediation progress.",
    "IAM & Access Assurance": "Review identity controls, role permissions and access reviews.",
    "Data Protection": "Review data classifications, handling requirements and key data flows.",
    "BC/DR": "Compare measured recovery results with PASS service targets.",
    "Incident Response": "Walk through the PASS ransomware scenario and response lifecycle.",
    "SOC & Monitoring": "Review proposed log coverage, alert triage and escalation.",
    "Cloud / IoT / OT Security": "Review trust boundaries, technical controls and vendor access.",
    "AI Governance": "Review oversight, privacy and risk for PASS video analytics and crowd prediction.",
    "AI Risk & Control Assistant": "Score a PASS risk and review recommended controls and evidence.",
    "AI Evaluation": "Compare analyzer results with human references and measure processing time.",
    "Maturity & Roadmap": "Assess assurance capabilities and track approved actions across three years.",
}


@st.cache_resource(show_spinner=False)
def initialize_database(path):
    """Migrate once per database/process; keep record reads fresh."""
    initialize(path)
    initialize_final()
    return path


def main():
    st.set_page_config(page_title="PASS Information Assurance & GRC Dashboard", layout="wide")
    initialize_database(str(default_path().resolve()))
    apply_theme(GROUPS)
    page_groups = {page: group for group, pages in GROUPS.items() for page in pages}
    if st.session_state.get("navigation") == "Program Completion":
        st.session_state["navigation"] = "Submission & Coverage"
    if "navigation" not in st.session_state:
        st.session_state["navigation"] = "Executive Dashboard"
    with st.sidebar:
        sidebar_brand()
        scope = st.selectbox("Workspace", ["All pages", *GROUPS], key="workspace_filter", help="Narrow navigation to a work area.")
        search = st.text_input("Find a page", placeholder="Search pages…", key="page_search")
        options = [page for page in page_groups if (scope == "All pages" or page in GROUPS[scope])
                   and search.casefold() in page.casefold()]
        current = st.session_state.get("navigation", "Executive Dashboard")
        if not options:
            st.info("No matching pages. Clear your search to see all pages. Your current page stays open.")
        if current not in options:
            options = [current, *options]
            st.caption("Current page kept above filtered results. Select a page to open it.")
        current = st.radio("Navigation", options, key="navigation", label_visibility="collapsed")
        st.caption("PASS / Academic simulation\n\nSource-backed assessments · Human-reviewed AI")
    executive = current == "Executive Dashboard"
    page_header(
        "Executive overview" if executive else current,
        page_groups[current], DESCRIPTIONS[current], executive=executive,
    )
    if message := st.session_state.pop("saved_record", None):
        st.success(message)
    PAGES[current]()


if __name__ == "__main__":
    main()
