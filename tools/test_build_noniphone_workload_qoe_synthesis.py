#!/usr/bin/env python3
"""Regression tests for non-iPhone workload QoE synthesis."""

from __future__ import annotations

import csv
import tempfile
from pathlib import Path

from build_noniphone_workload_qoe_synthesis import (
    SourceSpec,
    build_synthesis,
    emit_markdown,
)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_synthesis_groups_completion_and_qoe() -> None:
    with tempfile.TemporaryDirectory() as raw:
        base = Path(raw)
        media = base / "media.csv"
        buffered = base / "buffered.csv"
        upload = base / "upload.csv"
        write_csv(
            media,
            [
                "status",
                "media_complete",
                "retry_attempts",
                "drop_window_ms",
                "chrome_quic_sessions",
                "qlog_path_challenge",
                "qlog_path_response",
                "media_elapsed_ms",
            ],
            [
                {
                    "status": "FAIL",
                    "media_complete": "",
                    "retry_attempts": "0",
                    "drop_window_ms": "6000",
                    "chrome_quic_sessions": "2",
                    "qlog_path_challenge": "0",
                    "qlog_path_response": "0",
                    "media_elapsed_ms": "",
                },
                {
                    "status": "PASS",
                    "media_complete": "true",
                    "retry_attempts": "1",
                    "drop_window_ms": "6000",
                    "chrome_quic_sessions": "3",
                    "qlog_path_challenge": "1",
                    "qlog_path_response": "1",
                    "media_elapsed_ms": "12000",
                },
            ],
        )
        write_csv(
            buffered,
            [
                "status",
                "buffered_media_complete",
                "retry_attempts",
                "drop_window_ms",
                "chrome_quic_sessions",
                "qlog_path_challenge",
                "qlog_path_response",
                "elapsed_ms",
                "rebuffer_events",
                "startup_elapsed_ms",
            ],
            [
                {
                    "status": "PASS",
                    "buffered_media_complete": "true",
                    "retry_attempts": "0",
                    "drop_window_ms": "3000",
                    "chrome_quic_sessions": "2",
                    "qlog_path_challenge": "3",
                    "qlog_path_response": "2",
                    "elapsed_ms": "22000",
                    "rebuffer_events": "14",
                    "startup_elapsed_ms": "80",
                }
            ],
        )
        write_csv(
            upload,
            [
                "status",
                "upload_sink_request_bytes",
                "netlog_target_quic_session_count",
                "qlog_path_challenge",
                "qlog_path_response",
                "server_remote_addr_count",
            ],
            [
                {
                    "status": "PASS",
                    "upload_sink_request_bytes": "131072",
                    "netlog_target_quic_session_count": "1",
                    "qlog_path_challenge": "1",
                    "qlog_path_response": "1",
                    "server_remote_addr_count": "1",
                }
            ],
        )
        payload = build_synthesis(
            [
                SourceSpec(media.as_posix(), "media", "music-like segment", "media"),
                SourceSpec(buffered.as_posix(), "buffered", "buffered video playback", "buffered"),
                SourceSpec(upload.as_posix(), "upload", "large upload", "upload"),
            ]
        )
        groups = {item["workload_group"]: item for item in payload["groups"]}
        assert groups["music-like segment"]["completion_rate"] == "1/2"
        assert groups["music-like segment"]["retry_profile"] == "0:1, 1:1"
        assert "rebuffer 14-14" in groups["buffered video playback"]["qoe_signal"]
        assert groups["large upload"]["single_session_rows"] == "1"
        text = emit_markdown(payload, "data/out.csv")
        assert "Do not call retry/reconnect recovery single-session CM" in text


def main() -> int:
    test_synthesis_groups_completion_and_qoe()
    print("build_noniphone_workload_qoe_synthesis=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
