#!/usr/bin/env python3
"""Summarize Chrome local UDP rebinding return-path drop control artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


CSV_FIELDS = [
    "profile",
    "workload",
    "run_id",
    "configured_bytes",
    "configured_chunks",
    "duration_ms",
    "rebind_after",
    "expected_status",
    "status",
    "classification",
    "dump_application_complete",
    "dump_has_chrome_error",
    "server_request_count",
    "server_remote_addr_count",
    "netlog_target_quic_session_count",
    "qlog_has_h3",
    "qlog_path_challenge",
    "qlog_path_response",
    "proxy_switched",
    "drop_a_server_after_switch",
    "drop_b_server_after_switch",
    "dropped_server_packets_a",
    "dropped_server_packets_b",
    "dropped_server_bytes_a",
    "dropped_server_bytes_b",
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
    workload, artifact = raw.split(":", 1)
    if workload not in {"downlink", "upload"}:
        raise ValueError(f"unsupported workload {workload!r}")
    return workload, Path(artifact)


def proxy_client_packet_counts(artifact_dir: Path) -> tuple[int, int]:
    counts = {"A": 0, "B": 0}
    path = artifact_dir / "logs" / "rebinding-proxy.jsonl"
    if not path.exists():
        return 0, 0
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not raw_line.strip():
            continue
        try:
            item = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        if item.get("event") != "client_to_server":
            continue
        upstream = str(item.get("upstream") or "").upper()
        if upstream in counts:
            counts[upstream] += 1
    return counts["A"], counts["B"]


def upload_sink_stats(artifact_dir: Path, summary: dict[str, Any]) -> tuple[int, int]:
    server = read_json(artifact_dir / "results" / "server.json")
    requests = server.get("requests") or summary.get("server_requests") or []
    uploads = [item for item in requests if isinstance(item, dict) and item.get("path") == "/upload-sink"]
    return len(uploads), sum(int(item.get("request_bytes") or 0) for item in uploads)


def row_from_spec(raw: str) -> dict[str, str]:
    workload, artifact_dir = parse_run_spec(raw)
    spec = read_json(artifact_dir / "results" / "return-path-drop-spec.json")
    summary = read_json(artifact_dir / "results" / "chrome-summary.json")
    proxy = summary.get("rebinding_proxy") if isinstance(summary.get("rebinding_proxy"), dict) else {}
    qlog_counts = summary.get("qlog_counts") if isinstance(summary.get("qlog_counts"), dict) else {}
    client_a, client_b = proxy_client_packet_counts(artifact_dir)
    upload_count, upload_bytes = upload_sink_stats(artifact_dir, summary)
    return {
        "profile": str(spec.get("profile") or artifact_dir.name),
        "workload": workload,
        "run_id": artifact_dir.name,
        "configured_bytes": str(spec.get("bytes") or ""),
        "configured_chunks": str(spec.get("chunks") or ""),
        "duration_ms": str(spec.get("duration_ms") or ""),
        "rebind_after": str(spec.get("rebind_after") or ""),
        "expected_status": str(spec.get("expected_status") or ""),
        "status": str(summary.get("status") or "missing"),
        "classification": str(summary.get("classification") or "missing"),
        "dump_application_complete": str(summary.get("dump_application_complete") is True).lower(),
        "dump_has_chrome_error": str(summary.get("dump_has_chrome_error") is True).lower(),
        "server_request_count": str(summary.get("server_request_count") or 0),
        "server_remote_addr_count": str(summary.get("server_remote_addr_count") or 0),
        "netlog_target_quic_session_count": str(summary.get("netlog_target_quic_session_count") or 0),
        "qlog_has_h3": str(summary.get("qlog_has_h3") is True).lower(),
        "qlog_path_challenge": str(qlog_counts.get("path_challenge") or 0),
        "qlog_path_response": str(qlog_counts.get("path_response") or 0),
        "proxy_switched": str(proxy.get("switched") is True).lower(),
        "drop_a_server_after_switch": str(proxy.get("drop_a_server_after_switch") is True).lower(),
        "drop_b_server_after_switch": str(proxy.get("drop_b_server_after_switch") is True).lower(),
        "dropped_server_packets_a": str(proxy.get("dropped_server_packets_a") or 0),
        "dropped_server_packets_b": str(proxy.get("dropped_server_packets_b") or 0),
        "dropped_server_bytes_a": str(proxy.get("dropped_server_bytes_a") or 0),
        "dropped_server_bytes_b": str(proxy.get("dropped_server_bytes_b") or 0),
        "proxy_client_packets_a": str(client_a),
        "proxy_client_packets_b": str(client_b),
        "proxy_server_packets_a": str(proxy.get("server_packets_a") or 0),
        "proxy_server_packets_b": str(proxy.get("server_packets_b") or 0),
        "upload_sink_request_count": str(upload_count) if workload == "upload" else "",
        "upload_sink_request_bytes": str(upload_bytes) if workload == "upload" else "",
        "artifact_dir": artifact_dir.as_posix(),
    }


def count_by(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(row[key] for row in rows).items()))


def count_true(rows: list[dict[str, str]], key: str) -> str:
    return f"{sum(1 for row in rows if row[key] == 'true')}/{len(rows)}"


def sum_int(rows: list[dict[str, str]], key: str) -> int:
    return sum(int(row.get(key) or 0) for row in rows)


def emit_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Chrome H3 Local Rebinding Return-Path Drop Controls",
        "",
        f"Generated: `{utc_date_iso()}`",
        "",
        "This summary aggregates local Chrome forced-H3 UDP rebinding controls that selectively drop server-to-client packets after proxy switch. B-only drop tests whether the old return path can still carry the task; A+B drop is the stronger expected-failure return-path-loss control. These rows are local controls, not public browser handover results.",
        "",
        "## Aggregate",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| runs | `{len(rows)}` |",
        f"| expected status counts | `{count_by(rows, 'expected_status')}` |",
        f"| actual status counts | `{count_by(rows, 'status')}` |",
        f"| classification counts | `{count_by(rows, 'classification')}` |",
        f"| application complete | `{count_true(rows, 'dump_application_complete')}` |",
        f"| proxy switched | `{count_true(rows, 'proxy_switched')}` |",
        f"| B-side drop enabled | `{count_true(rows, 'drop_b_server_after_switch')}` |",
        f"| total dropped A-side server packets | `{sum_int(rows, 'dropped_server_packets_a')}` |",
        f"| total dropped B-side server packets | `{sum_int(rows, 'dropped_server_packets_b')}` |",
        "",
        "## Runs",
        "",
        "| profile | workload | expected | actual | classification | app complete | server requests | Chrome QUIC sessions | qlog PATH C/R | drop A/B | client packets A/B | server packets A/B | dropped A/B packets | upload bytes |",
        "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- | ---: |",
    ]
    for row in rows:
        upload_bytes = row["upload_sink_request_bytes"] or "-"
        lines.append(
            "| {profile} | {workload} | {expected_status} | {status} | `{classification}` | "
            "{dump_application_complete} | {server_request_count} | {netlog_target_quic_session_count} | "
            "{qlog_path_challenge}/{qlog_path_response} | {drop_a_server_after_switch}/{drop_b_server_after_switch} | "
            "{proxy_client_packets_a}/{proxy_client_packets_b} | {proxy_server_packets_a}/{proxy_server_packets_b} | "
            "{dropped_server_packets_a}/{dropped_server_packets_b} | {upload_bytes} |".format(
                **row, upload_bytes=upload_bytes
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "The B-only rows show that dropping only new-path server packets is not necessarily a failure because the old return path can still deliver application data. The A+B rows are the stronger failure boundary: once both old and new return paths are unavailable after switch, browser application completion should fail. This distinction prevents overclaiming path-validation or packet-drop evidence as application continuity.",
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
    parser.add_argument("--output", default="docs/results/chrome-h3-rebinding-return-path-drop-controls-20260624.md")
    parser.add_argument("--csv-output", default="data/chrome-h3-rebinding-return-path-drop-controls-20260624.csv")
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
