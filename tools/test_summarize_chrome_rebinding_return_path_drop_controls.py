#!/usr/bin/env python3
"""Regression tests for return-path-drop rebinding control summaries."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from summarize_chrome_rebinding_return_path_drop_controls import emit_markdown, row_from_spec, write_csv


def write_control_artifact(artifact_dir: Path, *, workload: str, expected: str) -> None:
    result_dir = artifact_dir / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    (result_dir / "return-path-drop-spec.json").write_text(
        json.dumps(
            {
                "profile": f"{workload}-{expected.lower()}",
                "workload": workload,
                "bytes": 1048576,
                "chunks": 16,
                "duration_ms": 8000,
                "rebind_after": "500ms",
                "drop_a_server_after_switch": expected == "FAIL",
                "drop_b_server_after_switch": True,
                "expected_status": expected,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    server_requests = [{"path": f"/browser-{workload}", "remote_addr": "127.0.0.1:1"}]
    if workload == "upload":
        server_requests.append({"path": "/upload-sink", "remote_addr": "127.0.0.1:1", "request_bytes": 1048576})
    (result_dir / "server.json").write_text(json.dumps({"requests": server_requests}) + "\n", encoding="utf-8")
    (result_dir / "chrome-summary.json").write_text(
        json.dumps(
            {
                "status": expected,
                "classification": "browser_application_task_failed" if expected == "FAIL" else "nat_rebinding_path_validation_without_observed_tuple_change",
                "dump_application_complete": expected == "PASS",
                "dump_has_chrome_error": False,
                "server_request_count": len(server_requests),
                "server_remote_addr_count": 1,
                "netlog_target_quic_session_count": 1,
                "qlog_has_h3": True,
                "qlog_counts": {"path_challenge": 1, "path_response": 0},
                "rebinding_proxy": {
                    "switched": True,
                    "drop_a_server_after_switch": expected == "FAIL",
                    "drop_b_server_after_switch": True,
                    "dropped_server_packets_a": 4 if expected == "FAIL" else 0,
                    "dropped_server_packets_b": 8,
                    "dropped_server_bytes_a": 800 if expected == "FAIL" else 0,
                    "dropped_server_bytes_b": 1600,
                    "server_packets_a": 4,
                    "server_packets_b": 0,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    logs = artifact_dir / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "rebinding-proxy.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"event": "client_to_server", "upstream": "A", "bytes": 1200}),
                json.dumps({"event": "client_to_server", "upstream": "B", "bytes": 800}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_rows_and_markdown() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        pass_artifact = root / "downlink-pass"
        fail_artifact = root / "upload-fail"
        write_control_artifact(pass_artifact, workload="downlink", expected="PASS")
        write_control_artifact(fail_artifact, workload="upload", expected="FAIL")
        rows = [row_from_spec(f"downlink:{pass_artifact}"), row_from_spec(f"upload:{fail_artifact}")]
        assert rows[0]["status"] == "PASS"
        assert rows[0]["drop_b_server_after_switch"] == "true"
        assert rows[1]["status"] == "FAIL"
        assert rows[1]["upload_sink_request_bytes"] == "1048576"
        markdown = emit_markdown(rows)
        assert "B-only rows" in markdown
        assert "A+B rows" in markdown


def test_csv_writer_uses_stable_header() -> None:
    with TemporaryDirectory() as tmp:
        artifact = Path(tmp) / "downlink-pass"
        write_control_artifact(artifact, workload="downlink", expected="PASS")
        csv_path = Path(tmp) / "controls.csv"
        write_csv([row_from_spec(f"downlink:{artifact}")], csv_path)
        text = csv_path.read_text(encoding="utf-8")
        assert text.startswith("profile,workload,run_id,configured_bytes")
        assert "dropped_server_packets_b" in text.splitlines()[0]


def main() -> int:
    test_rows_and_markdown()
    test_csv_writer_uses_stable_header()
    print("summarize_chrome_rebinding_return_path_drop_controls=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
