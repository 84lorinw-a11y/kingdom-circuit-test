from __future__ import annotations

import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class PublishedSiteWorkflowTests(unittest.TestCase):
    def test_workflow_captures_the_deployed_site_instead_of_rebuilding_it(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "mirror-live.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("scripts/capture_live_site.py", workflow)
        self.assertIn('LIVE_SITE: https://kingdomcircuit.com', workflow)
        self.assertIn("_live_site _site", workflow)
        self.assertIn("--min-html 800", workflow)
        self.assertIn("--min-files 900", workflow)
        self.assertNotIn("Build the exact production artifact", workflow)
        self.assertNotIn("Pillow", workflow)
        self.assertNotIn("KC_MIRROR_DATE", workflow)

    def test_workflow_keeps_test_only_deployment_protections(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "mirror-live.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("test ! -e _site/CNAME", workflow)
        self.assertIn("test ! -e _site/run-status.json", workflow)
        self.assertIn("noindex,nofollow", workflow)
        self.assertIn("Disallow: /", workflow)

    def test_workflow_supplies_full_live_history_to_test_redesign(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "mirror-live.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn("event-history.json?ref=${LIVE_SHA}", workflow)
        self.assertIn("_live_source_event_history.json", workflow)
        self.assertIn("--source-history _live_source_event_history.json", workflow)
        self.assertIn('.events | type == "array"', workflow)


if __name__ == "__main__":
    unittest.main()
