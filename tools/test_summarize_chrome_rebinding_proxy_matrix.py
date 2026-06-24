#!/usr/bin/env python3
"""Regression tests for Chrome rebinding repetition summaries."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from summarize_chrome_rebinding_proxy_matrix import emit_markdown, read_rows, write_csv


def write_summary(artifact_dir: Path, *, heartbeat: bool, classification: str, sessions: int) -> None:
    results = artifact_dir / "results"
    results.mkdir(parents=True)
    paths = ["/browser-downlink", "/downlink-stream"]
    labels = ["chrome-rebinding-downlink", "chrome-rebinding-downlink-stream"]
    if heartbeat:
        paths.append("/heartbeat")
        labels.append("chrome-rebinding-downlink-heartbeat")
    (results / "chrome-summary.json").write_text(
        json.dumps(
            {
                "status": "PASS",
                "classification": classification,
                "server_request_paths": paths,
                "server_request_labels": labels,
                "server_remote_addr_count": 2 if heartbeat else 1,
                "netlog_target_quic_session_count": sessions,
                "netlog_target_quic_source_ids": ["7"],
                "netlog_target_using_quic_job_count": 3 if heartbeat else 2,
                "qlog_counts": {"path_challenge": 1, "path_response": 1},
                "rebinding_proxy": {
                    "switched": True,
                    "upstream_a_addr": "127.0.0.1:4700",
                    "upstream_b_addr": "127.0.0.1:4702",
                },
            }
        ),
        encoding="utf-8",
    )
    logs = artifact_dir / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "rebinding-proxy.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"event": "client_to_server", "upstream": "A", "bytes": 1200}),
                json.dumps({"event": "client_to_server", "upstream": "B", "bytes": 900}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    chrome = artifact_dir / "chrome"
    chrome.mkdir(parents=True, exist_ok=True)
    (chrome / "netlog.json").write_text(
        json.dumps(
            {
                "constants": {
                    "logEventTypes": {
                        "QUIC_SESSION_PATH_CHALLENGE_FRAME_RECEIVED": 1,
                        "QUIC_SESSION_PATH_RESPONSE_FRAME_SENT": 2,
                    }
                },
                "events": [
                    {"type": 1, "source": {"id": 7}},
                    {"type": 2, "source": {"id": 7}},
                    {"type": 1, "source": {"id": 99}},
                ],
            }
        ),
        encoding="utf-8",
    )


def test_summary_rows_and_markdown() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        noheartbeat = root / "noheartbeat-r1"
        heartbeat = root / "heartbeat-r1"
        write_summary(
            noheartbeat,
            heartbeat=False,
            classification="nat_rebinding_path_validation_without_observed_tuple_change",
            sessions=1,
        )
        write_summary(
            heartbeat,
            heartbeat=True,
            classification="nat_rebinding_multiple_quic_sessions",
            sessions=2,
        )
        rows = read_rows([noheartbeat, heartbeat])
        assert rows[0]["heartbeat"] == "noheartbeat"
        assert rows[1]["heartbeat"] == "heartbeat"
        assert rows[1]["netlog_target_quic_session_count"] == "2"
        assert rows[0]["proxy_packet_rebind_observed"] == "true"
        assert rows[0]["netlog_target_path_validation_observed"] == "true"
        markdown = emit_markdown(rows)
        assert "heartbeat::nat_rebinding_multiple_quic_sessions" in markdown
        assert "NetLog target PATH C/R" in markdown
        assert "proxy client packets A/B" in markdown
        assert "final controlled-public browser handover protocol" in markdown


def test_csv_writer_uses_stable_header() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        artifact = root / "heartbeat-r1"
        write_summary(
            artifact,
            heartbeat=True,
            classification="nat_rebinding_multiple_quic_sessions",
            sessions=2,
        )
        rows = read_rows([artifact])
        csv_path = root / "out.csv"
        write_csv(rows, csv_path)
        text = csv_path.read_text(encoding="utf-8")
        assert text.startswith("run_id,heartbeat,status,classification")
        assert "nat_rebinding_multiple_quic_sessions" in text


def main() -> int:
    test_summary_rows_and_markdown()
    test_csv_writer_uses_stable_header()
    print("summarize_chrome_rebinding_proxy_matrix=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
