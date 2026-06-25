#!/usr/bin/env python3
"""Build a public-safe handoff packet for external final handover inputs."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from research_clock import utc_date_iso
from pathlib import Path
from typing import Any

from build_controlled_public_config_worksheet import build_worksheet
from build_final_handover_operator_checklist import (
    DEFAULT_CONFIG,
    DEFAULT_EXPERIMENTS,
    DEFAULT_REQUIREMENTS,
    build_checklist,
)
from check_aws_identity_readiness import build_readiness as build_aws_identity_readiness
from check_handover_readiness import build_readiness as build_handover_readiness
from check_next_final_handover_trial_readiness import DEFAULT_CHROME, DEFAULT_SAFARI, DEFAULT_SAFARI_TP


DEFAULT_OUTPUT = "docs/results/final-handover-external-inputs-20260624.md"


@dataclass(frozen=True)
class ExternalInputItem:
    id: str
    urgency: str
    status: str
    input_needed: str
    why: str
    validation_command: str
    safe_handling: str
    evidence: str


def status_label(ready: bool, when_ready: str = "ready", when_missing: str = "needed") -> str:
    return when_ready if ready else when_missing


def join_keys(keys: list[str]) -> str:
    return ", ".join(keys) if keys else "-"


def build_items(
    worksheet: dict[str, Any],
    checklist: dict[str, Any],
    handover: dict[str, Any],
) -> list[ExternalInputItem]:
    storage = checklist["storage"]
    final_trials = checklist["final_trials"]
    next_trial = checklist["next_trial"] or {}
    baseline_missing = worksheet["baseline_missing"]
    active_missing = worksheet["active_missing"]
    android_missing = worksheet["android_missing"]

    items = [
        ExternalInputItem(
            id="disk-free-space",
            urgency="now",
            status=status_label(storage["target_met_by_selected"]),
            input_needed=f"Free local disk until at least {storage['target_free_gib']} GiB is available before heavy NetLog/qlog captures.",
            why=(
                "Controlled-public wrappers now enforce the same minimum free-space guard used by readiness checks; "
                f"current cleanup plan still has external gap {storage['remaining_gap_human']}."
            ),
            validation_command="python3 tools/plan_artifact_cleanup.py --target-free-gib 7 --candidate-policy review-unreferenced --output docs/results/artifact-cleanup-dry-run-20260624.md",
            safe_handling="Do not delete CSV-referenced raw artifacts unless they are archived and paper evidence is preserved.",
            evidence=f"current_free={storage['current_free_human']}; target_met={storage['target_met_by_selected']}",
        ),
        ExternalInputItem(
            id="controlled-public-baseline-config",
            urgency="now",
            status=status_label(worksheet["baseline_config_ready"]),
            input_needed="Create the ignored controlled-public origin env file and fill baseline DNS/TLS/Alt-Svc/Chrome fields.",
            why="The next selected final trial is the controlled-public Chrome application H3 baseline.",
            validation_command="python3 tools/check_controlled_public_config.py --require-baseline-ready",
            safe_handling="Keep real domain, certificate path, private key path, and account-specific values out of tracked files.",
            evidence=f"missing_baseline_keys={join_keys(baseline_missing)}",
        ),
        ExternalInputItem(
            id="public-origin-host",
            urgency="now",
            status=status_label(worksheet["baseline_config_ready"]),
            input_needed="Provide a public WebPKI origin that serves both TCP HTTPS Alt-Svc bootstrap and UDP HTTP/3 on the configured port.",
            why="Browser CM results are interpretable only after a controlled public application H3 baseline passes.",
            validation_command="python3 tools/check_public_origin_readiness.py --url \"$PUBLIC_ORIGIN_URL\" --require-h3-alt-svc --format markdown",
            safe_handling="Run origin-host file checks on the origin host; local client reports must not expose TLS paths.",
            evidence=f"next_trial={next_trial.get('trial_id', '-')}; baseline_ready={worksheet['baseline_config_ready']}",
        ),
        ExternalInputItem(
            id="active-network-change-path",
            urgency="after-baseline",
            status=status_label(
                handover["secondary_path_ready"] and not active_missing,
                when_missing="needed-after-baseline",
            ),
            input_needed="Prepare a real active secondary path and an explicit NETWORK_CHANGE_CMD for desktop Chrome/Safari active trials.",
            why="Server tuple/qlog evidence cannot be interpreted as CM unless the client active path actually changes.",
            validation_command="python3 tools/check_handover_readiness.py --format markdown && python3 tools/check_controlled_public_config.py --require-active-ready",
            safe_handling="Use only an operator-approved local command; do not commit machine-specific interface commands.",
            evidence=(
                f"secondary_path_ready={handover['secondary_path_ready']}; "
                f"missing_active_keys={join_keys(active_missing)}"
            ),
        ),
        ExternalInputItem(
            id="android-p1-feasibility",
            urgency="p1-alternative",
            status=status_label(
                handover["android_ready"] and not android_missing,
                when_missing="optional-missing",
            ),
            input_needed="Connect an Android device over ADB and provide an approved Android network-change command if Android is used for P1 feasibility.",
            why="The P1 requirement can be satisfied by Safari or Android, but Android evidence needs ADB route/address/connectivity snapshots.",
            validation_command="adb devices && python3 tools/check_handover_readiness.py --format markdown",
            safe_handling="Do not commit device identifiers or carrier-specific command output.",
            evidence=f"android_ready={handover['android_ready']}; missing_android_keys={join_keys(android_missing)}",
        ),
        ExternalInputItem(
            id="aws-identity",
            urgency="automation-optional",
            status=status_label(handover["aws_identity_ok"], when_missing="optional-missing"),
            input_needed="Provide AWS CLI identity only if automated EC2/public-origin or CloudFront follow-up provisioning should be run.",
            why="Current final browser handover baseline can proceed with a manually managed public origin, but AWS automation needs caller identity.",
            validation_command="python3 tools/check_aws_identity_readiness.py --require-ok",
            safe_handling="Use local AWS profiles/SSO/env vars only; never commit credentials or access-key CSV files.",
            evidence=(
                f"aws_identity_ok={handover['aws_identity_ok']}; "
                f"classification={handover.get('aws_identity_classification', '-')}"
            ),
        ),
        ExternalInputItem(
            id="final-protocol-completion",
            urgency="loop",
            status=status_label(final_trials["complete"], when_missing="incomplete"),
            input_needed="Repeat the selected final trial packet, artifact bundle gate, validation, append, and audit loop until all requirements complete.",
            why="The paper cannot claim final browser/mobile handover results before required rows are counted.",
            validation_command="python3 tools/audit_final_browser_handover_trials.py --require-complete",
            safe_handling="Append only with --require-final-countable and --require-artifact-bundle.",
            evidence=f"completion={final_trials['complete_count']}/{final_trials['requirement_count']}",
        ),
    ]
    return items


def handover_payload(handover: Any, aws_identity: Any) -> dict[str, Any]:
    return {
        "secondary_path_ready": handover.secondary_path_ready,
        "android_ready": handover.android_ready,
        "aws_identity_ok": aws_identity.identity_ok,
        "aws_identity_classification": aws_identity.classification,
        "disk_available_gib": handover.disk_available_gib,
    }


def build_handoff(args: argparse.Namespace) -> dict[str, Any]:
    worksheet = build_worksheet(Path(args.config), check_files=args.check_local_files)
    checklist_args = argparse.Namespace(
        config=args.config,
        experiments=args.experiments,
        requirements=args.requirements,
        use_local_config_for_plan=args.use_local_config_for_plan,
        repetitions=args.repetitions,
        prefer_p1=args.prefer_p1,
        chrome_bin=args.chrome_bin,
        safari_bin=args.safari_bin,
        safari_tp_bin=args.safari_tp_bin,
        min_disk_gib=args.min_disk_gib,
        target_free_gib=args.target_free_gib,
        check_local_files=args.check_local_files,
        timeout=args.timeout,
    )
    checklist = build_checklist(checklist_args)
    aws_identity = build_aws_identity_readiness(timeout=args.timeout)
    handover = handover_payload(build_handover_readiness(args.chrome_bin), aws_identity)
    items = build_items(worksheet, checklist, handover)
    now_ready = checklist["next_trial_ready"]
    needed_now = [item for item in items if item.urgency == "now" and item.status != "ready"]
    return {
        "check_date": utc_date_iso(),
        "public_safe": True,
        "next_trial": checklist["next_trial"],
        "next_trial_ready": now_ready,
        "can_codex_run_next_trial_now": now_ready and not needed_now,
        "needed_now_count": len(needed_now),
        "items": [asdict(item) for item in items],
    }


def emit_markdown(handoff: dict[str, Any]) -> str:
    next_trial = handoff["next_trial"] or {}
    lines = [
        "# Final Handover External Inputs Handoff",
        "",
        f"Generated: `{handoff['check_date']}`",
        "",
        "This packet is public-safe. It lists required external inputs and validation commands without printing domains, TLS paths, private keys, AWS account IDs, device IDs, or network-change command bodies.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| next trial | `{next_trial.get('trial_id', '-')}` |",
        f"| next trial ready | `{'yes' if handoff['next_trial_ready'] else 'no'}` |",
        f"| Codex can run next trial now | `{'yes' if handoff['can_codex_run_next_trial_now'] else 'no'}` |",
        f"| needed-now inputs | `{handoff['needed_now_count']}` |",
        f"| public safe | `{'yes' if handoff['public_safe'] else 'no'}` |",
        "",
        "## Inputs",
        "",
        "| id | urgency | status | input needed | validation command | evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in handoff["items"]:
        lines.append(
            f"| `{item['id']}` | `{item['urgency']}` | `{item['status']}` | {item['input_needed']} | `{item['validation_command']}` | `{item['evidence']}` |"
        )
    lines.extend(["", "## Safe Handling", ""])
    for item in handoff["items"]:
        lines.append(f"- `{item['id']}`: {item['safe_handling']}")
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
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    handoff = build_handoff(args)
    text = json.dumps(handoff, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(handoff)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
