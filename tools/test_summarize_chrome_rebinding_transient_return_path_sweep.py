#!/usr/bin/env python3
"""Regression tests for transient return-path outage sweep summaries."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from summarize_chrome_rebinding_transient_return_path_sweep import emit_markdown, local_boundary_summary, row_from_spec, write_csv


def write_sweep_artifact(artifact_dir: Path, *, workload: str, status: str, drop_window_ms: int) -> None:
    result_dir = artifact_dir / "results"
    result_dir.mkdir(parents=True, exist_ok=True)
    (result_dir / "transient-return-path-spec.json").write_text(
        json.dumps(
            {
                "profile": f"{workload}-{drop_window_ms}ms",
                "workload": workload,
                "bytes": 1048576,
                "chunks": 16,
                "duration_ms": 8000,
                "rebind_after": "500ms",
                "drop_a_server_after_switch": True,
                "drop_b_server_after_switch": True,
                "drop_window": f"{drop_window_ms}ms",
                "drop_window_ms": drop_window_ms,
                "expected_status": "MEASURE",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    server_requests = [{"path": f"/browser-{workload}", "remote_addr": "127.0.0.1:1"}]
    if workload == "upload":
        server_requests.append({"path": "/upload-sink", "remote_addr": "127.0.0.1:1", "request_bytes": 1048576 if status == "PASS" else 0})
    (result_dir / "server.json").write_text(json.dumps({"requests": server_requests}) + "\n", encoding="utf-8")
    (result_dir / "chrome-summary.json").write_text(
        json.dumps(
            {
                "status": status,
                "classification": "browser_application_task_failed" if status == "FAIL" else "nat_rebinding_path_validation_without_observed_tuple_change",
                "dump_application_complete": status == "PASS",
                "dump_task_elapsed_ms": 8123 if status == "PASS" else None,
                "dump_task_error_elapsed_ms": None,
                "dump_has_chrome_error": False,
                "server_request_count": len(server_requests),
                "server_remote_addr_count": 1,
                "netlog_target_quic_session_count": 1,
                "qlog_has_h3": True,
                "qlog_counts": {"path_challenge": 2, "path_response": 1},
                "rebinding_proxy": {
                    "switched": True,
                    "drop_a_server_after_switch": True,
                    "drop_b_server_after_switch": True,
                    "drop_a_server_after_switch_for_ms": drop_window_ms,
                    "drop_b_server_after_switch_for_ms": drop_window_ms,
                    "dropped_server_packets_a": 4,
                    "dropped_server_packets_b": 8,
                    "dropped_server_bytes_a": 800,
                    "dropped_server_bytes_b": 1600,
                    "server_packets_a": 4,
                    "server_packets_b": 2 if status == "PASS" else 0,
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
                json.dumps({"event": "server_to_client_dropped", "upstream": "A", "bytes": 1200, "since_switch_ms": drop_window_ms - 1}),
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
        write_sweep_artifact(pass_artifact, workload="downlink", status="PASS", drop_window_ms=250)
        write_sweep_artifact(fail_artifact, workload="upload", status="FAIL", drop_window_ms=3000)
        rows = [row_from_spec(f"downlink:{pass_artifact}"), row_from_spec(f"upload:{fail_artifact}")]
        assert rows[0]["status"] == "PASS"
        assert rows[0]["drop_window"] == "250ms"
        assert rows[0]["dump_task_elapsed_ms"] == "8123"
        assert rows[1]["status"] == "FAIL"
        assert rows[1]["max_drop_since_switch_ms"] == "2999"
        markdown = emit_markdown(rows)
        assert "transient outage tolerance" in markdown
        assert "status by drop window" in markdown
        assert "max PASS window `250ms`; min later FAIL window `3000ms`" in markdown
        assert local_boundary_summary(rows) == "Observed local boundary: max PASS window `250ms`; min later FAIL window `3000ms`."


def test_csv_writer_uses_stable_header() -> None:
    with TemporaryDirectory() as tmp:
        artifact = Path(tmp) / "downlink-pass"
        write_sweep_artifact(artifact, workload="downlink", status="PASS", drop_window_ms=250)
        csv_path = Path(tmp) / "sweep.csv"
        write_csv([row_from_spec(f"downlink:{artifact}")], csv_path)
        text = csv_path.read_text(encoding="utf-8")
        assert text.startswith("profile,workload,run_id,configured_bytes")
        assert "drop_window_ms" in text.splitlines()[0]
        assert "dump_task_elapsed_ms" in text.splitlines()[0]


def main() -> int:
    test_rows_and_markdown()
    test_csv_writer_uses_stable_header()
    print("summarize_chrome_rebinding_transient_return_path_sweep=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
