#!/usr/bin/env python3
"""Summarize quic-go HTTP/3 mid-flight migration repetition artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from research_clock import utc_date_iso
from pathlib import Path
from typing import Any


MODES = ("midflight-upload", "midflight-download")
CSV_FIELDS = [
    "run_id",
    "mode",
    "status",
    "client_ok",
    "server_ok",
    "local_addr_changed_to_socket_b",
    "migration_triggered",
    "migration_at_bytes",
    "request_bytes",
    "response_bytes",
    "server_decode_successful",
    "client_migration_event_lines",
    "artifact_dir",
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def client_migration_event_lines(case_dir: Path) -> int:
    path = case_dir / "logs" / "h3client.jsonl"
    if not path.exists():
        return 0
    needles = (
        "midflight_migration_threshold_reached",
        "switch_before_probe_checked",
        "path_probe_success",
        "path_switch_success",
        "post_migration_addr_checked",
    )
    return sum(1 for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if any(needle in line for needle in needles))


def bool_cell(value: Any) -> str:
    return str(value is True).lower()


def status_for(client: dict[str, Any], server: dict[str, Any], task: dict[str, Any], request: dict[str, Any]) -> str:
    checks = [
        client.get("ok") is True,
        server.get("ok") is True,
        client.get("local_addr_changed_to_socket_b") is True,
        task.get("migration_triggered") is True,
        request.get("decode_successful") is True,
    ]
    return "PASS" if all(checks) else "FAIL"


def row_from_case(run_dir: Path, mode: str) -> dict[str, str]:
    case_dir = run_dir / mode
    client = read_json(case_dir / "results" / "h3client.json")
    server = read_json(case_dir / "results" / "h3server.json")
    tasks = client.get("tasks") if isinstance(client.get("tasks"), list) else []
    requests = server.get("requests") if isinstance(server.get("requests"), list) else []
    task = tasks[0] if tasks else {}
    request = requests[0] if requests else {}
    return {
        "run_id": run_dir.name,
        "mode": mode,
        "status": status_for(client, server, task, request),
        "client_ok": bool_cell(client.get("ok")),
        "server_ok": bool_cell(server.get("ok")),
        "local_addr_changed_to_socket_b": bool_cell(client.get("local_addr_changed_to_socket_b")),
        "migration_triggered": bool_cell(task.get("migration_triggered")),
        "migration_at_bytes": str(task.get("migration_at_bytes") or ""),
        "request_bytes": str(task.get("request_bytes") or ""),
        "response_bytes": str(task.get("response_bytes") or ""),
        "server_decode_successful": bool_cell(request.get("decode_successful")),
        "client_migration_event_lines": str(client_migration_event_lines(case_dir)),
        "artifact_dir": case_dir.as_posix(),
    }


def read_rows(run_dirs: list[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for run_dir in run_dirs:
        for mode in MODES:
            rows.append(row_from_case(run_dir, mode))
    return rows


def count_by(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(row[key] for row in rows).items()))


def count_by_pair(rows: list[dict[str, str]], key_a: str, key_b: str) -> dict[str, int]:
    return dict(sorted(Counter(f"{row[key_a]}::{row[key_b]}" for row in rows).items()))


def emit_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# quic-go HTTP/3 Mid-Flight Migration Repetition Summary",
        "",
        f"Generated: `{utc_date_iso()}`",
        "",
        "This summary aggregates local quic-go HTTP/3 active-migration repetitions. It is a library-controlled positive control, not a browser handover result.",
        "",
        "## Aggregate",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| cases | `{len(rows)}` |",
        f"| status counts | `{count_by(rows, 'status')}` |",
        f"| mode counts | `{count_by(rows, 'mode')}` |",
        f"| mode/status counts | `{count_by_pair(rows, 'mode', 'status')}` |",
        "",
        "## Cases",
        "",
        "| run | mode | status | socket B | migration triggered | migration bytes | request bytes | response bytes | decode ok | client migration event lines |",
        "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |",
    ]
    for row in rows:
        lines.append(
            "| {run_id} | {mode} | {status} | {local_addr_changed_to_socket_b} | {migration_triggered} | "
            "{migration_at_bytes} | {request_bytes} | {response_bytes} | {server_decode_successful} | "
            "{client_migration_event_lines} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "Use these rows as implementation-level positive controls: quic-go can perform controlled active migration during HTTP/3 upload and download tasks while preserving application completion. They do not prove that Chrome, Safari, or Android Chrome expose the same behavior during real network handover.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_dirs", nargs="+")
    parser.add_argument("--output", default="docs/results/quic-go-h3-midflight-repetition-summary-20260624.md")
    parser.add_argument("--csv-output", default="data/quic-go-h3-midflight-repetition-summary-20260624.csv")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    rows = read_rows([Path(item) for item in args.artifact_dirs])
    if args.csv_output:
        write_csv(rows, Path(args.csv_output))
    text = json.dumps(rows, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(rows)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
