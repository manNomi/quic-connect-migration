#!/usr/bin/env python3
"""Select the next final browser handover trial from current CSV state."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from research_clock import utc_date_iso
from pathlib import Path
from typing import Any

from audit_final_browser_handover_trials import build_audit, load_rows
from plan_final_browser_handover_runs import (
    DEFAULT_CONFIG,
    DEFAULT_REQUIRED_TRIALS,
    PUBLIC_TEMPLATE_VALUES,
    TrialPlan,
    make_plan,
    parse_env_file,
)


DEFAULT_EXPERIMENTS = "data/experiment-results.csv"
DEFAULT_OUTPUT = "docs/results/final-handover-next-trial-20260624.md"


def write_output(text: str, output_arg: str | None) -> None:
    if output_arg == "-":
        print(text, end="")
        return
    if output_arg:
        output = Path(output_arg)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def plan_values(config: str, use_local_config: bool) -> dict[str, str]:
    values = dict(PUBLIC_TEMPLATE_VALUES)
    if use_local_config:
        values.update({key: value for key, value in parse_env_file(Path(config)).items() if value})
    return values


def existing_trial_ids(experiments_path: Path) -> set[str]:
    return {row["trial_id"] for row in load_rows(experiments_path)}


def incomplete_requirements(audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["requirement_id"]: item
        for item in audit["results"]
        if not item["complete"]
    }


def select_next_plan(plans: list[TrialPlan], incomplete: dict[str, dict[str, Any]], existing: set[str]) -> TrialPlan | None:
    for plan in plans:
        if plan.requirement_id in incomplete and plan.trial_id not in existing:
            return plan
    return None


def build_selection(args: argparse.Namespace) -> dict[str, Any]:
    experiments_path = Path(args.experiments)
    requirements_path = Path(args.requirements)
    audit = build_audit(requirements_path, experiments_path)
    values = plan_values(args.config, args.use_local_config)
    plans = make_plan(values, args.repetitions, args.prefer_p1)
    incomplete = incomplete_requirements(audit)
    existing = existing_trial_ids(experiments_path)
    selected = select_next_plan(plans, incomplete, existing)
    selection = {
        "generated": utc_date_iso(),
        "experiments": experiments_path.as_posix(),
        "requirements": requirements_path.as_posix(),
        "config_source": args.config if args.use_local_config else "public template",
        "public_safe_default": not args.use_local_config,
        "protocol_complete": audit["complete"],
        "complete_count": audit["complete_count"],
        "requirement_count": audit["requirement_count"],
        "blockers": audit["blockers"],
        "existing_trial_count": len(existing),
        "planned_trial_count": len(plans),
        "next_trial": asdict(selected) if selected else None,
        "next_trial_index": (plans.index(selected) + 1) if selected else None,
        "post_trial_commands": [],
    }
    if selected:
        artifact_dir = f"repro/quic-go-min-repro/{selected.artifact_dir}"
        selection["post_trial_commands"] = [
            (
                "python3 tools/check_final_handover_trial_artifact_bundle.py "
                f"--trial-id {selected.trial_id} "
                f"--artifact-dir {artifact_dir} "
                "--require-final-countable "
                "--require-complete"
            ),
            (
                "python3 tools/validate_final_handover_trial_artifact.py "
                f"--trial-id {selected.trial_id} "
                f"--artifact-dir {artifact_dir} "
                "--require-final-countable"
            ),
            (
                "python3 tools/append_final_handover_result_row.py "
                f"--trial-id {selected.trial_id} "
                f"--artifact-dir {artifact_dir} "
                "--require-final-countable "
                "--require-artifact-bundle "
                "--output /tmp/final-handover-append-dry-run.md"
            ),
            (
                "python3 tools/append_final_handover_result_row.py "
                f"--trial-id {selected.trial_id} "
                f"--artifact-dir {artifact_dir} "
                "--require-final-countable "
                "--require-artifact-bundle "
                "--apply"
            ),
            "python3 tools/audit_final_browser_handover_trials.py --output docs/results/final-browser-handover-trial-audit-20260624.md",
        ]
    return selection


def emit_markdown(selection: dict[str, Any]) -> str:
    next_trial = selection["next_trial"]
    blockers = selection["blockers"] or ["-"]
    lines = [
        "# Final Handover Next Trial",
        "",
        f"Generated: `{selection['generated']}`",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| experiments | `{selection['experiments']}` |",
        f"| config source | `{selection['config_source']}` |",
        f"| public-safe default | `{'yes' if selection['public_safe_default'] else 'no'}` |",
        f"| final protocol complete | `{'yes' if selection['protocol_complete'] else 'no'}` |",
        f"| complete requirements | `{selection['complete_count']}/{selection['requirement_count']}` |",
        f"| existing trial rows | `{selection['existing_trial_count']}` |",
        f"| planned trial executions | `{selection['planned_trial_count']}` |",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {item}" for item in blockers)

    if not next_trial:
        lines.extend(
            [
                "",
                "## Next Trial",
                "",
                "No next trial was selected. Either the final protocol is complete, or every planned trial id for incomplete requirements already exists in the experiment CSV.",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    lines.extend(
        [
            "",
            "## Next Trial",
            "",
            "| field | value |",
            "| --- | --- |",
            f"| queue index | `{selection['next_trial_index']}` |",
            f"| trial_id | `{next_trial['trial_id']}` |",
            f"| requirement | `{next_trial['requirement_id']}` |",
            f"| phase | `{next_trial['phase']}` |",
            f"| browser | `{next_trial['browser']}` |",
            f"| workload | `{next_trial['workload']}` |",
            f"| heartbeat | `{next_trial['heartbeat']}` |",
            f"| expected requests | `{next_trial['expected_requests']}` |",
            f"| artifact dir | `{next_trial['artifact_dir']}` |",
            f"| claim gate | `{next_trial['claim_gate']}` |",
            "",
            "Server/origin terminal:",
            "",
            "```bash",
            next_trial["server_command"],
            "```",
            "",
            "Browser/client terminal:",
            "",
            "```bash",
            next_trial["client_command"],
            "```",
            "",
            "Post-trial registration commands:",
            "",
            "```bash",
            "\n".join(selection["post_trial_commands"]),
            "```",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--requirements", default=DEFAULT_REQUIRED_TRIALS)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--use-local-config", action="store_true")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--prefer-p1", choices=["safari", "android", "both"], default="safari")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if args.repetitions < 1:
        raise SystemExit("--repetitions must be positive")

    selection = build_selection(args)
    text = json.dumps(selection, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(selection)
    write_output(text, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
