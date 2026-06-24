#!/usr/bin/env python3
"""Regression tests for quic-go HTTP/3 mid-flight repetition summaries."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from summarize_quic_go_h3_midflight_matrix import emit_markdown, read_rows, write_csv


def write_case(run_dir: Path, mode: str, *, migration_at: int) -> None:
    case_dir = run_dir / mode
    results = case_dir / "results"
    results.mkdir(parents=True)
    (results / "h3client.json").write_text(
        json.dumps(
            {
                "ok": True,
                "local_addr_changed_to_socket_b": True,
                "tasks": [
                    {
                        "migration_triggered": True,
                        "migration_at_bytes": migration_at,
                        "request_bytes": 1048576 if mode == "midflight-upload" else 0,
                        "response_bytes": 1048576 if mode == "midflight-download" else 0,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (results / "h3server.json").write_text(
        json.dumps({"ok": True, "requests": [{"decode_successful": True}]}),
        encoding="utf-8",
    )
    logs = case_dir / "logs"
    logs.mkdir()
    (logs / "h3client.jsonl").write_text(
        "\n".join(
            [
                '{"event":"midflight_migration_threshold_reached"}',
                '{"event":"path_probe_success"}',
                '{"event":"path_switch_success"}',
                '{"event":"post_migration_addr_checked"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_midflight_summary_rows_and_markdown() -> None:
    with TemporaryDirectory() as tmp:
        run_dir = Path(tmp) / "r1"
        write_case(run_dir, "midflight-upload", migration_at=524288)
        write_case(run_dir, "midflight-download", migration_at=524288)
        rows = read_rows([run_dir])
        assert [row["mode"] for row in rows] == ["midflight-upload", "midflight-download"]
        assert {row["status"] for row in rows} == {"PASS"}
        assert rows[0]["client_migration_event_lines"] == "4"
        markdown = emit_markdown(rows)
        assert "midflight-upload::PASS" in markdown
        assert "library-controlled positive control" in markdown


def test_midflight_csv_writer_uses_stable_header() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        run_dir = root / "r1"
        write_case(run_dir, "midflight-upload", migration_at=524288)
        write_case(run_dir, "midflight-download", migration_at=524288)
        rows = read_rows([run_dir])
        csv_path = root / "out.csv"
        write_csv(rows, csv_path)
        text = csv_path.read_text(encoding="utf-8")
        assert text.startswith("run_id,mode,status,client_ok")
        assert "midflight-download" in text


def main() -> int:
    test_midflight_summary_rows_and_markdown()
    test_midflight_csv_writer_uses_stable_header()
    print("summarize_quic_go_h3_midflight_matrix=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
