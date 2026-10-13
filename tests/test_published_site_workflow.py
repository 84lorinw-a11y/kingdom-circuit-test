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

    def test_workflow_preserves_experiments_without_reapplying_global_redesign(self) -> None:
        workflow = (ROOT / ".github/workflows/mirror-live.yml").read_text()
        self.assertIn("python scripts/build_mobile_show_test.py _site --isolated", workflow)
        self.assertIn("python scripts/build_artist_intake_mockup.py _site", workflow)
        self.assertNotIn("python scripts/apply_test_redesign.py _site", workflow)
        self.assertNotIn("python scripts/finalize_artist_details.py _site\n", workflow)
        gate = workflow.index("python scripts/verify_live_baseline.py _live_site _site")
        self.assertGreater(gate, workflow.index("python scripts/build_artist_intake_mockup.py _site"))
        self.assertLess(gate, workflow.index("uses: actions/upload-pages-artifact"))

    def test_mobile_seo_overlay_is_test_only_and_runs_before_final_gate(self) -> None:
        workflow = (ROOT / ".github/workflows/mirror-live.yml").read_text()
        overlay = workflow.index("python scripts/mobile_seo_preview.py _site _live_site")
        self.assertLess(overlay, workflow.index("python scripts/verify_live_baseline.py _live_site _site"))
        self.assertGreater(overlay, workflow.index("python scripts/live_mirror_v2.py"))
        self.assertIn('scripts/mobile_seo_preview.py', workflow.split('schedule:')[0])


if __name__ == "__main__":
    unittest.main()
