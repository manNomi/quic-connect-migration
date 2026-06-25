#!/usr/bin/env python3
"""Build a paper-oriented application recovery tradeoff table."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import median

from research_clock import utc_date_iso


DATASETS = [
    (
        "no-retry upload fine boundary",
        "data/chrome-h3-rebinding-transient-upload-fine-boundary-20260624.csv",
    ),
    (
        "no-retry upload 4750ms replication",
        "data/chrome-h3-rebinding-transient-upload-4750-replication-20260625.csv",
    ),
    (
        "one-retry upload boundary",
        "data/chrome-h3-rebinding-transient-upload-retry-boundary-20260624.csv",
    ),
    (
        "one-retry long outage",
        "data/chrome-h3-rebinding-transient-upload-retry-long-outage-20260624.csv",
    ),
    (
        "one-retry stress boundary",
        "data/chrome-h3-rebinding-transient-upload-retry-stress-boundary-20260624.csv",
    ),
    (
        "two-retry 15000ms recovery",
        "data/chrome-h3-rebinding-transient-upload-retry2-15000ms-20260624.csv",
    ),
    (
        "two-retry stress boundary",
        "data/chrome-h3-rebinding-transient-upload-retry2-stress-boundary-20260624.csv",
    ),
]

CSV_FIELDS = [
    "retry_attempts",
    "retry_delay_ms",
    "drop_window_ms",
    "datasets",
    "runs",
    "pass_count",
    "fail_count",
    "application_complete_count",
    "status_summary",
    "classification_summary",
    "complete_ms_min",
    "complete_ms_median",
    "complete_ms_max",
    "error_ms_min",
    "error_ms_median",
    "error_ms_max",
    "chrome_quic_sessions_min",
    "chrome_quic_sessions_max",
    "upload_sink_requests_min",
    "upload_sink_requests_max",
    "upload_bytes_min",
    "upload_bytes_max",
]


@dataclass(frozen=True)
class GroupKey:
    retry_attempts: int
    retry_delay_ms: int
    drop_window_ms: int


def load_rows(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for label, raw_path in DATASETS:
        path = root / raw_path
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as fp:
            for row in csv.DictReader(fp):
                if row.get("workload") != "upload":
                    continue
                row = dict(row)
                row["dataset"] = label
                rows.append(row)
    return rows


def int_value(value: str | None, default: int = 0) -> int:
    if value in {None, ""}:
        return default
    return int(value)


def canonical_retry_delay_ms(retry_attempts: int, retry_delay_ms: int) -> int:
    if retry_attempts == 0:
        return 0
    return retry_delay_ms


def int_values(rows: list[dict[str, str]], key: str) -> list[int]:
    values: list[int] = []
    for row in rows:
        raw = row.get(key)
        if raw not in {None, ""}:
            values.append(int(raw))
    return values


def fmt_range(values: list[int]) -> tuple[str, str, str]:
    if not values:
        return "", "", ""
    return str(min(values)), str(int(median(values))), str(max(values))


def fmt_min_max(values: list[int]) -> tuple[str, str]:
    if not values:
        return "", ""
    return str(min(values)), str(max(values))


def fmt_counter(counter: Counter[str]) -> str:
    return "; ".join(f"{key}={counter[key]}" for key in sorted(counter))


def group_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[GroupKey, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        retry_attempts = int_value(row.get("upload_retry_attempts"))
        key = GroupKey(
            retry_attempts=retry_attempts,
            retry_delay_ms=canonical_retry_delay_ms(
                retry_attempts,
                int_value(row.get("upload_retry_delay_ms")),
            ),
            drop_window_ms=int_value(row.get("drop_window_ms")),
        )
        grouped[key].append(row)

    output: list[dict[str, str]] = []
    for key in sorted(grouped, key=lambda item: (item.retry_attempts, item.drop_window_ms, item.retry_delay_ms)):
        items = grouped[key]
        complete_min, complete_median, complete_max = fmt_range(int_values(items, "dump_task_elapsed_ms"))
        error_min, error_median, error_max = fmt_range(int_values(items, "dump_task_error_elapsed_ms"))
        session_min, session_max = fmt_min_max(int_values(items, "netlog_target_quic_session_count"))
        request_min, request_max = fmt_min_max(int_values(items, "upload_sink_request_count"))
        bytes_min, bytes_max = fmt_min_max(int_values(items, "upload_sink_request_bytes"))
        statuses = Counter(row.get("status", "") for row in items)
        classifications = Counter(row.get("classification", "") for row in items)
        output.append(
            {
                "retry_attempts": str(key.retry_attempts),
                "retry_delay_ms": str(key.retry_delay_ms),
                "drop_window_ms": str(key.drop_window_ms),
                "datasets": "; ".join(sorted({row["dataset"] for row in items})),
                "runs": str(len(items)),
                "pass_count": str(statuses["PASS"]),
                "fail_count": str(statuses["FAIL"]),
                "application_complete_count": str(sum(1 for row in items if row.get("dump_application_complete") == "true")),
                "status_summary": fmt_counter(statuses),
                "classification_summary": fmt_counter(classifications),
                "complete_ms_min": complete_min,
                "complete_ms_median": complete_median,
                "complete_ms_max": complete_max,
                "error_ms_min": error_min,
                "error_ms_median": error_median,
                "error_ms_max": error_max,
                "chrome_quic_sessions_min": session_min,
                "chrome_quic_sessions_max": session_max,
                "upload_sink_requests_min": request_min,
                "upload_sink_requests_max": request_max,
                "upload_bytes_min": bytes_min,
                "upload_bytes_max": bytes_max,
            }
        )
    return output


def boundary_rows(grouped: list[dict[str, str]]) -> list[list[str]]:
    by_retry: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in grouped:
        by_retry[int(row["retry_attempts"])].append(row)

    rows: list[list[str]] = []
    for retry in sorted(by_retry):
        items = sorted(by_retry[retry], key=lambda row: int(row["drop_window_ms"]))
        all_pass = [row for row in items if int(row["pass_count"]) == int(row["runs"])]
        all_fail = [row for row in items if int(row["fail_count"]) == int(row["runs"])]
        mixed = [row for row in items if int(row["pass_count"]) > 0 and int(row["fail_count"]) > 0]
        stable = all_pass[-1] if all_pass else None
        later_failures = [
            row
            for row in all_fail
            if stable is None or int(row["drop_window_ms"]) > int(stable["drop_window_ms"])
        ]
        first_fail = later_failures[0] if later_failures else None
        stable_latency = ""
        stable_sessions = ""
        if stable:
            stable_latency = f"{stable['complete_ms_min']}-{stable['complete_ms_max']}ms"
            stable_sessions = f"{stable['chrome_quic_sessions_min']}-{stable['chrome_quic_sessions_max']}"
        fail_timing = ""
        if first_fail:
            fail_timing = f"{first_fail['error_ms_min']}-{first_fail['error_ms_max']}ms"
        rows.append(
            [
                f"{retry} retry",
                f"{stable['drop_window_ms']}ms" if stable else "-",
                ", ".join(f"{row['drop_window_ms']}ms" for row in mixed) or "-",
                f"{first_fail['drop_window_ms']}ms" if first_fail else "-",
                stable_latency or "-",
                stable_sessions or "-",
                fail_timing or "-",
            ]
        )
    return rows


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def build_markdown(grouped: list[dict[str, str]]) -> str:
    detail_rows = [
        [
            f"{row['retry_attempts']}x/{row['retry_delay_ms']}ms",
            f"{row['drop_window_ms']}ms",
            f"{row['pass_count']}/{row['runs']}",
            row["application_complete_count"],
            f"{row['complete_ms_min']}-{row['complete_ms_max']}ms" if row["complete_ms_min"] else "-",
            f"{row['error_ms_min']}-{row['error_ms_max']}ms" if row["error_ms_min"] else "-",
            f"{row['chrome_quic_sessions_min']}-{row['chrome_quic_sessions_max']}",
            f"{row['upload_sink_requests_min']}-{row['upload_sink_requests_max']}",
            f"{row['upload_bytes_min']}-{row['upload_bytes_max']}",
            row["classification_summary"],
        ]
        for row in grouped
    ]
    sections = [
        "# Application Recovery Tradeoff",
        "",
        f"Generated: `{utc_date_iso()}`",
        "",
        "This synthesis combines the Chrome forced-H3 local UDP rebinding upload-only boundary controls. It is an application recovery table, not a browser connection migration success table.",
        "",
        "## Source CSVs",
        "",
        "\n".join(f"- `{path}` ({label})" for label, path in DATASETS),
        "",
        "## Boundary Summary",
        "",
        markdown_table(
            [
                "retry budget",
                "latest all-pass window",
                "mixed window",
                "first later all-fail window",
                "latency at latest all-pass",
                "Chrome QUIC sessions",
                "error timing at fail",
            ],
            boundary_rows(grouped),
        ),
        "",
        "## Detailed Groups",
        "",
        markdown_table(
            [
                "retry",
                "drop window",
                "PASS/runs",
                "app complete",
                "complete ms",
                "error ms",
                "Chrome sessions",
                "upload attempts",
                "upload bytes",
                "classification",
            ],
            detail_rows,
        ),
        "",
        "## Interpretation",
        "",
        "- No-retry upload completion is stable through 4600ms, mixed at 4750ms, and repeatedly fails from 4900ms in this curated local boundary set.",
        "- One application-level retry moves the repeated-pass region through 12000ms but fails repeatedly at 15000ms.",
        "- Two application-level retries recover 15000ms and 18000ms but fail repeatedly at 21000ms.",
        "- Retry budget increases user-visible task recovery, but the successful retry rows use replacement/multiple Chrome QUIC sessions and increasing completion latency; this must not be reported as single-session browser CM success.",
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
    parser.add_argument("--output", default="docs/results/application-recovery-tradeoff-20260624.md")
    parser.add_argument("--csv-output", default="data/application-recovery-tradeoff-20260624.csv")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root)
    grouped = group_rows(load_rows(root))
    write_csv(root / args.csv_output, grouped)
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_markdown(grouped), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
