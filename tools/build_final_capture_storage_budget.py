#!/usr/bin/env python3
"""Estimate local disk budget for remaining final browser handover captures."""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from report_artifact_storage import DEFAULT_ROOTS, build_report as build_storage_report, human_size
from research_clock import utc_date_iso


DEFAULT_MATRIX = "data/final-protocol-readiness-matrix-20260624.csv"
DEFAULT_OUTPUT = "docs/results/final-capture-storage-budget-20260624.md"
DEFAULT_CSV_OUTPUT = "data/final-capture-storage-budget-20260624.csv"

CSV_FIELDS = [
    "scope",
    "planned_executions",
    "reserve_gib_each",
    "required_gib",
    "usable_gib_before_floor",
    "storage_ready",
    "cleanup_needed_gib",
    "interpretation",
]


@dataclass(frozen=True)
class BudgetRow:
    scope: str
    planned_executions: int
    reserve_gib_each: float
    required_gib: float
    usable_gib_before_floor: float
    storage_ready: bool
    cleanup_needed_gib: float
    interpretation: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def incomplete_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("ready") != "True"]


def gib_to_bytes(value: float) -> int:
    return int(value * (1024**3))


def bytes_to_gib(value: int) -> float:
    return round(value / (1024**3), 2)


def budget_row(scope: str, planned: int, reserve_gib: float, usable_gib: float, interpretation: str) -> BudgetRow:
    required = round(planned * reserve_gib, 2)
    cleanup_needed = max(0.0, round(required - usable_gib, 2))
    return BudgetRow(
        scope=scope,
        planned_executions=planned,
        reserve_gib_each=reserve_gib,
        required_gib=required,
        usable_gib_before_floor=usable_gib,
        storage_ready=usable_gib >= required,
        cleanup_needed_gib=cleanup_needed,
        interpretation=interpretation,
    )


def build_budget(args: argparse.Namespace) -> dict[str, object]:
    matrix = read_csv(Path(args.matrix))
    remaining = incomplete_rows(matrix)
    storage = build_storage_report(args.roots or DEFAULT_ROOTS, args.max_entries)
    free_bytes = int(storage["disk"]["free_bytes"])  # type: ignore[index]
    min_free_bytes = gib_to_bytes(args.min_free_gib)
    usable_bytes = max(0, free_bytes - min_free_bytes)
    usable_gib = bytes_to_gib(usable_bytes)
    reserve_gib = round(args.per_trial_reserve_gib, 2)
    remaining_count = len(remaining)
    next_trial = remaining[0]["trial_id"] if remaining else "-"

    rows = [
        budget_row(
            "next-planned-execution",
            1 if remaining else 0,
            reserve_gib,
            usable_gib,
            "Enough space to attempt only the next selected capture if storage_ready=yes.",
        ),
        budget_row(
            "all-remaining-final-executions",
            remaining_count,
            reserve_gib,
            usable_gib,
            "Enough space for the full remaining final browser handover queue if storage_ready=yes.",
        ),
    ]
    max_executions = math.floor(usable_gib / reserve_gib) if reserve_gib > 0 else 0

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "matrix": args.matrix,
        "next_trial": next_trial,
        "remaining_planned_executions": remaining_count,
        "per_trial_reserve_gib": reserve_gib,
        "min_free_gib_floor": round(args.min_free_gib, 2),
        "disk_free_gib": storage["disk"]["free_gib"],  # type: ignore[index]
        "usable_gib_before_floor": usable_gib,
        "max_executions_before_floor": max_executions,
        "artifact_roots_total": int(storage["total_artifact_bytes"]),
        "rows": [asdict(row) for row in rows],
    }


def bool_text(value: bool) -> str:
    return "yes" if value else "no"


def emit_markdown(budget: dict[str, object]) -> str:
    rows = list(budget["rows"])  # type: ignore[arg-type]
    lines = [
        "# Final Capture Storage Budget",
        "",
        f"Generated: `{budget['generated']}`",
        "",
        "This public-safe budget estimates whether the local machine can store remaining final browser handover NetLog/qlog artifacts before reaching the minimum free-space floor.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| next trial | `{budget['next_trial']}` |",
        f"| remaining planned executions | `{budget['remaining_planned_executions']}` |",
        f"| per-trial reserve GiB | `{budget['per_trial_reserve_gib']}` |",
        f"| disk free GiB | `{budget['disk_free_gib']}` |",
        f"| minimum free GiB floor | `{budget['min_free_gib_floor']}` |",
        f"| usable GiB before floor | `{budget['usable_gib_before_floor']}` |",
        f"| max executions before floor | `{budget['max_executions_before_floor']}` |",
        f"| current local artifact roots | `{human_size(int(budget['artifact_roots_total']))}` |",
        "",
        "## Budget Rows",
        "",
        "| scope | planned executions | required GiB | storage ready | cleanup needed GiB | interpretation |",
        "| --- | ---: | ---: | --- | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['scope']}` | {row['planned_executions']} | {row['required_gib']} | `{bool_text(bool(row['storage_ready']))}` | {row['cleanup_needed_gib']} | {row['interpretation']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This is a conservative planning estimate, not a measurement of future artifact size.",
            "- If only `next-planned-execution` is ready, run one capture and re-check storage before the next trial.",
            "- Do not delete ignored raw artifacts until the cleanup safety audit and paper evidence references are reviewed.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_csv(budget: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(budget["rows"])  # type: ignore[arg-type]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", default=DEFAULT_MATRIX)
    parser.add_argument("--root", action="append", dest="roots")
    parser.add_argument("--max-entries", type=int, default=10)
    parser.add_argument("--per-trial-reserve-gib", type=float, default=2.0)
    parser.add_argument("--min-free-gib", type=float, default=5.0)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    args = parser.parse_args()

    if args.per_trial_reserve_gib <= 0:
        raise SystemExit("--per-trial-reserve-gib must be positive")
    if args.min_free_gib < 0:
        raise SystemExit("--min-free-gib must be non-negative")

    budget = build_budget(args)
    write_csv(budget, Path(args.csv_output))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(budget), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
