#!/usr/bin/env python3
"""Build a paper-facing acceptance scorecard for final browser handover trials."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from research_clock import utc_date_iso
from pathlib import Path
from typing import Any

from audit_final_browser_handover_trials import build_audit, load_rows
from build_final_handover_trial_packet import expected_artifacts
from plan_final_browser_handover_runs import DEFAULT_CONFIG, DEFAULT_REQUIRED_TRIALS, PUBLIC_TEMPLATE_VALUES, make_plan, parse_env_file
from select_next_final_handover_trial import DEFAULT_EXPERIMENTS


DEFAULT_OUTPUT = "docs/results/final-trial-acceptance-scorecard-20260624.md"
DEFAULT_CSV_OUTPUT = "data/final-trial-acceptance-scorecard-20260624.csv"


@dataclass(frozen=True)
class AcceptanceRow:
    requirement_id: str
    phase: str
    browser: str
    min_count: int
    matched_count: int
    complete: bool
    accepted_statuses: str
    planned_trial_ids: str
    acceptance_rule: str
    reject_if: str
    required_artifact_roles: str
    paper_use: str


def split_cell(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(";") if item.strip()]


def plan_values(config: str, use_local_config: bool) -> dict[str, str]:
    values = dict(PUBLIC_TEMPLATE_VALUES)
    if use_local_config:
        values.update({key: value for key, value in parse_env_file(Path(config)).items() if value})
    return values


def planned_trials_by_requirement(config: str, use_local_config: bool, repetitions: int, prefer_p1: str) -> dict[str, list[dict[str, Any]]]:
    plans = make_plan(plan_values(config, use_local_config), repetitions, prefer_p1)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for plan in plans:
        grouped.setdefault(plan.requirement_id, []).append(asdict(plan))
    return grouped


def rule_parts(requirement: dict[str, str]) -> list[str]:
    parts = [f"status in {requirement.get('accepted_statuses', '-') or '-'}"]
    mapping = [
        ("trial_id_contains_all", "trial_id contains"),
        ("deployment_contains_all", "deployment contains"),
        ("trigger_contains_all", "trigger contains"),
        ("task_contains_all", "task contains"),
        ("notes_contains_all", "notes contain all"),
        ("notes_contains_any", "notes contain any"),
    ]
    for field, label in mapping:
        values = split_cell(requirement.get(field, ""))
        if values:
            parts.append(f"{label}: {', '.join(values)}")
    return parts


def reject_rule(requirement: dict[str, str]) -> str:
    rejects = split_cell(requirement.get("notes_excludes_any", ""))
    if not rejects:
        return "-"
    return "reject if notes/failure evidence contains: " + ", ".join(rejects)


def artifact_roles(plans: list[dict[str, Any]]) -> str:
    if not plans:
        return "-"
    roles = [item["role"] for item in expected_artifacts(plans[0])]
    return "; ".join(roles)


def paper_use_for(complete: bool, phase: str, browser: str) -> str:
    if complete:
        if "Safari" in browser or "Android" in browser:
            return "P1 feasibility evidence available"
        if phase == "active-network-change":
            return "browser CM evidence available for scoped claim"
        return "baseline/control evidence available"
    if phase == "active-network-change":
        return "pending; do not claim browser CM success"
    return "pending; required before active CM claim"


def build_scorecard(
    requirements_path: Path,
    experiments_path: Path,
    config: str,
    use_local_config: bool,
    repetitions: int,
    prefer_p1: str,
) -> dict[str, Any]:
    requirements = load_rows(requirements_path)
    audit = build_audit(requirements_path, experiments_path)
    audit_by_id = {row["requirement_id"]: row for row in audit["results"]}
    planned_by_requirement = planned_trials_by_requirement(config, use_local_config, repetitions, prefer_p1)
    rows: list[AcceptanceRow] = []

    for requirement in requirements:
        rid = requirement["requirement_id"]
        audit_row = audit_by_id[rid]
        plans = planned_by_requirement.get(rid, [])
        rows.append(
            AcceptanceRow(
                requirement_id=rid,
                phase=requirement["phase"],
                browser=requirement["browser"],
                min_count=int(requirement["min_count"]),
                matched_count=int(audit_row["matched_count"]),
                complete=bool(audit_row["complete"]),
                accepted_statuses=requirement.get("accepted_statuses", ""),
                planned_trial_ids=";".join(plan["trial_id"] for plan in plans) if plans else "-",
                acceptance_rule="; ".join(rule_parts(requirement)),
                reject_if=reject_rule(requirement),
                required_artifact_roles=artifact_roles(plans),
                paper_use=paper_use_for(bool(audit_row["complete"]), requirement["phase"], requirement["browser"]),
            )
        )

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "requirements": requirements_path.as_posix(),
        "experiments": experiments_path.as_posix(),
        "config_source": config if use_local_config else "public template",
        "final_protocol_complete": audit["complete"],
        "complete_count": audit["complete_count"],
        "requirement_count": audit["requirement_count"],
        "rows": [asdict(row) for row in rows],
    }


def emit_markdown(scorecard: dict[str, Any]) -> str:
    lines = [
        "# Final Trial Acceptance Scorecard",
        "",
        f"Generated: `{scorecard['generated']}`",
        "",
        "This scorecard is public-safe. It states which final browser handover rows can be accepted into the paper protocol, what each row must prove, and what evidence excludes a CM success claim.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| final protocol complete | `{'yes' if scorecard['final_protocol_complete'] else 'no'}` |",
        f"| complete requirements | `{scorecard['complete_count']}/{scorecard['requirement_count']}` |",
        f"| config source | `{scorecard['config_source']}` |",
        f"| public safe | `{'yes' if scorecard['public_safe'] else 'no'}` |",
        "",
        "## Acceptance Rows",
        "",
        "| requirement | phase | browser | matched | planned trials | paper use |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in scorecard["rows"]:
        lines.append(
            f"| `{row['requirement_id']}` | {row['phase']} | {row['browser']} | {row['matched_count']}/{row['min_count']} | `{row['planned_trial_ids']}` | {row['paper_use']} |"
        )

    lines.extend(["", "## Acceptance Rules", ""])
    for row in scorecard["rows"]:
        lines.extend(
            [
                f"### `{row['requirement_id']}`",
                "",
                f"- accept when: {row['acceptance_rule']}",
                f"- reject CM success when: {row['reject_if']}",
                f"- required artifact roles: {row['required_artifact_roles']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_csv(scorecard: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "requirement_id",
        "phase",
        "browser",
        "min_count",
        "matched_count",
        "complete",
        "accepted_statuses",
        "planned_trial_ids",
        "acceptance_rule",
        "reject_if",
        "required_artifact_roles",
        "paper_use",
    ]
    with output.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(scorecard["rows"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", default=DEFAULT_REQUIRED_TRIALS)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--use-local-config", action="store_true")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--prefer-p1", choices=["safari", "android", "both"], default="safari")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    scorecard = build_scorecard(
        Path(args.requirements),
        Path(args.experiments),
        args.config,
        args.use_local_config,
        args.repetitions,
        args.prefer_p1,
    )
    if args.csv_output:
        write_csv(scorecard, Path(args.csv_output))
    text = json.dumps(scorecard, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(scorecard)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
