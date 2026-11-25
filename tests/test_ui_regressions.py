"""Regressions for navigation, validation, lazy sections and shared theme."""
import re
import unittest
from pathlib import Path
from unittest.mock import patch

import test_app as original_app
from services.design_system import COLORS, PALETTE, native_theme


class InteractionRegressions(unittest.TestCase):
    setUp = original_app.AppTests.setUp
    go = original_app.AppTests.go
    widget = original_app.AppTests.widget

    def test_filtering_keeps_current_page_until_explicit_selection(self):
        self.go("Asset Register")
        self.app.sidebar.selectbox(key="workspace_filter").select("AI Automation").run()
        self.assertEqual(self.app.sidebar.radio[0].value, "Asset Register")
        self.assertIn("AI Evaluation", self.app.sidebar.radio[0].options)
        self.assertNotIn("Risk Register", self.app.sidebar.radio[0].options)
        self.app.sidebar.text_input(key="page_search").input("no-such-page").run()
        self.assertEqual(self.app.sidebar.radio[0].value, "Asset Register")
        self.assertTrue(any("No matching pages" in item.value for item in self.app.info))
        self.assertFalse(self.app.exception)

    def test_shortcut_navigates_and_clears_sidebar_filters(self):
        self.app.sidebar.selectbox(key="workspace_filter").select("Overview").run()
        self.widget("button", "Analyze a scenario").click().run()
        self.assertEqual(self.app.sidebar.radio[0].value, "AI Risk & Control Assistant")
        self.assertEqual(self.app.sidebar.selectbox(key="workspace_filter").value, "All pages")
        self.assertFalse(self.app.exception)

    def test_required_field_errors_preserve_other_inputs(self):
        self.go("Asset Register")
        self.assertEqual(self.widget("text_input", "Asset").label, "Asset (required)")
        self.widget("text_input", "Owner").input("Demo reviewer")
        self.widget("button", "Save record").click().run()
        self.assertTrue(any("Enter Asset before saving" in item.value for item in self.app.error))
        self.assertTrue(any("unique record ID" in item.value for item in self.app.error))
        self.assertEqual(self.widget("text_input", "Owner").value, "Demo reviewer")
        self.assertFalse(self.app.exception)

    def test_executive_overview_contains_all_required_sections(self):
        sections = [item.value for item in self.app.subheader]
        for title in ('Executive assurance overview', 'AI automation impact', 'Top 5 Risks', 'Priority control gaps', 'Top 5 Recommendations'):
            self.assertIn(title, sections)
        self.assertFalse(self.app.tabs)
        self.assertFalse(self.app.exception)

    def test_reruns_do_not_repeat_database_migrations(self):
        with patch("services.database.initialize", side_effect=AssertionError("Repeated migration")):
            self.app.run()
            self.go("Asset Register")
        self.assertFalse(self.app.exception)


class ThemeTests(unittest.TestCase):
    def test_native_theme_matches_shared_tokens(self):
        config = Path(__file__).resolve().parents[1] / ".streamlit/config.toml"
        self.assertEqual(config.read_text(), native_theme())
        css = (config.parents[1] / "views/styles.css").read_text()
        self.assertFalse(re.search(r"#[0-9a-fA-F]{3,8}\b", css))

    def test_text_contrast_pairs_meet_aa(self):
        def luminance(color):
            values = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
            linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
            return sum(v * w for v, w in zip(linear, (.2126, .7152, .0722)))
        pairs = [*(PALETTE.values()), (COLORS["canvas"], COLORS["accent"]),
                 (COLORS["canvas"], COLORS["muted"]), (COLORS["surface"], COLORS["muted"]),
                 (COLORS["sidebar"], COLORS["sidebar-muted"]),
                 (COLORS["sidebar-selected"], COLORS["sidebar-ink"]),
                 (COLORS["accent-soft"], COLORS["accent-ink"]),
                 (COLORS["accent"], COLORS["surface"])]
        for background, foreground in pairs:
            with self.subTest(background=background, foreground=foreground):
                low, high = sorted([luminance(background), luminance(foreground)])
                self.assertGreaterEqual((high + .05) / (low + .05), 4.5)
