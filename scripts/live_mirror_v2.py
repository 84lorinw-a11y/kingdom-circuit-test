from __future__ import annotations

import hashlib
import json
import pathlib
import re
import shutil
import sys

TEST_BASE = "/kingdom-circuit-test/"
TEST_ORIGIN = "https://84lorinw-a11y.github.io"
TEST_SITE = TEST_ORIGIN + TEST_BASE.rstrip("/")
LIVE_SITE = "https://kingdomcircuit.com"
LIVE_GA = "G-N2KK9XF4TJ"
TEST_GA = "G-TEST-DISABLED"


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rewrite_html(text: str) -> str:
    text = text.replace(LIVE_SITE + "/", TEST_SITE + "/")
    text = text.replace(LIVE_SITE, TEST_SITE)
    text = text.replace(LIVE_GA, TEST_GA)

    # Preserve the live markup/layout while making root-relative runtime paths work
    # from GitHub Pages' /kingdom-circuit-test/ subpath.
    text = re.sub(
        r'(?P<prefix>\b(?:href|src|action)=["\'])/(?!/)',
        lambda m: m.group("prefix") + TEST_BASE,
        text,
    )

    # Test must never be indexed, regardless of the live page's current policy.
    robots = re.compile(r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*["\']\s*/?>', re.I)
    if robots.search(text):
        text = robots.sub('<meta name="robots" content="noindex,nofollow">', text)
    elif "<head>" in text:
        text = text.replace("<head>", '<head>\n  <meta name="robots" content="noindex,nofollow">', 1)
    return text


def rewrite_js(text: str) -> str:
    text = text.replace(LIVE_SITE + "/", TEST_SITE + "/")
    text = text.replace(LIVE_SITE, TEST_SITE)
    text = text.replace(LIVE_GA, TEST_GA)
    text = text.replace('const BASE = "/";', f'const BASE = "{TEST_BASE}";')
    return text


def rewrite_css(text: str) -> str:
    text = text.replace(LIVE_SITE + "/", TEST_SITE + "/")
    text = text.replace(LIVE_SITE, TEST_SITE)
    return text


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: live_mirror_v2.py LIVE_ARTIFACT TEST_OUTPUT LIVE_SHA")

    live_dir = pathlib.Path(sys.argv[1]).resolve()
    out_dir = pathlib.Path(sys.argv[2]).resolve()
    live_sha = sys.argv[3]

    if not (live_dir / "index.html").is_file():
        raise SystemExit(f"Missing live artifact: {live_dir}")

    if out_dir.exists():
        shutil.rmtree(out_dir)
    shutil.copytree(live_dir, out_dir)

    cname = out_dir / "CNAME"
    if cname.exists():
        cname.unlink()

    for path in out_dir.rglob("*"):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix == ".html":
            path.write_text(rewrite_html(path.read_text(encoding="utf-8")), encoding="utf-8")
        elif suffix == ".js":
            path.write_text(rewrite_js(path.read_text(encoding="utf-8")), encoding="utf-8")
        elif suffix == ".css":
            path.write_text(rewrite_css(path.read_text(encoding="utf-8")), encoding="utf-8")
        elif suffix == ".xml":
            text = path.read_text(encoding="utf-8")
            text = text.replace(LIVE_SITE + "/", TEST_SITE + "/").replace(LIVE_SITE, TEST_SITE)
            path.write_text(text, encoding="utf-8")

    (out_dir / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")

    # Safety/parity checks. CSS, data, config, and all image assets stay byte-identical.
    failures: list[str] = []
    for relative in ["styles.css", "events.json", "supplemental-events.json", "config/artists.json"]:
        live_path = live_dir / relative
        test_path = out_dir / relative
        if not test_path.is_file() or sha256(live_path) != sha256(test_path):
            failures.append(f"changed:{relative}")

    for live_asset in (live_dir / "assets").rglob("*"):
        if not live_asset.is_file():
            continue
        relative = live_asset.relative_to(live_dir)
        test_asset = out_dir / relative
        if not test_asset.is_file() or sha256(live_asset) != sha256(test_asset):
            failures.append(f"asset:{relative}")

    bad_root = re.compile(r'\b(?:href|src|action)=["\']/(?!kingdom-circuit-test(?:/|["\']))')
    for html_file in out_dir.rglob("*.html"):
        text = html_file.read_text(encoding="utf-8")
        rel = html_file.relative_to(out_dir)
        if '<meta name="robots" content="noindex,nofollow">' not in text:
            failures.append(f"indexable:{rel}")
        if bad_root.search(text):
            failures.append(f"bad-root-path:{rel}")
        if LIVE_GA in text:
            failures.append(f"live-analytics:{rel}")

    app = (out_dir / "app.js").read_text(encoding="utf-8")
    if f'const BASE = "{TEST_BASE}";' not in app:
        failures.append("app-base-not-rewritten")
    if (out_dir / "CNAME").exists():
        failures.append("cname-present")

    if failures:
        raise SystemExit(json.dumps({"failures": failures[:100]}, indent=2))

    manifest = {
        "mode": "live-baseline-only",
        "liveCommit": live_sha,
        "source": "84lorinw-a11y/kingdom-circuit@main",
        "testBase": TEST_BASE,
        "liveStylesByteIdentical": True,
        "liveDataByteIdentical": True,
        "liveAssetsByteIdentical": True,
        "testNoindex": True,
        "liveAnalyticsDisabled": True,
        "cnameRemoved": True,
        "seoPhase2OverlayApplied": False,
    }
    (out_dir / "test-live-mirror-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
