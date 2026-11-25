import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from services.ai_service import recommend
from services.calculations import (
    UNKNOWN, ai_accuracy, automation_gain, compliance, control_effectiveness, evaluation_gain,
    maturity, recovery_outcome, recovery_readiness, risk_level, risk_score,
)
from services.database import initialize, query, recovery_services, save
from services.policy_engine import NOTICE, control_catalog


class CalculationTests(unittest.TestCase):
    def test_risk_score(self):
        self.assertEqual(risk_score(4, 5), 20)
        self.assertIsNone(risk_score(None, 5))
        with self.assertRaises(ValueError):
            risk_score(6, 2)

    def test_pass_risk_classification(self):
        expected = {
            None: UNKNOWN, 1: "Low", 4: "Low", 5: "Medium", 9: "Medium",
            10: "High", 16: "High", 17: "Critical", 25: "Critical",
        }
        for score, level in expected.items():
            with self.subTest(score=score):
                self.assertEqual(risk_level(score), level)

    def test_compliance(self):
        rows = [
            {"applicable": 1, "status": "Compliant"},
            {"applicable": 1, "status": "Partially Compliant"},
            {"applicable": 1, "status": "Weak"},
            {"applicable": 1, "status": "Non-Compliant"},
            {"applicable": 0, "status": "Compliant"},
        ]
        self.assertEqual(compliance(rows), 25)
        self.assertIsNone(compliance([{"applicable": 1, "status": None}]))

    def test_control_effectiveness(self):
        rows = [
            {"applicable": 1, "effectiveness": "Effective"},
            {"applicable": 1, "effectiveness": None},
            {"applicable": 0, "effectiveness": "Effective"},
        ]
        self.assertEqual(control_effectiveness(rows), 50)
        self.assertIsNone(control_effectiveness(rows[1:]))

    def test_maturity(self):
        self.assertEqual(maturity([2, 3, 4]), 3)
        self.assertIsNone(maturity([2, None, 4]))

    def test_recovery_target_units_and_exempt_rpo(self):
        network = dict(rto="30 min", rpo="4 hr config", restore_result="Restored",
                       actual_rto_minutes=30, actual_rpo_minutes=240)
        self.assertEqual(recovery_outcome(network), "Targets met")
        self.assertEqual(recovery_outcome({**network, "actual_rpo_minutes": 241}), "Target missed")
        self.assertEqual(recovery_outcome({**network, "actual_rpo_minutes": None}), "Incomplete measurement")
        self.assertEqual(recovery_outcome({**network, "rpo": "N/A", "actual_rpo_minutes": None}), "Targets met")
        self.assertIsNone(recovery_readiness([None, "Incomplete measurement"]))

    def test_automation_gain(self):
        self.assertEqual(automation_gain(10, 4), 60)
        self.assertEqual(automation_gain(10, 12), -20)
        self.assertIsNone(automation_gain(0, 0))

    def test_ai_accuracy_and_paired_times_use_verified_results(self):
        rows = [
            {"human_verified": 1, "correct": 1, "manual_seconds": 60, "ai_seconds": 30},
            {"human_verified": 1, "correct": 0, "manual_seconds": 40, "ai_seconds": 30},
            {"human_verified": 0, "correct": 1, "manual_seconds": 60, "ai_seconds": 0},
        ]
        self.assertEqual(ai_accuracy(rows), 50)
        self.assertEqual(evaluation_gain(rows), 40)
        self.assertIsNone(ai_accuracy(rows[2:]))


class PassDatabaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "test.sqlite3"
        self.enterContext(patch.dict(os.environ, {"PASS_DB_PATH": str(self.path)}))
        initialize()

    def test_readiness_uses_latest_dated_attempt_even_if_it_failed(self):
        save("recovery_tests", {
            "id": "NEWER", "asset_id": "A01", "tested_on": "2026-11-02", "restore_result": "Failed",
        })
        save("recovery_tests", {
            "id": "OLDER", "asset_id": "A01", "tested_on": "2026-11-01", "restore_result": "Restored",
            "actual_rto_minutes": 10, "actual_rpo_minutes": 0,
        })
        outcomes = [recovery_outcome(service) for service in recovery_services()]
        self.assertEqual(outcomes.count("Restore failed"), 1)
        self.assertEqual(recovery_readiness(outcomes), 0)

    def test_sqlite_initialization_source_counts_and_idempotency(self):
        for table, count in {
            "assets": 16, "risks": 16, "controls": 15, "risk_controls": 15, "compliance_requirements": 9,
            "evidence": 15, "audit_findings": 9, "iam_roles": 9, "bcdr_services": 10,
            "maturity_scores": 10, "roadmap": 3, "ai_evaluations": 0, "risk_rationales": 16,
            "data_items": 22, "ai_risk_reviews": 9,
        }.items():
            with self.subTest(table=table):
                self.assertEqual(query(f"SELECT count(*) AS n FROM {table}")[0]["n"], count)
        self.assertEqual(query("PRAGMA foreign_key_check"), [])
        save("assets", {"owner": "Test edit"}, existing="A01")
        initialize()
        self.assertEqual(query("SELECT owner FROM assets WHERE id = 'A01'")[0]["owner"], "Test edit")
        self.assertEqual(query("SELECT rto, rpo FROM bcdr_services WHERE asset_id = 'A01'"), [{"rto": "15 min", "rpo": "5 min"}])
        self.assertEqual(query("SELECT score FROM maturity_scores WHERE score IS NOT NULL"), [])
        risks = query("SELECT likelihood, impact, residual_target FROM risks ORDER BY id")
        self.assertEqual(
            [risk_score(row["likelihood"], row["impact"]) for row in risks],
            [16, 12, 12, 15, 12, 15, 12, 9, 12, 20, 20, 20, 15, 15, 12, 12],
        )
        self.assertEqual(
            [row["residual_target"] for row in risks],
            [8, 8, 8, 10, 8, 10, 8, None, 8, 10, 10, 10, 10, 10, 8, 8],
        )

    def test_register_links_roll_back_with_invalid_foreign_key(self):
        with self.assertRaises(sqlite3.IntegrityError):
            save("controls", {"name": "Test edit"}, existing="C10", links=[
                ("risk_controls", "control_id", "risk_id", ["NOT-A-RISK"]),
            ])
        self.assertEqual(query("SELECT risk_id FROM risk_controls WHERE control_id = 'C10'"), [{"risk_id": "R10"}])
        self.assertEqual(query("SELECT name FROM controls WHERE id = 'C10'")[0]["name"], "MFA, PAM and access review")

    def test_keyless_ai_and_exclusion_of_existing_controls(self):
        with patch.dict(os.environ, {"PASS_LLM_API_KEY": ""}):
            result = recommend("A13", "Privileged account theft", "Weak MFA and password reuse", [], 4, 5, control_catalog())
        self.assertEqual((result["score"], result["level"], result["mode"]), (20, "Critical", "Rule-based"))
        self.assertEqual(result["controls"][0]["control_id"], "C10")
        self.assertEqual(result["approval"], NOTICE)
        result = recommend("A13", "Privileged account theft", "Weak MFA", ["C10"], 4, 5, control_catalog())
        self.assertNotIn("C10", [row["control_id"] for row in result["controls"]])

    def test_external_failure_falls_back_to_local_result(self):
        with patch("services.ai_service.provider_rank", side_effect=URLError("test failure")):
            result = recommend("A13", "Privileged account theft", "Weak MFA", [], 4, 5, control_catalog(), external=True)
        self.assertEqual(result["mode"], "Rule-based")
        self.assertIn("provider_status", result)

    def test_external_mode_rejects_invented_ids(self):
        response = {"choices": [{"message": {"content": json.dumps({"control_ids": ["C999"]})}}]}
        with (
            patch("services.ai_service.provider_settings", return_value=("https://example.invalid/chat", "test", "test-key")),
            patch("services.ai_service.build_opener") as opener,
        ):
            opener.return_value.open.return_value.__enter__.return_value.read.return_value = json.dumps(response).encode()
            result = recommend("A13", "Privileged account theft", "Weak MFA", [], 4, 5, control_catalog(), external=True)
        self.assertEqual(result["mode"], "Rule-based")
        self.assertEqual(result["controls"][0]["control_id"], "C10")
