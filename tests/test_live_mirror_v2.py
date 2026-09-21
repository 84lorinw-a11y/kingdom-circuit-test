from __future__ import annotations

import importlib.util
import json
import pathlib
import tempfile
import unittest


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "live_mirror_v2.py"
SPEC = importlib.util.spec_from_file_location("live_mirror_v2", SCRIPT)
assert SPEC and SPEC.loader
mirror = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mirror)


class ExactLiveMirrorTests(unittest.TestCase):
    def make_live_fixture(self, root: pathlib.Path) -> pathlib.Path:
        live = root / "live"
        (live / "assets").mkdir(parents=True)
        (live / "config").mkdir(parents=True)
        (live / "artists" / "petrina-delacey").mkdir(parents=True)

        html = (
            '<html><head><meta name="robots" content="index,follow">'
            '<link rel="canonical" href="https://kingdomcircuit.com/">'
            '<script src="/app.js"></script>'
            '<script>gtag("config","G-N2KK9XF4TJ")</script></head>'
            '<body><a href="/artists/petrina-delacey/">Petrina DeLacey</a>'
            '<img src="/assets/petrina.jpg"></body></html>'
        )
        (live / "index.html").write_text(html, encoding="utf-8")
        (live / "artists" / "petrina-delacey" / "index.html").write_text(
            html,
            encoding="utf-8",
        )
        (live / "app.js").write_text(
            'const BASE = "/";\n'
            'const LIVE_EVENTS_URL = `${BASE}events.json`;\n'
            'const LIVE_ARTISTS_URL = `${BASE}config/artists.json`;\n',
            encoding="utf-8",
        )
        (live / "styles.css").write_text("body{color:#fff}\n", encoding="utf-8")
        (live / "seo-static.js").write_text(
            'const fallback = "/assets/event-fallback.webp";\n',
            encoding="utf-8",
        )
        (live / "seo-enhancements.js").write_text("\n", encoding="utf-8")
        (live / "robots.txt").write_text(
            "User-agent: *\nAllow: /\nSitemap: https://kingdomcircuit.com/sitemap.xml\n",
            encoding="utf-8",
        )
        (live / "sitemap.xml").write_text(
            "<loc>https://kingdomcircuit.com/</loc>\n",
            encoding="utf-8",
        )
        (live / "CNAME").write_text("kingdomcircuit.com\n", encoding="utf-8")
        (live / "assets" / "petrina.jpg").write_bytes(b"official-image-bytes")

        data = {
            "artwork-audit.json": [],
            "events.json": [{"artists": ["Petrina DeLacey"]}],
            "supplemental-events.json": [],
            "run-status.json": {"ok": True},
            "config/artists.json": [
                {"name": "Petrina DeLacey"},
                {"name": "BIG HOLY"},
            ],
            "sep12-closeout-report.json": {"ok": True},
            "seo-build-manifest.json": {"mode": "production-indexable"},
            "seo-indexing-policy.json": {"mode": "production"},
            "seo-overlay-manifest.json": {"mode": "production-seo-overlay-v1"},
        }
        for relative, payload in data.items():
            path = live / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        return live

    def test_preserves_content_and_only_changes_test_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            live = self.make_live_fixture(root)
            test = root / "test"
            test.mkdir()

            mirror.write_test_copy(live, test)
            result = mirror.verify_exact_mirror(live, test)

            self.assertGreaterEqual(result["htmlPageCount"], 2)
            self.assertFalse((test / "CNAME").exists())
            for relative in mirror.OMITTED_REPORT_FILES:
                self.assertFalse((test / relative).exists(), relative)
            self.assertEqual(
                (test / "assets" / "petrina.jpg").read_bytes(),
                (live / "assets" / "petrina.jpg").read_bytes(),
            )
            self.assertEqual(
                (test / "config" / "artists.json").read_bytes(),
                (live / "config" / "artists.json").read_bytes(),
            )
            home = (test / "index.html").read_text(encoding="utf-8")
            self.assertIn('content="noindex,nofollow"', home)
            self.assertIn("/kingdom-circuit-test/assets/petrina.jpg", home)
            self.assertIn(
                "https://84lorinw-a11y.github.io/kingdom-circuit-test/",
                home,
            )
            self.assertNotIn("G-N2KK9XF4TJ", home)
            helper = (test / "seo-static.js").read_text(encoding="utf-8")
            self.assertIn("/kingdom-circuit-test/assets/event-fallback.webp", helper)

    def test_omits_operational_reports_without_changing_runtime_data(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            live = self.make_live_fixture(root)
            test = root / "test"
            test.mkdir()

            mirror.write_test_copy(live, test)
            mirror.verify_exact_mirror(live, test)

            self.assertEqual(
                (test / "events.json").read_bytes(),
                (live / "events.json").read_bytes(),
            )
            self.assertEqual(
                (test / "config" / "artists.json").read_bytes(),
                (live / "config" / "artists.json").read_bytes(),
            )
            self.assertTrue(mirror.OMITTED_REPORT_FILES)
            self.assertFalse((test / "run-status.json").exists())
            self.assertTrue(
                all(not (test / relative).exists() for relative in mirror.OMITTED_REPORT_FILES)
            )

    def test_verifier_rejects_content_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            live = self.make_live_fixture(root)
            test = root / "test"
            test.mkdir()
            mirror.write_test_copy(live, test)
            (test / "events.json").write_text("[]\n", encoding="utf-8")

            with self.assertRaises(SystemExit):
                mirror.verify_exact_mirror(live, test)


if __name__ == "__main__":
    unittest.main()
