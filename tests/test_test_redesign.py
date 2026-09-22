from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "verify_test_redesign.py"
SPEC = importlib.util.spec_from_file_location("verify_test_redesign", MODULE_PATH)
assert SPEC and SPEC.loader
verify = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = verify
SPEC.loader.exec_module(verify)


def shell(body: str) -> str:
    return f'''<!doctype html><html><head>
<meta name="robots" content="noindex,nofollow">
<link rel="icon" type="image/png" sizes="48x48" href="/kingdom-circuit-test/assets/favicon-kc-stacked-v2-48.png">
<link rel="icon" type="image/png" sizes="96x96" href="/kingdom-circuit-test/assets/favicon-kc-stacked-v2-96.png">
<link rel="apple-touch-icon" sizes="180x180" href="/kingdom-circuit-test/assets/favicon-kc-stacked-v2-180.png">
<link rel="manifest" href="/kingdom-circuit-test/manifest.webmanifest">
<meta name="apple-mobile-web-app-title" content="Kingdom Circuit">
<link rel="stylesheet" href="/kingdom-circuit-test/assets/kc-redesign-v1.css">
<script src="/kingdom-circuit-test/assets/kc-redesign-v1.js" defer></script>
</head><body><header class="kc-rd-header"><div class="kc-rd-followbar"><a href="https://www.instagram.com/thekingdomcircuit/">Follow @thekingdomcircuit</a></div><a href="/kingdom-circuit-test/">Kingdom Circuit</a></header>
{body}</body></html>'''


class TestRedesignVerifier(unittest.TestCase):
    def build_site(self, root: pathlib.Path) -> None:
        (root / "assets").mkdir(parents=True)
        (root / "assets" / "kc-redesign-v1.css").write_text(
            ".kc-rd-header{display:flex}.kc-rd-directory-intro{font-size:2rem}.kc-rd-profile-page{display:block}"
            "[data-artist-directory] .artist-visual img{position: absolute;width: 100%;height: 100%;object-fit: cover}"
            "body .event-detail-section{padding-top:24px}body .event-detail-copy h1{font-size:clamp(2rem,4vw,4rem)}",
            encoding="utf-8",
        )
        (root / "assets" / "kc-redesign-v1.js").write_text("document.documentElement.classList.add('kc-rd-ready');", encoding="utf-8")
        favicon_names = (
            "favicon-kc-stacked-v2-48.png",
            "favicon-kc-stacked-v2-96.png",
            "favicon-kc-stacked-v2-180.png",
            "favicon-kc-stacked-v2-192.png",
            "favicon-kc-stacked-v2-512.png",
            "favicon-kc-stacked-v2-maskable-512.png",
        )
        for filename in favicon_names:
            (root / "assets" / filename).write_bytes(b"test-png")
        web_manifest = {
            "name": "Kingdom Circuit",
            "start_url": "/kingdom-circuit-test/",
            "scope": "/kingdom-circuit-test/",
            "icons": [
                {"src": "/kingdom-circuit-test/assets/favicon-kc-stacked-v2-192.png"},
                {"src": "/kingdom-circuit-test/assets/favicon-kc-stacked-v2-512.png"},
                {"src": "/kingdom-circuit-test/assets/favicon-kc-stacked-v2-maskable-512.png"},
            ],
        }
        (root / "manifest.webmanifest").write_text(json.dumps(web_manifest), encoding="utf-8")

        home = shell('''
<main class="kc-rd-home">
  <h1 class="kc-rd-home-title"><span>Find Christian</span><span>Hip Hop Shows</span><span>Near You!</span></h1>
  <div><strong data-kc-rd-stat="shows">2 shows</strong><strong data-kc-rd-stat="artists">2 artists</strong></div>
  <article data-event-card><a href="/kingdom-circuit-test/event/one/">One</a></article>
  <article data-event-card><a href="/kingdom-circuit-test/event/two/">Two</a></article>
</main>''')
        (root / "index.html").write_text(home, encoding="utf-8")

        artists = shell('''
<main>
  <section class="kc-rd-directory-intro"><h1>Meet the artists we track.</h1><p class="kc-rd-directory-count"><strong>2</strong> CHH Artists</p><a href="/kingdom-circuit-test/submit/">Submit a Show</a><a href="/kingdom-circuit-test/submit/artist/">Submit a CHH Artist to Be Listed</a></section>
  <label><input type="checkbox" data-has-shows-filter> Artists with shows</label>
  <section data-artist-directory>
    <article data-artist-card><a class="artist-visual" href="/kingdom-circuit-test/artists/alpha/"><img src="/kingdom-circuit-test/assets/alpha.webp" alt="Alpha"></a><div class="artist-card-body"><h2><a href="/kingdom-circuit-test/artists/alpha/">Alpha</a></h2><p class="seo-card-next">Next: Sep 22, 2026 · Detroit, MI</p></div></article>
    <article data-artist-card><a class="artist-visual-empty" href="/kingdom-circuit-test/artists/beta/">B</a><div class="artist-card-body"><h2><a href="/kingdom-circuit-test/artists/beta/">Beta</a></h2></div></article>
  </section>
</main>''')
        (root / "artists").mkdir()
        (root / "artists" / "index.html").write_text(artists, encoding="utf-8")

        profile = shell('''
<main class="kc-rd-artist-profile">
  <section class="kc-rd-next-show"><a href="/kingdom-circuit-test/event/one/">Sep 22 — Detroit</a></section>
  <div class="kc-rd-profile-section-title"><h2>All Alpha Shows</h2><span class="kc-rd-upcoming-total">2 upcoming</span></div>
  <div class="kc-rd-show-list">
    <article class="kc-rd-show-row"><a href="/kingdom-circuit-test/event/one/">Sep 22 — Detroit — Saint Andrew's Hall</a></article>
    <article class="kc-rd-show-row"><a href="/kingdom-circuit-test/event/two/">Sep 23 — Chicago — House of Blues</a></article>
  </div>
  <section class="kc-rd-past-shows"><details><summary><span>Past shows</span><span class="past-count">1 archived show</span></summary><div class="past-show-list"><article class="past-show-row"><div class="past-show-date">Sep 19, 2026</div><div class="past-show-copy"><h3><a href="/kingdom-circuit-test/event/past-one/">Past show</a></h3><p>Past Venue · Chicago, IL</p></div></article></div></details></section>
</main>''')
        (root / "artists" / "alpha").mkdir()
        (root / "artists" / "alpha" / "index.html").write_text(profile, encoding="utf-8")

        form = shell('''
<main><form class="kc-rd-artist-submit" action="/kingdom-circuit-test/submit/" method="post">
  <input name="artistName" required>
  <input name="officialUrl" type="url" required>
  <input name="environment" type="hidden" value="test">
  <button type="submit">Submit artist</button>
</form></main>''')
        (root / "submit" / "artist").mkdir(parents=True)
        (root / "submit" / "artist" / "index.html").write_text(form, encoding="utf-8")

        generic = shell('<main><a href="/kingdom-circuit-test/artists/">Artists</a></main>')
        (root / "event" / "one").mkdir(parents=True)
        (root / "event" / "one" / "index.html").write_text(generic, encoding="utf-8")

        manifest = {
            "mode": "mobile-first-test-redesign-v1",
            "showCount": 2,
            "artistCount": 2,
            "profilePageCount": 1,
            "profileShowRowCount": 2,
            "profilePastShowRowCount": 1,
            "profilePagesWithPastShows": 1,
            "headerPageCount": 5,
            "artistSubmissionPath": "/kingdom-circuit-test/submit/artist/",
            "productionChanged": False,
            "htmlPageCount": 5,
        }
        (root / "test-redesign-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    def test_valid_redesign_passes_helpers_and_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self.build_site(root)
            report = verify.verify_site(root)
            self.assertEqual(report["showCount"], 2)
            self.assertEqual(report["artistCount"], 2)
            self.assertEqual(report["profilePageCount"], 1)
            result = subprocess.run(
                [sys.executable, str(MODULE_PATH), str(root)],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["failures"], [])

    def test_old_header_and_manifest_drift_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self.build_site(root)
            home = root / "index.html"
            home.write_text(home.read_text(encoding="utf-8").replace("kc-rd-header", "site-header"), encoding="utf-8")
            manifest = json.loads((root / "test-redesign-manifest.json").read_text(encoding="utf-8"))
            manifest["showCount"] = 99
            (root / "test-redesign-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            report = verify.audit_site(root)
            joined = "\n".join(report["failures"])
            self.assertIn("old-header:index.html:site-header", joined)
            self.assertIn("missing-redesign-header:index.html", joined)
            self.assertIn("manifest:showCount:99!=2", joined)

    def test_profile_without_shows_or_past_archive_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self.build_site(root)
            beta = root / "artists" / "beta"
            beta.mkdir()
            (beta / "index.html").write_text(
                shell('<main class="kc-rd-artist-profile"><div class="kc-rd-profile-section-title"><h2>All Beta Shows</h2><span class="kc-rd-upcoming-total">0 upcoming</span></div><p>No upcoming shows.</p></main>'),
                encoding="utf-8",
            )
            manifest_path = root / "test-redesign-manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["profilePageCount"] = 2
            manifest["headerPageCount"] = 6
            manifest["htmlPageCount"] = 6
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            report = verify.verify_site(root)
            self.assertEqual(report["profilePageCount"], 2)
            self.assertEqual(report["profileShowRowCount"], 2)

    def test_followbar_arrow_and_directory_time_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self.build_site(root)
            home = root / "index.html"
            home.write_text(
                home.read_text(encoding="utf-8").replace(
                    "Follow @thekingdomcircuit</a>",
                    "Follow @thekingdomcircuit <span>↗</span></a>",
                    1,
                ),
                encoding="utf-8",
            )
            directory = root / "artists" / "index.html"
            directory.write_text(
                directory.read_text(encoding="utf-8").replace(
                    "Sep 22, 2026 ·",
                    "Sep 22, 2026 - 7:00 PM ·",
                    1,
                ),
                encoding="utf-8",
            )
            failures = "\n".join(verify.audit_site(root)["failures"])
            self.assertIn("followbar-arrow:index.html", failures)
            self.assertIn("directory:next-show-time:0", failures)

    def test_legacy_or_missing_favicon_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self.build_site(root)
            home = root / "index.html"
            home.write_text(
                home.read_text(encoding="utf-8").replace(
                    '<link rel="icon" type="image/png" sizes="48x48" href="/kingdom-circuit-test/assets/favicon-kc-stacked-v2-48.png">',
                    '<link rel="icon" href="/kingdom-circuit-test/assets/favicon.svg" type="image/svg+xml">',
                    1,
                ),
                encoding="utf-8",
            )
            failures = "\n".join(verify.audit_site(root)["failures"])
            self.assertIn("favicon-link:index.html:/kingdom-circuit-test/assets/favicon-kc-stacked-v2-48.png", failures)
            self.assertIn("legacy-favicon:index.html", failures)


if __name__ == "__main__":
    unittest.main()
