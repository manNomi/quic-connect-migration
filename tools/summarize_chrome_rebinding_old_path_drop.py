#!/usr/bin/env python3
"""Summarize Chrome local UDP rebinding runs with old-path server packet drops."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

import summarize_chrome_rebinding_proxy_matrix as downlink
import summarize_chrome_rebinding_upload_matrix as upload
from research_clock import utc_date_iso


CSV_FIELDS = [
    "workload",
    "run_id",
    "heartbeat",
    "status",
    "classification",
    "server_remote_addr_count",
    "netlog_target_quic_session_count",
    "netlog_target_path_challenge_received",
    "netlog_target_path_response_sent",
    "netlog_target_path_validation_observed",
    "qlog_path_challenge",
    "qlog_path_response",
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


def parse_run_spec(raw: str) -> tuple[str, Path]:
    parts = raw.split(":", 1)
    if len(parts) != 2:
        raise ValueError(f"run specs must use workload:artifact_dir, got {raw!r}")
    workload, artifact_dir = parts
    if workload not in {"downlink", "upload"}:
        raise ValueError(f"unsupported workload {workload!r}")
    return workload, Path(artifact_dir)


def qlog_path_validation_observed(row: dict[str, str]) -> str:
    challenge = int(row.get("qlog_path_challenge") or 0)
    response = int(row.get("qlog_path_response") or 0)
    return str(challenge > 0 and response > 0).lower()


def row_from_spec(raw: str) -> dict[str, str]:
    workload, artifact_dir = parse_run_spec(raw)
    if workload == "downlink":
        base = downlink.row_from_artifact(artifact_dir)
        heartbeat = base["heartbeat"]
        upload_count = ""
        upload_bytes = ""
    else:
        base = upload.row_from_artifact(artifact_dir)
        heartbeat = "n/a"
        upload_count = base["upload_sink_request_count"]
        upload_bytes = base["upload_sink_request_bytes"]
    proxy = read_json(artifact_dir / "results" / "rebinding-proxy.json")
    return {
        "workload": workload,
        "run_id": artifact_dir.name,
        "heartbeat": heartbeat,
        "status": base["status"],
        "classification": base["classification"],
        "server_remote_addr_count": base["server_remote_addr_count"],
        "netlog_target_quic_session_count": base["netlog_target_quic_session_count"],
        "netlog_target_path_challenge_received": base["netlog_target_path_challenge_received"],
        "netlog_target_path_response_sent": base["netlog_target_path_response_sent"],
        "netlog_target_path_validation_observed": base["netlog_target_path_validation_observed"],
        "qlog_path_challenge": base["qlog_path_challenge"],
        "qlog_path_response": base["qlog_path_response"],
        "qlog_path_validation_observed": qlog_path_validation_observed(base),
        "proxy_switched": base["proxy_switched"],
        "drop_a_server_after_switch": str(proxy.get("drop_a_server_after_switch") is True).lower(),
        "dropped_server_packets_a": str(proxy.get("dropped_server_packets_a") or 0),
        "dropped_server_bytes_a": str(proxy.get("dropped_server_bytes_a") or 0),
        "proxy_client_packets_a": base["proxy_client_packets_a"],
        "proxy_client_packets_b": base["proxy_client_packets_b"],
        "proxy_server_packets_a": str(proxy.get("server_packets_a") or 0),
        "proxy_server_packets_b": str(proxy.get("server_packets_b") or 0),
        "upload_sink_request_count": upload_count,
        "upload_sink_request_bytes": upload_bytes,
        "artifact_dir": artifact_dir.as_posix(),
    }


def count_by(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(row[key] for row in rows).items()))


def count_true(rows: list[dict[str, str]], key: str) -> str:
    total = len(rows)
    return f"{sum(1 for row in rows if row[key] == 'true')}/{total}"


def sum_int(rows: list[dict[str, str]], key: str) -> int:
    return sum(int(row.get(key) or 0) for row in rows)


def emit_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Chrome H3 Local Rebinding Old-Path Drop Summary",
        "",
        f"Generated: `{utc_date_iso()}`",
        "",
        "This summary aggregates local Chrome forced-H3 UDP rebinding runs where the proxy drops server-to-client packets arriving on upstream A after client traffic has switched to upstream B. It is a local NAT-rebinding control, not a public Wi-Fi/LTE handover result.",
        "",
        "## Aggregate",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| runs | `{len(rows)}` |",
        f"| status counts | `{count_by(rows, 'status')}` |",
        f"| workload counts | `{count_by(rows, 'workload')}` |",
        f"| heartbeat counts | `{count_by(rows, 'heartbeat')}` |",
        f"| classification counts | `{count_by(rows, 'classification')}` |",
        f"| proxy switched | `{count_true(rows, 'proxy_switched')}` |",
        f"| old-path drop enabled | `{count_true(rows, 'drop_a_server_after_switch')}` |",
        f"| qlog path validation | `{count_true(rows, 'qlog_path_validation_observed')}` |",
        f"| NetLog target path validation | `{count_true(rows, 'netlog_target_path_validation_observed')}` |",
        f"| total dropped A-side server packets | `{sum_int(rows, 'dropped_server_packets_a')}` |",
        f"| total dropped A-side server bytes | `{sum_int(rows, 'dropped_server_bytes_a')}` |",
        "",
        "## Runs",
        "",
        "| workload | run | heartbeat | status | classification | remote tuples | Chrome QUIC sessions | qlog PATH C/R | NetLog target PATH C/R | client packets A/B | server packets A/B | dropped A server packets | upload bytes |",
        "| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | ---: | ---: |",
    ]
    for row in rows:
        upload_bytes = row["upload_sink_request_bytes"] or "-"
        lines.append(
            "| {workload} | {run_id} | {heartbeat} | {status} | `{classification}` | "
            "{server_remote_addr_count} | {netlog_target_quic_session_count} | "
            "{qlog_path_challenge}/{qlog_path_response} | "
            "{netlog_target_path_challenge_received}/{netlog_target_path_response_sent} | "
            "{proxy_client_packets_a}/{proxy_client_packets_b} | "
            "{proxy_server_packets_a}/{proxy_server_packets_b} | "
            "{dropped_server_packets_a} | {upload_bytes} |".format(**row, upload_bytes=upload_bytes)
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "Use these rows as local old-path-unavailable controls. Application completion under old-path drop is stronger than tuple-only evidence, but it still does not prove browser handover success. Chrome target QUIC session counts, qlog path validation, proxy packet logs, and actual client path-change evidence remain separate requirements.",
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
    parser.add_argument("--output", default="docs/results/chrome-h3-rebinding-old-path-drop-20260624.md")
    parser.add_argument("--csv-output", default="data/chrome-h3-rebinding-old-path-drop-20260624.csv")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    rows = [row_from_spec(item) for item in args.runs]
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
