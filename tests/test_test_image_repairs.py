from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import apply_test_image_repairs as repairs  # noqa: E402
import optimize_test_images as optimizer  # noqa: E402
import verify_test_image_repairs as verifier  # noqa: E402


CJ = repairs.CJ_EMULOUS_SOURCE
HULVEY = "https://s1.ticketm.net/dam/a/d4e/a49ecab3-089d-46ff-baa5-7942c994ed4e_SOURCE"


class TestImageRepairs(unittest.TestCase):
    def build_site(self, root: Path) -> Path:
        site = root / "site"
        (site / "config").mkdir(parents=True)
        (site / "event" / "sample").mkdir(parents=True)
        page = f'''<!doctype html><html><head><title>Test</title></head><body>
<article class="event-card" data-event-card><a class="event-media"><img class="event-artwork extra" src="{CJ}" style="color:red;object-position:center" width="1333" height="1333"></a></article>
<article class="event-card" data-event-card><a class="event-media"><img class="event-artwork" src="{HULVEY}" width="1600" height="900"></a></article>
</body></html>'''
        (site / "index.html").write_text(page, encoding="utf-8")
        (site / "event" / "sample" / "index.html").write_text(page, encoding="utf-8")
        events = [
            {"title": "CJ", "image": CJ, "imageType": "fallback", "imagePosition": "center"},
            {"title": "Hulvey", "image": HULVEY, "imageType": "event_artwork", "imagePosition": "center"},
        ]
        (site / "events.json").write_text(json.dumps(events), encoding="utf-8")
        (site / "supplemental-events.json").write_text(json.dumps(events), encoding="utf-8")
        (site / "config" / "artists.json").write_text("[]", encoding="utf-8")
        return site

    def test_overlay_is_scoped_idempotent_and_verifiable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            site = self.build_site(Path(raw))
            first = repairs.apply(site)
            first_html = (site / "index.html").read_text(encoding="utf-8")
            second = repairs.apply(site)
            second_html = (site / "index.html").read_text(encoding="utf-8")

            self.assertEqual(first_html, second_html)
            self.assertEqual(first["eventCardImagesSized"], 4)
            self.assertEqual(second["focalHtmlImagesNormalized"], 4)
            self.assertEqual(first_html.count("data-kc-test-image-overlay"), 1)
            self.assertIn(f'sizes="{repairs.CARD_SIZES}"', first_html)
            self.assertIn('class="extra artist-photo"', first_html)
            self.assertIn('data-kc-image-focal="cj-emulous"', first_html)
            self.assertIn('object-position:center top', first_html)
            self.assertIn('data-kc-image-focal="hulvey"', first_html)
            self.assertIn('object-position:50% 30%', first_html)

            values = json.loads((site / "events.json").read_text(encoding="utf-8"))
            self.assertEqual(values[0]["imageType"], "artist")
            self.assertEqual(values[0]["imagePosition"], "center top")
            self.assertEqual(values[1]["imageType"], "artist")
            self.assertEqual(values[1]["imagePosition"], "50% 30%")

            failures, report = verifier.verify(site)
            self.assertEqual(failures, [])
            self.assertEqual(report["focalHtmlImages"], {"cj-emulous": 2, "hulvey": 2})

    def test_optimizer_uses_1280_and_context_specific_sizes(self) -> None:
        self.assertEqual(optimizer.DEFAULT_WIDTHS, (320, 640, 960, 1280))
        with tempfile.TemporaryDirectory() as raw:
            site = Path(raw).resolve()
            source = site / "source.jpg"
            source.write_bytes(b"source-placeholder")
            source_value = "/kingdom-circuit-test/source.jpg"
            ref = optimizer.source_ref(source_value, site, repairs.TEST_BASE)
            self.assertIsNotNone(ref)
            assert ref is not None
            variants = tuple(
                optimizer.Variant(
                    width=width,
                    height=width,
                    filename=f"image-w{width}.webp",
                    url=f"/kingdom-circuit-test/assets/optimized/image-w{width}.webp",
                )
                for width in optimizer.DEFAULT_WIDTHS
            )
            result = optimizer.OptimizedImage("image", 1600, 1600, variants)
            html = f'<div class="event-media"><img class="artist-photo" src="{source_value}"></div>'
            rewritten, count, _, _, _ = optimizer.rewrite_html_page(
                html,
                site,
                repairs.TEST_BASE,
                "https://84lorinw-a11y.github.io",
                {ref.key: result},
            )
            self.assertEqual(count, 1)
            self.assertIn("1280w", rewritten)
            self.assertIn(f'sizes="{repairs.CARD_SIZES}"', rewritten)

    def test_focal_only_preparation_avoids_test_presentation_overlay(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            site = self.build_site(Path(raw))
            report = repairs.apply(site, focal_only=True)
            updated = (site / "index.html").read_text(encoding="utf-8")

            self.assertEqual(report["scope"], "focal-preparation")
            self.assertEqual(report["eventCardImagesSized"], 0)
            self.assertIn('data-kc-image-focal="cj-emulous"', updated)
            self.assertIn('data-kc-image-focal="hulvey"', updated)
            self.assertNotIn("data-kc-test-image-overlay", updated)
            self.assertNotIn(repairs.CARD_SIZES, updated)
            self.assertFalse((site / "assets" / repairs.CSS_NAME).exists())

    def test_target_guard_rejects_git_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            site = self.build_site(Path(raw))
            (site / ".git").mkdir()
            with self.assertRaises(SystemExit):
                repairs.apply(site)


if __name__ == "__main__":
    unittest.main()
