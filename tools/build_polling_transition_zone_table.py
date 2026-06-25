#!/usr/bin/env python3
"""Build a paper-oriented polling transition-zone table."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from research_clock import utc_date_iso


DATASETS = [
    (
        "poll short boundary",
        "data/chrome-h3-rebinding-transient-poll-boundary-20260624.csv",
    ),
    (
        "poll long boundary",
        "data/chrome-h3-rebinding-transient-poll-long-boundary-20260624.csv",
    ),
    (
        "poll 4000ms replication",
        "data/chrome-h3-rebinding-transient-poll-4000-replication-20260625.csv",
    ),
]

CSV_FIELDS = [
    "drop_window_ms",
    "datasets",
    "runs",
    "pass_count",
    "fail_count",
    "application_complete_count",
    "server_request_count_min",
    "server_request_count_max",
    "chrome_quic_sessions_min",
    "chrome_quic_sessions_max",
    "qlog_path_challenge_min",
    "qlog_path_challenge_max",
    "qlog_path_response_min",
    "qlog_path_response_max",
    "status_summary",
    "classification_summary",
]


def load_rows(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for label, raw_path in DATASETS:
        path = root / raw_path
        if not path.exists():
            continue
        with path.open(newline="", encoding="utf-8") as fp:
            for row in csv.DictReader(fp):
                row = dict(row)
                row["dataset"] = label
                rows.append(row)
    return rows


def int_values(rows: list[dict[str, str]], key: str) -> list[int]:
    values: list[int] = []
    for row in rows:
        raw = row.get(key)
        if raw not in {None, ""}:
            values.append(int(raw))
    return values


def fmt_min_max(values: list[int]) -> tuple[str, str]:
    if not values:
        return "", ""
    return str(min(values)), str(max(values))


def fmt_counter(counter: Counter[str]) -> str:
    return "; ".join(f"{key}={counter[key]}" for key in sorted(counter))


def group_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[int(row.get("drop_window_ms") or 0)].append(row)

    output: list[dict[str, str]] = []
    for drop_window in sorted(grouped):
        items = grouped[drop_window]
        statuses = Counter(row.get("status", "") for row in items)
        classifications = Counter(row.get("classification", "") for row in items)
        req_min, req_max = fmt_min_max(int_values(items, "server_request_count"))
        session_min, session_max = fmt_min_max(int_values(items, "netlog_target_quic_session_count"))
        challenge_min, challenge_max = fmt_min_max(int_values(items, "qlog_path_challenge"))
        response_min, response_max = fmt_min_max(int_values(items, "qlog_path_response"))
        output.append(
            {
                "drop_window_ms": str(drop_window),
                "datasets": "; ".join(sorted({row["dataset"] for row in items})),
                "runs": str(len(items)),
                "pass_count": str(statuses["PASS"]),
                "fail_count": str(statuses["FAIL"]),
                "application_complete_count": str(sum(1 for row in items if row.get("dump_application_complete") == "true")),
                "server_request_count_min": req_min,
                "server_request_count_max": req_max,
                "chrome_quic_sessions_min": session_min,
                "chrome_quic_sessions_max": session_max,
                "qlog_path_challenge_min": challenge_min,
                "qlog_path_challenge_max": challenge_max,
                "qlog_path_response_min": response_min,
                "qlog_path_response_max": response_max,
                "status_summary": fmt_counter(statuses),
                "classification_summary": fmt_counter(classifications),
            }
        )
    return output


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def build_markdown(grouped: list[dict[str, str]]) -> str:
    by_window = {row["drop_window_ms"]: row for row in grouped}
    short_rows = [row for row in grouped if int(row["drop_window_ms"]) <= 3000]
    short_runs = sum(int(row["runs"]) for row in short_rows)
    short_passes = sum(int(row["pass_count"]) for row in short_rows)
    row_4000 = by_window.get("4000", {})
    row_6000 = by_window.get("6000", {})
    row_9000 = by_window.get("9000", {})
    fail_6000_9000 = sum(int(row.get("fail_count") or 0) for row in (row_6000, row_9000))
    runs_6000_9000 = sum(int(row.get("runs") or 0) for row in (row_6000, row_9000))
    detail_rows = [
        [
            f"{row['drop_window_ms']}ms",
            f"{row['pass_count']}/{row['runs']}",
            row["application_complete_count"],
            f"{row['server_request_count_min']}-{row['server_request_count_max']}",
            f"{row['chrome_quic_sessions_min']}-{row['chrome_quic_sessions_max']}",
            f"{row['qlog_path_challenge_min']}-{row['qlog_path_challenge_max']}",
            f"{row['qlog_path_response_min']}-{row['qlog_path_response_max']}",
            row["classification_summary"],
        ]
        for row in grouped
    ]
    sections = [
        "# Polling Transition-Zone Synthesis",
        "",
        f"Generated: `{utc_date_iso()}`",
        "",
        "This synthesis combines the Chrome forced-H3 local UDP rebinding polling/dashboard controls. It is a dashboard-like repeated fetch continuity summary, not public browser handover evidence.",
        "",
        "## Source CSVs",
        "",
        "\n".join(f"- `{path}` ({label})" for label, path in DATASETS),
        "",
        "## Grouped Evidence",
        "",
        markdown_table(
            [
                "drop window",
                "PASS/runs",
                "app complete",
                "server requests",
                "Chrome sessions",
                "qlog PATH_CHALLENGE",
                "qlog PATH_RESPONSE",
                "classification",
            ],
            detail_rows,
        ),
        "",
        "## Interpretation",
        "",
        f"- The polling workload completed {short_passes}/{short_runs} through 3000ms in the short-boundary control.",
        (
            "- At 4000ms the result remains a transition-zone result: "
            f"{row_4000.get('pass_count', '0')}/{row_4000.get('runs', '0')} PASS and "
            f"{row_4000.get('fail_count', '0')}/{row_4000.get('runs', '0')} FAIL."
        ),
        f"- At 6000ms and 9000ms it repeatedly failed: {fail_6000_9000}/{runs_6000_9000} FAIL.",
        "- PASS rows still used two Chrome target QUIC sessions, so polling completion is not single-session browser CM evidence.",
        "- Use this table to justify dashboard recovery as a separate application-level metric that must be reported with session attribution.",
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
    parser.add_argument("--output", default="docs/results/polling-transition-zone-synthesis-20260624.md")
    parser.add_argument("--csv-output", default="data/polling-transition-zone-synthesis-20260624.csv")
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
