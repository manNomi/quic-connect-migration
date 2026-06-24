#!/usr/bin/env python3
"""Regression tests for Chrome UDP rebinding upload matrix summarizer."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from summarize_chrome_rebinding_upload_matrix import emit_markdown, read_rows


def write_summary(artifact_dir: Path, *, classification: str, sessions: int, upload_bytes: int) -> None:
    result_dir = artifact_dir / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": "PASS",
        "classification": classification,
        "server_remote_addr_count": 1,
        "netlog_target_quic_session_count": sessions,
        "netlog_target_using_quic_job_count": 2,
        "qlog_counts": {"path_challenge": 1, "path_response": 1},
        "server_requests": [
            {"path": "/browser-upload", "request_bytes": 0},
            {"path": "/upload-sink", "request_bytes": upload_bytes},
        ],
        "rebinding_proxy": {
            "switched": True,
            "upstream_a_addr": "127.0.0.1:1",
            "upstream_b_addr": "127.0.0.1:2",
        },
    }
    (result_dir / "chrome-summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    server = {
        "requests": [
            {"path": "/browser-upload", "request_bytes": 0},
            {"path": "/upload-sink", "request_bytes": upload_bytes},
        ]
    }
    (result_dir / "server.json").write_text(json.dumps(server, indent=2) + "\n", encoding="utf-8")
    log_dir = artifact_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / "rebinding-proxy.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"event": "client_to_server", "upstream": "A", "bytes": 1200}),
                json.dumps({"event": "client_to_server", "upstream": "B", "bytes": 800}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_upload_rows_include_sink_bytes() -> None:
    with TemporaryDirectory() as tmp:
        artifact = Path(tmp) / "upload-r1"
        write_summary(
            artifact,
            classification="nat_rebinding_path_validation_without_observed_tuple_change",
            sessions=1,
            upload_bytes=262144,
        )
        rows = read_rows([artifact])
        assert rows[0]["upload_sink_request_count"] == "1"
        assert rows[0]["upload_sink_request_bytes"] == "262144"
        assert rows[0]["proxy_switched"] == "true"
        assert rows[0]["proxy_client_packets_a"] == "1"
        assert rows[0]["proxy_client_packets_b"] == "1"
        assert rows[0]["proxy_packet_rebind_observed"] == "true"
        markdown = emit_markdown(rows)
        assert "Chrome H3 Local UDP Rebinding Upload Summary" in markdown
        assert "262144" in markdown
        assert "packet rebinding observed counts" in markdown


def main() -> int:
    test_upload_rows_include_sink_bytes()
    print("summarize_chrome_rebinding_upload_matrix=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
