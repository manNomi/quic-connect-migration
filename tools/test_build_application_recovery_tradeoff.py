#!/usr/bin/env python3
"""Regression tests for application recovery tradeoff synthesis."""

from __future__ import annotations

import csv
from pathlib import Path
from tempfile import TemporaryDirectory

from build_application_recovery_tradeoff import DATASETS, build_markdown, group_rows, load_rows


FIELDS = [
    "workload",
    "upload_retry_attempts",
    "upload_retry_delay_ms",
    "drop_window_ms",
    "status",
    "classification",
    "dump_application_complete",
    "dump_task_elapsed_ms",
    "dump_task_error_elapsed_ms",
    "netlog_target_quic_session_count",
    "upload_sink_request_count",
    "upload_sink_request_bytes",
]


def write_rows(root: Path, dataset_path: str, rows: list[dict[str, str]]) -> None:
    path = root / dataset_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def upload_row(status: str, retry_delay_ms: str = "0") -> dict[str, str]:
    return {
        "workload": "upload",
        "upload_retry_attempts": "0",
        "upload_retry_delay_ms": retry_delay_ms,
        "drop_window_ms": "4750",
        "status": status,
        "classification": "nat_rebinding_path_validation_without_observed_tuple_change"
        if status == "PASS"
        else "browser_application_task_failed",
        "dump_application_complete": "true" if status == "PASS" else "false",
        "dump_task_elapsed_ms": "10466" if status == "PASS" else "",
        "dump_task_error_elapsed_ms": "" if status == "PASS" else "6920",
        "netlog_target_quic_session_count": "2",
        "upload_sink_request_count": "1",
        "upload_sink_request_bytes": "1048576" if status == "PASS" else "0",
    }


def test_application_recovery_includes_upload_4750ms_replication_dataset() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        assert any("upload-4750-replication" in path for _, path in DATASETS)
        write_rows(
            root,
            "data/chrome-h3-rebinding-transient-upload-fine-boundary-20260624.csv",
            [upload_row("PASS"), upload_row("FAIL"), upload_row("FAIL")],
        )
        write_rows(
            root,
            "data/chrome-h3-rebinding-transient-upload-4750-replication-20260625.csv",
            [upload_row("PASS", "500"), upload_row("PASS", "500"), upload_row("FAIL", "500")],
        )

        grouped = group_rows(load_rows(root))
        rows = [item for item in grouped if item["retry_attempts"] == "0" and item["drop_window_ms"] == "4750"]
        assert len(rows) == 1
        row = rows[0]
        assert row["retry_delay_ms"] == "0"
        assert row["runs"] == "6"
        assert row["pass_count"] == "3"
        assert row["fail_count"] == "3"
        markdown = build_markdown(grouped)
        assert "| 0x/0ms | 4750ms | 3/6 |" in markdown


def main() -> int:
    test_application_recovery_includes_upload_4750ms_replication_dataset()
    print("build_application_recovery_tradeoff=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
