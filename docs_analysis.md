# PASS source analysis

PDF page numbers below count the cover. The project folder originally contained no `docs/`; the five explicitly attached PDFs were read in place. The course plan defines deliverables. Its example organizations, scores, audit values, and timings are illustrative. Assignments 1–3 supply the PASS baseline.

| Reference | Attached source | Coverage |
|---|---|---|
| A1 | Group 10 Assignment1 (1).pdf | 13 pages, PASS foundation |
| A2 | Assignment2_IA (1).pdf | 9 pages, PASS GRC, including embedded text panels |
| A3 | Assignment_03_PakArena_Group10.pdf | 11 pages, PASS resilience |
| A4 | IA_A4_23i2116-23i2127-23i2079.docx | 27 pages, independent third-party documentary audit of PASS |
| Plan | Assignments and Project plan -Information Assurance.pdf | 17 pages, course requirements |

## Organization and governance

A1 pp. 2–5 describes a hypothetical multipurpose stadium in Pakistan serving approximately 45,000 spectators with around 350 permanent staff and 1,200 temporary staff at peak. Services include digital tickets and gate validation, public Wi-Fi, event operations, venue safety and security, facilities/BMS, commerce/POS, and corporate functions. Ticketing, mobile services and analytics use cloud services. Vendors support ticketing, payments, internet and maintenance. The Board sets appetite and approves strategy, major investments and policies. The CEO/GM is accountable for operations and continuity. The CIO owns IT/cloud/networks, the CISO leads security/risk/response, Operations owns event delivery, Facilities/OT owns BMS and engineering, Physical Security owns CCTV and access procedures, Risk and Compliance reviews treatment and exceptions, Privacy oversees personal data, SOC monitors and investigates, system owners manage service needs, and vendors operate under contract. Internal Audit reports independently to senior leadership/the Board. Approved quantitative appetite and versioned PASS policies were not supplied.

## Assets and risk

A1 pp. 5–7 records A01 turnstiles, A02 online ticketing, A03 mobile app, A04 spectator database, A05 POS, A06 CCTV, A07 BMS, A08 IoT sensors, A09 internal network, A10 public Wi-Fi, A11 signage, A12 cloud, A13 IAM, A14 backup, A15 SOC/SIEM, and A16 crowd-prediction AI. Criticality is 1–5. A06 and A16 remain separate assets. The source does not have a standalone environment column. R11 (Core IT / Operations) and R13 (Third-Party Services) are cross-cutting scopes without a matching standalone asset ID. Mobile and public Wi-Fi have no dedicated risk row.

A1 pp. 6–11 uses ordinal likelihood and impact scales, each 1–5, and their product. Low is 1–4, Medium 5–9, High 10–16, Critical 17–25. The 16 scores and A2 pp. 3–5 treatment targets are summarized below. R10 reflects targeted admins and the reach of elevated accounts; R11 reflects multiple entry paths and correlated disruption; R12 reflects public-facing dependencies and the impact of personal-data loss. R04, R06, R13 and R14 each score 15 due to their wider operational or recovery impact.

| Risk | Event | L | I | Score | A2 treatment | Expected residual |
|---|---|---:|---:|---:|---|---:|
| R01 | Ticketing DDoS | 4 | 4 | 16 | Mitigate | 8 |
| R02 | Replayed QR tickets | 3 | 4 | 12 | Mitigate | 8 |
| R03 | POS malware | 3 | 4 | 12 | Mitigate | 8 |
| R04 | Guest network reaches internal systems | 3 | 5 | 15 | Mitigate | 10 |
| R05 | Unauthorized access to CCTV | 3 | 4 | 12 | Mitigate | 8 |
| R06 | BMS manipulation | 3 | 5 | 15 | Mitigate | 10 |
| R07 | False IoT data | 3 | 4 | 12 | Mitigate | 8 |
| R08 | Signage takeover | 3 | 3 | 9 | Routine monitoring and access control | TODO |
| R09 | Cloud exposure | 3 | 4 | 12 | Mitigate | 8 |
| R10 | Privileged account compromise | 4 | 5 | 20 | Mitigate | 10 |
| R11 | Ransomware disrupts stadium operations | 4 | 5 | 20 | Mitigate | 10 |
| R12 | Spectator data breach | 4 | 5 | 20 | Mitigate | 10 |
| R13 | Third-party compromise | 3 | 5 | 15 | Transfer / Mitigate | 10 |
| R14 | Backup compromise | 3 | 5 | 15 | Mitigate | 10 |
| R15 | Monitoring failure | 3 | 4 | 12 | Mitigate | 8 |
| R16 | Manipulated or drifted AI inputs | 3 | 4 | 12 | Mitigate | 8 |

Treatment targets are planning estimates. Residual likelihood and impact, verified residuals, named risk owners, acceptance decisions and lifecycle statuses are missing. Asset owners remain visible separately.

## Controls, compliance and audit

A2 pp. 5–8 defines 15 control packages (nine Partial, six Gap) and their evidence needs. Packages include DDoS/rate limiting, QR anti-replay, POS hardening, network segmentation/NAC, CCTV MFA, BMS remote access, IoT identity/encryption, cloud privilege/configuration, MFA/PAM/review, EDR/patching/backup, database access/encryption, vendor access, immutable backup/restore, SIEM alert validation and AI governance/model monitoring. The nine selected frameworks are NIST CSF, NIST RMF, ISO/IEC 27001, COBIT, CIS Controls, IEC 62443, NIST SP 800-82, NIST AI RMF, and PISF 2026. PISF appears explicitly against R11, R13 and R14. Formal clause text, clause-level applicability and evidence mapping are TODO. The heat map records four Partially Compliant, four Weak and one Non-Compliant area. The control matrix uses Partial/Gap rather than tested effectiveness. No operational logs, verified tests, certifications or pass rates were supplied.

A2 p. 8 has nine initial design findings and proposed tests covering privileged access, ransomware, network separation, CCTV, BMS, cloud, vendors, SIEM and AI. Evidence fields name requested artifacts. Source severity, action owner, target date, verified closure and quantified risk reduction are TODO. A2 suggests quarterly review of admin rights. The later A3 IAM design sets monthly privileged/admin review and quarterly permanent-employee review. The application retains the historical A2 recommendation and uses A3 for IAM policy.

## IAM and data

A3 pp. 4–6 defines User → Identity → Authentication → Authorization → Least Privilege → Monitoring. RBAC roles are Spectator, Event Staff, Security Staff, Stadium Operations, Facilities / OT Engineer, Finance / Commercial, SOC Analyst, IT Administrator, and Vendor / Contractor. Privilege uses separate admin accounts, restricted systems, authorized changes and SIEM logging. MFA applies to remote employee access, cloud/email/IAM administration, VPN, vendors, and privileged access even inside the network. Spectator MFA is stepped up for sensitive actions. Temporary access is reviewed before/after events, vendors before the access window and monthly for long contracts, leavers/dormant accounts are disabled immediately once confirmed. Vendors require a PASS sponsor, defined scope, expiry, MFA, approved gateway, and logging. The ABAC table expresses those contextual rules as policy conditions. Separate standard/admin accounts are documented. A formal incompatible-role matrix is TODO.

A3 pp. 6–7 defines Public (schedules/announcements, approved sharing), Internal (staff procedures and contacts on approved systems), Confidential (network diagrams/contracts/HR and incident notes, need-to-know and encryption when sent externally), Restricted (CCTV, access logs, payment documents, evidence and spectator information, encryption/logging/approved sharing/limited retention), and Critical (backup keys, BMS configuration, IAM/DR secrets, restricted privilege/MFA/encryption/monitoring and protected recovery copies). Exact retention periods and a complete per-dataset ownership register are TODO.

## Continuity, response and SOC

A3 pp. 7–8 records RTO/RPO for ten services. Turnstiles 15 min/5 min, spectator DB 30 min/15 min, internal network 30 min/4 hr config, employee IAM 30 min/15 min, CCTV 30 min/5 min, BMS 30 min/15 min, ticketing 1 hr/15 min, SIEM 1 hr/15 min, AI crowd prediction 2 hr/30 min, public Wi-Fi 8 hr/N/A. Outage impacts are in the BIA. Restoration groups are network/IAM/core security, gates/DB/event control, CCTV/BMS/operational monitoring, ticketing/POS, then AI/public Wi-Fi. SIEM has a recovery target, but no explicit standalone recovery sequence number. The design uses Primary → Replication → Backup → DR Site, with protected copies, monthly sample restores, at least two DR exercises per year and pre-event checks. Measured RTO/RPO, backup status, actual restore results, formal MTD and readiness scores are unavailable.

A3 pp. 9–11 models R11 ransomware on the morning of a sold-out match. Office endpoints, shared files and ticketing support are affected in the simulation. Turnstile/BMS impact must be checked. The seven stages cover preparation, detection, analysis, containment, eradication, recovery and lessons learned. The SOC correlates IAM and endpoint alerts, informs Stadium Operations, and coordinates investigation with IT, security and facilities. Endpoint, IAM, firewall, VPN, server and cloud logs support investigation. OT logging is conditional on safe availability. The proposed SOC can include human-reviewed SOAR workflows. Live SOC coverage, SOAR deployment and formal IR readiness are TODO.

## Emerging technology, maturity and roadmap

A1–A3 support cloud IAM least privilege and configuration review, secure key handling, network segregation of guest/staff/OT, constrained BMS vendor access, and IoT authentication, encryption and firmware management. IEC 62443 and NIST SP 800-82 are supported for OT, with zones/conduits and safe remote access. The proposed trust-boundary view is a synthesis. Cloud provider/responsibility matrix, detailed device lifecycle/firmware inventory, OT design validation and PQC dependency inventory are TODO. Existing supply-chain treatment R13 calls for reviews, contractual security clauses, limited access, logs and insurance where suitable. Supplier-by-supplier assessment is TODO.

A16 AI Video Analytics & Crowd Prediction is owned by Head of Physical Security / Data Science. Video/crowd signals support crowd monitoring, with human review of safety-related output, input validation, drift monitoring, inventory and model review proposed. A2 rates AI RMF Non-Compliant. Approved governance and model evaluation are TODO. The Plan requires reviewing hallucination, bias, data leakage, prompt injection, drift, over-reliance, explainability, availability and vendor risk. Applicability is contextual: hallucination and prompt injection primarily apply to the optional text assistant, and manipulated sensor/video input and drift apply to crowd prediction. These topics are assessment prompts until reviewed.

**Updated A4 source (22 November 2026):** The authoritative independent PASS audit is IA_A4_23i2116-23i2127-23i2079.docx, 27 pages, by Syed Ali Shah, Heba Hammad and Laiba Nasir. Its 13 findings and four control tests are imported with external provenance. The reported weighted score is 44.46/100, interpreted as Insufficient under its own scale. Date and conclusion inconsistencies are recorded under Submission & Coverage. The earlier Karobar.pk audit is superseded as a PASS source. A1-A3 register values remain preserved. Final-project documentary maturity scores use an explicit self-assessment rubric and remain subject to reviewer approval. Proposed roadmap and design supplements are identified separately from operating results. Eight scoped PISF paragraph mappings are sourced from the official 2026 framework; legal applicability remains dependent on entity scope.


## Implementation provenance

Seed row identifiers for controls, compliance, evidence and findings are application identifiers. Source references and explicit linkages preserve the distinction between source claims and local design. The evidence baseline includes only documentation references and requested artifacts. A newly entered mock artifact must be marked Simulated Evidence. The rule-based assistant reuses documented PASS treatments and control mappings. Automation accuracy and gain depend on actual human-verified evaluation entries.
