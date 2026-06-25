#!/usr/bin/env python3
"""Build a paper-oriented workload transition-zone table."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

from research_clock import utc_date_iso


DATASETS = [
    (
        "downlink fine boundary",
        "data/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624.csv",
    ),
    (
        "downlink 5000/5500ms replication",
        "data/chrome-h3-rebinding-transient-downlink-5000-5500-replication-20260625.csv",
    ),
    (
        "upload fine boundary",
        "data/chrome-h3-rebinding-transient-upload-fine-boundary-20260624.csv",
    ),
    (
        "upload 4750ms replication",
        "data/chrome-h3-rebinding-transient-upload-4750-replication-20260625.csv",
    ),
]

CSV_FIELDS = [
    "workload",
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
    grouped: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row.get("workload", ""), int(row.get("drop_window_ms") or 0))].append(row)

    output: list[dict[str, str]] = []
    for key in sorted(grouped, key=lambda item: (item[0], item[1])):
        workload, drop_window = key
        items = grouped[key]
        complete_min, complete_median, complete_max = fmt_range(int_values(items, "dump_task_elapsed_ms"))
        error_min, error_median, error_max = fmt_range(int_values(items, "dump_task_error_elapsed_ms"))
        session_min, session_max = fmt_min_max(int_values(items, "netlog_target_quic_session_count"))
        statuses = Counter(row.get("status", "") for row in items)
        classifications = Counter(row.get("classification", "") for row in items)
        output.append(
            {
                "workload": workload,
                "drop_window_ms": str(drop_window),
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
    by_key = {(row["workload"], row["drop_window_ms"]): row for row in grouped}
    downlink_5000 = by_key.get(("downlink", "5000"), {})
    downlink_5500 = by_key.get(("downlink", "5500"), {})
    downlink_6000 = by_key.get(("downlink", "6000"), {})
    upload_4600 = by_key.get(("upload", "4600"), {})
    upload_4750 = by_key.get(("upload", "4750"), {})
    upload_4900 = by_key.get(("upload", "4900"), {})
    upload_5000 = by_key.get(("upload", "5000"), {})
    detail_rows = [
        [
            row["workload"],
            f"{row['drop_window_ms']}ms",
            f"{row['pass_count']}/{row['runs']}",
            row["application_complete_count"],
            f"{row['complete_ms_min']}-{row['complete_ms_max']}ms" if row["complete_ms_min"] else "-",
            f"{row['error_ms_min']}-{row['error_ms_max']}ms" if row["error_ms_min"] else "-",
            f"{row['chrome_quic_sessions_min']}-{row['chrome_quic_sessions_max']}",
            row["classification_summary"],
        ]
        for row in grouped
    ]
    sections = [
        "# Workload Transition-Zone Synthesis",
        "",
        f"Generated: `{utc_date_iso()}`",
        "",
        "This synthesis combines the Chrome forced-H3 local UDP rebinding downlink and upload fine-boundary controls. It compares DOM task completion across workload direction; it is not public browser handover evidence.",
        "",
        "## Source CSVs",
        "",
        "\n".join(f"- `{path}` ({label})" for label, path in DATASETS),
        "",
        "## Grouped Evidence",
        "",
        markdown_table(
            [
                "workload",
                "drop window",
                "PASS/runs",
                "app complete",
                "complete ms",
                "error ms",
                "Chrome sessions",
                "classification",
            ],
            detail_rows,
        ),
        "",
        "## Interpretation",
        "",
        (
            "- Downlink remains mixed at 5000ms "
            f"({downlink_5000.get('pass_count', '0')}/{downlink_5000.get('runs', '0')} PASS) "
            "and 5500ms "
            f"({downlink_5500.get('pass_count', '0')}/{downlink_5500.get('runs', '0')} PASS), "
            "then repeatedly fails at 6000ms "
            f"({downlink_6000.get('pass_count', '0')}/{downlink_6000.get('runs', '0')} PASS)."
        ),
        (
            "- Upload is stable at 4600ms "
            f"({upload_4600.get('pass_count', '0')}/{upload_4600.get('runs', '0')} PASS), "
            "remains mixed at 4750ms "
            f"({upload_4750.get('pass_count', '0')}/{upload_4750.get('runs', '0')} PASS), "
            "and repeatedly fails at 4900ms/5000ms "
            f"({upload_4900.get('pass_count', '0')}/{upload_4900.get('runs', '0')} and "
            f"{upload_5000.get('pass_count', '0')}/{upload_5000.get('runs', '0')} PASS)."
        ),
        "- Workload direction changes the transition zone; a single outage-duration threshold would hide this behavior.",
        "- qlog path evidence appears in both PASS and FAIL rows, so transport evidence and DOM task completion must remain separate outcomes.",
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
    parser.add_argument("--output", default="docs/results/workload-transition-zone-synthesis-20260624.md")
    parser.add_argument("--csv-output", default="data/workload-transition-zone-synthesis-20260624.csv")
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
