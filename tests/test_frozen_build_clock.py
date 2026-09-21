from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]


class FrozenBuildClockTests(unittest.TestCase):
    def test_workflow_runs_the_production_release_finalizer(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "mirror-live.yml").read_text(
            encoding="utf-8"
        )
        self.assertIn('KC_FINALIZE_PUBLIC_EXPERIENCE: "1"', workflow)

    def test_mirror_date_freezes_date_sensitive_builders(self) -> None:
        env = os.environ.copy()
        env["KC_MIRROR_DATE"] = "2026-09-18"
        env["PYTHONPATH"] = str(ROOT / "scripts")
        code = (
            "import datetime,json;"
            "from zoneinfo import ZoneInfo;"
            "print(json.dumps({"
            "'today':datetime.date.today().isoformat(),"
            "'utc':datetime.datetime.now(datetime.timezone.utc).date().isoformat(),"
            "'pacific':datetime.datetime.now(ZoneInfo('America/Los_Angeles')).date().isoformat()"
            "}))"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            check=True,
            capture_output=True,
            text=True,
            env=env,
            cwd=ROOT,
        )
        self.assertEqual(
            json.loads(result.stdout),
            {
                "today": "2026-09-18",
                "utc": "2026-09-18",
                "pacific": "2026-09-18",
            },
        )

    def test_normal_commands_keep_the_real_clock(self) -> None:
        env = os.environ.copy()
        env.pop("KC_MIRROR_DATE", None)
        env["PYTHONPATH"] = str(ROOT / "scripts")
        result = subprocess.run(
            [sys.executable, "-c", "import datetime; print(datetime.date.today().isoformat())"],
            check=True,
            capture_output=True,
            text=True,
            env=env,
            cwd=ROOT,
        )
        self.assertNotEqual(result.stdout.strip(), "2026-09-18")
