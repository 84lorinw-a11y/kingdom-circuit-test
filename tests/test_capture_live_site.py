from __future__ import annotations

import importlib.util
from email.message import Message
from email.utils import formatdate
import hashlib
import io
import json
import pathlib
import tempfile
import threading
import unittest
import urllib.error
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "capture_live_site.py"
SPEC = importlib.util.spec_from_file_location("capture_live_site", SCRIPT)
assert SPEC and SPEC.loader
capture_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(capture_module)


class FixtureHandler(BaseHTTPRequestHandler):
    payloads: dict[str, tuple[str, bytes]] = {
        "/": (
            "text/html",
            b'<link rel="stylesheet" href="/styles.css"><a href="/artists/a/">A</a>'
            b'<script src="/app.js"></script><img src="/assets/hero.webp">'
            b'<meta property="og:image" content="PLACEHOLDER/assets/social.webp">'
            b'<meta name="twitter:image" content="PLACEHOLDER/assets/missing.webp">'
            b'<script type="application/ld+json">'
            b'{"image":"PLACEHOLDER/assets/structured.webp"}</script>',
        ),
        "/404.html": ("text/html", b"404"),
        "/artists/": ("text/html", b"artists"),
        "/artists/a/": ("text/html", b'<img srcset="/assets/a.webp 1x">'),
        "/artists/profile/": ("text/html", b"profile"),
        "/event/": ("text/html", b"event"),
        "/submit/": ("text/html", b"submit"),
        "/styles.css": ("text/css", b"body{background:url('/assets/bg.webp')}") ,
        "/app.js": (
            "application/javascript",
            b'const art="/assets/js.webp"; const valid=art.startsWith("/assets/");',
        ),
        "/seo-static.js": ("application/javascript", b""),
        "/seo-enhancements.js": ("application/javascript", b""),
        "/events.json": ("application/json", json.dumps([{"image": "assets/event.webp"}]).encode()),
        "/supplemental-events.json": (
            "application/json",
            b'[{"legacyEventPaths":["/event/retired-merge-path/"]}]',
        ),
        "/config/artists.json": (
            "application/json",
            json.dumps([{"image": "assets/config.webp"}]).encode(),
        ),
        "/robots.txt": ("text/plain", b"User-agent: *\nAllow: /\n"),
        "/sitemap.xml": (
            "application/xml",
            b'<?xml version="1.0"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
            b"<url><loc>PLACEHOLDER/artists/</loc></url>"
            b"<url><loc>PLACEHOLDER/artists/a/</loc></url></urlset>",
        ),
    }
    for asset in (
        "hero.webp",
        "a.webp",
        "bg.webp",
        "js.webp",
        "event.webp",
        "config.webp",
        "social.webp",
        "structured.webp",
    ):
        payloads[f"/assets/{asset}"] = ("image/webp", asset.encode())

    def do_GET(self):  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path not in self.payloads:
            self.send_response(404)
            self.end_headers()
            return
        content_type, payload = self.payloads[path]
        if b"PLACEHOLDER" in payload:
            origin = f"http://127.0.0.1:{self.server.server_port}".encode()
            payload = payload.replace(b"PLACEHOLDER", origin)
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args):
        return


class LiveCaptureTests(unittest.TestCase):
    def setUp(self):
        # Loopback fixtures exercise capture integrity. Request pacing and
        # retries have injected-clock coverage below without real sleeps.
        class ImmediatePacer:
            def wait(self, deadline):
                return
            def cooldown(self, seconds):
                return
        self.pacer_patch = patch.object(capture_module, 'REQUEST_PACER', ImmediatePacer())
        self.pacer_patch.start()
        self.addCleanup(self.pacer_patch.stop)

    def test_publication_manifest_captures_unlinked_files_and_checks_release(self):
        payloads = dict(FixtureHandler.payloads)
        payloads['/assets/dynamic-map.json'] = ('application/json', b'{"locations":{}}')
        payloads['/event/old-alias/'] = ('text/html', b'<meta name="robots" content="noindex"><p>Retained alias</p>')
        payloads['/play/'] = ('text/html', b'Older production game, not the independent Apollo test game')
        manifest = {'releaseId': 'fixture-release', 'files': {
            path: {'kind': 'html' if 'html' in payloads[path][0] else 'asset',
                   'sha256': hashlib.sha256(payloads[path][1]).hexdigest()}
            for path in ('/assets/dynamic-map.json', '/event/old-alias/', '/play/')
        }}
        manifest['files']['/__publication-audit-not-found__/'] = {'kind': 'not-found', 'status': 404}
        payloads['/publication-manifest.json'] = ('application/json', json.dumps(manifest).encode())
        with patch.object(FixtureHandler, 'payloads', payloads):
            server = ThreadingHTTPServer(('127.0.0.1', 0), FixtureHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                origin = f'http://127.0.0.1:{server.server_port}'
                with tempfile.TemporaryDirectory() as temporary:
                    output = pathlib.Path(temporary) / 'site'
                    report = capture_module.capture(origin, output, workers=4, publication_manifest=True)
                    self.assertTrue(report['publicationManifestVerified'])
                    self.assertEqual(report['publicationReleaseId'], 'fixture-release')
                    self.assertTrue((output / 'assets/dynamic-map.json').is_file())
                    self.assertTrue((output / 'event/old-alias/index.html').is_file())
                    self.assertFalse((output / '__publication-audit-not-found__').exists())
                    self.assertFalse((output / 'play').exists())
                    payloads['/assets/dynamic-map.json'] = ('application/json', b'{"changed":true}')
                    with self.assertRaises(SystemExit) as failed:
                        capture_module.capture(origin, output, workers=4, publication_manifest=True)
                    self.assertIn('publication-mismatch:/assets/dynamic-map.json', str(failed.exception))
            finally:
                server.shutdown()
                server.server_close()

    def test_tracking_attributes_are_not_navigation_or_image_urls(self) -> None:
        origin = "https://kingdomcircuit.com"
        required, _ = capture_module.discovered_urls(
            origin + "/artists/mike-malagies/", "text/html",
            b'<a data-empty-action="explore" href="/shows/#browse-states">Explore</a>'
            b'<a data-empty-action="instagram" href="https://www.instagram.com/thekingdomcircuit/">Follow</a>'
            b'<img data-src="not-a-live-image" SRC="/assets/live.webp" data-srcset="not-live.webp 2x" srcset="/assets/live-2x.webp 2x">'
            b'<form action="/submit/"></form><video poster="/assets/poster.webp"></video>', origin,
        )
        self.assertEqual(required, {origin + path for path in (
            "/shows/", "/assets/live.webp", "/assets/live-2x.webp", "/submit/", "/assets/poster.webp",
        )})

    def test_retired_catalog_history_is_metadata_but_live_urls_remain_required(self) -> None:
        origin = "https://kingdomcircuit.com"
        payload = json.dumps([{
            "legacyEventPaths": ["/event/retired/", "/event/current/"],
            "url": "/event/current/", "image": "assets/event.webp",
        }]).encode()
        required, optional = capture_module.discovered_urls(
            origin + "/supplemental-events.json", "application/json", payload, origin,
        )
        self.assertEqual(required, {origin + "/event/current/", origin + "/assets/event.webp"})
        self.assertEqual(optional, {origin + "/event/retired/"})
        html_required, _ = capture_module.discovered_urls(
            origin + "/", "text/html", b'<a href="/event/retired/">Still linked</a>', origin,
        )
        self.assertEqual(html_required, {origin + "/event/retired/"})

    def test_asset_directory_prefix_is_not_a_javascript_dependency(self) -> None:
        origin = "https://kingdomcircuit.com"
        required, _ = capture_module.discovered_urls(
            origin + "/assets/fan-discovery.js", "application/javascript",
            b"src.startsWith('/assets/'); const photo='/assets/portrait.webp';"
            b"const artists='/artists/';", origin,
        )
        self.assertEqual(required, {origin + "/assets/portrait.webp", origin + "/artists/"})
        html_required, _ = capture_module.discovered_urls(
            origin + "/", "text/html", b'<img src="/assets/">', origin,
        )
        self.assertEqual(html_required, {origin + "/assets/"})

    def test_captures_sitemap_pages_and_runtime_dependencies(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), FixtureHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = f"http://127.0.0.1:{server.server_port}"
            with tempfile.TemporaryDirectory() as temporary:
                output = pathlib.Path(temporary) / "site"
                result = capture_module.capture(
                    origin,
                    output,
                    workers=4,
                    min_html=6,
                    min_files=15,
                )
                self.assertGreaterEqual(result["htmlFiles"], 6)
                self.assertEqual(result["optionalMissingMetadataFiles"], 2)
                self.assertEqual(
                    (output / "supplemental-events.json").read_bytes(),
                    FixtureHandler.payloads["/supplemental-events.json"][1],
                )
                for relative in (
                    "index.html",
                    "artists/index.html",
                    "artists/a/index.html",
                    "assets/bg.webp",
                    "assets/js.webp",
                    "assets/event.webp",
                    "assets/config.webp",
                    "assets/social.webp",
                    "assets/structured.webp",
                    "config/artists.json",
                ):
                    self.assertTrue((output / relative).is_file(), relative)
        finally:
            server.shutdown()
            server.server_close()

    def test_ignores_external_and_operational_urls(self) -> None:
        origin = "https://kingdomcircuit.com"
        self.assertIsNone(
            capture_module.canonical_url(
                "https://example.com/image.jpg", origin + "/", origin
            )
        )
        self.assertIsNone(
            capture_module.canonical_url("/run-status.json", origin + "/", origin)
        )

    def test_history_does_not_excuse_a_broken_visible_link(self) -> None:
        class BrokenLinkHandler(FixtureHandler):
            payloads = dict(FixtureHandler.payloads)
            payloads["/"] = (
                "text/html",
                FixtureHandler.payloads["/"][1]
                + b'<a href="/event/retired-merge-path/">Current listing</a>',
            )

        server = ThreadingHTTPServer(("127.0.0.1", 0), BrokenLinkHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                with self.assertRaises(SystemExit) as failure:
                    capture_module.capture(
                        f"http://127.0.0.1:{server.server_port}",
                        pathlib.Path(temporary) / "site", workers=4,
                    )
                self.assertIn("/event/retired-merge-path/", str(failure.exception))
                self.assertIn("404", str(failure.exception))
        finally:
            server.shutdown()
            server.server_close()


class FakeClock:
    def __init__(self):
        self.value = 0.0
        self.sleeps = []

    def now(self):
        return self.value

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.value += seconds


class CaptureRequestPolicyTests(unittest.TestCase):
    URL = 'https://kingdomcircuit.com/publication-manifest.json'

    def setUp(self):
        self.clock = FakeClock()
        self.pacer = capture_module.RequestPacer(clock=self.clock.now, sleep=self.clock.sleep)

    def response(self, payload=b'{}'):
        response = io.BytesIO(payload)
        response.headers = Message()
        response.headers['Content-Type'] = 'application/json'
        response.geturl = lambda: self.URL
        return response

    def error(self, status, retry_after=None):
        headers = Message()
        if retry_after is not None:
            headers['Retry-After'] = retry_after
        return urllib.error.HTTPError(self.URL, status, 'fixture', headers, io.BytesIO(b'error'))

    def fetch(self, opener, **kwargs):
        return capture_module.fetch(self.URL, pacer=self.pacer, opener=opener,
                                    clock=self.clock.now, sleep=self.clock.sleep, **kwargs)

    def test_shared_pacer_spaces_requests_and_cooldown_extends_every_caller(self):
        started = []
        for _ in range(4):
            self.pacer.wait(100)
            started.append(self.clock.now())
        self.assertEqual([0, .25, .5, .75], started)
        self.pacer.cooldown(7)
        self.pacer.cooldown(2)
        self.pacer.wait(100)
        self.assertEqual(7.75, self.clock.now())
        self.pacer.wait(100)
        self.assertEqual(8, self.clock.now())

    def test_429_obeys_retry_after_and_the_same_pacer_is_shared_with_next_fetch(self):
        starts = []
        def opener(request, timeout):
            starts.append(self.clock.now())
            if len(starts) == 1:
                raise self.error(429, '7')
            return self.response()
        self.assertEqual(b'{}', self.fetch(opener)[2])
        self.fetch(opener)
        self.assertEqual([0, 7, 7.25], starts)

    def test_retry_after_accepts_numeric_and_http_dates_and_rejects_nonfinite(self):
        self.assertEqual(9, capture_module.retry_after_seconds('9'))
        self.assertEqual(20, capture_module.retry_after_seconds(formatdate(1020, usegmt=True), wall_clock=lambda: 1000))
        self.assertEqual(0, capture_module.retry_after_seconds(formatdate(990, usegmt=True), wall_clock=lambda: 1000))
        for value in ('invalid', 'inf', 'nan', None):
            self.assertIsNone(capture_module.retry_after_seconds(value))

    def test_persistent_429_is_bounded_and_missing_retry_after_uses_global_backoff(self):
        starts = []
        def opener(request, timeout):
            starts.append(self.clock.now())
            raise self.error(429)
        with self.assertRaisesRegex(RuntimeError, '429'):
            self.fetch(opener)
        self.assertEqual([0, 5, 15, 35, 75], starts)
        self.assertEqual(5, len(starts))

    def test_long_server_cooldown_fails_deadline_without_retrying_early(self):
        calls = []
        def opener(request, timeout):
            calls.append(timeout)
            raise self.error(429, '600')
        with self.assertRaisesRegex(RuntimeError, 'deadline'):
            self.fetch(opener)
        self.assertEqual([30], calls)
        self.assertEqual([], self.clock.sleeps)

    def test_authentication_and_missing_resources_fail_once_but_404_page_is_preserved(self):
        for status in (401, 403, 404):
            calls = []
            def opener(request, timeout):
                calls.append(request.full_url)
                raise self.error(status)
            with self.assertRaisesRegex(RuntimeError, str(status)):
                self.fetch(opener)
            self.assertEqual(1, len(calls))
        error = urllib.error.HTTPError('https://kingdomcircuit.com/404.html', 404, 'missing', Message(), io.BytesIO(b'custom missing page'))
        with patch.object(capture_module.urllib.request, 'urlopen', side_effect=error):
            result = capture_module.fetch('https://kingdomcircuit.com/404.html', pacer=self.pacer,
                                          clock=self.clock.now, sleep=self.clock.sleep)
        self.assertEqual(('https://kingdomcircuit.com/404.html', 'text/html', b'custom missing page'), result)

    def test_temporary_network_failure_retries_but_late_response_cannot_pass(self):
        starts = []
        def opener(request, timeout):
            starts.append(self.clock.now())
            if len(starts) == 1:
                raise urllib.error.URLError('temporary network failure')
            return self.response(b'complete')
        self.assertEqual(b'complete', self.fetch(opener)[2])
        self.assertEqual([0, 1], starts)
        def slow(request, timeout):
            self.clock.value += 301
            return self.response(b'too late')
        with self.assertRaisesRegex(RuntimeError, 'deadline'):
            self.fetch(slow)


if __name__ == "__main__":
    unittest.main()
