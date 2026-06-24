#!/usr/bin/env python3
"""Summarize Chrome local UDP rebinding old-path-drop stress artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso
from summarize_chrome_rebinding_old_path_drop import row_from_spec


CSV_FIELDS = [
    "profile",
    "workload",
    "run_id",
    "heartbeat",
    "configured_bytes",
    "configured_chunks",
    "duration_ms",
    "rebind_after",
    "status",
    "classification",
    "server_remote_addr_count",
    "netlog_target_quic_session_count",
    "netlog_target_path_validation_observed",
    "qlog_path_validation_observed",
    "proxy_switched",
    "drop_a_server_after_switch",
    "dropped_server_packets_a",
    "dropped_server_bytes_a",
    "proxy_client_packets_a",
    "proxy_client_packets_b",
    "proxy_server_packets_a",
    "proxy_server_packets_b",
    "upload_sink_request_count",
    "upload_sink_request_bytes",
    "artifact_dir",
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def parse_artifact_dir(raw: str) -> Path:
    _, artifact = raw.split(":", 1)
    return Path(artifact)


def row_from_stress_spec(raw: str) -> dict[str, str]:
    artifact_dir = parse_artifact_dir(raw)
    base = row_from_spec(raw)
    spec = read_json(artifact_dir / "results" / "stress-spec.json")
    return {
        "profile": str(spec.get("profile") or artifact_dir.name),
        "workload": base["workload"],
        "run_id": base["run_id"],
        "heartbeat": base["heartbeat"],
        "configured_bytes": str(spec.get("bytes") or ""),
        "configured_chunks": str(spec.get("chunks") or ""),
        "duration_ms": str(spec.get("duration_ms") or ""),
        "rebind_after": str(spec.get("rebind_after") or ""),
        "status": base["status"],
        "classification": base["classification"],
        "server_remote_addr_count": base["server_remote_addr_count"],
        "netlog_target_quic_session_count": base["netlog_target_quic_session_count"],
        "netlog_target_path_validation_observed": base["netlog_target_path_validation_observed"],
        "qlog_path_validation_observed": base["qlog_path_validation_observed"],
        "proxy_switched": base["proxy_switched"],
        "drop_a_server_after_switch": base["drop_a_server_after_switch"],
        "dropped_server_packets_a": base["dropped_server_packets_a"],
        "dropped_server_bytes_a": base["dropped_server_bytes_a"],
        "proxy_client_packets_a": base["proxy_client_packets_a"],
        "proxy_client_packets_b": base["proxy_client_packets_b"],
        "proxy_server_packets_a": base["proxy_server_packets_a"],
        "proxy_server_packets_b": base["proxy_server_packets_b"],
        "upload_sink_request_count": base["upload_sink_request_count"],
        "upload_sink_request_bytes": base["upload_sink_request_bytes"],
        "artifact_dir": base["artifact_dir"],
    }


def count_by(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(row[key] for row in rows).items()))


def count_true(rows: list[dict[str, str]], key: str) -> str:
    return f"{sum(1 for row in rows if row[key] == 'true')}/{len(rows)}"


def sum_int(rows: list[dict[str, str]], key: str) -> int:
    return sum(int(row.get(key) or 0) for row in rows)


def rows_with(rows: list[dict[str, str]], **conditions: str) -> list[dict[str, str]]:
    return [row for row in rows if all(row.get(key) == value for key, value in conditions.items())]


def emit_markdown(rows: list[dict[str, str]]) -> str:
    upload_rows = rows_with(rows, workload="upload")
    downlink_rows = rows_with(rows, workload="downlink")
    lines = [
        "# Chrome H3 Local Rebinding Old-Path Drop Stress Summary",
        "",
        f"Generated: `{utc_date_iso()}`",
        "",
        "This summary aggregates local Chrome forced-H3 UDP rebinding stress rows where the proxy switches client traffic to upstream B and drops any later server-to-client packets from upstream A. It is a local old-path-unavailable control, not a public browser handover result.",
        "",
        "## Aggregate",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| runs | `{len(rows)}` |",
        f"| status counts | `{count_by(rows, 'status')}` |",
        f"| workload counts | `{count_by(rows, 'workload')}` |",
        f"| configured bytes counts | `{count_by(rows, 'configured_bytes')}` |",
        f"| classification counts | `{count_by(rows, 'classification')}` |",
        f"| proxy switched | `{count_true(rows, 'proxy_switched')}` |",
        f"| old-path drop enabled | `{count_true(rows, 'drop_a_server_after_switch')}` |",
        f"| qlog path validation | `{count_true(rows, 'qlog_path_validation_observed')}` |",
        f"| NetLog target path validation | `{count_true(rows, 'netlog_target_path_validation_observed')}` |",
        f"| upload bytes received | `{sum_int(upload_rows, 'upload_sink_request_bytes')}` |",
        f"| downlink configured bytes | `{sum_int(downlink_rows, 'configured_bytes')}` |",
        f"| total dropped A-side server packets | `{sum_int(rows, 'dropped_server_packets_a')}` |",
        f"| total dropped A-side server bytes | `{sum_int(rows, 'dropped_server_bytes_a')}` |",
        "",
        "## Runs",
        "",
        "| profile | workload | heartbeat | bytes | duration ms | status | classification | remote tuples | Chrome QUIC sessions | qlog path | NetLog path | client packets A/B | server packets A/B | dropped A packets | upload bytes |",
        "| --- | --- | --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- | --- | ---: | ---: |",
    ]
    for row in rows:
        upload_bytes = row["upload_sink_request_bytes"] or "-"
        lines.append(
            "| {profile} | {workload} | {heartbeat} | {configured_bytes} | {duration_ms} | {status} | "
            "`{classification}` | {server_remote_addr_count} | {netlog_target_quic_session_count} | "
            "{qlog_path_validation_observed} | {netlog_target_path_validation_observed} | "
            "{proxy_client_packets_a}/{proxy_client_packets_b} | {proxy_server_packets_a}/{proxy_server_packets_b} | "
            "{dropped_server_packets_a} | {upload_bytes} |".format(**row, upload_bytes=upload_bytes)
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "These rows are stress controls for Chrome forced-H3 local NAT rebinding. Passing rows show application completion while the proxy removes the old return path after rebinding, but they still do not prove real Chrome/Safari/Android Wi-Fi-to-cellular handover. The final claim still requires a controlled public WebPKI origin, an actual client path change, and countable final browser handover trials.",
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
    parser.add_argument("runs", nargs="+", help="Run spec as workload:artifact_dir")
    parser.add_argument("--output", default="docs/results/chrome-h3-rebinding-old-path-drop-stress-20260624.md")
    parser.add_argument("--csv-output", default="data/chrome-h3-rebinding-old-path-drop-stress-20260624.csv")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    rows = [row_from_stress_spec(item) for item in args.runs]
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
