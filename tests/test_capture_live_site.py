from __future__ import annotations

import importlib.util
import json
import pathlib
import tempfile
import threading
import unittest
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
        "/app.js": ("application/javascript", b'const art="/assets/js.webp";'),
        "/seo-static.js": ("application/javascript", b""),
        "/seo-enhancements.js": ("application/javascript", b""),
        "/events.json": ("application/json", json.dumps([{"image": "assets/event.webp"}]).encode()),
        "/supplemental-events.json": ("application/json", b"[]"),
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
                self.assertEqual(result["optionalMissingMetadataFiles"], 1)
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


if __name__ == "__main__":
    unittest.main()
