#!/usr/bin/env python3
"""Regression test for the final handover registration wrapper."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "harness" / "scripts" / "final-handover-register-trial.sh"


def test_wrapper_fails_closed_without_artifacts() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        output_dir = tmp / "registration-results"
        env = dict(os.environ)
        env.update(
            {
                "TRIAL_ID": "controlled-public-chrome-h3-baseline-001",
                "ARTIFACT_DIR": (tmp / "missing-artifacts").as_posix(),
                "FINAL_HANDOVER_REGISTRATION_OUTPUT_DIR": output_dir.as_posix(),
                "APPLY": "0",
            }
        )
        proc = subprocess.run(
            ["bash", WRAPPER.as_posix()],
            cwd=ROOT,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 1
        assert "final_handover_registration=blocked" in proc.stdout
        assert "artifact_bundle_check=blocked" in proc.stdout
        assert "append_apply=skipped" in proc.stdout
        assert (output_dir / "artifact-bundle-check.md").exists()
        assert not (output_dir / "append-apply.md").exists()
        assert "AKIA" not in combined
        assert "PRIVATE_KEY" not in combined


def main() -> int:
    test_wrapper_fails_closed_without_artifacts()
    print("final_handover_register_trial_wrapper=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
