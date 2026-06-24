#!/usr/bin/env python3
"""Regression tests for Chrome rebinding old-path-drop stress summaries."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from summarize_chrome_rebinding_stress_matrix import emit_markdown, row_from_stress_spec, write_csv
from test_summarize_chrome_rebinding_old_path_drop import write_artifact


def write_spec(artifact_dir: Path, *, profile: str, workload: str, bytes_value: int) -> None:
    path = artifact_dir / "results" / "stress-spec.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "profile": profile,
                "workload": workload,
                "heartbeat": "false" if workload == "downlink" else "n/a",
                "bytes": bytes_value,
                "chunks": 16,
                "duration_ms": 8000,
                "rebind_after": "500ms",
                "drop_a_server_after_switch": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_rows_and_markdown_include_stress_spec() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        downlink = root / "downlink-1m-noheartbeat"
        upload = root / "upload-1m"
        write_artifact(downlink, workload="downlink")
        write_spec(downlink, profile="downlink-1m-noheartbeat", workload="downlink", bytes_value=1048576)
        write_artifact(upload, workload="upload")
        write_spec(upload, profile="upload-1m", workload="upload", bytes_value=1048576)

        rows = [
            row_from_stress_spec(f"downlink:{downlink}"),
            row_from_stress_spec(f"upload:{upload}"),
        ]
        assert rows[0]["profile"] == "downlink-1m-noheartbeat"
        assert rows[0]["configured_bytes"] == "1048576"
        assert rows[1]["upload_sink_request_bytes"] == "262144"
        markdown = emit_markdown(rows)
        assert "configured bytes counts" in markdown
        assert "old-path-unavailable control" in markdown


def test_csv_writer_uses_stable_header() -> None:
    with TemporaryDirectory() as tmp:
        artifact = Path(tmp) / "upload-1m"
        write_artifact(artifact, workload="upload")
        write_spec(artifact, profile="upload-1m", workload="upload", bytes_value=1048576)
        csv_path = Path(tmp) / "stress.csv"
        write_csv([row_from_stress_spec(f"upload:{artifact}")], csv_path)
        text = csv_path.read_text(encoding="utf-8")
        assert text.startswith("profile,workload,run_id,heartbeat")
        assert "configured_bytes" in text.splitlines()[0]


def main() -> int:
    test_rows_and_markdown_include_stress_spec()
    test_csv_writer_uses_stable_header()
    print("summarize_chrome_rebinding_stress_matrix=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
