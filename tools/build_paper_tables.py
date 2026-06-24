#!/usr/bin/env python3
"""Build paper-ready Markdown tables from the public experiment CSVs."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def cell(value: object) -> str:
    text = str(value if value is not None else "")
    return text.replace("|", "\\|").replace("\n", "<br>")


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell(value) for value in row) + " |")
    return "\n".join(lines)


def yes_no(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "true":
        return "yes"
    if normalized == "false":
        return "no"
    return value


def short_note(text: str, limit: int = 130) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "..."


def group_name(row: dict[str, str]) -> str:
    trial_id = row["trial_id"]
    tier = row["deployment_tier"].lower()
    impl = row["implementation"].lower()
    if "chrome" in impl or "safari" in impl or "browser" in tier or "public webpki" in tier:
        return "browser / public web"
    if "aws" in tier or "nlb" in tier or "ec2" in tier:
        return "cloud deployment"
    if "haproxy" in impl or "proxy" in tier:
        return "proxy / intermediary"
    if "quic-go" in impl or "quiche" in impl or "s2n" in impl:
        return "implementation control"
    if "alt-svc" in trial_id:
        return "browser / public web"
    return "other"


def format_counts(counter: Counter[str]) -> str:
    return "; ".join(f"{key}={counter[key]}" for key in sorted(counter))


def representative_rows(rows: list[dict[str, str]], statuses: set[str], limit: int = 12) -> list[dict[str, str]]:
    filtered = [row for row in rows if row["status"] in statuses]
    priority_terms = [
        "direct-origin",
        "nlb",
        "midflight",
        "chrome-h3",
        "alt-svc",
        "public",
        "downlink",
    ]

    def rank(row: dict[str, str]) -> tuple[int, str]:
        trial = row["trial_id"]
        score = 0
        for index, term in enumerate(priority_terms):
            if term in trial:
                score += index + 1
        return score, trial

    return sorted(filtered, key=rank)[:limit]


def build_markdown(experiments: list[dict[str, str]], rubric: list[dict[str, str]]) -> str:
    status_counts = Counter(row["status"] for row in experiments)
    group_counts = Counter(group_name(row) for row in experiments)
    failure_counts = Counter(row["failure_layer"] for row in experiments if row["failure_layer"] != "none")
    application_success_counts = Counter(row["application_success"] for row in experiments)

    sections: list[str] = [
        "# Paper Tables",
        "Generated from `data/experiment-results.csv` and `data/evidence-chain-rubric.csv`.",
        "## Table 1. Experiment Corpus Summary",
        markdown_table(
            ["metric", "value"],
            [
                ["total trials", len(experiments)],
                ["status counts", format_counts(status_counts)],
                ["application success counts", format_counts(application_success_counts)],
                ["experiment groups", format_counts(group_counts)],
                ["non-none failure layers", format_counts(failure_counts)],
            ],
        ),
        "## Table 2. Evidence Chain Rubric",
        markdown_table(
            ["claim", "evidence item", "minimum required", "current status", "notes"],
            [
                [
                    row["claim"],
                    row["evidence_item"],
                    row["minimum_required"],
                    row["current_repo_status"],
                    row["notes"],
                ]
                for row in rubric
            ],
        ),
        "## Table 3. Representative Positive / Feasibility Controls",
        markdown_table(
            ["trial", "implementation", "environment", "trigger", "path validation", "tuple change", "app success", "note"],
            [
                [
                    row["trial_id"],
                    row["implementation"],
                    row["deployment_tier"],
                    short_note(row["migration_trigger"], 90),
                    yes_no(row["path_validation_observed"]),
                    yes_no(row["tuple_change_observed"]),
                    yes_no(row["application_success"]),
                    short_note(row["notes"]),
                ]
                for row in representative_rows(experiments, {"PASS", "PASS_FEASIBILITY"}, limit=14)
            ],
        ),
        "## Table 4. Negative Controls and Failure-Layer Evidence",
        markdown_table(
            ["trial", "environment", "failure layer", "path validation", "tuple change", "app success", "interpretation"],
            [
                [
                    row["trial_id"],
                    row["deployment_tier"],
                    row["failure_layer"],
                    yes_no(row["path_validation_observed"]),
                    yes_no(row["tuple_change_observed"]),
                    yes_no(row["application_success"]),
                    short_note(row["notes"]),
                ]
                for row in representative_rows(experiments, {"PASS_NEGATIVE_CONTROL"}, limit=14)
            ],
        ),
    ]

    browser_rows = [
        row
        for row in experiments
        if "chrome" in row["trial_id"] or "safari" in row["trial_id"] or "browser" in row["deployment_tier"].lower()
    ]
    sections.extend(
        [
            "## Table 5. Browser / Public Web Evidence",
            markdown_table(
                [
                    "trial",
                    "status",
                    "environment",
                    "trigger",
                    "path validation",
                    "tuple change",
                    "classification / note",
                ],
                [
                    [
                        row["trial_id"],
                        row["status"],
                        row["deployment_tier"],
                        short_note(row["migration_trigger"], 90),
                        yes_no(row["path_validation_observed"]),
                        yes_no(row["tuple_change_observed"]),
                        short_note(row["notes"]),
                    ]
                    for row in browser_rows
                ],
            ),
        ]
    )

    pending_items = [
        row
        for row in rubric
        if row["current_repo_status"].strip().lower() in {"pending", "partially_observed"}
    ]
    sections.extend(
        [
            "## Table 6. Remaining Evidence Gaps",
            markdown_table(
                ["claim", "missing or weak evidence", "current status", "next proof needed"],
                [
                    [
                        row["claim"],
                        row["evidence_item"],
                        row["current_repo_status"],
                        row["minimum_required"],
                    ]
                    for row in pending_items
                ],
            ),
        ]
    )

    return "\n\n".join(sections).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments", default="data/experiment-results.csv")
    parser.add_argument("--rubric", default="data/evidence-chain-rubric.csv")
    parser.add_argument("--output")
    args = parser.parse_args()

    experiments = load_rows(Path(args.experiments))
    rubric = load_rows(Path(args.rubric))
    text = build_markdown(experiments, rubric)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
