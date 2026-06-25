#!/usr/bin/env python3
"""Regression tests for polling transition-zone synthesis."""

from __future__ import annotations

import csv
from pathlib import Path
from tempfile import TemporaryDirectory

from build_polling_transition_zone_table import DATASETS, build_markdown, group_rows, load_rows


FIELDS = [
    "drop_window_ms",
    "status",
    "classification",
    "dump_application_complete",
    "server_request_count",
    "netlog_target_quic_session_count",
    "qlog_path_challenge",
    "qlog_path_response",
]


def write_rows(root: Path, dataset_path: str, rows: list[dict[str, str]]) -> None:
    path = root / dataset_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_polling_synthesis_includes_4000ms_replication_dataset() -> None:
    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        assert any("poll-4000-replication" in path for _, path in DATASETS)
        write_rows(
            root,
            "data/chrome-h3-rebinding-transient-poll-boundary-20260624.csv",
            [
                {
                    "drop_window_ms": "3000",
                    "status": "PASS",
                    "classification": "nat_rebinding_multiple_quic_sessions",
                    "dump_application_complete": "true",
                    "server_request_count": "7",
                    "netlog_target_quic_session_count": "2",
                    "qlog_path_challenge": "0",
                    "qlog_path_response": "0",
                }
            ],
        )
        write_rows(
            root,
            "data/chrome-h3-rebinding-transient-poll-long-boundary-20260624.csv",
            [
                {
                    "drop_window_ms": "4000",
                    "status": "PASS",
                    "classification": "nat_rebinding_multiple_quic_sessions",
                    "dump_application_complete": "true",
                    "server_request_count": "7",
                    "netlog_target_quic_session_count": "2",
                    "qlog_path_challenge": "7",
                    "qlog_path_response": "4",
                },
                {
                    "drop_window_ms": "4000",
                    "status": "FAIL",
                    "classification": "browser_application_task_failed",
                    "dump_application_complete": "false",
                    "server_request_count": "2",
                    "netlog_target_quic_session_count": "2",
                    "qlog_path_challenge": "0",
                    "qlog_path_response": "0",
                },
                {
                    "drop_window_ms": "4000",
                    "status": "FAIL",
                    "classification": "browser_application_task_failed",
                    "dump_application_complete": "false",
                    "server_request_count": "2",
                    "netlog_target_quic_session_count": "2",
                    "qlog_path_challenge": "0",
                    "qlog_path_response": "0",
                },
            ],
        )
        write_rows(
            root,
            "data/chrome-h3-rebinding-transient-poll-4000-replication-20260625.csv",
            [
                {
                    "drop_window_ms": "4000",
                    "status": "FAIL",
                    "classification": "browser_application_task_failed",
                    "dump_application_complete": "false",
                    "server_request_count": "2",
                    "netlog_target_quic_session_count": "2",
                    "qlog_path_challenge": "0",
                    "qlog_path_response": "0",
                }
                for _ in range(3)
            ],
        )

        grouped = group_rows(load_rows(root))
        rows_by_window = {row["drop_window_ms"]: row for row in grouped}
        assert rows_by_window["4000"]["runs"] == "6"
        assert rows_by_window["4000"]["pass_count"] == "1"
        assert rows_by_window["4000"]["fail_count"] == "5"
        markdown = build_markdown(grouped)
        assert "At 4000ms the result remains a transition-zone result: 1/6 PASS and 5/6 FAIL." in markdown


def main() -> int:
    test_polling_synthesis_includes_4000ms_replication_dataset()
    print("build_polling_transition_zone_table=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
