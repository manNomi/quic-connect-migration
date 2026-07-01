#!/usr/bin/env python3
"""Regression tests for buffered-media rebinding artifact summarizer."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from summarize_chrome_rebinding_buffered_media_matrix import build_markdown, summarize_artifact


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_summarize_artifact_extracts_buffered_media_fields() -> None:
    with tempfile.TemporaryDirectory() as raw:
        base = Path(raw) / "buffered-run"
        write(
            base / "results" / "chrome-summary.json",
            json.dumps(
                {
                    "status": "PASS",
                    "classification": "nat_rebinding_multiple_quic_sessions",
                    "server_request_count": 9,
                    "server_remote_addr_count": 2,
                    "netlog_target_quic_session_count": 2,
                    "qlog_counts": {"path_challenge": 3, "path_response": 2},
                    "rebinding_proxy": {
                        "drop_a_server_after_switch_for_ms": 3000,
                        "dropped_server_packets_a": 10,
                        "dropped_server_packets_b": 2,
                    },
                }
            ),
        )
        write(
            base / "chrome" / "dump-dom.txt",
            '<body data-buffered-media-complete="true" data-buffered-media-played-count="8" '
            'data-buffered-media-fetched-count="8" data-buffered-media-rebuffer-events="3" '
            'data-buffered-media-retries-used="0" data-buffered-media-elapsed-ms="11000" '
            'data-buffered-media-startup-elapsed-ms="100">'
            '<script>const count=8,playbackInterval=1000,startupBuffer=1,maxBuffer=1,retryAttempts=0;</script>'
            "</body>",
        )
        row = summarize_artifact(base, "low-buffer")
        assert row["profile"] == "low-buffer"
        assert row["drop_window_ms"] == "3000"
        assert row["segments"] == "8"
        assert row["startup_buffer_segments"] == "1"
        assert row["max_buffer_segments"] == "1"
        assert row["rebuffer_events"] == "3"
        assert "rebuffer event" in row["notes"]


def test_build_markdown_contains_boundary() -> None:
    text = build_markdown(
        [
            {
                "profile": "high-buffer",
                "trial_id": "run-1",
                "drop_window_ms": "3000",
                "retry_attempts": "0",
                "segments": "8",
                "startup_buffer_segments": "4",
                "max_buffer_segments": "6",
                "playback_interval_ms": "1000",
                "status": "PASS",
                "classification": "nat_rebinding_multiple_quic_sessions",
                "buffered_media_complete": "true",
                "played_count": "8",
                "fetched_count": "8",
                "rebuffer_events": "0",
                "retries_used": "0",
                "elapsed_ms": "23000",
                "startup_elapsed_ms": "15000",
                "server_request_count": "9",
                "server_remote_addr_count": "2",
                "chrome_quic_sessions": "2",
                "qlog_path_challenge": "3",
                "qlog_path_response": "2",
                "dropped_server_packets_a": "10",
                "dropped_server_packets_b": "2",
                "artifact_dir": "artifacts/run-1",
                "notes": "",
            }
        ],
        "data/out.csv",
    )
    assert "playback-level continuity" in text
    assert "startup delay and rebuffer events" in text
    assert "UTC /" in text


def main() -> int:
    test_summarize_artifact_extracts_buffered_media_fields()
    test_build_markdown_contains_boundary()
    print("summarize_chrome_rebinding_buffered_media_matrix=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
