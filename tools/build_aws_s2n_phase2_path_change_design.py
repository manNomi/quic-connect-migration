#!/usr/bin/env python3
"""Build the AWS NLB + s2n-quic phase-2 path-change experiment design."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_S2N_API_AUDIT = "data/s2n-active-migration-api-audit-20260630.json"
DEFAULT_SAFETY_AUDIT = "data/aws-s2n-live-runner-safety-audit-20260701.json"
DEFAULT_GATE_RERUN = "data/non-iphone-gate-rerun-20260701.json"
DEFAULT_OUTPUT = "docs/results/aws-s2n-phase2-path-change-design-20260701.md"
DEFAULT_JSON_OUTPUT = "data/aws-s2n-phase2-path-change-design-20260701.json"


@dataclass(frozen=True)
class DesignOption:
    id: str
    rank: int
    label: str
    design_type: str
    prerequisite: str
    mechanism: str
    evidence_required: tuple[str, ...]
    claim_if_success: str
    do_not_claim: str
    feasibility: str
    next_action: str


OPTIONS = [
    DesignOption(
        id="phase1_forwarding_echo_prerequisite",
        rank=0,
        label="Live forwarding echo prerequisite",
        design_type="prerequisite",
        prerequisite="AWS identity ok and live runner safety audit ok.",
        mechanism="Run the existing AWS NLB+s2n live runner without path-change injection.",
        evidence_required=(
            "validation=ok",
            "client_echo_matches=true",
            "server_success_count=1",
            "successful_target present",
            "cleanup_status recorded",
        ),
        claim_if_success="AWS NLB can forward a deterministic s2n-quic echo workload to exactly one CID-routed target in this setup.",
        do_not_claim="Active migration or path-change continuity.",
        feasibility="blocked_until_aws_identity_ok",
        next_action="Refresh AWS credentials, then run `harness/scripts/run-aws-s2n-nlb-live-data-plane.sh` with default cleanup.",
    ),
    DesignOption(
        id="phase2_nat_rebinding_proxy",
        rank=1,
        label="NAT-rebinding proxy path-change",
        design_type="preferred_phase2",
        prerequisite="Phase-1 forwarding echo passes; NLB endpoint, server IDs, and cleanup are validated.",
        mechanism="Insert a UDP rebinding proxy between the s2n client and the NLB endpoint so the server/NLB observes a source tuple change while the application workload continues.",
        evidence_required=(
            "client echo or stream continuity",
            "proxy upstream A/B packet counters",
            "server observed remote tuple count >= 2 or active-path update event",
            "same successful target before/after rebind",
            "PATH_CHALLENGE/PATH_RESPONSE or s2n active-path event when available",
            "CID Server ID remains routable",
        ),
        claim_if_success="AWS NLB+s2n can tolerate a controlled NAT-rebinding style path change for the tested echo/stream workload.",
        do_not_claim="Application-triggered active migration API support or browser handover.",
        feasibility="best_next_design_without_s2n_public_active_api",
        next_action="Run the packaged live-runner variant with PATH_CHANGE_MODE=rebinding_proxy after forwarding echo is stable, then inspect client/proxy/server evidence.",
    ),
    DesignOption(
        id="phase2_linux_network_namespace_rebind",
        rank=2,
        label="Linux namespace/SNAT client path-change",
        design_type="deployment_like_variant",
        prerequisite="Linux/EC2 client host with permission to create namespaces, veth, routes, or NAT rules.",
        mechanism="Run the s2n client on a Linux host and change the egress source tuple using namespace/routing/SNAT controls during a longer stream workload.",
        evidence_required=(
            "client path-change command log",
            "before/after local route or SNAT state",
            "server tuple change",
            "same target after path change",
            "workload completion",
            "s2n event/qlog evidence if enabled",
        ),
        claim_if_success="The AWS NLB+s2n setup survives a host-level Linux client path-change trigger under the tested conditions.",
        do_not_claim="Mobile Wi-Fi/cellular handover or public browser continuity.",
        feasibility="requires_linux_client_host",
        next_action="Use only after forwarding echo and proxy rebinding design are stable, or when a Linux EC2 client host is easier than local desktop path-change.",
    ),
    DesignOption(
        id="phase2_s2n_test_io_rebind",
        rank=3,
        label="s2n test-IO rebind adaptation",
        design_type="implementation_variant",
        prerequisite="Access to s2n-quic test IO hooks or a forked test harness.",
        mechanism="Adapt the s2n test-suite socket rebind mechanism into a controlled local or lab runner to reproduce the library's tested rebind path outside the public app API.",
        evidence_required=(
            "socket.rebind-style trigger",
            "ActivePathUpdated event",
            "workload completion",
            "negative-control blocked-port row",
        ),
        claim_if_success="s2n-quic's lower-level rebind machinery works in a reproduced lab harness.",
        do_not_claim="Public application API support, AWS NLB deployment success, or browser behavior.",
        feasibility="useful_but_lower_paper_value",
        next_action="Keep as fallback if AWS remains blocked and implementation-depth appendix becomes necessary.",
    ),
    DesignOption(
        id="phase2_public_api_wait_or_patch",
        rank=4,
        label="Wait for or patch public active API",
        design_type="long_term",
        prerequisite="Upstream public path migration provider or an explicit research fork.",
        mechanism="Expose a quic-go-like application trigger in s2n-quic, then perform AddPath/Probe/Switch-like migration through AWS NLB.",
        evidence_required=(
            "public API call trace",
            "path probe before switch",
            "validated new path",
            "payload continuity",
            "same target through NLB",
        ),
        claim_if_success="A modified or future s2n-quic API can perform application-triggered active migration through CID-aware NLB routing.",
        do_not_claim="Current upstream public API behavior.",
        feasibility="not_current_upstream",
        next_action="Do not block the paper on this; mention as future improvement direction unless a fork is approved.",
    ),
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_design(s2n_api_audit: Path, safety_audit: Path, gate_rerun: Path) -> dict[str, Any]:
    api = read_json(s2n_api_audit)
    safety = read_json(safety_audit)
    gate = read_json(gate_rerun)
    classification = api.get("classification", {})
    safety_summary = safety.get("summary", {})
    open_gates = gate.get("open_gates", [])

    public_active_api = bool(api.get("public_active_trigger_api_found", False))
    live_safety_ok = all(
        bool(safety_summary.get(key, False))
        for key in ("fail_closed_ok", "resource_inventory_ok", "cleanup_coverage_ok", "risk_boundary_ok")
    )
    aws_open = "aws-s2n-nlb-live-forwarding" in open_gates
    recommended = "phase1_forwarding_echo_prerequisite"
    if live_safety_ok and aws_open:
        recommended = "phase1_forwarding_echo_prerequisite"
    if live_safety_ok and not public_active_api:
        preferred_phase2 = "phase2_nat_rebinding_proxy"
    else:
        preferred_phase2 = "phase2_public_api_wait_or_patch"

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "source_paths": {
            "s2n_api_audit": s2n_api_audit.as_posix(),
            "safety_audit": safety_audit.as_posix(),
            "gate_rerun": gate_rerun.as_posix(),
        },
        "source_exists": {
            "s2n_api_audit": s2n_api_audit.exists(),
            "safety_audit": safety_audit.exists(),
            "gate_rerun": gate_rerun.exists(),
        },
        "summary": {
            "public_active_trigger_api_found": public_active_api,
            "migration_tests_present": bool(classification.get("migration_tests_present", False)),
            "active_path_events_present": bool(classification.get("active_path_events_present", False)),
            "path_migration_provider_public": bool(classification.get("path_migration_provider_public", False)),
            "live_runner_safety_ok": live_safety_ok,
            "aws_gate_open": aws_open,
            "current_open_gates": open_gates,
            "recommended_first_step": recommended,
            "preferred_phase2_design": preferred_phase2,
            "decision": "Run live forwarding echo first when AWS opens; because s2n lacks a current public AddPath/Probe/Switch API, use NAT-rebinding proxy as the preferred phase-2 path-change design.",
        },
        "options": [asdict(option) | {"evidence_required": list(option.evidence_required)} for option in OPTIONS],
        "claim_boundary": {
            "safe_claim": "The current design separates AWS forwarding, NAT-rebinding style path change, implementation-level test-IO rebind evidence, and future public active API work.",
            "unsafe_claim": "The current upstream s2n public API already supports application-triggered active migration through AWS NLB.",
            "paper_use": "Use this as the methods plan for the AWS follow-up, not as a result row.",
        },
    }


def emit_markdown(design: dict[str, Any]) -> str:
    summary = design["summary"]
    lines = [
        "# AWS s2n Phase-2 Path-Change Design",
        "",
        f"Generated: `{design['generated']}`",
        "",
        "This public-safe design fixes the next AWS NLB + s2n-quic experiment sequence after the live forwarding echo. It does not include credentials, account IDs, hostnames, IP addresses, key material, qlogs, keylogs, pcaps, or NetLogs.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| public active trigger API found | `{str(summary['public_active_trigger_api_found']).lower()}` |",
        f"| migration tests present | `{str(summary['migration_tests_present']).lower()}` |",
        f"| active path events present | `{str(summary['active_path_events_present']).lower()}` |",
        f"| path migration provider public | `{str(summary['path_migration_provider_public']).lower()}` |",
        f"| live runner safety ok | `{str(summary['live_runner_safety_ok']).lower()}` |",
        f"| AWS gate open | `{str(summary['aws_gate_open']).lower()}` |",
        f"| current open gates | `{summary['current_open_gates']}` |",
        f"| recommended first step | `{summary['recommended_first_step']}` |",
        f"| preferred phase-2 design | `{summary['preferred_phase2_design']}` |",
        f"| decision | {summary['decision']} |",
        "",
        "## Claim Boundary",
        "",
        f"- Safe claim: {design['claim_boundary']['safe_claim']}",
        f"- Unsafe claim: {design['claim_boundary']['unsafe_claim']}",
        f"- Paper use: {design['claim_boundary']['paper_use']}",
        "",
        "## Design Options",
        "",
        "| rank | id | label | type | prerequisite | mechanism | evidence required | claim if success | do not claim | feasibility | next action |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for option in design["options"]:
        evidence = "<br>".join(f"- {item}" for item in option["evidence_required"])
        lines.append(
            "| {rank} | `{id}` | {label} | `{design_type}` | {prerequisite} | {mechanism} | {evidence} | {claim_if_success} | {do_not_claim} | `{feasibility}` | {next_action} |".format(
                rank=option["rank"],
                id=option["id"],
                label=option["label"],
                design_type=option["design_type"],
                prerequisite=option["prerequisite"],
                mechanism=option["mechanism"],
                evidence=evidence,
                claim_if_success=option["claim_if_success"],
                do_not_claim=option["do_not_claim"],
                feasibility=option["feasibility"],
                next_action=option["next_action"],
            )
        )
    lines.extend(
        [
            "",
            "## Recommended Sequence",
            "",
            "1. Keep live AWS execution blocked until `aws_identity_ok=yes`.",
            "2. Run the existing live forwarding echo and inspect `validation=ok`, `client_echo_matches=true`, and `server_success_count=1`.",
            "3. Run the packaged NAT-rebinding proxy variant only after forwarding echo is stable.",
            "4. Treat proxy or namespace path-change evidence as passive/NAT-rebinding continuity unless a current public s2n active migration API is introduced.",
            "5. Keep a future public API/fork path as future work rather than the next paper-critical blocker.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(output: Path, json_output: Path, design: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(design), encoding="utf-8")
    json_output.write_text(json.dumps(design, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--s2n-api-audit", default=DEFAULT_S2N_API_AUDIT)
    parser.add_argument("--safety-audit", default=DEFAULT_SAFETY_AUDIT)
    parser.add_argument("--gate-rerun", default=DEFAULT_GATE_RERUN)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    design = build_design(Path(args.s2n_api_audit), Path(args.safety_audit), Path(args.gate_rerun))
    write_outputs(Path(args.output), Path(args.json_output), design)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
