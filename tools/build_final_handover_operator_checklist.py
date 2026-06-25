#!/usr/bin/env python3
"""Build the operator checklist for completing final browser handover trials."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from research_clock import utc_date_iso
from pathlib import Path
from typing import Any

from audit_final_browser_handover_trials import build_audit as build_final_trial_audit
from check_controlled_public_config import build_report as build_config_report
from check_next_final_handover_trial_readiness import (
    DEFAULT_CHROME,
    DEFAULT_SAFARI,
    DEFAULT_SAFARI_TP,
    build_readiness as build_next_readiness,
)
from plan_artifact_cleanup import build_plan as build_cleanup_plan


DEFAULT_CONFIG = "harness/config/controlled-public-origin.env"
DEFAULT_EXPERIMENTS = "data/experiment-results.csv"
DEFAULT_REQUIREMENTS = "data/final-browser-handover-required-trials.csv"
DEFAULT_OUTPUT = "docs/results/final-handover-operator-checklist-20260624.md"


@dataclass
class ActionItem:
    priority: int
    status: str
    scope: str
    action: str
    reason: str
    commands: list[str]


def add_action(
    actions: list[ActionItem],
    priority: int,
    status: str,
    scope: str,
    action: str,
    reason: str,
    commands: list[str] | None = None,
) -> None:
    actions.append(ActionItem(priority, status, scope, action, reason, commands or []))


def build_actions(
    config: dict[str, Any],
    next_readiness: dict[str, Any],
    cleanup: dict[str, Any],
    final_audit: dict[str, Any],
) -> list[ActionItem]:
    actions: list[ActionItem] = []
    if not config["baseline_config_ready"]:
        add_action(
            actions,
            1,
            "todo-now",
            "controlled public baseline",
            "Create and fill the private controlled public origin config.",
            "The next selected trial is a controlled-public Chrome baseline and config baseline readiness is false.",
            [
                "bash harness/scripts/init-controlled-public-config.sh",
                "python3 tools/build_controlled_public_config_worksheet.py --output docs/results/controlled-public-config-worksheet-20260624.md",
                "$EDITOR harness/config/controlled-public-origin.env",
                "python3 tools/check_controlled_public_config.py --require-baseline-ready",
            ],
        )
    else:
        add_action(
            actions,
            1,
            "ready",
            "controlled public baseline",
            "Controlled public baseline config is ready.",
            "Baseline config keys are present and non-placeholder.",
            [
                "python3 tools/build_controlled_public_config_worksheet.py --output docs/results/controlled-public-config-worksheet-20260624.md",
                "python3 tools/check_controlled_public_config.py --require-baseline-ready",
            ],
        )

    if not cleanup["target_met_by_selected"]:
        add_action(
            actions,
            2,
            "todo-now",
            "storage",
            "Free enough disk before running heavy browser/qlog captures.",
            (
                "Current artifact cleanup candidates are insufficient for the target free-space threshold; "
                f"remaining external cleanup gap is {cleanup['remaining_gap_human']}."
            ),
            [
                "python3 tools/plan_artifact_cleanup.py --target-free-gib 7 --candidate-policy review-unreferenced --output docs/results/artifact-cleanup-dry-run-20260624.md",
                "python3 tools/apply_artifact_cleanup_plan.py --target-free-gib 7 --candidate-policy review-unreferenced --output docs/results/artifact-cleanup-apply-report-20260625.md",
                "python3 tools/audit_artifact_cleanup_safety.py --target-free-gib 7 --output docs/results/artifact-cleanup-safety-audit-20260624.md",
            ],
        )
    else:
        add_action(
            actions,
            2,
            "ready",
            "storage",
            "Disk target can be met by reviewed artifact cleanup candidates.",
            f"Selected cleanup candidates reclaim {cleanup['selected_reclaimable_human']}.",
            [
                "python3 tools/plan_artifact_cleanup.py --target-free-gib 7 --candidate-policy review-unreferenced --output docs/results/artifact-cleanup-dry-run-20260624.md",
                "python3 tools/apply_artifact_cleanup_plan.py --target-free-gib 7 --candidate-policy review-unreferenced --output docs/results/artifact-cleanup-apply-report-20260625.md",
                "python3 tools/audit_artifact_cleanup_safety.py --target-free-gib 7 --output docs/results/artifact-cleanup-safety-audit-20260624.md",
            ],
        )

    if next_readiness["ready"]:
        add_action(
            actions,
            3,
            "ready-to-run",
            "next trial",
            f"Run next trial {next_readiness['next_trial']['trial_id']}.",
            "All gates required by the selected next trial are ready.",
            [
                "bash harness/scripts/final-handover-run-next.sh",
                "python3 tools/select_next_final_handover_trial.py --output docs/results/final-handover-next-trial-20260624.md",
                "python3 tools/check_next_final_handover_trial_readiness.py --min-disk-gib 7 --output docs/results/final-handover-next-trial-readiness-20260624.md",
            ],
        )
    else:
        add_action(
            actions,
            3,
            "blocked-now",
            "next trial",
            "Do not run the next final handover trial yet.",
            "Missing required gates: " + ", ".join(next_readiness["missing_required_gates"] or ["none"]),
            [
                "bash harness/scripts/final-handover-run-next.sh",
                "python3 tools/check_next_final_handover_trial_readiness.py --min-disk-gib 7 --output docs/results/final-handover-next-trial-readiness-20260624.md",
            ],
        )

    if not config["active_network_change_config_ready"]:
        add_action(
            actions,
            4,
            "todo-later",
            "active network-change",
            "Prepare active network-change config before Chrome/Safari active trials.",
            "The final protocol requires active path-change trials after the baseline/no-change rows are registered.",
            [
                "python3 tools/check_controlled_public_config.py --require-active-ready",
                "python3 tools/check_final_browser_handover_readiness.py --output docs/results/final-browser-handover-readiness-20260624.md",
            ],
        )
    if not next_readiness["handover"]["secondary_path_ready"]:
        add_action(
            actions,
            5,
            "todo-later",
            "desktop path-change",
            "Provide a real active secondary path before desktop active network-change trials.",
            "Chrome/Safari active trials require a path change, but the current machine has no secondary active non-loopback IPv4 path.",
            ["python3 tools/check_handover_readiness.py --format markdown"],
        )
    if not next_readiness["handover"]["android_ready"]:
        add_action(
            actions,
            6,
            "todo-later",
            "Android P1",
            "Connect an Android device over ADB before Android Chrome feasibility trials.",
            "The P1 feasibility requirement can be satisfied by Safari or Android, but Android remains unavailable.",
            ["adb devices", "python3 tools/check_handover_readiness.py --format markdown"],
        )
    if not final_audit["complete"]:
        add_action(
            actions,
            7,
            "incomplete",
            "final protocol",
            "Continue the final trial loop until all required rows are counted.",
            f"Current final completion is {final_audit['complete_count']}/{final_audit['requirement_count']}.",
            ["python3 tools/audit_final_browser_handover_trials.py --require-complete"],
        )
    return sorted(actions, key=lambda item: item.priority)


def build_checklist(args: argparse.Namespace) -> dict[str, Any]:
    redact_sensitive = bool(getattr(args, "redact_sensitive", False))
    config = build_config_report(Path(args.config), check_files=False)
    next_args = argparse.Namespace(
        experiments=args.experiments,
        requirements=args.requirements,
        config=args.config,
        use_local_config_for_plan=args.use_local_config_for_plan,
        repetitions=args.repetitions,
        prefer_p1=args.prefer_p1,
        chrome_bin=args.chrome_bin,
        safari_bin=args.safari_bin,
        safari_tp_bin=args.safari_tp_bin,
        min_disk_gib=args.min_disk_gib,
        check_local_files=args.check_local_files,
        check_public_origin=False,
        timeout=args.timeout,
        redact_sensitive=redact_sensitive,
    )
    next_readiness = build_next_readiness(next_args)
    cleanup = build_cleanup_plan(
        ["repro/quic-go-min-repro/artifacts", "harness/results"],
        args.target_free_gib,
        candidate_policy="review-unreferenced",
        experiments_path=Path(args.experiments),
        repetitions=args.repetitions,
        prefer_p1=args.prefer_p1,
    )
    final_audit = build_final_trial_audit(Path(args.requirements), Path(args.experiments))
    actions = build_actions(config, next_readiness, cleanup, final_audit)
    return {
        "generated": utc_date_iso(),
        "objective": "complete final controlled-public/browser handover evidence for the QUIC/HTTP/3 CM paper",
        "redact_sensitive": redact_sensitive,
        "next_trial": next_readiness["next_trial"],
        "next_trial_ready": next_readiness["ready"],
        "config": {
            "baseline_config_ready": config["baseline_config_ready"],
            "active_network_change_config_ready": config["active_network_change_config_ready"],
            "android_network_change_config_ready": config["android_network_change_config_ready"],
        },
        "storage": {
            "current_free_human": cleanup["current_free_human"],
            "target_free_gib": cleanup["target_free_gib"],
            "target_met_by_selected": cleanup["target_met_by_selected"],
            "remaining_gap_human": cleanup["remaining_gap_human"],
        },
        "final_trials": {
            "complete": final_audit["complete"],
            "complete_count": final_audit["complete_count"],
            "requirement_count": final_audit["requirement_count"],
            "blockers": final_audit["blockers"],
        },
        "actions": [asdict(item) for item in actions],
    }


def emit_markdown(checklist: dict[str, Any]) -> str:
    next_trial = checklist["next_trial"]
    lines = [
        "# Final Handover Operator Checklist",
        "",
        f"Generated: `{checklist['generated']}`",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| next trial | `{next_trial['trial_id'] if next_trial else '-'}` |",
        f"| next trial ready | `{'yes' if checklist['next_trial_ready'] else 'no'}` |",
        f"| sensitive values redacted | `{'yes' if checklist.get('redact_sensitive') else 'no'}` |",
        f"| baseline config ready | `{'yes' if checklist['config']['baseline_config_ready'] else 'no'}` |",
        f"| active config ready | `{'yes' if checklist['config']['active_network_change_config_ready'] else 'no'}` |",
        f"| Android config ready | `{'yes' if checklist['config']['android_network_change_config_ready'] else 'no'}` |",
        f"| current disk free | `{checklist['storage']['current_free_human']}` |",
        f"| target free GiB | `{checklist['storage']['target_free_gib']}` |",
        f"| storage target met by artifact cleanup | `{'yes' if checklist['storage']['target_met_by_selected'] else 'no'}` |",
        f"| remaining external cleanup gap | `{checklist['storage']['remaining_gap_human']}` |",
        f"| final trial completion | `{checklist['final_trials']['complete_count']}/{checklist['final_trials']['requirement_count']}` |",
        "",
        "## Actions",
        "",
        "| priority | status | scope | action | reason |",
        "| ---: | --- | --- | --- | --- |",
    ]
    for item in checklist["actions"]:
        lines.append(
            f"| {item['priority']} | `{item['status']}` | {item['scope']} | {item['action']} | {item['reason']} |"
        )
    lines.extend(["", "## Commands", ""])
    for item in checklist["actions"]:
        if not item["commands"]:
            continue
        lines.extend(
            [
                f"### {item['priority']}. {item['scope']}",
                "",
                "```bash",
                "\n".join(item["commands"]),
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--requirements", default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--use-local-config-for-plan", action="store_true")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--prefer-p1", choices=["safari", "android", "both"], default="safari")
    parser.add_argument("--chrome-bin", default=DEFAULT_CHROME)
    parser.add_argument("--safari-bin", default=DEFAULT_SAFARI)
    parser.add_argument("--safari-tp-bin", default=DEFAULT_SAFARI_TP)
    parser.add_argument("--min-disk-gib", type=float, default=7.0)
    parser.add_argument("--target-free-gib", type=float, default=7.0)
    parser.add_argument("--check-local-files", action="store_true")
    parser.add_argument("--redact-sensitive", action="store_true")
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    checklist = build_checklist(args)
    text = json.dumps(checklist, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(checklist)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
