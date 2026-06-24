#!/usr/bin/env python3
"""Summarize the public experiment-results CSV."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def build_summary(rows: list[dict[str, str]]) -> dict[str, object]:
    status = Counter(row["status"] for row in rows)
    tier = Counter(row["deployment_tier"] for row in rows)
    implementation = Counter(row["implementation"] for row in rows)
    protocol = Counter(row["protocol"] for row in rows)
    application_success = Counter(row["application_success"] for row in rows)
    by_status: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        by_status[row["status"]].append(row["trial_id"])
    return {
        "total_trials": len(rows),
        "status": dict(status),
        "deployment_tier": dict(tier),
        "implementation": dict(implementation),
        "protocol": dict(protocol),
        "application_success": dict(application_success),
        "trial_ids_by_status": dict(by_status),
    }


def emit_markdown(rows: list[dict[str, str]], summary: dict[str, object]) -> None:
    print("# Experiment Result Summary\n")
    print(f"- total trials: `{summary['total_trials']}`")
    print(f"- status: `{summary['status']}`")
    print(f"- application_success: `{summary['application_success']}`")
    print("\n| trial_id | status | implementation | environment | protocol | app success | failure layer |")
    print("| --- | --- | --- | --- | --- | ---: | --- |")
    for row in rows:
        print(
            "| {trial_id} | {status} | {implementation} | {deployment_tier} | {protocol} | {application_success} | {failure_layer} |".format(
                **row
            )
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/experiment-results.csv")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    path = Path(args.input)
    rows = load_rows(path)
    summary = build_summary(rows)
    if args.format == "json":
        print(json.dumps({"summary": summary, "rows": rows}, indent=2, ensure_ascii=False))
    else:
        emit_markdown(rows, summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
