#!/usr/bin/env python3
"""Build a one-trial operator packet for the final browser handover loop."""

from __future__ import annotations

import argparse
import json
import sys
from research_clock import utc_date_iso
from pathlib import Path
from typing import Any

from check_next_final_handover_trial_readiness import (
    DEFAULT_CHROME,
    DEFAULT_CONFIG,
    DEFAULT_REQUIREMENTS,
    DEFAULT_SAFARI,
    DEFAULT_SAFARI_TP,
    build_readiness,
)
from select_next_final_handover_trial import DEFAULT_EXPERIMENTS, build_selection


DEFAULT_OUTPUT = "docs/results/final-handover-trial-packet-20260624.md"


def redact_sensitive_enabled(args: argparse.Namespace) -> bool:
    return bool(getattr(args, "redact_sensitive", False))


def artifact_root(next_trial: dict[str, Any]) -> str:
    return f"repro/quic-go-min-repro/{next_trial['artifact_dir']}"


def summary_filename(next_trial: dict[str, Any]) -> str:
    phase = next_trial["phase"]
    browser = next_trial["browser"]
    if phase in {"baseline", "no-change-baseline"}:
        return "controlled-public-h3-baseline-summary.json"
    if browser == "Safari":
        return "safari-controlled-public-h3-network-change-summary.json"
    if browser == "Android Chrome":
        return "android-chrome-controlled-public-h3-network-change-summary.json"
    return "controlled-public-h3-network-change-summary.json"


def expected_artifacts(next_trial: dict[str, Any] | None) -> list[dict[str, str]]:
    if not next_trial:
        return []
    root = artifact_root(next_trial)
    phase = next_trial["phase"]
    browser = next_trial["browser"]
    artifacts = [
        {"role": "server result", "path": f"{root}/results/server.json"},
        {"role": "server qlog directory", "path": f"{root}/qlog"},
        {"role": "public origin readiness", "path": f"{root}/results/public-origin-readiness.json"},
        {"role": "classifier summary", "path": f"{root}/results/{summary_filename(next_trial)}"},
    ]
    if phase in {"baseline", "no-change-baseline"}:
        artifacts.extend(
            [
                {"role": "Chrome bootstrap NetLog", "path": f"{root}/chrome/bootstrap-netlog.json"},
                {"role": "Chrome second NetLog", "path": f"{root}/chrome/second-netlog.json"},
                {"role": "Chrome public H3 summary", "path": f"{root}/results/chrome-public-h3-summary.json"},
            ]
        )
    else:
        artifacts.extend(
            [
                {"role": "network-change command record", "path": f"{root}/results/network-change.json"},
                {"role": "client path-change summary", "path": f"{root}/results/client-path-change-summary.json"},
            ]
        )
        if browser == "Chrome":
            artifacts.append({"role": "Chrome network-change NetLog", "path": f"{root}/chrome/network-change-netlog.json"})
        elif browser == "Safari":
            artifacts.append({"role": "Safari navigation summary", "path": f"{root}/results/safari-navigation.json"})
        elif browser == "Android Chrome":
            artifacts.extend(
                [
                    {"role": "Android navigation summary", "path": f"{root}/results/android-chrome-navigation.json"},
                    {"role": "Android route snapshots", "path": f"{root}/android/ip-route-*.txt"},
                    {"role": "Android address snapshots", "path": f"{root}/android/ip-addr-*.txt"},
                ]
            )
    return artifacts


def build_selection_args(args: argparse.Namespace) -> argparse.Namespace:
    redact_sensitive = redact_sensitive_enabled(args)
    return argparse.Namespace(
        experiments=args.experiments,
        requirements=args.requirements,
        config=args.config,
        use_local_config=args.use_local_config,
        repetitions=args.repetitions,
        prefer_p1=args.prefer_p1,
        redact_sensitive=redact_sensitive,
    )


def build_readiness_args(args: argparse.Namespace) -> argparse.Namespace:
    redact_sensitive = redact_sensitive_enabled(args)
    return argparse.Namespace(
        experiments=args.experiments,
        requirements=args.requirements,
        config=args.config,
        use_local_config_for_plan=args.use_local_config,
        repetitions=args.repetitions,
        prefer_p1=args.prefer_p1,
        chrome_bin=args.chrome_bin,
        safari_bin=args.safari_bin,
        safari_tp_bin=args.safari_tp_bin,
        min_disk_gib=args.min_disk_gib,
        check_local_files=args.check_local_files,
        check_public_origin=args.check_public_origin,
        allow_latent_secondary_path=getattr(args, "allow_latent_secondary_path", False),
        network_change_cmd=getattr(args, "network_change_cmd", ""),
        android_network_change_cmd=getattr(args, "android_network_change_cmd", ""),
        timeout=args.timeout,
        redact_sensitive=redact_sensitive,
    )


def option_flags(args: argparse.Namespace) -> str:
    redact_sensitive = redact_sensitive_enabled(args)
    flags: list[str] = []
    if args.use_local_config:
        flags.append("--use-local-config")
    if redact_sensitive:
        flags.append("--redact-sensitive")
    if args.check_public_origin:
        flags.append("--check-public-origin")
    if getattr(args, "allow_latent_secondary_path", False):
        flags.append("--allow-latent-secondary-path")
    if getattr(args, "network_change_cmd", ""):
        flags.append("--network-change-cmd <configured>")
    if getattr(args, "android_network_change_cmd", ""):
        flags.append("--android-network-change-cmd <configured>")
    if args.check_local_files:
        flags.append("--check-local-files")
    if args.repetitions != 3:
        flags.append(f"--repetitions {args.repetitions}")
    if args.prefer_p1 != "safari":
        flags.append(f"--prefer-p1 {args.prefer_p1}")
    return " ".join(flags)


def build_preflight_commands(args: argparse.Namespace) -> list[str]:
    redact_sensitive = redact_sensitive_enabled(args)
    selection_flags = []
    readiness_flags = []
    checklist_flags = []
    if args.use_local_config:
        selection_flags.append("--use-local-config")
        readiness_flags.append("--use-local-config-for-plan")
        checklist_flags.append("--use-local-config-for-plan")
    if redact_sensitive:
        selection_flags.append("--redact-sensitive")
        readiness_flags.append("--redact-sensitive")
        checklist_flags.append("--redact-sensitive")
    if args.check_public_origin:
        readiness_flags.append("--check-public-origin")
    if getattr(args, "allow_latent_secondary_path", False):
        readiness_flags.append("--allow-latent-secondary-path")
    if getattr(args, "network_change_cmd", ""):
        readiness_flags.extend(
            ["--network-change-cmd", "'<redacted-network-change-cmd>'" if redact_sensitive else args.network_change_cmd]
        )
    if getattr(args, "android_network_change_cmd", ""):
        readiness_flags.extend(
            [
                "--android-network-change-cmd",
                "'<redacted-android-network-change-cmd>'" if redact_sensitive else args.android_network_change_cmd,
            ]
        )
    if args.check_local_files:
        readiness_flags.append("--check-local-files")
        checklist_flags.append("--check-local-files")
    if args.repetitions != 3:
        selection_flags.extend(["--repetitions", str(args.repetitions)])
        readiness_flags.extend(["--repetitions", str(args.repetitions)])
        checklist_flags.extend(["--repetitions", str(args.repetitions)])
    if args.prefer_p1 != "safari":
        selection_flags.extend(["--prefer-p1", args.prefer_p1])
        readiness_flags.extend(["--prefer-p1", args.prefer_p1])
        checklist_flags.extend(["--prefer-p1", args.prefer_p1])
    return [
        "python3 tools/check_controlled_public_config.py --require-baseline-ready",
        " ".join(
            [
                "python3 tools/select_next_final_handover_trial.py",
                *selection_flags,
                "--output docs/results/final-handover-next-trial-20260624.md",
            ]
        ),
        " ".join(
            [
                "python3 tools/check_next_final_handover_trial_readiness.py",
                *readiness_flags,
                "--output docs/results/final-handover-next-trial-readiness-20260624.md",
            ]
        ),
        " ".join(
            [
                "python3 tools/build_final_handover_operator_checklist.py",
                *checklist_flags,
                "--output docs/results/final-handover-operator-checklist-20260624.md",
            ]
        ),
    ]


def build_post_registration_commands(selection: dict[str, Any]) -> list[str]:
    commands = list(selection.get("post_trial_commands") or [])
    commands.extend(
        [
            "python3 tools/build_paper_tables.py --output docs/results/paper-tables-20260624.md",
            "python3 tools/audit_research_bundle.py --output docs/results/research-bundle-audit-20260624.md",
            "python3 tools/verify_research_bundle.py --output docs/results/research-verification-report-20260624.md",
        ]
    )
    return commands


def build_packet(args: argparse.Namespace) -> dict[str, Any]:
    redact_sensitive = redact_sensitive_enabled(args)
    selection = build_selection(build_selection_args(args))
    readiness = build_readiness(build_readiness_args(args))
    next_trial = selection["next_trial"]
    if next_trial is None:
        state = "protocol_complete_or_no_next_trial"
    elif readiness["ready"]:
        state = "ready_to_run"
    else:
        state = "blocked_by_readiness"

    return {
        "generated": utc_date_iso(),
        "state": state,
        "public_safe_default": (not args.use_local_config) or redact_sensitive,
        "redact_sensitive": redact_sensitive,
        "option_flags": option_flags(args),
        "next_trial": next_trial,
        "next_trial_ready": readiness["ready"],
        "missing_required_gates": readiness["missing_required_gates"],
        "required_gates": readiness["required_gates"],
        "gate_values": readiness["gates"],
        "preflight_commands": build_preflight_commands(args),
        "server_command": next_trial["server_command"] if next_trial else "",
        "client_command": next_trial["client_command"] if next_trial else "",
        "expected_artifacts": expected_artifacts(next_trial),
        "post_trial_registration_commands": build_post_registration_commands(selection) if next_trial else [],
        "final_completion": {
            "complete_count": selection["complete_count"],
            "requirement_count": selection["requirement_count"],
            "protocol_complete": selection["protocol_complete"],
            "blockers": selection["blockers"],
        },
    }


def emit_markdown(packet: dict[str, Any]) -> str:
    next_trial = packet["next_trial"]
    missing = packet["missing_required_gates"] or ["-"]
    blockers = packet["final_completion"]["blockers"] or ["-"]
    lines = [
        "# Final Handover Trial Packet",
        "",
        f"Generated: `{packet['generated']}`",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| state | `{packet['state']}` |",
        f"| public-safe default | `{'yes' if packet['public_safe_default'] else 'no'}` |",
        f"| sensitive values redacted | `{'yes' if packet.get('redact_sensitive') else 'no'}` |",
        f"| next trial ready | `{'yes' if packet['next_trial_ready'] else 'no'}` |",
        f"| next trial | `{next_trial['trial_id'] if next_trial else '-'}` |",
        f"| next browser | `{next_trial['browser'] if next_trial else '-'}` |",
        f"| next phase | `{next_trial['phase'] if next_trial else '-'}` |",
        f"| final completion | `{packet['final_completion']['complete_count']}/{packet['final_completion']['requirement_count']}` |",
        "",
        "## Missing Required Gates",
        "",
    ]
    lines.extend(f"- {item}" for item in missing)
    lines.extend(["", "## Final Protocol Blockers", ""])
    lines.extend(f"- {item}" for item in blockers)
    lines.extend(["", "## Preflight Commands", "", "```bash", "\n".join(packet["preflight_commands"]), "```"])
    if next_trial:
        lines.extend(
            [
                "",
                "## Trial",
                "",
                "| field | value |",
                "| --- | --- |",
                f"| trial_id | `{next_trial['trial_id']}` |",
                f"| requirement | `{next_trial['requirement_id']}` |",
                f"| workload | `{next_trial['workload']}` |",
                f"| heartbeat | `{next_trial['heartbeat']}` |",
                f"| expected requests | `{next_trial['expected_requests']}` |",
                f"| artifact dir | `{next_trial['artifact_dir']}` |",
                f"| claim gate | `{next_trial['claim_gate']}` |",
                "",
                "Server/origin terminal:",
                "",
                "```bash",
                packet["server_command"],
                "```",
                "",
                "Browser/client terminal:",
                "",
                "```bash",
                packet["client_command"],
                "```",
                "",
                "Expected artifacts:",
                "",
                "| role | path |",
                "| --- | --- |",
            ]
        )
        for artifact in packet["expected_artifacts"]:
            lines.append(f"| {artifact['role']} | `{artifact['path']}` |")
        lines.extend(
            [
                "",
                "## Post-Trial Registration",
                "",
                "```bash",
                "\n".join(packet["post_trial_registration_commands"]),
                "```",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_output(text: str, output_arg: str | None) -> None:
    if output_arg == "-":
        sys.stdout.write(text)
        return
    if not output_arg:
        sys.stdout.write(text)
        return
    output = Path(output_arg)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--requirements", default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--use-local-config", action="store_true")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--prefer-p1", choices=["safari", "android", "both"], default="safari")
    parser.add_argument("--chrome-bin", default=DEFAULT_CHROME)
    parser.add_argument("--safari-bin", default=DEFAULT_SAFARI)
    parser.add_argument("--safari-tp-bin", default=DEFAULT_SAFARI_TP)
    parser.add_argument("--min-disk-gib", type=float, default=7.0)
    parser.add_argument("--check-local-files", action="store_true")
    parser.add_argument("--check-public-origin", action="store_true")
    parser.add_argument("--allow-latent-secondary-path", action="store_true")
    parser.add_argument("--network-change-cmd", default="")
    parser.add_argument("--android-network-change-cmd", default="")
    parser.add_argument("--redact-sensitive", action="store_true")
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    packet = build_packet(args)
    text = json.dumps(packet, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(packet)
    write_output(text, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
