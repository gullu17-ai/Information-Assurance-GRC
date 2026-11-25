# Dashboard cleanup - 23 November 2026

The Executive Dashboard now presents all required indicators in one overview. Submission & Coverage is last in navigation. AI benchmark and Trust Score appear in AI Evaluation. Report downloads have no duplicate metrics. Open corrective actions count external findings, and untested control effectiveness is unassessed in both app and PDF. Documentary maturity/readiness labels are explicit. Developer notes are under docs/developer. The launcher installs missing requirements even when a virtual environment already exists. All 33 tests pass.

# Final submission update - 22 November 2026

Open Submission & Coverage to review all 27 required areas, source traceability, expanded test plan, dependency-aware BIA and supplier assessments. Audit & Corrective Actions includes the independent PASS audit with 13 findings. The Executive Dashboard exports a one-page CISO PDF. The submission folder includes the final report, one-page AI Automation Card and integrated CSV registers.

The project contains a design and functioning prototype. Documentary maturity is explicitly self-assessed; external audit findings remain open until verified closure. No human-reviewed AI timing data were supplied, so measured end-to-end automation gain and human trust accuracy remain pending. The 18-case automated benchmark is labeled separately.

Start-PASS.cmd (Windows) or Start-PASS.ps1 installs the requirements into a local virtual environment on first launch. To reuse a newer database, make a backup and set PASS_DB_PATH to its path before starting. The app adds final-program tables and preserves existing reviewed entries.

The authoritative A4 is now the independent PASS audit IA_A4_23i2116-23i2127-23i2079.docx. The following original implementation notes describe the historical baseline; final-program additions and updated provenance are documented in DESIGN.md, docs_analysis.md and docs/README.md.

# PASS Information Assurance & GRC Dashboard

A local university capstone for PakArena Smart Stadium (PASS), a hypothetical multipurpose venue in Pakistan. It integrates source-backed governance, security risk, control design, compliance, audit and resilience information. Its AI-assisted analyzer helps a security analyst choose which existing PASS controls and evidence to review.

PASS serves approximately 45,000 spectators and has around 350 permanent staff and 1,200 temporary event staff at peak. Its assurance scope covers cloud ticketing and mobile services, gate entry, payments, CCTV, IoT, building management, identity, backup, SOC/SIEM and AI crowd prediction.

## Run in VS Code

Use Python 3.11 or newer. Open the project folder in VS Code and select `.venv\Scripts\python.exe` with **Python: Select Interpreter** after creating the environment. Run these commands in PowerShell from the project root.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m services.database
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

Open http://127.0.0.1:8501. If a local process is using that port, append `--server.port 8502`. The app initializes the SQLite database on first run and adds assessment tables and fields to existing databases in place. Baseline imports are transactional and subsequent starts preserve edits. The default file is `data/pass.sqlite3`. Set `PASS_DB_PATH` to a different file for an independent demo or a clean baseline.

## Architecture and sources

Streamlit renders the dashboard, registers, assurance views, and evaluation forms. Pandas formats tabular views. SQLite stores register rows, links, maturity assessments, roadmap activities and AI evaluations. Python functions calculate metrics and map inputs to the local control catalog.

| Source | Application modules |
|---|---|
| Assignment 1 | Organization and reporting, 16 assets, 16 inherent risks, scoring bands and rating rationale |
| Assignment 2 | Treatment and residual targets, 15 control packages, framework selection, PISF links, compliance heat map, evidence requests, nine initial findings and corrective recommendations |
| Assignment 3 | RBAC and contextual access policies, MFA and reviews, data classes, BIA and recovery targets, ransomware response and monitoring sources |
| Assignment 4 attachment | Independent PASS documentary audit with 13 findings, four tests and a 44.46/100 weighted score. |
| Course project plan | Final deliverables, maturity dimensions, roadmap phase names, automation card and evaluation requirements |

```text
app.py                         Streamlit entry point and 19-page navigation
views/                         Dashboard, registers, assurance and AI workflows
services/
  schema.sql                   SQLite tables and relationships
  database.py                  Seed import, transactions and CRUD
  calculations.py              Risk, compliance, effectiveness, maturity and AI metrics
  policy_engine.py             Local PASS risk/control matching
  ai_service.py                 Optional provider adapter and response validation
data/
  seed/                        Provenance-tagged baseline JSON
  pass.sqlite3                 Generated local database
docs/                          Source location note
docs_analysis.md               Source extraction, gaps and conflicts
tests/                         Unit, database and Streamlit workflow tests
requirements.txt
.env.example
```

## Calculations

- **Inherent and assessed residual risk** multiply likelihood by impact on the A1 five-point scales. PASS bands are 1–4 Low, 5–9 Medium, 10–16 High and 17–25 Critical. The A2 expected residual targets are displayed separately.
- **Inherent risk exposure** averages all stored inherent scores. The dashboard ranks risks by score, impact, then ID. It ranks Gap controls by their highest linked inherent score. A critical control gap is an applicable control marked Gap with a linked Critical risk.
- **Compliance** is 100 × compliant applicable entries ÷ all applicable entries in each scope. The framework-area KPI starts at zero of nine compliant A2 areas. The separate PISF KPI uses only entered PISF 2026 clauses with a clause identifier and source. Partial, Weak, Non-Compliant and blank statuses receive zero credit. A scope with no assessed applicable entries displays Not Yet Assessed. The PISF percentage reflects entered scope only.
- **Control effectiveness** is 100 × applicable controls marked Effective ÷ all applicable controls. Enter the operating test or evidence behind a new verdict. The dashboard shows assessment coverage alongside the KPI. The KPI stays Not Yet Assessed until the first applicable verdict.
- **Governance maturity** averages all ten scored dimensions and remains Not Yet Assessed while any are missing. IAM, incident response and OT readiness show individual maturity dimensions. AI governance readiness scales its assessed dimension from five points to ten.
- **BC/DR readiness** is 100 × services that met their targets in their latest dated test ÷ all registered recovery services. A failed restore or a missed applicable target earns no credit. RPO is excluded for a service with an explicit N/A target. When no result can be assessed, the KPI stays Not Yet Assessed.
- **Roadmap completion** is 100 × complete actions ÷ all recorded actions. The KPI stays Not Yet Assessed until an action has a status. **Assessed residual exposure** averages risks with entered residual likelihood and impact. The dashboard displays assessment coverage for both.
- **AI accuracy** is 100 × correct recommendations ÷ human-verified cases with a verdict. **Automation gain** is 100 × (total manual time − total AI-assisted time) ÷ total manual time over verified cases with paired times. A negative value means the AI-assisted workflow took longer. Count verification separately and use equivalent start/end points when timing both workflows.

## Viva demonstration

1. Open the Executive Dashboard and trace the top three Critical risks to the Risk Register. Verify one product and inspect its expected residual target.
2. Filter or add an Asset Register entry. Trace R10 → C10 → E10 → F01 and read the corrective recommendation. Compare A2's quarterly admin-review recommendation with the later A3 monthly privileged-review policy.
3. Review the Assignment 2 PISF mapping, then enter a confirmed clause under **Compliance Register** with its source, control links, evidence and status. Record a control test verdict in **Control Register**. In **BC/DR**, enter a dated recovery result and compare measured time and loss to the 15-minute gate RTO and five-minute gate RPO.
4. In **AI Risk & Control Assistant**, choose A13 Employee Identity & Access System, use `Privileged account theft` and `Weak MFA and password reuse`, and set likelihood 4 and impact 5. Compare the 20 Critical score, C10 recommendation, framework names and evidence requirements with the source registers. Open the **AI Automation Card** tab.
5. In **AI Evaluation**, save the analyzer result as a draft. Reopen it, compare it with a human reference, record the actual verdict and paired end-to-end times, and mark the case human verified.
6. In **Maturity & Roadmap**, record reviewed PASS scores with their basis and enter approved actions under the three phases. Return to the executive dashboard to see coverage and the calculated KPIs. Use a separate database for practice entries.

## Optional external LLM

Rule-based mode works offline. External mode ranks up to three of the locally matched PASS control IDs using an HTTPS chat-completions-compatible endpoint. Scoring and catalog lookup always run locally. Configure process variables as documented in `.env.example` before launching Streamlit.

```powershell
$env:PASS_LLM_URL = 'https://your-provider.example/v1/chat/completions'
$env:PASS_LLM_MODEL = 'your-model'
$env:PASS_LLM_API_KEY = Read-Host 'Provider API key'
```

The external provider receives the selected asset/scope ID, supplied threat and vulnerability text, and candidate control IDs and names. Use synthetic or non-sensitive inputs and a vetted provider. The app validates returned IDs against the candidate list, rejects redirects, and falls back to the rule-based result on provider failure. Every recommendation requires human verification. Risk acceptance, certification, critical control changes and final audit conclusions belong to authorized reviewers.

## Limitations and outstanding source work

- The local demo assumes a trusted workstation and loopback binding. The IAM design represents stadium access rules. The demo has no application login, role enforcement or tamper-evident audit log.
- The assignments describe an assurance baseline and proposed architecture. Evidence rows begin as requests. Label any added mock artifact **Simulated Evidence**. Source design findings and treatment targets require operating tests before they can support final assurance conclusions.
- A PASS-specific third-party Assignment 4 has now been integrated. Reviewer sign-off on documentary maturity and proposed roadmap actions remains required. Confirm official PISF clause text, assessed control effectiveness, verified residual scores, operational recovery results, vendor-specific assessments and AI evaluation results. See `docs_analysis.md` for the complete source gap list.

## Run tests

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The suite exercises calculations, the baseline and SQLite relationships, keyless analysis and provider-response validation, all 19 pages, and representative register and evaluation workflows. Test records use temporary SQLite files.
