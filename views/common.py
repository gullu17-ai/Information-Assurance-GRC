"""Shared table rendering and explicit record forms."""
from dataclasses import dataclass
from datetime import date
import sqlite3

import pandas as pd
import streamlit as st

from services.calculations import UNKNOWN
from services.database import query, save
from views.theme import PALETTE, empty_state, flow, status_tone


def heading(column):
    return " ".join(
        token.upper() if token in {"id", "rto", "rpo", "ai", "iam"} else token.capitalize()
        for token in column.split("_")
    )


def table(rows, *, labels=None, missing=UNKNOWN, height="auto"):
    if not rows:
        empty_state("No matching records", "Records will appear here when available.")
        return
    frame = pd.DataFrame(rows, dtype=object)
    for column in frame:
        if frame[column].isna().any():
            frame[column] = frame[column].map(lambda value: missing if pd.isna(value) else str(value))
        else:
            frame[column] = frame[column].infer_objects()
    names = {column: (labels or {}).get(column, heading(column)) for column in frame}
    status_columns = {
        "status", "risk_level", "severity", "effectiveness", "assessment_evidence_status",
        "governance_status", "outcome", "restore_result", "correct", "display_status",
    }
    styled_columns = [names[column] for column in frame if column in status_columns]
    frame = frame.rename(columns=names)
    widths = {
        names[column]: st.column_config.Column(width=width)
        for column, width in {
            "id": "small", "risk_id": "small", "risk_score": "small", "severity": "small",
            "name": "medium", "risk_event": "large", "description": "large", "finding": "large",
            "status": "medium", "risk_level": "small", "owner": "medium", "source": "medium",
        }.items() if column in names
    }
    if styled_columns:
        frame = frame.style.map(_status_cell, subset=styled_columns)
    st.dataframe(frame, hide_index=True, width="stretch", height=height, column_config=widths, row_height=40)


def _status_cell(value):
    background, foreground = PALETTE[status_tone(value)]
    return f"background-color: {background}; color: {foreground}; font-weight: bold"


def show(sql, parameters=(), **kwargs):
    table(query(sql, parameters), **kwargs)


def number(value, suffix=""):
    return UNKNOWN if value is None else f"{value:.1f}{suffix}"


def filter_rows(rows, *facets, labels=None):
    columns = st.columns([2, *[1 for _ in facets]], gap="small") if facets else [st]
    phrase = columns[0].text_input("Search register", placeholder="Search records").strip().casefold()
    filters = {}
    for column, facet in zip(columns[1:], facets):
        options = sorted({row[facet] for row in rows if row[facet] is not None})
        filters[facet] = column.selectbox((labels or {}).get(facet, heading(facet)), [None, *options],
                                          format_func=lambda x: "All" if x is None else str(x))
    visible = [
        row for row in rows
        if (not phrase or any(phrase in str(value).casefold() for value in row.values()))
        and all(active is None or row[facet] == active for facet, active in filters.items())
    ]
    st.caption(f"{len(visible)} of {len(rows)} records")
    return visible


@dataclass(frozen=True)
class Field:
    key: str
    label: str = ""
    options: tuple | None = None
    kind: str = "text"
    required: bool = False


def record_editor(table_name, fields, *, key="id", title_column=None, links=(), edit_only=False,
                  label=None, validate=None):
    with st.expander(label or ("Edit record" if edit_only else "Add or edit record")):
        rows = query(f"SELECT * FROM {table_name} ORDER BY {key}")
        indexed = {row[key]: row for row in rows}
        options = list(indexed) if edit_only else [None, *indexed]
        selected = st.selectbox(
            "Record", options, key=f"{table_name}_selected",
            format_func=lambda choice: (
                "Add new record" if choice is None else
                f"{choice} · {indexed[choice][title_column]}" if title_column else str(choice)
            ),
        )
        row = indexed.get(selected, {})
        with st.form(f"{table_name}_{selected}"):
            st.caption("Fields marked (required) must be completed before saving.")
            values = {}
            error_slots = {}
            if selected is None and key == "id":
                values[key] = st.text_input("Record ID (required)", help="Use a unique ID, such as A17 or R17.").strip().upper() or None
                error_slots[key] = st.empty()
            for field in fields:
                field_label = field.label or heading(field.key)
                if field.required:
                    field_label += " (required)"
                value = row.get(field.key)
                if field.options is not None:
                    choices = list(field.options)
                    if value not in choices:
                        choices.append(value)
                    value = st.selectbox(field_label, choices, index=choices.index(value), format_func=_choice_label)
                elif field.kind == "bool":
                    value = int(st.checkbox(field_label, value=bool(row.get(field.key, 1))))
                elif field.kind == "area":
                    value = st.text_area(field_label, value=value or "").strip() or None
                elif field.kind == "date":
                    value = st.date_input(field_label, value=date.fromisoformat(value) if value else None)
                    value = value.isoformat() if value else None
                elif field.kind == "minutes":
                    value = st.number_input(field_label, value=value, min_value=0.0, step=0.1)
                else:
                    value = st.text_input(field_label, value=value or "").strip() or None
                values[field.key] = value
                if field.required:
                    error_slots[field.key] = st.empty()
            updates = []
            for link_table, parent_col, other_col, choices, label in links:
                prior = query(f"SELECT {other_col} FROM {link_table} WHERE {parent_col} = ?", (selected,))
                mapped = st.multiselect(label, choices, default=[item[other_col] for item in prior])
                updates.append((link_table, parent_col, other_col, mapped))
            submitted = st.form_submit_button("Save record", type="primary")
        if not submitted:
            return
        required = [field.label or heading(field.key) for field in fields if field.required and values[field.key] is None]
        for field in fields:
            if field.required and values[field.key] is None:
                error_slots[field.key].error(f"Enter {field.label or heading(field.key)} before saving.")
        if key == "id" and selected is None and not values[key]:
            required.append("Record ID")
            error_slots[key].error("Enter a unique record ID before saving.")
        if required:
            st.error("Enter " + ", ".join(required) + ".")
            return
        if selected is None:
            values["source"] = "Local entry"
        try:
            if validate:
                validate(values, row)
            save(table_name, values, key=key, existing=selected, links=updates)
        except sqlite3.IntegrityError:
            st.error("The record could not be saved. Check for duplicate IDs and complete related fields.")
        except ValueError as error:
            st.error(str(error))
        else:
            st.session_state["saved_record"] = f"Saved {table_name.replace('_', ' ')} record."
            st.rerun()


def _choice_label(value):
    return UNKNOWN if value is None else str(value)
