#!/usr/bin/env python3
"""Regression tests for Chrome rebinding timing-sensitivity summaries."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from summarize_chrome_rebinding_timing_sensitivity import emit_markdown, row_from_spec, write_csv


def write_common_artifact(artifact_dir: Path, *, workload: str, heartbeat: bool = False) -> None:
    results = artifact_dir / "results"
    results.mkdir(parents=True, exist_ok=True)
    paths = [f"/browser-{workload}"]
    labels = [f"chrome-rebinding-{workload}"]
    server_requests = []
    if workload == "downlink":
        paths.append("/downlink-stream")
        labels.append("chrome-rebinding-downlink-stream")
        if heartbeat:
            paths.append("/heartbeat")
            labels.append("chrome-rebinding-downlink-heartbeat")
    else:
        paths.append("/upload-sink")
        labels.append("chrome-rebinding-upload-sink")
        server_requests = [
            {"path": "/browser-upload", "request_bytes": 0},
            {"path": "/upload-sink", "request_bytes": 262144},
        ]
        (results / "server.json").write_text(json.dumps({"requests": server_requests}) + "\n", encoding="utf-8")

    summary = {
        "status": "PASS",
        "classification": "nat_rebinding_path_validation_without_observed_tuple_change",
        "server_request_paths": paths,
        "server_request_labels": labels,
        "server_requests": server_requests,
        "server_remote_addr_count": 1,
        "netlog_target_quic_session_count": 1,
        "netlog_target_quic_source_ids": ["7"],
        "netlog_target_using_quic_job_count": len(paths),
        "qlog_counts": {"path_challenge": 1, "path_response": 1},
        "rebinding_proxy": {
            "switched": True,
            "upstream_a_addr": "127.0.0.1:1",
            "upstream_b_addr": "127.0.0.1:2",
        },
    }
    (results / "chrome-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    logs = artifact_dir / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "rebinding-proxy.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"event": "client_to_server", "upstream": "A", "bytes": 1200}),
                json.dumps({"event": "client_to_server", "upstream": "B", "bytes": 800}),
                json.dumps({"event": "client_to_server", "upstream": "B", "bytes": 600}),
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
        write_common_artifact(downlink, workload="downlink", heartbeat=True)
        write_common_artifact(upload, workload="upload")
        rows = [
            row_from_spec(f"downlink:early:500ms:{downlink}"),
            row_from_spec(f"upload:late:5s:{upload}"),
        ]
        assert rows[0]["heartbeat"] == "heartbeat"
        assert rows[0]["proxy_client_packet_share_b"] == "0.667"
        assert rows[1]["upload_sink_request_bytes"] == "262144"
        assert rows[1]["qlog_path_validation_observed"] == "true"
        markdown = emit_markdown(rows)
        assert "Timing Groups" in markdown
        assert "downlink" in markdown
        assert "upload" in markdown
        assert "controlled-public active browser handover protocol" in markdown


def test_csv_writer_uses_stable_header() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        artifact = root / "upload-r1"
        write_common_artifact(artifact, workload="upload")
        rows = [row_from_spec(f"upload:early:500ms:{artifact}")]
        csv_path = root / "timing.csv"
        write_csv(rows, csv_path)
        text = csv_path.read_text(encoding="utf-8")
        assert text.startswith("workload,timing,rebinding_after,run_id")
        assert "proxy_client_packet_share_b" in text.splitlines()[0]


def main() -> int:
    test_rows_and_markdown()
    test_csv_writer_uses_stable_header()
    print("summarize_chrome_rebinding_timing_sensitivity=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
