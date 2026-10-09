"""Gate the final artifact: exact live baseline plus a closed list of experiments."""
import argparse
import json
from pathlib import Path

from live_mirror_v2 import verify_exact_mirror
from build_mobile_show_test import verify as verify_calendar
from build_artist_intake_mockup import verify as verify_intake

EXPERIMENT_FILES = frozenset({
    "test-all-shows/index.html", "test-show-feed/index.html", "test-artist-intake/index.html",
    "assets/mobile-show-test.css", "assets/mobile-show-test.js", "assets/show-feed-samples.css",
    "assets/kingdom-circuit-mobile-preview.zip",
    "assets/artist-intake-mockup.css", "assets/artist-intake-mockup.js",
})
ADDITIONS = EXPERIMENT_FILES | {".nojekyll", "test-live-mirror-manifest.json"}


def verify(live: Path, site: Path) -> dict:
    parity = verify_exact_mirror(live, site, allowed_additions=ADDITIONS)
    verify_calendar(site, isolated=True)
    verify_intake(site)
    manifest_path = site / "test-live-mirror-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    assert manifest["mode"] == "exact-live-artifact-mirror"
    assert manifest["contentAndLayoutParity"] is True
    manifest.update(parity)
    manifest["preservedExperimentPaths"] = ["/test-all-shows/", "/test-show-feed/", "/test-artist-intake/"]
    manifest["isolatedExperimentFileCount"] = len(EXPERIMENT_FILES)
    manifest["testRedesignApplied"] = False
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("live", type=Path)
    parser.add_argument("site", type=Path)
    args = parser.parse_args()
    verify(args.live, args.site)
