#!/usr/bin/env python3
"""Regression tests for final handover artifact bundle presence checks."""

from __future__ import annotations

import tempfile
from pathlib import Path

from check_final_handover_trial_artifact_bundle import check_path


def test_file_presence_reports_size() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "server.json"
        path.write_text('{"ok": true}\n', encoding="utf-8")
        result = check_path(path.as_posix(), "server result")
    assert result.exists is True
    assert result.kind == "file"
    assert result.match_count == 1
    assert result.size_bytes > 0


def test_directory_requires_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp) / "qlog"
        directory.mkdir()
        empty = check_path(directory.as_posix(), "server qlog directory")
        (directory / "trace.qlog").write_text("{}\n", encoding="utf-8")
        present = check_path(directory.as_posix(), "server qlog directory")
    assert empty.exists is False
    assert empty.detail == "directory_missing_or_empty"
    assert present.exists is True
    assert present.kind == "directory"
    assert present.match_count == 1


def test_glob_presence_requires_match() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        missing = check_path((root / "ip-route-*.txt").as_posix(), "Android route snapshots")
        (root / "ip-route-before.txt").write_text("default dev wlan0\n", encoding="utf-8")
        present = check_path((root / "ip-route-*.txt").as_posix(), "Android route snapshots")
    assert missing.exists is False
    assert missing.kind == "glob"
    assert present.exists is True
    assert present.match_count == 1


def main() -> int:
    test_file_presence_reports_size()
    test_directory_requires_files()
    test_glob_presence_requires_match()
    print("check_final_handover_trial_artifact_bundle=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
