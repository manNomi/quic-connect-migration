#!/usr/bin/env python3
"""Regression tests for workload transition-zone synthesis."""

from __future__ import annotations

import csv
from pathlib import Path
from tempfile import TemporaryDirectory

from build_workload_transition_zone_table import DATASETS, build_markdown, group_rows, load_rows


FIELDS = [
    "workload",
    "drop_window_ms",
    "status",
    "classification",
    "dump_application_complete",
    "dump_task_elapsed_ms",
    "dump_task_error_elapsed_ms",
    "netlog_target_quic_session_count",
]


def write_rows(root: Path, dataset_path: str, rows: list[dict[str, str]]) -> None:
    path = root / dataset_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def transition_row(workload: str, drop_window_ms: str, status: str, complete: str) -> dict[str, str]:
    return {
        "workload": workload,
        "drop_window_ms": drop_window_ms,
        "status": status,
        "classification": "nat_rebinding_path_validation_without_observed_tuple_change"
        if status == "PASS"
        else "browser_application_task_failed",
        "dump_application_complete": complete,
        "dump_task_elapsed_ms": "10466" if status == "PASS" else "",
        "dump_task_error_elapsed_ms": "" if status == "PASS" else "6920",
        "netlog_target_quic_session_count": "2",
    }


def test_workload_synthesis_includes_upload_4750ms_replication_dataset() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        assert any("upload-4750-replication" in path for _, path in DATASETS)
        write_rows(
            root,
            "data/chrome-h3-rebinding-transient-upload-fine-boundary-20260624.csv",
            [
                transition_row("upload", "4750", "PASS", "true"),
                transition_row("upload", "4750", "FAIL", "false"),
                transition_row("upload", "4750", "FAIL", "false"),
            ],
        )
        write_rows(
            root,
            "data/chrome-h3-rebinding-transient-upload-4750-replication-20260625.csv",
            [
                transition_row("upload", "4750", "PASS", "true"),
                transition_row("upload", "4750", "PASS", "true"),
                transition_row("upload", "4750", "FAIL", "false"),
            ],
        )

        grouped = group_rows(load_rows(root))
        rows_by_key = {(row["workload"], row["drop_window_ms"]): row for row in grouped}
        upload_4750 = rows_by_key[("upload", "4750")]
        assert upload_4750["runs"] == "6"
        assert upload_4750["pass_count"] == "3"
        assert upload_4750["fail_count"] == "3"
        markdown = build_markdown(grouped)
        assert "remains mixed at 4750ms (3/6 PASS)" in markdown


def test_workload_synthesis_includes_downlink_5000_5500ms_replication_dataset() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        assert any("downlink-5000-5500-replication" in path for _, path in DATASETS)
        write_rows(
            root,
            "data/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624.csv",
            [
                transition_row("downlink", "5000", "PASS", "true"),
                transition_row("downlink", "5000", "PASS", "true"),
                transition_row("downlink", "5000", "FAIL", "false"),
                transition_row("downlink", "5500", "PASS", "true"),
                transition_row("downlink", "5500", "PASS", "true"),
                transition_row("downlink", "5500", "FAIL", "false"),
            ],
        )
        write_rows(
            root,
            "data/chrome-h3-rebinding-transient-downlink-5000-5500-replication-20260625.csv",
            [
                transition_row("downlink", "5000", "PASS", "true"),
                transition_row("downlink", "5000", "PASS", "true"),
                transition_row("downlink", "5000", "PASS", "true"),
                transition_row("downlink", "5500", "PASS", "true"),
                transition_row("downlink", "5500", "PASS", "true"),
                transition_row("downlink", "5500", "FAIL", "false"),
            ],
        )

        grouped = group_rows(load_rows(root))
        rows_by_key = {(row["workload"], row["drop_window_ms"]): row for row in grouped}
        assert rows_by_key[("downlink", "5000")]["pass_count"] == "5"
        assert rows_by_key[("downlink", "5000")]["runs"] == "6"
        assert rows_by_key[("downlink", "5500")]["pass_count"] == "4"
        assert rows_by_key[("downlink", "5500")]["runs"] == "6"
        markdown = build_markdown(grouped)
        assert "Downlink remains mixed at 5000ms (5/6 PASS) and 5500ms (4/6 PASS)" in markdown


def main() -> int:
    test_workload_synthesis_includes_upload_4750ms_replication_dataset()
    test_workload_synthesis_includes_downlink_5000_5500ms_replication_dataset()
    print("build_workload_transition_zone_table=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
