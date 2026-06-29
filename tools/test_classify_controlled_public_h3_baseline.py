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


def test_downlink_complete_with_retry_last_error_marks_application_success(tmp_path: Path) -> None:
    write_cdp_summary(
        tmp_path,
        {
            "downlinkAttempt": "2",
            "downlinkComplete": "true",
            "downlinkBytes": "65536",
            "downlinkLastError": "AbortError: BodyStreamBuffer was aborted",
            "downlinkRetriesUsed": "1",
        },
    )
    summary = application_summary(tmp_path)
    assert summary["workload"] == "downlink"
    assert summary["complete"] is True
    assert summary["success"] is True
    assert summary["error_keys"] == ["downlinkLastError"]
    assert summary["terminal_error_keys"] == []


def test_poll_complete_marks_application_success(tmp_path: Path) -> None:
    write_cdp_summary(tmp_path, {"pollComplete": "true"})
    summary = application_summary(tmp_path)
    assert summary["workload"] == "poll"
    assert summary["complete"] is True
    assert summary["success"] is True


def test_poll_error_marks_application_failure(tmp_path: Path) -> None:
    write_cdp_summary(tmp_path, {"pollError": "TypeError: Failed to fetch"})
    summary = application_summary(tmp_path)
    assert summary["workload"] == "poll"
    assert summary["complete"] is False
    assert summary["success"] is False
    assert summary["terminal_error_keys"] == ["pollError"]


def test_media_complete_marks_application_success(tmp_path: Path) -> None:
    write_cdp_summary(tmp_path, {"mediaComplete": "true", "mediaCompletedCount": "6"})
    summary = application_summary(tmp_path)
    assert summary["workload"] == "media"
    assert summary["complete"] is True
    assert summary["success"] is True


def test_media_error_marks_application_failure(tmp_path: Path) -> None:
    write_cdp_summary(tmp_path, {"mediaCompletedCount": "2", "mediaError": "TypeError: Failed to fetch"})
    summary = application_summary(tmp_path)
    assert summary["workload"] == "media"
    assert summary["complete"] is False
    assert summary["success"] is False
    assert summary["terminal_error_keys"] == ["mediaError"]


def main() -> int:
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as first:
        test_downlink_dataset_error_marks_application_failure(Path(first))
    with TemporaryDirectory() as second:
        test_downlink_complete_without_error_marks_application_success(Path(second))
    with TemporaryDirectory() as third:
        test_downlink_complete_with_retry_last_error_marks_application_success(Path(third))
    with TemporaryDirectory() as fourth:
        test_poll_complete_marks_application_success(Path(fourth))
    with TemporaryDirectory() as fifth:
        test_poll_error_marks_application_failure(Path(fifth))
    with TemporaryDirectory() as sixth:
        test_media_complete_marks_application_success(Path(sixth))
    with TemporaryDirectory() as seventh:
        test_media_error_marks_application_failure(Path(seventh))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
