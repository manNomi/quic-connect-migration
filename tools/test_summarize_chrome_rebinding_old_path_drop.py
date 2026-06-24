#!/usr/bin/env python3
"""Regression tests for old-path-drop rebinding summaries."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from summarize_chrome_rebinding_old_path_drop import emit_markdown, row_from_spec, write_csv


def write_artifact(artifact_dir: Path, *, workload: str) -> None:
    result_dir = artifact_dir / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    paths = [f"/browser-{workload}"]
    labels = [f"chrome-rebinding-{workload}"]
    server_requests = []
    if workload == "downlink":
        paths.append("/downlink-stream")
        labels.append("chrome-rebinding-downlink-stream")
    else:
        paths.append("/upload-sink")
        labels.append("chrome-rebinding-upload-sink")
        server_requests = [
            {"path": "/browser-upload", "request_bytes": 0},
            {"path": "/upload-sink", "request_bytes": 262144},
        ]
        (result_dir / "server.json").write_text(json.dumps({"requests": server_requests}) + "\n", encoding="utf-8")
    (result_dir / "chrome-summary.json").write_text(
        json.dumps(
            {
                "status": "PASS",
                "classification": "nat_rebinding_path_validation_without_observed_tuple_change",
                "server_request_paths": paths,
                "server_request_labels": labels,
                "server_requests": server_requests,
                "server_remote_addr_count": 1,
                "netlog_target_quic_session_count": 1,
                "netlog_target_quic_source_ids": ["7"],
                "netlog_target_using_quic_job_count": 2,
                "qlog_counts": {"path_challenge": 1, "path_response": 1},
                "rebinding_proxy": {
                    "switched": True,
                    "upstream_a_addr": "127.0.0.1:1",
                    "upstream_b_addr": "127.0.0.1:2",
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (result_dir / "rebinding-proxy.json").write_text(
        json.dumps(
            {
                "switched": True,
                "drop_a_server_after_switch": True,
                "dropped_server_packets_a": 3,
                "dropped_server_bytes_a": 1200,
                "server_packets_a": 4,
                "server_packets_b": 5,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
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
                ],
            }
        ),
        encoding="utf-8",
    )


def test_rows_and_markdown() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        downlink = root / "downlink-r1"
        upload = root / "upload-r1"
        write_artifact(downlink, workload="downlink")
        write_artifact(upload, workload="upload")
        rows = [
            row_from_spec(f"downlink:{downlink}"),
            row_from_spec(f"upload:{upload}"),
        ]
        assert rows[0]["drop_a_server_after_switch"] == "true"
        assert rows[0]["dropped_server_packets_a"] == "3"
        assert rows[1]["upload_sink_request_bytes"] == "262144"
        markdown = emit_markdown(rows)
        assert "total dropped A-side server packets" in markdown
        assert "old-path-unavailable controls" in markdown


def test_csv_writer_uses_stable_header() -> None:
    with TemporaryDirectory() as tmp:
        artifact = Path(tmp) / "downlink-r1"
        write_artifact(artifact, workload="downlink")
        csv_path = Path(tmp) / "old-path.csv"
        write_csv([row_from_spec(f"downlink:{artifact}")], csv_path)
        text = csv_path.read_text(encoding="utf-8")
        assert text.startswith("workload,run_id,heartbeat,status")
        assert "dropped_server_packets_a" in text.splitlines()[0]


def main() -> int:
    test_rows_and_markdown()
    test_csv_writer_uses_stable_header()
    print("summarize_chrome_rebinding_old_path_drop=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
