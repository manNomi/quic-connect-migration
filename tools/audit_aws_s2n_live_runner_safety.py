#!/usr/bin/env python3
"""Audit the AWS NLB + s2n-quic live runner safety boundaries."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_RUNNER = "harness/scripts/run-aws-s2n-nlb-live-data-plane.sh"
DEFAULT_GATE_ENV = "harness/results/s2n-nlb-live-readiness-20260701-gate/results/result.env"
DEFAULT_OUTPUT = "docs/results/aws-s2n-live-runner-safety-audit-20260701.md"
DEFAULT_JSON_OUTPUT = "data/aws-s2n-live-runner-safety-audit-20260701.json"


@dataclass(frozen=True)
class TokenCheck:
    name: str
    token: str
    present: bool
    meaning: str


FAIL_CLOSED_TOKENS = [
    ("identity_checker", "tools/check_aws_identity_readiness.py", "AWS identity is checked before live resource creation."),
    ("identity_ok_gate", 'if [[ "$AWS_IDENTITY_OK" != "yes" ]]', "Invalid credentials stop the runner before AWS resources are created."),
    ("readiness_exit_gate", 'if [[ "$AWS_READINESS_EXIT" != "0" ]]', "Non-zero readiness checker exit is fail-closed."),
    ("blocked_result_writer", "write_blocked_result", "Blocked runs write a public-safe result artifact."),
    ("require_live_switch", 'REQUIRE_LIVE="${REQUIRE_LIVE:-0}"', "Operators can force blocked readiness to fail CI/local scripts when desired."),
]


RESOURCE_TOKENS = [
    ("key_pair", "aws ec2 import-key-pair", "Temporary SSH key pair for target bootstrap."),
    ("security_group", "aws ec2 create-security-group", "Temporary target security group."),
    ("target_instances", "aws ec2 run-instances", "Two temporary EC2 targets."),
    ("target_group", "aws elbv2 create-target-group", "Temporary QUIC target group."),
    ("load_balancer", "aws elbv2 create-load-balancer", "Temporary internet-facing NLB."),
    ("listener", "aws elbv2 create-listener", "Temporary QUIC listener."),
    ("target_registration", "aws elbv2 register-targets", "Target registration with QuicServerId."),
]


CLEANUP_TOKENS = [
    ("trap_cleanup", "trap cleanup EXIT", "Cleanup runs on normal exit and most shell errors."),
    ("collect_targets", "collect_all_targets", "Target artifacts are collected before teardown when possible."),
    ("delete_listener", "aws elbv2 delete-listener", "Listener teardown."),
    ("delete_load_balancer", "aws elbv2 delete-load-balancer", "NLB teardown."),
    ("wait_lb_deleted", "aws elbv2 wait load-balancers-deleted", "Waits until NLB deletion completes."),
    ("deregister_targets", "aws elbv2 deregister-targets", "Target deregistration."),
    ("delete_target_group", "aws elbv2 delete-target-group", "Target group teardown."),
    ("terminate_instances", "aws ec2 terminate-instances", "EC2 target termination."),
    ("wait_instances_terminated", "aws ec2 wait instance-terminated", "Waits until instances terminate."),
    ("delete_security_group", "aws ec2 delete-security-group", "Security group teardown."),
    ("delete_key_pair", "aws ec2 delete-key-pair", "AWS key pair teardown."),
    ("remove_local_key", 'rm -f "$KEY_PATH"', "Local private/public key cleanup."),
]


RISK_TOKENS = [
    ("keep_resources_override", "KEEP_AWS_RESOURCES", "If set, cleanup can be intentionally skipped for debugging."),
    ("client_public_cidr", "CLIENT_PUBLIC_CIDR", "SSH/UDP exposure is constrained to the operator public CIDR and VPC CIDR."),
    ("tag_run_id", "Key=RunId,Value=$RUN_ID", "Resources are tagged with RunId for cleanup/forensics."),
    ("claim_boundary", "s2n_nlb_forwarding_echo_not_active_migration", "The live runner only claims forwarding echo, not active migration."),
]


def read_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def check_tokens(text: str, token_defs: list[tuple[str, str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "token": token,
            "present": token in text,
            "meaning": meaning,
        }
        for name, token, meaning in token_defs
    ]


def summarize_presence(rows: list[dict[str, Any]]) -> dict[str, Any]:
    missing = [row["name"] for row in rows if not row["present"]]
    return {
        "total": len(rows),
        "present": len(rows) - len(missing),
        "missing": missing,
        "ok": not missing,
    }


def build_audit(runner_path: Path, gate_env_path: Path) -> dict[str, Any]:
    text = runner_path.read_text(encoding="utf-8", errors="ignore") if runner_path.exists() else ""
    gate = read_env(gate_env_path)
    fail_closed = check_tokens(text, FAIL_CLOSED_TOKENS)
    resources = check_tokens(text, RESOURCE_TOKENS)
    cleanup = check_tokens(text, CLEANUP_TOKENS)
    risks = check_tokens(text, RISK_TOKENS)

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "source_paths": {
            "runner": runner_path.as_posix(),
            "gate_env": gate_env_path.as_posix(),
        },
        "source_exists": {
            "runner": runner_path.exists(),
            "gate_env": gate_env_path.exists(),
        },
        "summary": {
            "fail_closed_ok": summarize_presence(fail_closed)["ok"],
            "resource_inventory_ok": summarize_presence(resources)["ok"],
            "cleanup_coverage_ok": summarize_presence(cleanup)["ok"],
            "risk_boundary_ok": summarize_presence(risks)["ok"],
            "estimated_live_resources": {
                "ec2_instances": 2,
                "network_load_balancers": 1,
                "target_groups": 1,
                "listeners": 1,
                "security_groups": 1,
                "key_pairs": 1,
            },
            "current_gate": {
                "aws_identity_ok": gate.get("aws_identity_ok", "unknown"),
                "aws_identity_classification": gate.get("aws_identity_classification", "unknown"),
                "can_run_live_s2n_nlb_now": gate.get("can_run_live_s2n_nlb_now", "unknown"),
                "blocked_reason": gate.get("blocked_reason", "unknown"),
                "local_proof_status": gate.get("local_proof_status", "unknown"),
                "s2n_live_nlb_runner_ready": gate.get("s2n_live_nlb_runner_ready", "unknown"),
            },
            "audit_decision": "Do not run live AWS resources until aws_identity_ok=yes; when opened, run forwarding echo first and keep active migration as phase 2.",
        },
        "checks": {
            "fail_closed": fail_closed,
            "resources": resources,
            "cleanup": cleanup,
            "risk_boundaries": risks,
        },
        "claim_boundary": {
            "safe_claim": "The live runner has explicit pre-resource AWS identity gating, an inventoried temporary resource set, and cleanup coverage for listener, NLB, target group, instances, security group, key pair, and local key material.",
            "unsafe_claim": "This safety audit proves live AWS forwarding, active Connection Migration, absence of cloud cost, or cleanup success under all possible process-kill/cloud-failure modes.",
            "next_step": "After credential refresh, run the live forwarding echo with default cleanup, then inspect result.env and summary.json before designing any active path-change variant.",
        },
    }


def emit_markdown(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    lines = [
        "# AWS s2n Live Runner Safety Audit",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This public-safe audit statically checks the AWS NLB + s2n-quic live runner before live resource creation. It does not include credentials, account IDs, hostnames, IP addresses, key material, qlogs, keylogs, pcaps, or NetLogs.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| fail-closed gate ok | `{str(summary['fail_closed_ok']).lower()}` |",
        f"| resource inventory ok | `{str(summary['resource_inventory_ok']).lower()}` |",
        f"| cleanup coverage ok | `{str(summary['cleanup_coverage_ok']).lower()}` |",
        f"| risk boundary ok | `{str(summary['risk_boundary_ok']).lower()}` |",
        f"| estimated live resources | `{summary['estimated_live_resources']}` |",
        f"| current gate | `{summary['current_gate']}` |",
        f"| audit decision | {summary['audit_decision']} |",
        "",
        "## Claim Boundary",
        "",
        f"- Safe claim: {audit['claim_boundary']['safe_claim']}",
        f"- Unsafe claim: {audit['claim_boundary']['unsafe_claim']}",
        f"- Next step: {audit['claim_boundary']['next_step']}",
        "",
    ]
    for group, title in [
        ("fail_closed", "Fail-closed Checks"),
        ("resources", "Temporary Resource Inventory"),
        ("cleanup", "Cleanup Coverage"),
        ("risk_boundaries", "Risk Boundaries"),
    ]:
        lines.extend(
            [
                f"## {title}",
                "",
                "| check | present | meaning |",
                "| --- | --- | --- |",
            ]
        )
        for row in audit["checks"][group]:
            lines.append(f"| `{row['name']}` | `{str(row['present']).lower()}` | {row['meaning']} |")
        lines.append("")
    lines.extend(
        [
            "## Interpretation",
            "",
            "1. This audit lowers execution risk but is not live AWS evidence.",
            "2. The current gate remains closed when `aws_identity_ok` is not `yes`.",
            "3. The first live run should prove only s2n target forwarding through AWS NLB.",
            "4. Active source/path migration for s2n remains a later design phase because the public application API does not expose a quic-go-like AddPath/Probe/Switch trigger.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(output: Path, json_output: Path, audit: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(audit), encoding="utf-8")
    json_output.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner", default=DEFAULT_RUNNER)
    parser.add_argument("--gate-env", default=DEFAULT_GATE_ENV)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    audit = build_audit(Path(args.runner), Path(args.gate_env))
    write_outputs(Path(args.output), Path(args.json_output), audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
