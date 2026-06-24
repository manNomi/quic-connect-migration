#!/usr/bin/env python3
"""Audit final browser handover trial completion against the paper protocol."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, asdict
from research_clock import utc_date_iso
from pathlib import Path
from typing import Any


DEFAULT_REQUIREMENTS = "data/final-browser-handover-required-trials.csv"
DEFAULT_EXPERIMENTS = "data/experiment-results.csv"


@dataclass
class RequirementResult:
    requirement_id: str
    phase: str
    browser: str
    description: str
    min_count: int
    matched_count: int
    complete: bool
    matching_trials: list[str]


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def split_cell(value: str) -> list[str]:
    return [item.strip().lower() for item in value.split(";") if item.strip()]


def text_for(row: dict[str, str], field: str) -> str:
    return (row.get(field) or "").lower()


def all_in(value: str, needles: list[str]) -> bool:
    return all(needle in value for needle in needles)


def any_in(value: str, needles: list[str]) -> bool:
    return not needles or any(needle in value for needle in needles)


def none_in(value: str, needles: list[str]) -> bool:
    return not any(needle in value for needle in needles)


def row_matches(requirement: dict[str, str], experiment: dict[str, str]) -> bool:
    accepted_statuses = set(split_cell(requirement.get("accepted_statuses", "")))
    if accepted_statuses and text_for(experiment, "status") not in accepted_statuses:
        return False

    field_rules = [
        ("trial_id_contains_all", "trial_id"),
        ("deployment_contains_all", "deployment_tier"),
        ("trigger_contains_all", "migration_trigger"),
        ("task_contains_all", "application_task"),
        ("notes_contains_all", "notes"),
    ]
    for rule_field, experiment_field in field_rules:
        if not all_in(text_for(experiment, experiment_field), split_cell(requirement.get(rule_field, ""))):
            return False

    combined = " ".join(
        text_for(experiment, field)
        for field in [
            "trial_id",
            "implementation",
            "deployment_tier",
            "protocol",
            "migration_trigger",
            "application_task",
            "failure_layer",
            "notes",
        ]
    )
    if not any_in(combined, split_cell(requirement.get("notes_contains_any", ""))):
        return False
    if not none_in(combined, split_cell(requirement.get("notes_excludes_any", ""))):
        return False
    return True


def evaluate(requirements: list[dict[str, str]], experiments: list[dict[str, str]]) -> list[RequirementResult]:
    results: list[RequirementResult] = []
    for requirement in requirements:
        matches = [row for row in experiments if row_matches(requirement, row)]
        min_count = int(requirement.get("min_count") or 0)
        results.append(
            RequirementResult(
                requirement_id=requirement["requirement_id"],
                phase=requirement["phase"],
                browser=requirement["browser"],
                description=requirement["description"],
                min_count=min_count,
                matched_count=len(matches),
                complete=len(matches) >= min_count,
                matching_trials=[row["trial_id"] for row in matches],
            )
        )
    return results


def build_audit(requirements_path: Path, experiments_path: Path) -> dict[str, Any]:
    requirements = load_rows(requirements_path)
    experiments = load_rows(experiments_path)
    results = evaluate(requirements, experiments)
    complete = all(result.complete for result in results)
    return {
        "check_date": utc_date_iso(),
        "requirements_path": str(requirements_path),
        "experiments_path": str(experiments_path),
        "requirement_count": len(results),
        "complete_count": sum(1 for result in results if result.complete),
        "complete": complete,
        "results": [asdict(result) for result in results],
        "blockers": [
            f"{result.requirement_id}: {result.matched_count}/{result.min_count}"
            for result in results
            if not result.complete
        ],
    }


def emit_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Final Browser Handover Trial Audit",
        "",
        f"Generated: `{audit['check_date']}`",
        "",
        "## Summary",
        "",
        "| check | value |",
        "| --- | --- |",
        f"| requirements | `{audit['requirement_count']}` |",
        f"| complete requirements | `{audit['complete_count']}` |",
        f"| final browser handover trials complete | `{'yes' if audit['complete'] else 'no'}` |",
        "",
        "## Requirements",
        "",
        "| requirement | phase | browser | matched | complete | matching trials |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for result in audit["results"]:
        trials = ", ".join(result["matching_trials"]) or "-"
        lines.append(
            f"| `{result['requirement_id']}` | {result['phase']} | {result['browser']} | {result['matched_count']}/{result['min_count']} | `{'yes' if result['complete'] else 'no'}` | {trials} |"
        )
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {blocker}" for blocker in (audit["blockers"] or ["-"]))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()

    audit = build_audit(Path(args.requirements), Path(args.experiments))
    text = json.dumps(audit, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(audit)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if args.require_complete and not audit["complete"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
