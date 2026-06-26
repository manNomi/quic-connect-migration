#!/usr/bin/env python3
"""Regression tests for controlled-public baseline classification helpers."""

from __future__ import annotations

import json
from pathlib import Path

from classify_controlled_public_h3_baseline import application_summary


def write_cdp_summary(root: Path, dataset: dict[str, str]) -> None:
    chrome = root / "chrome"
    chrome.mkdir(parents=True)
    (chrome / "cdp-summary.json").write_text(
        json.dumps({"page_state": {"body_dataset": dataset}}),
        encoding="utf-8",
    )


def test_downlink_dataset_error_marks_application_failure(tmp_path: Path) -> None:
    write_cdp_summary(
        tmp_path,
        {
            "downlinkAttempt": "1",
            "downlinkBytes": "8762",
            "downlinkError": "Error: TypeError: network error",
        },
    )
    summary = application_summary(tmp_path)
    assert summary["workload"] == "downlink"
    assert summary["complete"] is False
    assert summary["success"] is False
    assert summary["error_keys"] == ["downlinkError"]


def test_downlink_complete_without_error_marks_application_success(tmp_path: Path) -> None:
    write_cdp_summary(tmp_path, {"downlinkComplete": "true", "downlinkBytes": "65536"})
    summary = application_summary(tmp_path)
    assert summary["workload"] == "downlink"
    assert summary["complete"] is True
    assert summary["success"] is True


def main() -> int:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as first:
        test_downlink_dataset_error_marks_application_failure(Path(first))
    with TemporaryDirectory() as second:
        test_downlink_complete_without_error_marks_application_success(Path(second))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
