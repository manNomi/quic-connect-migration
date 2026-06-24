#!/usr/bin/env python3
"""Summarize Chrome local UDP rebinding transient return-path outage sweep artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
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
    "drop_window",
    "drop_window_ms",
    "status",
    "classification",
    "dump_application_complete",
    "dump_task_elapsed_ms",
    "dump_task_error_elapsed_ms",
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
    "drop_a_server_after_switch_for_ms",
    "drop_b_server_after_switch_for_ms",
    "dropped_server_packets_a",
    "dropped_server_packets_b",
    "dropped_server_bytes_a",
    "dropped_server_bytes_b",
    "max_drop_since_switch_ms",
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


def proxy_log_stats(artifact_dir: Path) -> tuple[int, int, int]:
    client_counts = {"A": 0, "B": 0}
    max_drop_since = 0
    path = artifact_dir / "logs" / "rebinding-proxy.jsonl"
    if not path.exists():
        return 0, 0, 0
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not raw_line.strip():
            continue
        try:
            item = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        event = item.get("event")
        if event == "client_to_server":
            upstream = str(item.get("upstream") or "").upper()
            if upstream in client_counts:
                client_counts[upstream] += 1
        elif event == "server_to_client_dropped":
            max_drop_since = max(max_drop_since, int(item.get("since_switch_ms") or 0))
    return client_counts["A"], client_counts["B"], max_drop_since


def upload_sink_stats(artifact_dir: Path, summary: dict[str, Any]) -> tuple[int, int]:
    server = read_json(artifact_dir / "results" / "server.json")
    requests = server.get("requests") or summary.get("server_requests") or []
    uploads = [item for item in requests if isinstance(item, dict) and item.get("path") == "/upload-sink"]
    return len(uploads), sum(int(item.get("request_bytes") or 0) for item in uploads)


def row_from_spec(raw: str) -> dict[str, str]:
    workload, artifact_dir = parse_run_spec(raw)
    spec = read_json(artifact_dir / "results" / "transient-return-path-spec.json")
    summary = read_json(artifact_dir / "results" / "chrome-summary.json")
    proxy = summary.get("rebinding_proxy") if isinstance(summary.get("rebinding_proxy"), dict) else {}
    qlog_counts = summary.get("qlog_counts") if isinstance(summary.get("qlog_counts"), dict) else {}
    client_a, client_b, max_drop_since = proxy_log_stats(artifact_dir)
    upload_count, upload_bytes = upload_sink_stats(artifact_dir, summary)
    return {
        "profile": str(spec.get("profile") or artifact_dir.name),
        "workload": workload,
        "run_id": artifact_dir.name,
        "configured_bytes": str(spec.get("bytes") or ""),
        "configured_chunks": str(spec.get("chunks") or ""),
        "duration_ms": str(spec.get("duration_ms") or ""),
        "rebind_after": str(spec.get("rebind_after") or ""),
        "drop_window": str(spec.get("drop_window") or ""),
        "drop_window_ms": str(spec.get("drop_window_ms") or ""),
        "status": str(summary.get("status") or "missing"),
        "classification": str(summary.get("classification") or "missing"),
        "dump_application_complete": str(summary.get("dump_application_complete") is True).lower(),
        "dump_task_elapsed_ms": str(summary.get("dump_task_elapsed_ms") or ""),
        "dump_task_error_elapsed_ms": str(summary.get("dump_task_error_elapsed_ms") or ""),
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
        "drop_a_server_after_switch_for_ms": str(proxy.get("drop_a_server_after_switch_for_ms") or 0),
        "drop_b_server_after_switch_for_ms": str(proxy.get("drop_b_server_after_switch_for_ms") or 0),
        "dropped_server_packets_a": str(proxy.get("dropped_server_packets_a") or 0),
        "dropped_server_packets_b": str(proxy.get("dropped_server_packets_b") or 0),
        "dropped_server_bytes_a": str(proxy.get("dropped_server_bytes_a") or 0),
        "dropped_server_bytes_b": str(proxy.get("dropped_server_bytes_b") or 0),
        "max_drop_since_switch_ms": str(max_drop_since),
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


def count_status_by_window(rows: list[dict[str, str]]) -> dict[str, dict[str, int]]:
    grouped: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        grouped[row["drop_window"]][row["status"]] += 1
    return {window: dict(sorted(counter.items())) for window, counter in sorted(grouped.items(), key=lambda item: int(item[0].rstrip("ms") or 0))}


def sum_int(rows: list[dict[str, str]], key: str) -> int:
    return sum(int(row.get(key) or 0) for row in rows)


def local_boundary_summary(rows: list[dict[str, str]]) -> str:
    pass_windows = sorted({int(row["drop_window_ms"]) for row in rows if row["status"] == "PASS" and row.get("drop_window_ms")})
    fail_windows = sorted({int(row["drop_window_ms"]) for row in rows if row["status"] == "FAIL" and row.get("drop_window_ms")})
    if not pass_windows or not fail_windows:
        return "Observed local boundary: inconclusive because the sweep does not contain both PASS and FAIL windows."
    max_pass = max(pass_windows)
    later_failures = [window for window in fail_windows if window > max_pass]
    if later_failures:
        min_fail = min(later_failures)
        return f"Observed local boundary: max PASS window `{max_pass}ms`; min later FAIL window `{min_fail}ms`."
    return f"Observed local boundary: PASS and FAIL windows overlap or are non-monotonic; inspect per-row evidence before drawing a threshold."


def emit_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Chrome H3 Local Rebinding Transient Return-Path Sweep",
        "",
        f"Generated: `{utc_date_iso()}`",
        "",
        "This summary aggregates local Chrome forced-H3 UDP rebinding runs where both A-side and B-side server-to-client packets are dropped only for a bounded window after proxy switch. The goal is to separate permanent return-path loss from transient outage tolerance. These rows are local controls, not public browser handover results.",
        "",
        "## Aggregate",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| runs | `{len(rows)}` |",
        f"| status counts | `{count_by(rows, 'status')}` |",
        f"| status by drop window | `{count_status_by_window(rows)}` |",
        f"| classification counts | `{count_by(rows, 'classification')}` |",
        f"| application complete | `{count_true(rows, 'dump_application_complete')}` |",
        f"| proxy switched | `{count_true(rows, 'proxy_switched')}` |",
        f"| total dropped A-side server packets | `{sum_int(rows, 'dropped_server_packets_a')}` |",
        f"| total dropped B-side server packets | `{sum_int(rows, 'dropped_server_packets_b')}` |",
        "",
        "## Runs",
        "",
        "| profile | workload | drop window | status | classification | app complete | complete ms | error ms | server requests | Chrome QUIC sessions | qlog PATH C/R | dropped A/B packets | max drop ms | client packets A/B | server packets A/B | upload bytes |",
        "| --- | --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- | ---: |",
    ]
    for row in rows:
        upload_bytes = row["upload_sink_request_bytes"] or "-"
        lines.append(
            "| {profile} | {workload} | {drop_window} | {status} | `{classification}` | "
            "{dump_application_complete} | {complete_ms} | {error_ms} | {server_request_count} | {netlog_target_quic_session_count} | "
            "{qlog_path_challenge}/{qlog_path_response} | {dropped_server_packets_a}/{dropped_server_packets_b} | "
            "{max_drop_since_switch_ms} | {proxy_client_packets_a}/{proxy_client_packets_b} | "
            "{proxy_server_packets_a}/{proxy_server_packets_b} | {upload_bytes} |".format(
                **row,
                complete_ms=row["dump_task_elapsed_ms"] or "-",
                error_ms=row["dump_task_error_elapsed_ms"] or "-",
                upload_bytes=upload_bytes,
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "Use this sweep to estimate the local browser workload's tolerance to a temporary server-to-client return-path outage. A PASS row means the browser task survived the bounded outage in this local NAT-rebinding harness; it does not prove real Wi-Fi/LTE handover success. A FAIL row means transport artifacts can exist while DOM-level task completion still fails.",
            "",
            local_boundary_summary(rows),
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
    parser.add_argument("--output", default="docs/results/chrome-h3-rebinding-transient-return-path-sweep-20260624.md")
    parser.add_argument("--csv-output", default="data/chrome-h3-rebinding-transient-return-path-sweep-20260624.csv")
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
