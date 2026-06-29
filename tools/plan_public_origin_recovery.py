#!/usr/bin/env python3
"""Plan the next public-origin recovery action for final browser CM trials."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from audit_final_browser_handover_trials import build_audit
from check_controlled_public_origin_access import build_report as build_origin_access_report
from check_final_browser_handover_readiness import baseline_ready, config_readiness
from check_public_origin_readiness import build_result as build_public_origin_readiness
from research_clock import utc_date_iso


DEFAULT_CONFIG = "harness/config/controlled-public-origin.env"
DEFAULT_REQUIRED_TRIALS = "data/final-browser-handover-required-trials.csv"
DEFAULT_EXPERIMENTS = "data/experiment-results.csv"
DEFAULT_OUTPUT = "docs/results/public-origin-recovery-plan-20260629.md"
DEFAULT_JSON_OUTPUT = "data/public-origin-recovery-plan-20260629.json"


@dataclass(frozen=True)
class RecoveryStep:
    step_id: str
    status: str
    reason: str
    next_command: str
    success_gate: str


def shell_block(command: str) -> str:
    return f"```bash\n{command.strip()}\n```"


def values_from_config(config_path: Path) -> dict[str, str]:
    _, values = config_readiness(config_path, {})
    return values


def public_origin_summary(values: dict[str, str], timeout: int) -> dict[str, Any]:
    url = values.get("PUBLIC_ORIGIN_NETWORK_CHANGE_URL") or values.get("PUBLIC_ORIGIN_URL", "")
    if not url:
        return {"attempted": False, "ok": False, "classification": "url_missing", "has_h3_alt_svc": False}
    try:
        result = build_public_origin_readiness(url, timeout)
    except Exception as exc:  # noqa: BLE001 - planner should preserve the diagnostic class.
        return {"attempted": True, "ok": False, "classification": f"exception:{type(exc).__name__}", "error_redacted": True}
    return {
        "attempted": True,
        "ok": result.ok,
        "classification": "ok" if result.ok else "not_ready",
        "tcp_tls_ok": result.tcp_tls_ok,
        "curl_https_ok": result.curl_https_ok,
        "has_h3_alt_svc": result.has_h3_alt_svc,
        "curl_exit": result.curl_exit,
        "final_status": result.final_status,
        "error_count": len(result.errors),
    }


def step_aws_credentials(origin_access: dict[str, Any]) -> RecoveryStep:
    aws = origin_access.get("aws", {})
    classification = aws.get("classification", "missing")
    if aws.get("identity_ok"):
        return RecoveryStep(
            "aws-credentials",
            "ready",
            "AWS identity is available for recovery/provisioning.",
            "bash harness/scripts/aws-preflight.sh",
            "aws-preflight prints preflight=ok",
        )
    return RecoveryStep(
        "aws-credentials",
        "blocked",
        f"AWS identity is not usable yet: {classification}.",
        "\n".join(
            [
                "python3 tools/import_aws_credentials_csv.py ~/Downloads/YOUR_AWS_CREDENTIALS.csv",
                "python3 tools/import_aws_credentials_csv.py ~/Downloads/YOUR_AWS_CREDENTIALS.csv \\",
                "  --profile default \\",
                "  --region ap-northeast-2 \\",
                "  --write \\",
                "  --validate",
                "bash harness/scripts/aws-preflight.sh",
            ]
        ),
        "tools/check_aws_identity_readiness.py reports identity ok",
    )


def step_origin_reachable(public_origin: dict[str, Any], origin_access: dict[str, Any]) -> RecoveryStep:
    tcp = origin_access.get("tcp", {}).get("classification", "missing")
    if public_origin.get("ok"):
        return RecoveryStep(
            "public-origin-reachable",
            "ready",
            "Public origin already passes TCP/TLS/Alt-Svc readiness.",
            "python3 tools/check_public_origin_readiness.py --url \"$PUBLIC_ORIGIN_URL\" --require-h3-alt-svc --redact-sensitive --format markdown",
            "public origin readiness ok=true",
        )
    if origin_access.get("recovery_paths", {}).get("remote_ssh_ready"):
        command = "\n".join(
            [
                "python3 tools/build_controlled_public_origin_deploy_packet.py \\",
                "  --build-package \\",
                "  --output docs/results/controlled-public-origin-deploy-packet-20260629.md",
                "open docs/results/controlled-public-origin-deploy-packet-20260629.md",
            ]
        )
        reason = "SSH access is available, so restart or redeploy the controlled H3 server on the origin host."
    elif origin_access.get("recovery_paths", {}).get("aws_identity_ready"):
        command = "\n".join(
            [
                "bash harness/scripts/aws-preflight.sh",
                "python3 tools/build_controlled_public_origin_deploy_packet.py \\",
                "  --build-package \\",
                "  --output docs/results/controlled-public-origin-deploy-packet-20260629.md",
                "open docs/results/controlled-public-origin-deploy-packet-20260629.md",
            ]
        )
        reason = "AWS identity is available, but the configured origin is not serving traffic."
    else:
        command = "\n".join(
            [
                "python3 tools/check_controlled_public_origin_access.py \\",
                "  --config harness/config/controlled-public-origin.env \\",
                "  --format markdown \\",
                "  --output docs/results/controlled-public-origin-access-check-rerun-20260629.md",
                "open docs/results/public-origin-recovery-queue-20260629.md",
            ]
        )
        reason = f"Public origin is not reachable yet; current TCP classification is {tcp} and no recovery path is ready."
    return RecoveryStep(
        "public-origin-reachable",
        "blocked",
        reason,
        command,
        "check_public_origin_readiness reports ok=true and has_h3_alt_svc=true",
    )


def step_fresh_baseline(baseline: dict[str, Any], public_origin: dict[str, Any]) -> RecoveryStep:
    if not public_origin.get("ok"):
        return RecoveryStep(
            "fresh-public-baseline",
            "waiting",
            "Baseline cannot be refreshed until the public origin is reachable.",
            "python3 tools/check_public_origin_readiness.py --url \"$PUBLIC_ORIGIN_URL\" --require-h3-alt-svc --redact-sensitive --format markdown",
            "public origin readiness ok=true",
        )
    if baseline.get("ready"):
        return RecoveryStep(
            "fresh-public-baseline",
            "ready-historical",
            "A controlled public baseline summary exists, but rerun it after origin recovery before active rows.",
            "bash harness/scripts/final-p0-baseline-preflight.sh && bash harness/scripts/final-p0-baseline-run.sh",
            "new controlled public Chrome application H3 baseline summary status PASS",
        )
    return RecoveryStep(
        "fresh-public-baseline",
        "blocked",
        "Controlled public baseline summary is missing or not PASS.",
        "bash harness/scripts/final-p0-baseline-preflight.sh && bash harness/scripts/final-p0-baseline-run.sh",
        "controlled public Chrome application H3 baseline summary status PASS",
    )


def step_active_trials(final_audit: dict[str, Any], public_origin: dict[str, Any]) -> RecoveryStep:
    if not public_origin.get("ok"):
        return RecoveryStep(
            "active-browser-trials",
            "waiting",
            "Do not run active browser rows while the origin is unreachable.",
            "python3 tools/plan_public_origin_recovery.py",
            "public origin and fresh baseline are ready",
        )
    if final_audit.get("complete"):
        return RecoveryStep(
            "active-browser-trials",
            "complete",
            "Final browser handover protocol requirements are complete.",
            "python3 tools/audit_final_browser_handover_trials.py --require-complete",
            "audit complete=true",
        )
    return RecoveryStep(
        "active-browser-trials",
        "next",
        "Final browser protocol is incomplete; run Chrome no-heartbeat active rows first.",
        "\n".join(
            [
                "ALLOW_LATENT_SECONDARY_PATH=1 \\",
                "CHROME_RUNNER=cdp \\",
                "NETWORK_CHANGE_READY_EXPR='Number(document.body.dataset.downlinkBytes || \"0\") > 0' \\",
                "NETWORK_CHANGE_AFTER_SECONDS=0 \\",
                "NETWORK_CHANGE_AFTER_SNAPSHOT_COUNT=4 \\",
                "NETWORK_CHANGE_AFTER_SNAPSHOT_INTERVAL_SECONDS=1 \\",
                "NETWORK_CHANGE_CMD=\"networksetup -setairportpower 'en0' off\" \\",
                "bash harness/scripts/final-chrome-network-change-run.sh",
            ]
        ),
        "artifact bundle validates and final trial audit count increases",
    )


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    config_path = Path(args.config)
    values = values_from_config(config_path)
    origin_access = build_origin_access_report(
        config_path,
        timeout=args.timeout,
        ssh_users=[user.strip() for user in args.ssh_users.split(",") if user.strip()],
        probe_network=not args.skip_network_probe,
        probe_ssh=not args.skip_ssh_probe,
        probe_aws=not args.skip_aws_probe,
    )
    public_origin = public_origin_summary(values, args.timeout) if not args.skip_public_origin_probe else {
        "attempted": False,
        "ok": False,
        "classification": "not_probed",
    }
    baseline = baseline_ready(values.get("CONTROLLED_PUBLIC_BASELINE_SUMMARY", ""))
    final_audit = build_audit(Path(args.required_trials), Path(args.experiments))
    steps = [
        step_aws_credentials(origin_access),
        step_origin_reachable(public_origin, origin_access),
        step_fresh_baseline(baseline, public_origin),
        step_active_trials(final_audit, public_origin),
    ]
    next_step = next((step for step in steps if step.status in {"blocked", "next", "waiting"}), steps[-1])
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "config": args.config,
        "public_origin": public_origin,
        "origin_access": origin_access,
        "baseline": baseline,
        "final_protocol": {
            "complete": final_audit.get("complete"),
            "complete_count": final_audit.get("complete_count"),
            "requirement_count": final_audit.get("requirement_count"),
            "blockers": final_audit.get("blockers"),
        },
        "steps": [asdict(step) for step in steps],
        "next_step": asdict(next_step),
        "claim_boundary": (
            "This planner selects recovery actions. It is not QUIC migration evidence; "
            "only final trial artifacts can support browser CM claims."
        ),
    }


def emit_markdown(plan: dict[str, Any]) -> str:
    next_step = plan["next_step"]
    origin = plan["origin_access"]
    public_origin = plan["public_origin"]
    final_protocol = plan["final_protocol"]
    lines = [
        "# Public Origin Recovery Plan",
        "",
        f"Generated: `{plan['generated']}`",
        "",
        "This report is public-safe. It does not print hostnames, IP addresses, AWS account IDs, SSH targets, TLS paths, private keys, or raw command output.",
        "",
        "## Current Gate Summary",
        "",
        "| gate | value |",
        "| --- | --- |",
        f"| DNS | `{origin.get('dns', {}).get('classification', '-')}` |",
        f"| TCP 443 | `{origin.get('tcp', {}).get('classification', '-')}` |",
        f"| public readiness | `{'ok' if public_origin.get('ok') else public_origin.get('classification', 'not_ready')}` |",
        f"| h3 Alt-Svc | `{'yes' if public_origin.get('has_h3_alt_svc') else 'no'}` |",
        f"| AWS identity | `{origin.get('aws', {}).get('classification', '-')}` |",
        f"| SSH recovery | `{'yes' if origin.get('recovery_paths', {}).get('remote_ssh_ready') else 'no'}` |",
        f"| any recovery path | `{'yes' if origin.get('recovery_paths', {}).get('any_recovery_path_ready') else 'no'}` |",
        f"| baseline ready | `{'yes' if plan.get('baseline', {}).get('ready') else 'no'}` |",
        f"| final protocol | `{final_protocol.get('complete_count')}/{final_protocol.get('requirement_count')}` |",
        "",
        "## Step Status",
        "",
        "| step | status | reason | success gate |",
        "| --- | --- | --- | --- |",
    ]
    for step in plan["steps"]:
        lines.append(
            "| {step_id} | `{status}` | {reason} | {success_gate} |".format(
                step_id=step["step_id"],
                status=step["status"],
                reason=str(step["reason"]).replace("|", "\\|"),
                success_gate=str(step["success_gate"]).replace("|", "\\|"),
            )
        )
    lines.extend(
        [
            "",
            "## Next Action",
            "",
            f"`{next_step['step_id']}`: {next_step['reason']}",
            "",
            shell_block(next_step["next_command"]),
            "",
            "## Final Protocol Blockers",
            "",
        ]
    )
    blockers = final_protocol.get("blockers") or ["-"]
    lines.extend(f"- {blocker}" for blocker in blockers)
    lines.extend(["", "## Claim Boundary", "", plan["claim_boundary"], ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--required-trials", default=DEFAULT_REQUIRED_TRIALS)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--ssh-users", default="ec2-user,ubuntu")
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--skip-network-probe", action="store_true")
    parser.add_argument("--skip-ssh-probe", action="store_true")
    parser.add_argument("--skip-aws-probe", action="store_true")
    parser.add_argument("--skip-public-origin-probe", action="store_true")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    plan = build_plan(args)
    if args.json_output:
        json_output = Path(args.json_output)
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    text = json.dumps(plan, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(plan)
    if args.output == "-":
        print(text, end="")
    else:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
