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


def force_noindex(text: str) -> str:
    robots_pattern = re.compile(r'<meta\s+name=["\']robots["\']\s+content=["\'][^"\']*["\']\s*/?>', re.I)
    replacement = '<meta name="robots" content="noindex,nofollow">'
    if robots_pattern.search(text):
        return robots_pattern.sub(replacement, text, count=1)
    return re.sub(r'(<head\b[^>]*>)', r'\1\n  ' + replacement, text, count=1, flags=re.I)


def rewrite_html(text: str) -> str:
    text = text.replace(LIVE_SITE + "/", TEST_SITE + "/")
    text = text.replace(LIVE_SITE, TEST_SITE)
    text = text.replace(LIVE_GA, TEST_GA)
    text = re.sub(
        r'(?P<attr>\b(?:href|src|action)\s*=\s*)(?P<quote>["\'])/(?!/)',
        lambda m: m.group("attr") + m.group("quote") + TEST_BASE,
        text,
        flags=re.I,
    )
    return force_noindex(text)


def rewrite_js(text: str) -> str:
    text = text.replace(LIVE_SITE + "/", TEST_SITE + "/")
    text = text.replace(LIVE_SITE, TEST_SITE)
    text = text.replace(LIVE_GA, TEST_GA)
    text = text.replace('const BASE = "/";', f'const BASE = "{TEST_BASE}";')
    text = re.sub(
        r'(?P<attr>\b(?:href|src|action)\s*=\s*\\?)(?P<quote>["\'])/(?!/)',
        lambda m: m.group("attr") + m.group("quote") + TEST_BASE,
        text,
        flags=re.I,
    )
    return text


def rewrite_css(text: str) -> str:
    text = text.replace(LIVE_SITE + "/", TEST_SITE + "/")
    text = text.replace(LIVE_SITE, TEST_SITE)
    text = re.sub(r'url\((?P<quote>["\']?)/(?!/)', lambda m: "url(" + m.group("quote") + TEST_BASE, text)
    return text


def normalize_test_html(text: str) -> str:
    text = text.replace(TEST_SITE + "/", LIVE_SITE + "/")
    text = text.replace(TEST_SITE, LIVE_SITE)
    text = text.replace(TEST_BASE, "/")
    text = text.replace(TEST_GA, LIVE_GA)
    text = text.replace('content="noindex,nofollow"', 'content="index,follow"')
    return text


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: mirror_live_baseline.py LIVE_SITE_DIR PROD_REFERENCE_DIR TEST_OUTPUT_DIR")

    live_dir = pathlib.Path(sys.argv[1]).resolve()
    reference_dir = pathlib.Path(sys.argv[2]).resolve()
    out_dir = pathlib.Path(sys.argv[3]).resolve()

    if not (live_dir / "index.html").is_file():
        raise SystemExit(f"Missing production artifact: {live_dir}")

    if reference_dir.exists():
        shutil.rmtree(reference_dir)
    shutil.copytree(live_dir, reference_dir)

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
            text = path.read_text(encoding="utf-8", errors="strict")
            path.write_text(rewrite_html(text), encoding="utf-8")
        elif suffix == ".js":
            text = path.read_text(encoding="utf-8", errors="strict")
            path.write_text(rewrite_js(text), encoding="utf-8")
        elif suffix == ".css":
            text = path.read_text(encoding="utf-8", errors="strict")
            path.write_text(rewrite_css(text), encoding="utf-8")
        elif suffix == ".xml":
            text = path.read_text(encoding="utf-8", errors="strict")
            text = text.replace(LIVE_SITE + "/", TEST_SITE + "/").replace(LIVE_SITE, TEST_SITE)
            path.write_text(text, encoding="utf-8")

    (out_dir / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")

    compare_paths = [
        "index.html",
        "shows/index.html",
        "shows/this-month/index.html",
        "festivals/index.html",
        "new-shows/index.html",
        "artists/index.html",
        "artists/profile/index.html",
        "submit/index.html",
    ]
    generated_artists = sorted((reference_dir / "artists").glob("*/index.html"))
    generated_artists = [p for p in generated_artists if p.parent.name != "profile"]
    if generated_artists:
        compare_paths.append(str(generated_artists[0].relative_to(reference_dir)))

    parity_failures = []
    for relative in compare_paths:
        prod = (reference_dir / relative).read_text(encoding="utf-8")
        test = (out_dir / relative).read_text(encoding="utf-8")
        if normalize_test_html(test) != prod:
            parity_failures.append(relative)

    asset_failures = []
    prod_assets = reference_dir / "assets"
    for prod in prod_assets.rglob("*"):
        if not prod.is_file():
            continue
        relative = prod.relative_to(reference_dir)
        test = out_dir / relative
        if not test.is_file() or sha256(prod) != sha256(test):
            asset_failures.append(str(relative))

    safety_failures = []
    unsafe_root_pattern = re.compile(
        r'\b(?:href|src|action)\s*=\s*["\']/(?!/|kingdom-circuit-test/)',
        re.I,
    )
    for path in out_dir.rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        if 'name="robots" content="noindex,nofollow"' not in text:
            safety_failures.append(f"missing-noindex:{path.relative_to(out_dir)}")
        if unsafe_root_pattern.search(text):
            safety_failures.append(f"root-path:{path.relative_to(out_dir)}")
        if LIVE_GA in text:
            safety_failures.append(f"live-ga:{path.relative_to(out_dir)}")

    app = (out_dir / "app.js").read_text(encoding="utf-8")
    if f'const BASE = "{TEST_BASE}";' not in app:
        safety_failures.append("app-base")

    if parity_failures or asset_failures or safety_failures:
        raise SystemExit(json.dumps({
            "parityFailures": parity_failures,
            "assetFailures": asset_failures,
            "safetyFailures": safety_failures[:50],
        }, indent=2))

    manifest = {
        "mode": "live-baseline-mirror",
        "liveCommit": "88fab267531e2b5061bad679b2ab1b401511a8bc",
        "testBase": TEST_BASE,
        "productionMarkupParityChecks": len(compare_paths),
        "productionMarkupParity": True,
        "assetsByteIdentical": True,
        "testNoindex": True,
        "productionAnalyticsDisabled": True,
        "cnameRemoved": True,
    }
    (out_dir / "test-live-mirror-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
