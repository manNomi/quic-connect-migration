#!/usr/bin/env python3
"""Summarize Chrome local UDP rebinding range-download artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any

from research_clock import utc_date_iso


CSV_FIELDS = [
    "profile",
    "trial_id",
    "drop_window_ms",
    "retry_attempts",
    "total_bytes",
    "range_bytes",
    "status",
    "classification",
    "range_complete",
    "range_completed_bytes",
    "range_completed_chunks",
    "range_retries_used",
    "range_elapsed_ms",
    "range_error_elapsed_ms",
    "server_request_count",
    "server_remote_addr_count",
    "chrome_quic_sessions",
    "qlog_path_challenge",
    "qlog_path_response",
    "dropped_server_packets_a",
    "dropped_server_packets_b",
    "artifact_dir",
    "notes",
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except (json.JSONDecodeError, OSError):
        return {}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def data_attr(text: str, name: str) -> str:
    match = re.search(rf'\bdata-{re.escape(name)}="([^"]*)"', text)
    return match.group(1) if match else ""


def js_int(text: str, name: str) -> str:
    match = re.search(rf"\b{re.escape(name)}=([0-9]+)", text)
    return match.group(1) if match else ""


def scalar_text(value: Any) -> str:
    return "" if value is None else str(value)


def note_for(row: dict[str, str]) -> str:
    complete = row["range_complete"] == "true"
    sessions = int(row["chrome_quic_sessions"] or "0")
    retries = int(row["range_retries_used"] or "0")
    if complete and retries:
        note = "Range task completed after retrying a failed byte range."
    elif complete:
        note = "Range task completed without an application retry in this run."
    else:
        note = "Range task did not complete at the DOM task level."
    if complete and sessions > 1:
        note += " Chrome used multiple target QUIC sessions."
    return note


def summarize_artifact(artifact_dir: Path, profile: str) -> dict[str, str]:
    summary = read_json(artifact_dir / "results" / "chrome-summary.json")
    proxy = summary.get("rebinding_proxy")
    if not isinstance(proxy, dict):
        proxy = read_json(artifact_dir / "results" / "rebinding-proxy.json")
    dump = read_text(artifact_dir / "chrome" / "dump-dom.txt")
    qlog_counts = summary.get("qlog_counts") if isinstance(summary.get("qlog_counts"), dict) else {}
    row = {
        "profile": profile,
        "trial_id": artifact_dir.name,
        "drop_window_ms": scalar_text(
            proxy.get("drop_a_server_after_switch_for_ms")
            or proxy.get("drop_b_server_after_switch_for_ms")
        ),
        "retry_attempts": js_int(dump, "retryAttempts"),
        "total_bytes": js_int(dump, "totalBytes"),
        "range_bytes": js_int(dump, "rangeBytes"),
        "status": scalar_text(summary.get("status")),
        "classification": scalar_text(summary.get("classification")),
        "range_complete": data_attr(dump, "range-complete"),
        "range_completed_bytes": data_attr(dump, "range-completed-bytes"),
        "range_completed_chunks": data_attr(dump, "range-completed-chunks"),
        "range_retries_used": data_attr(dump, "range-retries-used"),
        "range_elapsed_ms": data_attr(dump, "range-elapsed-ms"),
        "range_error_elapsed_ms": data_attr(dump, "range-error-elapsed-ms"),
        "server_request_count": scalar_text(summary.get("server_request_count")),
        "server_remote_addr_count": scalar_text(summary.get("server_remote_addr_count")),
        "chrome_quic_sessions": scalar_text(summary.get("netlog_target_quic_session_count")),
        "qlog_path_challenge": scalar_text(qlog_counts.get("path_challenge")),
        "qlog_path_response": scalar_text(qlog_counts.get("path_response")),
        "dropped_server_packets_a": scalar_text(proxy.get("dropped_server_packets_a")),
        "dropped_server_packets_b": scalar_text(proxy.get("dropped_server_packets_b")),
        "artifact_dir": artifact_dir.as_posix(),
        "notes": "",
    }
    row["notes"] = note_for(row)
    return row


def int_values(rows: list[dict[str, str]], key: str) -> list[int]:
    return [int(row[key]) for row in rows if row.get(key) not in {None, ""}]


def fmt_median(values: list[int]) -> str:
    if not values:
        return "-"
    return str(int(median(values)))


def fmt_range(values: list[int]) -> str:
    if not values:
        return "-"
    return f"{min(values)}-{max(values)}"


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def grouped_rows(rows: list[dict[str, str]]) -> list[list[str]]:
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["profile"], row["drop_window_ms"], row["retry_attempts"])].append(row)
    output: list[list[str]] = []
    for (profile, drop_window, retry_attempts), items in sorted(
        groups.items(),
        key=lambda item: (item[0][0], int(item[0][1] or 0), int(item[0][2] or 0)),
    ):
        statuses = Counter(row["status"] for row in items)
        classifications = Counter(row["classification"] for row in items)
        complete = sum(1 for row in items if row["range_complete"] == "true")
        retry_used = sum(1 for row in items if int(row["range_retries_used"] or "0") > 0)
        output.append(
            [
                profile,
                f"{drop_window}ms" if drop_window else "-",
                retry_attempts or "-",
                f"{statuses['PASS']}/{len(items)}",
                f"{complete}/{len(items)}",
                f"{retry_used}/{len(items)}",
                fmt_median(int_values(items, "range_elapsed_ms")),
                fmt_median(int_values(items, "range_error_elapsed_ms")),
                fmt_range(int_values(items, "chrome_quic_sessions")),
                "; ".join(f"{key}={classifications[key]}" for key in sorted(classifications)),
            ]
        )
    return output


def build_markdown(rows: list[dict[str, str]], csv_output: str) -> str:
    detail_rows = [
        [
            row["profile"],
            row["trial_id"],
            f"{row['drop_window_ms']}ms" if row["drop_window_ms"] else "-",
            row["retry_attempts"] or "-",
            row["status"] or "-",
            row["classification"] or "-",
            row["range_complete"] or "-",
            f"{row['range_completed_bytes'] or '0'}/{row['total_bytes']}",
            row["range_retries_used"] or "-",
            row["range_elapsed_ms"] or "-",
            row["range_error_elapsed_ms"] or "-",
            row["chrome_quic_sessions"] or "-",
            f"{row['qlog_path_challenge']}/{row['qlog_path_response']}",
            f"{row['dropped_server_packets_a']}/{row['dropped_server_packets_b']}",
        ]
        for row in rows
    ]
    sections = [
        "# Chrome H3 Rebinding Range Download Control",
        "",
        f"Generated: `{utc_date_iso()}`",
        "",
        "## Scope",
        "",
        "This report summarizes local Chrome forced-H3 byte-range download workloads under UDP rebinding and transient server-to-client packet loss. It models resumable large-download recovery. These rows are local proxy controls, not public Wi-Fi-to-cellular browser handover trials.",
        "",
        "## Grouped Result",
        "",
        markdown_table(
            [
                "profile",
                "drop window",
                "retry",
                "PASS/runs",
                "range complete",
                "retry used",
                "median elapsed ms",
                "median error ms",
                "Chrome sessions",
                "classification",
            ],
            grouped_rows(rows),
        ),
        "",
        "## Run Detail",
        "",
        markdown_table(
            [
                "profile",
                "trial",
                "drop",
                "retry",
                "status",
                "classification",
                "complete",
                "bytes",
                "retries used",
                "elapsed ms",
                "error ms",
                "Chrome sessions",
                "qlog C/R",
                "dropped A/B",
            ],
            detail_rows,
        ),
        "",
        "## Interpretation Boundary",
        "",
        "A completed range row is resumable application-level download continuity. It is not single-session QUIC Connection Migration unless the same row also shows one target QUIC session, changed path/tuple evidence, qlog path validation, and no replacement-session behavior.",
        "",
        "The expected paper use is to compare recovery semantics: a full-stream retry restarts a long response, while byte-range retry can resume from the failed chunk. Both still need session attribution before being called QUIC CM.",
        "",
        "## Data",
        "",
        f"- CSV: `{csv_output}`",
    ]
    return "\n".join(sections).rstrip() + "\n"


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_dirs", nargs="+")
    parser.add_argument("--profile", default="range-download")
    parser.add_argument("--output", default="docs/results/chrome-h3-rebinding-range-download-control-20260629.md")
    parser.add_argument("--csv-output", default="data/chrome-h3-rebinding-range-download-control-20260629.csv")
    args = parser.parse_args()

    rows = [summarize_artifact(Path(raw), args.profile) for raw in args.artifact_dirs]
    write_csv(Path(args.csv_output), rows)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_markdown(rows, args.csv_output), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
