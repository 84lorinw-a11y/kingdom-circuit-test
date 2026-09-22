from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "apply_test_redesign.py"
SPEC = importlib.util.spec_from_file_location("apply_test_redesign_production", MODULE_PATH)
assert SPEC and SPEC.loader
redesign = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = redesign
SPEC.loader.exec_module(redesign)


class ProductionRedesignModeTests(unittest.TestCase):
    def tearDown(self) -> None:
        redesign.configure_environment(False)

    def test_production_identity_uses_live_paths_and_indexing(self) -> None:
        redesign.configure_environment(True)
        self.assertEqual("/", redesign.TEST_BASE)
        self.assertEqual("production", redesign.DEPLOYMENT_ENVIRONMENT)
        self.assertEqual("index,follow", redesign.UPCOMING_PAGE_ROBOTS)
        self.assertEqual("noindex,follow", redesign.PAST_PAGE_ROBOTS)
        self.assertEqual("assets/live-redesign-manifest.json", redesign.MANIFEST_FILENAME)

    def test_generated_past_page_keeps_live_canonical_and_analytics(self) -> None:
        redesign.configure_environment(True)
        event = {
            "id": "manual:past-example",
            "title": "Past Example",
            "startDate": "2026-09-01",
            "venue": "Example Hall",
            "city": "Chicago",
            "state": "IL",
            "artists": ["Hulvey"],
        }
        with tempfile.TemporaryDirectory() as temp:
            site = pathlib.Path(temp)
            self.assertTrue(redesign.create_history_event_page(site, event))
            page = redesign.history_event_page(site, event).read_text(encoding="utf-8")
        self.assertIn('content="noindex,follow"', page)
        self.assertIn('rel="canonical" href="https://kingdomcircuit.com/event/', page)
        self.assertIn("G-N2KK9XF4TJ", page)
        self.assertNotIn("kingdom-circuit-test", page)
        self.assertNotIn("Kingdom Circuit Test", page)

    def test_instagram_favicon_overlay_is_test_only(self) -> None:
        inherited = '''<html><head><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"></head><body></body></html>'''
        redesign.configure_environment(False)
        test_page = redesign.inject_assets(inherited)
        self.assertNotIn("favicon.svg", test_page)
        self.assertIn("/kingdom-circuit-test/assets/favicon-kc-stacked-v2-48.png", test_page)
        self.assertIn("/kingdom-circuit-test/manifest.webmanifest", test_page)

        redesign.configure_environment(True)
        production_page = redesign.inject_assets(inherited)
        self.assertIn("/assets/favicon.svg", production_page)
        self.assertNotIn("favicon-kc-stacked-v2", production_page)


if __name__ == "__main__":
    unittest.main()
