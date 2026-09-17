from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import test_cleanup_overlay as overlay  # noqa: E402


GENERIC_PAGE = """<!doctype html><html><head>
<meta property="og:image" content="https://example.test/assets/logo-wordmark.svg?v=1">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://example.test/assets/logo-wordmark.svg?v=1">
</head><body></body></html>"""

EVENT_PAGE = """<!doctype html><html><head>
<meta property="og:image" content="https://images.example.test/event.jpg">
<meta name="twitter:image" content="https://images.example.test/event.jpg">
</head><body></body></html>"""

LEGACY_CARD_PAGE = """<!doctype html><html><head>
<meta property="og:image" content="https://example.test/assets/social-preview.png">
<meta name="twitter:image" content="https://example.test/assets/social-preview.png">
</head><body></body></html>"""


class TestSocialPreview(unittest.TestCase):
    def test_overlay_installs_preview_and_preserves_specific_event_art(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            site = Path(raw)
            event_page = site / "event" / "sample" / "index.html"
            event_page.parent.mkdir(parents=True)
            legacy_page = site / "artists" / "sample" / "index.html"
            legacy_page.parent.mkdir(parents=True)
            (site / "index.html").write_text(GENERIC_PAGE, encoding="utf-8")
            event_page.write_text(EVENT_PAGE, encoding="utf-8")
            legacy_page.write_text(LEGACY_CARD_PAGE, encoding="utf-8")

            overlay.install_social_preview(site)
            updated = overlay.clean_static_html(site, set())
            overlay.verify(site, set())

            homepage = (site / "index.html").read_text(encoding="utf-8")
            event = event_page.read_text(encoding="utf-8")
            self.assertEqual(updated, 2)
            self.assertEqual(
                overlay.meta_content(homepage, "og:image"),
                overlay.SOCIAL_PREVIEW_URL,
            )
            self.assertEqual(overlay.meta_content(homepage, "og:image:width"), "1200")
            self.assertEqual(overlay.meta_content(homepage, "og:image:height"), "630")
            self.assertEqual(
                overlay.meta_content(homepage, "twitter:image:alt"),
                overlay.SOCIAL_PREVIEW_ALT,
            )
            self.assertEqual(
                overlay.meta_content(event, "og:image"),
                "https://images.example.test/event.jpg",
            )
            legacy = legacy_page.read_text(encoding="utf-8")
            self.assertEqual(
                overlay.meta_content(legacy, "og:image"),
                overlay.SOCIAL_PREVIEW_URL,
            )
            self.assertEqual(
                overlay.png_dimensions(site / overlay.SOCIAL_PREVIEW_REL),
                overlay.SOCIAL_PREVIEW_SIZE,
            )

            self.assertEqual(overlay.clean_static_html(site, set()), 0)


if __name__ == "__main__":
    unittest.main()
