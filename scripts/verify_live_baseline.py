"""Gate the final artifact against exact, approved transforms and content invariants."""
import argparse
import json
from datetime import date
from pathlib import Path

from live_mirror_v2 import verify_exact_mirror
from build_mobile_show_test import verify as verify_calendar
from build_artist_intake_mockup import verify as verify_intake
from mobile_seo_preview import ASSETS, VERSION, verify_overlay
import national_discovery_preview as discovery

EXPERIMENT_FILES = frozenset({
    "test-all-shows/index.html", "test-show-feed/index.html", "test-artist-intake/index.html",
    "assets/mobile-show-test.css", "assets/mobile-show-test.js", "assets/show-feed-samples.css",
    "assets/kingdom-circuit-mobile-preview.zip",
    "assets/artist-intake-mockup.css", "assets/artist-intake-mockup.js",
})
ADDITIONS = (EXPERIMENT_FILES | {".nojekyll", "test-live-mirror-manifest.json", discovery.WEEKEND_PATH, discovery.ABOUT_PATH}
             | {f"assets/{name}" for name in (*ASSETS, *discovery.ASSETS)})


def verify(live: Path, site: Path) -> dict:
    manifest_path = site / "test-live-mirror-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    context = discovery.load_context(live, date.fromisoformat(manifest['nationalDiscovery']['asOfDate']))
    parity = verify_exact_mirror(live, site, allowed_additions=ADDITIONS,
                                approved_transform=lambda path, data: discovery.combined_transform(path, data, context))
    national = discovery.verify(live, site, context)
    overlay = verify_overlay(live, site, national_home=True)
    verify_calendar(site, isolated=True)
    verify_intake(site)
    assert manifest["mode"] in {"exact-live-artifact-mirror", "live-mirror-with-mobile-seo-preview", "live-mirror-with-national-discovery-preview"}
    manifest.update(parity)
    manifest["preservedExperimentPaths"] = ["/test-all-shows/", "/test-show-feed/", "/test-artist-intake/"]
    manifest["isolatedExperimentFileCount"] = len(EXPERIMENT_FILES)
    manifest["testRedesignApplied"] = False
    manifest["mode"] = "live-mirror-with-national-discovery-preview"
    manifest["contentAndLayoutParity"] = False
    manifest["dataFilesByteIdentical"] = True
    manifest["binaryAssetsByteIdentical"] = True
    manifest["mobileSeoPreview"] = {"version": VERSION, **overlay}
    manifest['nationalDiscovery'].update(national)
    change = "test-only state discovery, location reading order and optional quick-list view"
    if change not in manifest["testOnlyDifferences"]:
        manifest["testOnlyDifferences"].append(change)
    national_change = 'test-only national homepage, evergreen weekend calendar, About Us mission page, compact eight-link navigation, artist breadcrumbs and discovery links'
    if national_change not in manifest['testOnlyDifferences']:
        manifest['testOnlyDifferences'].append(national_change)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("live", type=Path)
    parser.add_argument("site", type=Path)
    args = parser.parse_args()
    verify(args.live, args.site)
