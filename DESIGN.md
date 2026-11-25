---
name: PASS enterprise dashboard
description: Restrained navy and teal interface for source-backed stadium assurance.
---

## Overview
The approved direction is a light enterprise interface with navy navigation and teal actions, for an instructor demonstration on a laptop. It uses native Streamlit controls and retains the underlying assessment workflows.

## Colors
`services/design_system.py` is the normative token source. It generates CSS custom properties, dataframe status colors and `.streamlit/config.toml`. After editing colors, run `python -m services.design_system` and restart Streamlit. Do not add standalone hexadecimal values to component CSS.

The canvas and white surfaces support reading. Navy identifies navigation. Teal indicates actions and selection. Critical, warning, caution, positive and informational states retain distinct text labels as well as colors. This is a light theme; a complete dark theme has not been implemented or validated.

## Typography
Use the system UI stack. Main headings scale from 1.8rem to 2.6rem with -0.03em tracking; body and inputs use 1rem. Secondary text has a 0.875rem floor. Tables and numeric summaries use tabular numerals. Paragraphs are limited to 75 characters where applicable.

## Layout
The main container has a 1600px maximum. The sidebar is 18rem, capped at the viewport width. At 1100px, content columns wrap with a 17rem basis; below 700px, they stack. Tables remain semantic tables with labeled, focusable horizontal scroll regions. Avoid forcing whole-page horizontal scrolling.

## Elevation & Depth
Use surface color and a single border for structure. Do not combine shadows with borders on summary cards, or add thick colored edge accents.

## Shapes
Summary surfaces use 12px corners; buttons use 8px corners. Status labels use compact rounded capsules. Do not nest decorative cards.

## Components
Navigation uses native labeled radio controls with visible inputs, 44px minimum targets and explicit focus outlines. Filtering preserves the current page until another page is selected. Shortcuts clear filters before navigating.

Required form labels include `(required)`. Missing values produce errors below their inputs and a summary after submission, preserving entered values. Database validation remains authoritative.

Dashboard tabs track active state; only the selected section executes. Initialization is cached by resolved database path, but mutable assessment queries remain uncached to reflect saves immediately.

## Do's and Don'ts
Keep severity text alongside color. Preserve keyboard access and visible focus. Keep product facts, incomplete assessments and simulated evidence honest. Do not hide native inputs or add redundant eyebrow labels. Test 1366px laptop layouts, narrow viewports, 200% zoom, keyboard navigation and table scrolling in a browser before claiming full visual or accessibility validation.
