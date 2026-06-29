#!/usr/bin/env python3
"""Regression tests for media-segment rebinding artifact summarizer."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from summarize_chrome_rebinding_media_matrix import build_markdown, summarize_artifact


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_summarize_artifact_extracts_media_fields() -> None:
    with tempfile.TemporaryDirectory() as raw:
        base = Path(raw) / "media-run"
        write(
            base / "results" / "chrome-summary.json",
            json.dumps(
                {
                    "status": "PASS",
                    "classification": "nat_rebinding_multiple_quic_sessions",
                    "server_request_count": 4,
                    "server_remote_addr_count": 2,
                    "netlog_target_quic_session_count": 2,
                    "qlog_counts": {"path_challenge": 4, "path_response": 3},
                    "rebinding_proxy": {
                        "drop_a_server_after_switch_for_ms": 3000,
                        "dropped_server_packets_a": 10,
                        "dropped_server_packets_b": 2,
                    },
                }
            ),
        )
        write(
            base / "results" / "server.json",
            json.dumps(
                {
                    "requests": [
                        {"path": "/browser-media-segments", "label": "media"},
                        {"path": "/media-segment", "label": "media-1"},
                        {"path": "/media-segment", "label": "media-2"},
                        {"path": "/media-segment", "label": "media-2"},
                    ]
                }
            ),
        )
        write(
            base / "chrome" / "dump-dom.txt",
            '<body data-media-complete="true" data-media-completed-count="2" '
            'data-media-retries-used="0" data-media-bytes="2048" data-media-elapsed-ms="1234">'
            '<script>const count=2,interval=500,segmentUrlPrefix="/media-segment?bytes=1024&duration_ms=100&chunks=2&label=media",retryAttempts=0;</script>'
            "</body>",
        )
        row = summarize_artifact(base, "video-like")
        assert row["profile"] == "video-like"
        assert row["drop_window_ms"] == "3000"
        assert row["segments"] == "2"
        assert row["segment_bytes"] == "1024"
        assert row["segment_duration_ms"] == "100"
        assert row["segment_interval_ms"] == "500"
        assert row["media_complete"] == "true"
        assert row["duplicate_segment_requests"] == "1"
        assert "multiple target QUIC sessions" in row["notes"]


def test_build_markdown_contains_boundary() -> None:
    text = build_markdown(
        [
            {
                "profile": "music-like",
                "trial_id": "run-1",
                "drop_window_ms": "6000",
                "retry_attempts": "0",
                "segments": "4",
                "segment_bytes": "8192",
                "segment_duration_ms": "50",
                "segment_interval_ms": "1000",
                "status": "PASS",
                "classification": "nat_rebinding_multiple_quic_sessions",
                "media_complete": "true",
                "media_completed_count": "4",
                "media_retries_used": "0",
                "media_bytes": "32768",
                "media_elapsed_ms": "4500",
                "media_error_elapsed_ms": "",
                "server_request_count": "5",
                "duplicate_segment_requests": "0",
                "server_remote_addr_count": "2",
                "chrome_quic_sessions": "2",
                "qlog_path_challenge": "4",
                "qlog_path_response": "2",
                "dropped_server_packets_a": "10",
                "dropped_server_packets_b": "2",
                "artifact_dir": "artifacts/run-1",
                "notes": "",
            }
        ],
        "data/out.csv",
    )
    assert "not single-session QUIC Connection Migration" in text
    assert "music-like" in text


def main() -> int:
    test_summarize_artifact_extracts_media_fields()
    test_build_markdown_contains_boundary()
    print("summarize_chrome_rebinding_media_matrix=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
