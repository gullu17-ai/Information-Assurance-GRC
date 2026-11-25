"""PASS risk bands and evidence-based dashboard calculations."""
import re
from statistics import mean

UNKNOWN = "Not Yet Assessed"


def risk_score(likelihood, impact):
    if likelihood is None or impact is None:
        return None
    if any(type(value) is not int or not 1 <= value <= 5 for value in (likelihood, impact)):
        raise ValueError("Likelihood and impact must be integers from 1 to 5.")
    return likelihood * impact


def risk_level(score):
    if score is None:
        return UNKNOWN
    if not 1 <= score <= 25:
        raise ValueError("Risk score must be from 1 to 25.")
    if score <= 4:
        return "Low"
    if score <= 9:
        return "Medium"
    if score <= 16:
        return "High"
    return "Critical"


def percentage(numerator, denominator):
    return numerator / denominator * 100 if denominator else None


def compliance(requirements):
    applicable = [row for row in requirements if row["applicable"]]
    assessed = ("Compliant", "Partially Compliant", "Weak", "Non-Compliant")
    if not any(row["status"] in assessed for row in applicable):
        return None
    return percentage(sum(row["status"] == "Compliant" for row in applicable), len(applicable))


def pisf_clauses(requirements):
    return [
        row for row in requirements
        if row["framework"].strip().casefold() == "pisf 2026" and row["clause_ref"] and row["reference_source"]
    ]


def control_effectiveness(controls):
    applicable = [row for row in controls if row["applicable"]]
    if not any(row["effectiveness"] in ("Effective", "Ineffective") for row in applicable):
        return None
    return percentage(sum(row["effectiveness"] == "Effective" for row in applicable), len(applicable))


def target_minutes(target):
    """Normalize the supported PASS RTO and RPO units, including configuration RPO."""
    match = re.fullmatch(r"(\d+)\s+(min|hr)(?:\s+config)?", (target or "").strip(), re.IGNORECASE)
    if match is None:
        return None
    amount, unit = match.groups()
    return int(amount) * (60 if unit.lower() == "hr" else 1)


def recovery_outcome(service):
    if service["restore_result"] == "Failed":
        return "Restore failed"
    if service["restore_result"] != "Restored":
        return None
    rto = target_minutes(service["rto"])
    rpo = target_minutes(service["rpo"])
    rpo_exempt = (service["rpo"] or "").strip().upper() == "N/A"
    actual_rto = service["actual_rto_minutes"]
    actual_rpo = service["actual_rpo_minutes"]
    rto_missed = rto is not None and actual_rto is not None and actual_rto > rto
    rpo_missed = rpo is not None and actual_rpo is not None and actual_rpo > rpo
    if rto_missed or rpo_missed:
        return "Target missed"
    if rto is None or actual_rto is None or (not rpo_exempt and (rpo is None or actual_rpo is None)):
        return "Incomplete measurement"
    return "Targets met"


def recovery_readiness(outcomes):
    assessed = {"Targets met", "Target missed", "Restore failed"}
    if not any(outcome in assessed for outcome in outcomes):
        return None
    return percentage(outcomes.count("Targets met"), len(outcomes))


def maturity(scores):
    scores = list(scores)
    return mean(scores) if scores and all(score is not None for score in scores) else None


def ai_accuracy(evaluations):
    verified = [row for row in evaluations if row["human_verified"] and row["correct"] is not None]
    return percentage(sum(row["correct"] for row in verified), len(verified))


def automation_gain(manual_time, ai_time):
    if manual_time is None or ai_time is None or manual_time <= 0:
        return None
    return percentage(manual_time - ai_time, manual_time)


def evaluation_gain(evaluations):
    paired = [
        row for row in evaluations
        if row["human_verified"] and row["manual_seconds"] is not None and row["ai_seconds"] is not None
    ]
    return automation_gain(sum(row["manual_seconds"] for row in paired), sum(row["ai_seconds"] for row in paired))
