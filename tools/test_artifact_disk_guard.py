#!/usr/bin/env python3
"""Regression tests for the artifact disk guard shell helper."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


SCRIPT = Path("repro/quic-go-min-repro/scripts/ensure-min-disk-free.sh")


def run_guard(min_gib: str, check_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", SCRIPT.as_posix(), min_gib, check_dir.as_posix()],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_zero_threshold_allows_smoke_tests() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_guard("0", Path(tmp))
        assert result.returncode == 0


def test_unreachable_threshold_blocks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_guard("999999", Path(tmp))
        assert result.returncode == 2
        assert "disk guard failed" in result.stderr


def main() -> int:
    test_zero_threshold_allows_smoke_tests()
    test_unreachable_threshold_blocks()
    print("artifact_disk_guard=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
