import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from services.database import query
from services.policy_engine import NOTICE


class AppTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.enterContext(patch.dict(os.environ, {
            "PASS_DB_PATH": str(Path(temporary.name) / "test.sqlite3"),
            "PASS_LLM_API_KEY": "",
        }))
        self.app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "app.py")).run()

    def go(self, page):
        self.app.sidebar.radio[0].set_value(page).run()
        self.assertFalse(self.app.exception, [exception.message for exception in self.app.exception])

    def widget(self, kind, label):
        return next(widget for widget in getattr(self.app, kind) if widget.label.removesuffix(" (required)") == label)

    def test_all_required_pages_render(self):
        pages = self.app.sidebar.radio[0].options
        self.assertEqual(len(pages), 19)
        for page in pages:
            with self.subTest(page=page):
                self.go(page)
                self.assertTrue(self.app.title)
        self.go("Executive Dashboard")
        metrics = {metric.label: metric.value for metric in self.app.metric}
        self.assertEqual(metrics["High / Critical risks"], "15")
        self.assertEqual(metrics["Overall risk exposure"], "14.31 / 25")
        self.assertIn("16 assets | 16 risks | 12 High / 3 Critical", [c.value for c in self.app.caption])
        self.assertEqual(metrics["Compliance"], "0.0%")

    def test_asset_create_search_and_edit(self):
        self.go("Asset Register")
        self.widget("text_input", "Record ID").input("T-01")
        self.widget("text_input", "Asset").input("Test record")
        self.widget("text_input", "Type").input("Test type")
        self.widget("button", "Save record").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(query("SELECT name FROM assets WHERE id = 'T-01'"), [{"name": "Test record"}])
        self.widget("text_input", "Search register").input("Test record").run()
        self.assertEqual(len(self.app.dataframe[0].value), 1)
        self.widget("selectbox", "Record").select("T-01").run()
        self.widget("text_input", "Owner").input("Test owner")
        self.widget("button", "Save record").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(query("SELECT owner FROM assets WHERE id = 'T-01'"), [{"owner": "Test owner"}])

    def test_keyless_assistant_and_measured_evaluation(self):
        self.go("AI Risk & Control Assistant")
        self.widget("selectbox", "Asset or PASS scope").select("A13")
        self.widget("text_input", "Threat").input("Privileged account theft")
        self.widget("text_area", "Vulnerability").input("Weak MFA")
        self.widget("select_slider", "Likelihood").set_value(4)
        self.widget("select_slider", "Impact").set_value(5)
        self.widget("button", "Analyze risk").click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.app.warning[0].value, NOTICE)
        self.assertEqual(self.app.metric[0].value, "20")
        self.go("AI Evaluation")
        self.widget("button", "Use last analyzer result").click().run()
        self.widget("text_input", "Test case").input("Test fixture")
        self.widget("button", "Save test result").click().run()
        self.assertEqual(query("SELECT human_verified FROM ai_evaluations"), [{"human_verified": 0}])
        self.go("Executive Dashboard")
        self.go("AI Evaluation")
        self.widget("selectbox", "Evaluation record").select(1).run()
        self.assertIn("C10", self.widget("text_area", "AI result").value)
        self.widget("text_area", "Human reference result").input("R10 / C10")
        self.widget("selectbox", "Verdict").select("Correct")
        self.widget("checkbox", "Human verified").check()
        self.widget("text_input", "Reviewer").input("Test reviewer")
        self.widget("number_input", "Manual processing time (seconds)").set_value(10.0)
        self.widget("number_input", "AI processing time (seconds)").set_value(4.0)
        self.widget("button", "Save test result").click().run()
        self.assertFalse(self.app.exception)
        metrics = {metric.label: metric.value for metric in self.app.metric}
        self.assertEqual(metrics["AI accuracy"], "100.0%")
        self.assertEqual(metrics["Automation gain"], "60.0%")
        self.assertEqual(query("SELECT count(*) AS n FROM ai_evaluations"), [{"n": 1}])
        self.go("Executive Dashboard")
        self.assertEqual(self.widget("metric", "AI accuracy").value, "100.0%")

    def test_assessments_update_executive_dashboard(self):
        self.go("BC/DR")
        self.widget("text_input", "Record ID").input("TEST-RESTORE")
        self.widget("selectbox", "Service asset ID").select("A01")
        self.widget("date_input", "Test date").set_value(date(2026, 11, 1))
        self.widget("selectbox", "Restore result").select("Restored")
        self.widget("number_input", "Measured recovery time (minutes)").set_value(15.0)
        self.widget("number_input", "Measured data loss (minutes)").set_value(5.0)
        self.app.button[-1].click().run()
        self.assertFalse(self.app.exception)
        self.assertEqual(self.widget("metric", "BC/DR readiness").value, "10.0%")

        self.go("Control Register")
        self.widget("selectbox", "Record").select("C10").run()
        self.widget("selectbox", "Effectiveness").select("Effective")
        self.widget("text_area", "Assessment basis").input("Reviewed fixture access test.")
        self.widget("button", "Save record").click().run()
        self.assertFalse(self.app.exception)

        self.go("Compliance Register")
        for label, value in {
            "Record ID": "PISF-TEST", "Framework": "PISF 2026", "Requirement": "Fixture requirement",
            "Clause identifier": "Fixture clause", "Source and version": "Fixture reference",
        }.items():
            self.widget("text_input", label).input(value)
        self.widget("selectbox", "Assessment status").select("Compliant")
        self.widget("multiselect", "Mapped controls").select("C10")
        self.widget("button", "Save record").click().run()
        self.assertFalse(self.app.exception)

        self.go("Maturity & Roadmap")
        self.app.selectbox(key="maturity_scores_selected").select("IAM").run()
        self.widget("selectbox", "Score").select(3)
        self.widget("text_area", "Assessment basis").input("Fixture maturity review.")
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        self.widget("text_input", "Record ID").input("ACTION-TEST")
        self.widget("selectbox", "Roadmap year").select(1)
        self.widget("text_area", "Action").input("Fixture action")
        self.widget("selectbox", "Status").select("Complete")
        self.app.button[-1].click().run()
        self.assertFalse(self.app.exception)

        self.go("Executive Dashboard")
        for label, value in {
            "BC/DR readiness": "10.0%", "Control effectiveness": "6.7%", "Compliance": "0.0%",
            "IAM readiness": "3.0 / 5",
        }.items():
            self.assertEqual(self.widget("metric", label).value, value)

        self.assertFalse(self.app.exception)
        self.assertEqual(self.widget("metric", "PISF clause compliance").value, "11.1%")
        self.assertEqual(self.widget("metric", "Roadmap completion").value, "5.0%")
