#!/usr/bin/env python3
"""Build a current unblock dashboard for final QUIC CM paper experiments."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from check_next_final_handover_trial_readiness import (
    DEFAULT_CHROME,
    DEFAULT_CONFIG,
    DEFAULT_REQUIREMENTS,
    DEFAULT_SAFARI,
    DEFAULT_SAFARI_TP,
    build_readiness as build_next_readiness,
)
from plan_public_origin_recovery import build_plan as build_public_origin_recovery_plan
from plan_public_origin_recovery import DEFAULT_EXPERIMENTS
from research_clock import utc_date_iso


DEFAULT_JSON_OUTPUT = "data/final-research-unblock-dashboard-20260629.json"
DEFAULT_CSV_OUTPUT = "data/final-research-unblock-dashboard-20260629.csv"
DEFAULT_MD_OUTPUT = "docs/results/final-research-unblock-dashboard-20260629.md"
DEFAULT_NETWORK_CHANGE_CMD = "networksetup -setairportpower 'en0' off"

ACTION_FIELDS = [
    "priority",
    "gate_id",
    "status",
    "owner",
    "evidence",
    "why_it_matters",
    "next_action",
    "success_gate",
]


def status_from_ready(ready: bool, blocked_label: str = "blocked") -> str:
    return "ready" if ready else blocked_label


def bool_text(value: object) -> str:
    return "yes" if bool(value) else "no"


def first_action(actions: list[str]) -> str:
    return actions[0] if actions else "-"


def action_rows(recovery: dict[str, Any], readiness: dict[str, Any]) -> list[dict[str, str]]:
    origin_access = recovery.get("origin_access", {})
    public_origin = recovery.get("public_origin", {})
    recovery_paths = origin_access.get("recovery_paths", {})
    aws = origin_access.get("aws", {})
    tcp = origin_access.get("tcp", {})
    baseline = recovery.get("baseline", {})
    final_protocol = recovery.get("final_protocol", {})
    iphone_usb = readiness.get("iphone_usb", {})
    next_trial = readiness.get("next_trial") or {}
    handover = readiness.get("handover", {})
    gates = readiness.get("gates", {})
    missing = readiness.get("missing_required_gates") or []

    rows = [
        {
            "priority": "P0",
            "gate_id": "aws_identity_or_manual_origin_access",
            "status": status_from_ready(
                bool(aws.get("identity_ok") or recovery_paths.get("remote_ssh_ready") or recovery_paths.get("local_tls_material_ready"))
            ),
            "owner": "operator",
            "evidence": (
                f"aws={aws.get('classification', '-')}; "
                f"ssh_ready={bool_text(recovery_paths.get('remote_ssh_ready'))}; "
                f"local_tls_ready={bool_text(recovery_paths.get('local_tls_material_ready'))}"
            ),
            "why_it_matters": "The controlled public origin cannot be restarted or redeployed without an access path.",
            "next_action": recovery.get("next_step", {}).get("next_command", "-")
            if recovery.get("next_step", {}).get("step_id") == "aws-credentials"
            else "Use whichever recovery path is ready to restart the controlled public H3 origin.",
            "success_gate": "AWS identity ready, SSH recovery ready, or local TLS/origin material ready.",
        },
        {
            "priority": "P0",
            "gate_id": "public_origin_live_h3",
            "status": status_from_ready(bool(public_origin.get("ok"))),
            "owner": "operator+codex",
            "evidence": (
                f"public_origin={public_origin.get('classification', '-')}; "
                f"tcp={tcp.get('classification', '-')}; "
                f"h3_alt_svc={bool_text(public_origin.get('has_h3_alt_svc'))}"
            ),
            "why_it_matters": "Browser CM rows are invalid until the controlled origin accepts HTTPS and advertises HTTP/3.",
            "next_action": "Recover/restart the controlled public origin, then rerun public origin readiness.",
            "success_gate": "check_public_origin_readiness ok=true and has_h3_alt_svc=true.",
        },
        {
            "priority": "P0",
            "gate_id": "desktop_path_change_ready",
            "status": status_from_ready(bool(gates.get("desktop_path_change_ready"))),
            "owner": "operator+codex",
            "evidence": (
                f"mode={handover.get('desktop_path_change_mode', '-')}; "
                f"iphone={iphone_usb.get('classification', '-')}; "
                f"secondary={bool_text(handover.get('secondary_path_ready'))}"
            ),
            "why_it_matters": "The selected Chrome active row requires a real client path change during the HTTP/3 workload.",
            "next_action": first_action(iphone_usb.get("next_actions") if isinstance(iphone_usb.get("next_actions"), list) else []),
            "success_gate": "desktop_path_change_ready=yes or latent_iphone_usb_failover_observed with --allow-latent-secondary-path.",
        },
        {
            "priority": "P1",
            "gate_id": "fresh_public_h3_baseline",
            "status": "waiting" if not public_origin.get("ok") else status_from_ready(bool(baseline.get("ready")), "blocked"),
            "owner": "codex",
            "evidence": f"historical_baseline={baseline.get('status', '-')}; public_origin_ok={bool_text(public_origin.get('ok'))}",
            "why_it_matters": "A fresh no-change browser H3 baseline prevents origin recovery artifacts from being mistaken for CM results.",
            "next_action": "Rerun the controlled public Chrome H3 no-change baseline after origin recovery.",
            "success_gate": "new controlled-public baseline summary status PASS with application HTTP/3 confirmed.",
        },
        {
            "priority": "P1",
            "gate_id": "next_chrome_active_row",
            "status": "ready" if readiness.get("ready") else "waiting",
            "owner": "codex",
            "evidence": (
                f"next_trial={next_trial.get('trial_id', '-')}; "
                f"missing={','.join(missing) or '-'}; "
                f"final={final_protocol.get('complete_count', '-')}/{final_protocol.get('requirement_count', '-')}"
            ),
            "why_it_matters": "This is the first missing final-protocol row for the paper's browser CM evidence chain.",
            "next_action": "Run the selected Chrome no-heartbeat active public row only after all P0 gates are ready.",
            "success_gate": "artifact bundle validates and final trial audit count increases for no-heartbeat active CM.",
        },
        {
            "priority": "P2",
            "gate_id": "p1_cross_browser_feasibility",
            "status": "waiting",
            "owner": "codex",
            "evidence": (
                f"safari_webdriver={bool_text(gates.get('safari_webdriver_ready'))}; "
                f"android_adb={bool_text(gates.get('android_adb_ready'))}"
            ),
            "why_it_matters": "The final paper should not rely only on Chrome if Safari or Android feasibility can be captured.",
            "next_action": "After Chrome active rows, run Safari feasibility first unless an Android ADB device is connected.",
            "success_gate": "At least one Safari or Android feasibility row is countable in final audit.",
        },
    ]
    return rows


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    def cell(value: object) -> str:
        return str(value if value is not None else "").replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def build_dashboard(args: argparse.Namespace) -> dict[str, Any]:
    recovery_args = argparse.Namespace(
        config=args.config,
        required_trials=args.requirements,
        experiments=args.experiments,
        ssh_users=args.ssh_users,
        timeout=args.timeout,
        skip_network_probe=False,
        skip_ssh_probe=False,
        skip_aws_probe=False,
        skip_public_origin_probe=False,
    )
    recovery = build_public_origin_recovery_plan(recovery_args)
    readiness_args = argparse.Namespace(
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
        check_local_files=False,
        check_public_origin=True,
        allow_latent_secondary_path=True,
        network_change_cmd=args.network_change_cmd,
        android_network_change_cmd=args.android_network_change_cmd,
        redact_sensitive=True,
        timeout=args.timeout,
    )
    readiness = build_next_readiness(readiness_args)
    rows = action_rows(recovery, readiness)
    p0_blockers = [row["gate_id"] for row in rows if row["priority"] == "P0" and row["status"] != "ready"]
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "next_trial": readiness.get("next_trial"),
        "next_trial_ready": readiness.get("ready"),
        "missing_required_gates": readiness.get("missing_required_gates"),
        "p0_blockers": p0_blockers,
        "final_protocol": recovery.get("final_protocol"),
        "public_origin": recovery.get("public_origin"),
        "iphone_usb": readiness.get("iphone_usb"),
        "actions": rows,
        "claim_boundary": (
            "This dashboard is an execution/unblock artifact. It is not QUIC migration evidence; "
            "only validated final trial artifacts can support browser CM claims."
        ),
    }


def write_outputs(dashboard: dict[str, Any], *, json_output: str, csv_output: str, md_output: str) -> None:
    json_path = Path(json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(dashboard, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    csv_path = Path(csv_output)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=ACTION_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(dashboard["actions"])

    md_path = Path(md_output)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(emit_markdown(dashboard), encoding="utf-8")


def emit_markdown(dashboard: dict[str, Any]) -> str:
    next_trial = dashboard.get("next_trial") or {}
    final = dashboard.get("final_protocol") or {}
    origin = dashboard.get("public_origin") or {}
    iphone = dashboard.get("iphone_usb") or {}
    actions = dashboard.get("actions") or []
    return "\n".join(
        [
            "# Final Research Unblock Dashboard",
            "",
            f"Generated: `{dashboard['generated']}`",
            "",
            "## Summary",
            "",
            markdown_table(
                ["field", "value"],
                [
                    ["next trial", next_trial.get("trial_id", "-")],
                    ["next trial ready", bool_text(dashboard.get("next_trial_ready"))],
                    ["missing required gates", ", ".join(dashboard.get("missing_required_gates") or ["-"])],
                    ["P0 blockers", ", ".join(dashboard.get("p0_blockers") or ["-"])],
                    ["final protocol", f"{final.get('complete_count', '-')}/{final.get('requirement_count', '-')}"],
                    ["public origin", origin.get("classification", "-")],
                    ["iPhone USB", iphone.get("classification", "-")],
                ],
            ),
            "",
            "## Unblock Actions",
            "",
            markdown_table(
                ["priority", "gate", "status", "owner", "evidence", "next action", "success gate"],
                [
                    [
                        row["priority"],
                        row["gate_id"],
                        row["status"],
                        row["owner"],
                        row["evidence"],
                        row["next_action"],
                        row["success_gate"],
                    ]
                    for row in actions
                ],
            ),
            "",
            "## Execution Rule",
            "",
            "- Do not run the selected Chrome active public row until every P0 gate is `ready`.",
            "- After P0 is ready, refresh the public H3 baseline before appending new active rows.",
            "- Treat this dashboard as readiness evidence only, not as QUIC CM success evidence.",
            "",
            "## Claim Boundary",
            "",
            dashboard["claim_boundary"],
            "",
            "## Regenerate",
            "",
            f"`python3 tools/{Path(__file__).name}`",
            "",
        ]
    )


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
    parser.add_argument("--network-change-cmd", default=DEFAULT_NETWORK_CHANGE_CMD)
    parser.add_argument("--android-network-change-cmd", default="")
    parser.add_argument("--ssh-users", default="ec2-user,ubuntu")
    parser.add_argument("--timeout", type=float, default=4.0)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    parser.add_argument("--md-output", default=DEFAULT_MD_OUTPUT)
    args = parser.parse_args()

    dashboard = build_dashboard(args)
    write_outputs(dashboard, json_output=args.json_output, csv_output=args.csv_output, md_output=args.md_output)
    return 0 if not dashboard["p0_blockers"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
