#!/usr/bin/env python3
"""Regression tests for range-download rebinding artifact summarizer."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from summarize_chrome_rebinding_range_matrix import build_markdown, summarize_artifact


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_summarize_artifact_extracts_range_fields() -> None:
    with tempfile.TemporaryDirectory() as raw:
        base = Path(raw) / "range-run"
        write(
            base / "results" / "chrome-summary.json",
            json.dumps(
                {
                    "status": "PASS",
                    "classification": "nat_rebinding_multiple_quic_sessions",
                    "server_request_count": 10,
                    "server_remote_addr_count": 2,
                    "netlog_target_quic_session_count": 2,
                    "qlog_counts": {"path_challenge": 7, "path_response": 3},
                    "rebinding_proxy": {
                        "drop_a_server_after_switch_for_ms": 6000,
                        "dropped_server_packets_a": 12,
                        "dropped_server_packets_b": 5,
                    },
                }
            ),
        )
        write(
            base / "chrome" / "dump-dom.txt",
            '<body data-range-complete="true" data-range-completed-bytes="1048576" '
            'data-range-completed-chunks="8" data-range-retries-used="1" data-range-elapsed-ms="15000">'
            '<script>const totalBytes=1048576,rangeBytes=131072,rangeUrl="/range-download?bytes=1048576",retryAttempts=2;</script>'
            "</body>",
        )
        row = summarize_artifact(base, "range")
        assert row["profile"] == "range"
        assert row["drop_window_ms"] == "6000"
        assert row["retry_attempts"] == "2"
        assert row["total_bytes"] == "1048576"
        assert row["range_bytes"] == "131072"
        assert row["range_complete"] == "true"
        assert row["range_retries_used"] == "1"
        assert "failed byte range" in row["notes"]


def test_build_markdown_contains_boundary() -> None:
    text = build_markdown(
        [
            {
                "profile": "range",
                "trial_id": "run-1",
                "drop_window_ms": "6000",
                "retry_attempts": "2",
                "total_bytes": "1048576",
                "range_bytes": "131072",
                "status": "PASS",
                "classification": "nat_rebinding_multiple_quic_sessions",
                "range_complete": "true",
                "range_completed_bytes": "1048576",
                "range_completed_chunks": "8",
                "range_retries_used": "1",
                "range_elapsed_ms": "15000",
                "range_error_elapsed_ms": "",
                "server_request_count": "10",
                "server_remote_addr_count": "2",
                "chrome_quic_sessions": "2",
                "qlog_path_challenge": "7",
                "qlog_path_response": "3",
                "dropped_server_packets_a": "12",
                "dropped_server_packets_b": "5",
                "artifact_dir": "artifacts/run-1",
                "notes": "",
            }
        ],
        "data/out.csv",
    )
    assert "resumable application-level download continuity" in text
    assert "byte-range retry" in text


def main() -> int:
    test_summarize_artifact_extracts_range_fields()
    test_build_markdown_contains_boundary()
    print("summarize_chrome_rebinding_range_matrix=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
