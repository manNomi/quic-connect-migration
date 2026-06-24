#!/usr/bin/env python3
"""Build a paper-ready comparison for downlink wait-only and retry controls."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from research_clock import utc_date_iso


DEFAULT_WAIT_CSV = "data/chrome-h3-rebinding-transient-downlink-wait-boundary-20260624.csv"
DEFAULT_RETRY_CSV = "data/chrome-h3-rebinding-transient-downlink-retry-boundary-20260624.csv"
DEFAULT_OUTPUT = "docs/results/downlink-recovery-comparison-20260624.md"
DEFAULT_CSV_OUTPUT = "data/downlink-recovery-comparison-20260624.csv"

CSV_FIELDS = [
    "policy",
    "source_csv",
    "drop_window_ms",
    "runs",
    "pass_count",
    "fail_count",
    "application_complete_count",
    "retries_used_summary",
    "classification_summary",
    "complete_ms_min",
    "complete_ms_median",
    "complete_ms_max",
    "error_ms_min",
    "error_ms_median",
    "error_ms_max",
    "chrome_quic_sessions_min",
    "chrome_quic_sessions_max",
]


def read_rows(path: Path, policy: str) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        rows = list(csv.DictReader(fp))
    for row in rows:
        row["policy"] = policy
        row["source_csv"] = path.as_posix()
    return rows


def int_values(rows: list[dict[str, str]], key: str) -> list[int]:
    values: list[int] = []
    for row in rows:
        value = row.get(key) or ""
        if not value:
            continue
        values.append(int(value))
    return sorted(values)


def median(values: list[int]) -> str:
    if not values:
        return ""
    index = len(values) // 2
    if len(values) % 2:
        return str(values[index])
    return str((values[index - 1] + values[index]) // 2)


def range_fields(rows: list[dict[str, str]], key: str) -> tuple[str, str, str]:
    values = int_values(rows, key)
    if not values:
        return "", "", ""
    return str(values[0]), median(values), str(values[-1])


def count_summary(rows: list[dict[str, str]], key: str) -> str:
    counter = Counter((row.get(key) or "-") for row in rows)
    return "; ".join(f"{name}={count}" for name, count in sorted(counter.items()))


def summarize(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["policy"], row["drop_window_ms"])].append(row)

    summaries: list[dict[str, str]] = []
    policy_order = {"wait_only_no_retry": 0, "retry_enabled_1x500ms": 1}
    for (policy, drop_window_ms), group in sorted(
        grouped.items(),
        key=lambda item: (policy_order.get(item[0][0], 99), int(item[0][1])),
    ):
        complete_min, complete_med, complete_max = range_fields(group, "dump_task_elapsed_ms")
        error_min, error_med, error_max = range_fields(group, "dump_task_error_elapsed_ms")
        sessions = int_values(group, "netlog_target_quic_session_count")
        summaries.append(
            {
                "policy": policy,
                "source_csv": group[0]["source_csv"],
                "drop_window_ms": drop_window_ms,
                "runs": str(len(group)),
                "pass_count": str(sum(1 for row in group if row.get("status") == "PASS")),
                "fail_count": str(sum(1 for row in group if row.get("status") == "FAIL")),
                "application_complete_count": str(sum(1 for row in group if row.get("dump_application_complete") == "true")),
                "retries_used_summary": count_summary(group, "retries_used"),
                "classification_summary": count_summary(group, "classification"),
                "complete_ms_min": complete_min,
                "complete_ms_median": complete_med,
                "complete_ms_max": complete_max,
                "error_ms_min": error_min,
                "error_ms_median": error_med,
                "error_ms_max": error_max,
                "chrome_quic_sessions_min": str(sessions[0]) if sessions else "",
                "chrome_quic_sessions_max": str(sessions[-1]) if sessions else "",
            }
        )
    return summaries


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def emit_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Downlink Recovery Comparison",
        "",
        f"Generated: `{utc_date_iso()}`",
        "",
        "This synthesis compares local Chrome forced-H3 downlink wait-only and one-retry controls under the same 6000ms/9000ms A+B return-path outage windows. It is local recovery evidence, not public browser handover evidence.",
        "",
        "## Comparison",
        "",
        "| policy | drop window | PASS/runs | app complete | retries used | complete ms | error ms | Chrome sessions | classification |",
        "| --- | ---: | ---: | ---: | --- | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        complete = "-"
        if row["complete_ms_min"]:
            complete = f"{row['complete_ms_min']}-{row['complete_ms_max']}"
        error = "-"
        if row["error_ms_min"]:
            error = f"{row['error_ms_min']}-{row['error_ms_max']}"
        sessions = "-"
        if row["chrome_quic_sessions_min"]:
            sessions = f"{row['chrome_quic_sessions_min']}-{row['chrome_quic_sessions_max']}"
        lines.append(
            "| {policy} | {drop_window_ms}ms | {pass_count}/{runs} | {application_complete_count} | `{retries_used_summary}` | {complete} | {error} | {sessions} | `{classification_summary}` |".format(
                **row,
                complete=complete,
                error=error,
                sessions=sessions,
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Wait-only no-retry rows fail even with the longer hold/grace timing used by the retry control.",
            "- The retry-enabled rows complete, but completion mechanism is mixed: some rows complete without consuming the retry, while others use one retry and create multiple Chrome target QUIC sessions.",
            "- Therefore downlink recovery must be reported as application-level recovery and retransmission/session-management behavior, not as single-session browser connection migration success.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wait-csv", default=DEFAULT_WAIT_CSV)
    parser.add_argument("--retry-csv", default=DEFAULT_RETRY_CSV)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    args = parser.parse_args()

    rows = []
    rows.extend(read_rows(Path(args.wait_csv), "wait_only_no_retry"))
    rows.extend(read_rows(Path(args.retry_csv), "retry_enabled_1x500ms"))
    summaries = summarize(rows)
    write_csv(summaries, Path(args.csv_output))
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(emit_markdown(summaries), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
