#!/usr/bin/env python3
"""Regression test for the final P0 baseline preflight wrapper."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "harness" / "scripts" / "final-p0-baseline-preflight.sh"


def run_wrapper(tmp: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update(
        {
            "CONTROLLED_PUBLIC_CONFIG": (tmp / "missing-controlled-public-origin.env").as_posix(),
            "FINAL_P0_PREFLIGHT_OUTPUT_DIR": (tmp / "preflight-results").as_posix(),
            "CONTROLLED_PUBLIC_READINESS_TIMEOUT": "1",
            "CHECK_LOCAL_FILES": "0",
            "CHECK_PUBLIC_ORIGIN": "0",
        }
    )
    return subprocess.run(
        ["bash", WRAPPER.as_posix()],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )


def test_wrapper_fails_closed_without_private_config() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        proc = run_wrapper(tmp)
        output_dir = tmp / "preflight-results"
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 1
        assert "final_p0_baseline_preflight=blocked" in proc.stdout
        assert "controlled_public_config=blocked" in proc.stdout
        assert "p0_baseline_preflight_guard=blocked" in proc.stdout
        assert (output_dir / "controlled-public-config-check.md").exists()
        assert (output_dir / "p0-baseline-preflight-check.md").exists()
        assert "AKIA" not in combined
        assert "PRIVATE_KEY" not in combined


def main() -> int:
    test_wrapper_fails_closed_without_private_config()
    print("final_p0_baseline_preflight_wrapper=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
