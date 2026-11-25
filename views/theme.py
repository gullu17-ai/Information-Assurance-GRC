"""Presentation components shared by the Streamlit pages."""
from datetime import date
from html import escape
from pathlib import Path

import streamlit as st

from services.calculations import UNKNOWN

CSS = Path(__file__).with_name("styles.css")
STATUS_TONES = {
    "critical": "critical", "non-compliant": "critical", "overdue": "critical",
    "restore failed": "critical", "failed": "critical",
    "high": "warning", "weak": "warning", "gap": "warning", "open": "warning",
    "partially compliant": "warning", "partial": "warning", "target missed": "warning",
    "medium": "caution",
    "low": "positive", "compliant": "positive", "implemented": "positive", "effective": "positive",
    "verified": "positive", "completed": "positive", "complete": "positive", "closed": "positive",
    "assessed": "positive", "targets met": "positive", "restored": "positive",
    "planned": "info", "in progress": "info", "collected": "info",
}
from services.design_system import PALETTE, css_variables


def apply_theme(groups=None):
    st.html(f"<style>{css_variables()}{CSS.read_text(encoding='utf-8')}</style>")


def sidebar_brand():
    st.html("""
        <div class="pass-brand">
          <span class="pass-mark">PASS</span>
          <div><strong>PakArena Smart Stadium</strong><small>Information Assurance &amp; GRC</small></div>
        </div>
    """)


def navigate(page):
    st.session_state["navigation"] = page
    st.session_state["workspace_filter"] = "All pages"
    st.session_state["page_search"] = ""


def quick_link(label, page, *, key):
    st.button(label, key=key, width="stretch", on_click=navigate, args=(page,))


def page_header(title, group, description, *, executive=False):
    with st.container(key="pass_header"):
        st.title(title, anchor=False)
        if executive:
            st.caption("PakArena Smart Stadium / Academic simulation")
        st.html(f'<div class="pass-header-description">{escape(description)}</div>')


def section(title, detail=None):
    st.subheader(title, anchor=False)
    if detail:
        st.caption(detail)


def status_tone(value):
    normalized = str(value).strip().casefold()
    return STATUS_TONES.get(normalized, "neutral")


def status_badge(value):
    text = str(value)
    return f'<span class="pass-badge pass-tone-{status_tone(text)}">{escape(text)}</span>'


def kpi(label, value, detail=None, *, tone="default"):
    """Keep native metric values for accessibility and existing integrations."""
    with st.container(key=f"pass_metric_{tone}_{label}"):
        if value in (UNKNOWN, "Pending Evaluation", "Assessment Pending"):
            st.html(
                f'<div class="pass-missing"><span>{escape(label)}</span>{status_badge(value)}</div>'
            )
        else:
            st.metric(label, value, border=False)
        if detail:
            st.html(f'<div class="pass-metric-detail">{escape(detail)}</div>')


def kpis(*items):
    for column, (label, value, *detail) in zip(st.columns(len(items), gap="small"), items):
        with column:
            kpi(label, value, *detail)


def empty_state(title, detail):
    st.html(
        f'<div class="pass-empty"><strong>{escape(title)}</strong>'
        f'<p>{escape(detail)}</p></div>'
    )


def summary_table(headers, rows, *, badge_columns=()):
    if not rows:
        empty_state("No records", "Matching records will appear here when available.")
        return
    head = "".join(f'<th scope="col">{escape(label)}</th>' for label in headers)
    body = []
    for row in rows:
        cells = []
        for index, value in enumerate(row):
            text = UNKNOWN if value is None else str(value)
            content = status_badge(text) if index in badge_columns else escape(text)
            cells.append(f"<td>{content}</td>")
        body.append(f"<tr>{''.join(cells)}</tr>")
    st.html(
        f'<div class="pass-table-wrap" tabindex="0" role="region" aria-label="{escape(" / ".join(headers), quote=True)} table, scroll horizontally for more columns"><table class="pass-table"><thead><tr>{head}</tr></thead>'
        f"<tbody>{''.join(body)}</tbody></table></div>"
    )


def flow(*steps, vertical=False, boundary=None):
    classes = "pass-flow pass-flow-vertical" if vertical else "pass-flow"
    cards = "".join(
        f'<li class="{"pass-boundary" if step == boundary else ""}">{escape(step)}</li>' for step in steps
    )
    st.html(f'<ol class="{classes}">{cards}</ol>')


def bar_rows(rows, maximum, *, tone="info"):
    lines = []
    for label, value, display in rows:
        width = min(100, max(0, value / maximum * 100)) if value is not None and maximum else 0
        style = status_tone(label) if tone == "severity" else tone
        value_html = status_badge(display) if value is None else escape(str(display))
        lines.append(
            f'<div class="pass-bar-row"><span>{escape(str(label))}</span>'
            f'<div class="pass-track" aria-hidden="true"><i class="pass-fill-{style}" style="width:{width:.2f}%"></i></div>'
            f'<span>{value_html}</span></div>'
        )
    st.html(f'<div class="pass-bars">{"".join(lines)}</div>')


def action_status(row, today=None):
    """Display overdue dates without modifying the saved corrective-action status."""
    status = row["status"]
    if status in ("Closed", "Completed", "Complete"):
        return "Completed"
    if row.get("target_date"):
        try:
            due = date.fromisoformat(row["target_date"])
        except ValueError:
            return status
        if due < (today or date.today()):
            return "Overdue"
    return status
