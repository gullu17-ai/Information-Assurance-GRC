"""Match analyst inputs to documented PASS risk and control packages."""
import re

from services.calculations import risk_level, risk_score

NOTICE = "AI-assisted recommendation — Human verification required."
STOP_WORDS = set("and the for with from into when weak limited access system systems data risk security".split())


def words(value):
    return set(re.findall(r"[a-z0-9]{3,}", (value or "").lower())) - STOP_WORDS


def analyze(asset_id, threat, vulnerability, existing, likelihood, impact, catalog):
    score = risk_score(likelihood, impact)
    level = risk_level(score)
    scenario = words(f"{threat} {vulnerability}")
    candidates = []
    for row in catalog:
        if not row["applicable"]:
            continue
        matches = scenario & words(f'{row["threat"]} {row["event"]} {row["vulnerability"]}')
        same_asset = bool(asset_id and row["asset_id"] == asset_id)
        same_scope = bool(row["scope"] and f'scope:{row["scope"]}' == asset_id)
        if same_asset or same_scope or len(matches) >= 2:
            candidates.append((same_asset or same_scope, len(matches), row))
    candidates.sort(key=lambda item: (-item[0], -item[1], item[2]["control_id"]))
    existing = set(existing)
    choices = {}
    for _, _, row in candidates:
        if row["control_id"] not in existing:
            choices.setdefault(row["control_id"], row)
    reference = candidates[0][2] if candidates else None
    if reference and reference["treatment"]:
        treatment = reference["treatment"]
        rationale = f'Documented reference {reference["risk_id"]}. {reference["treatment_action"] or ""}'.strip()
    elif level in ("Critical", "High"):
        treatment = "Review mitigation options with the risk owner"
        rationale = "The scenario warrants priority treatment under the PASS risk bands."
    else:
        treatment = "Review and monitor with the risk owner"
        rationale = "The scenario needs owner review under the PASS risk bands."
    if not choices:
        rationale += " Review coverage with an analyst. No additional supported control package was matched."
    return {
        "score": score, "level": level, "treatment": treatment, "explanation": rationale,
        "choices": list(choices.values())[:6], "approval": NOTICE,
    }


def control_catalog():
    from services.database import query

    return query("""
        SELECT c.id AS control_id, c.name, c.frameworks, c.evidence_requirement, c.status, c.applicable,
               r.id AS risk_id, r.asset_id, r.scope, r.event, r.threat, r.vulnerability, r.treatment, r.treatment_action
        FROM risk_controls AS m JOIN controls AS c ON c.id = m.control_id JOIN risks AS r ON r.id = m.risk_id
        ORDER BY c.id, r.id
    """)
