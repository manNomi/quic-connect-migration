#!/usr/bin/env python3
"""Build a public-safe audit of why non-quic-go checks have uneven depth."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_SURVEY = "data/implementation-survey.csv"
DEFAULT_AWS_RESULT_ENV = "data/aws-s2n-live-runner-safety-audit-20260701.json"
DEFAULT_OUTPUT = "docs/results/non-quicgo-execution-depth-audit-20260701.md"
DEFAULT_JSON_OUTPUT = "data/non-quicgo-execution-depth-audit-20260701.json"
DEFAULT_CSV_OUTPUT = "data/non-quicgo-execution-depth-audit-20260701.csv"


DEPTH_ORDER = [
    "local_test_suite_rerun",
    "local_runtime_or_app_demo",
    "focused_partial_runtime",
    "client_policy_source_plus_local_baseline",
    "source_test_map_only",
    "managed_or_external_deployment_gate",
    "negative_control_runtime",
]


DEPTH_BY_STATUS = {
    "fresh_rerun_20260630": "local_test_suite_rerun",
    "fresh_app_demo_20260630": "local_runtime_or_app_demo",
    "fresh_runtime_20260630": "local_runtime_or_app_demo",
    "fresh_rebind_demo_20260630": "focused_partial_runtime",
    "fresh_focused_e2e_20260630": "focused_partial_runtime",
    "source_and_local_browser_baseline": "client_policy_source_plus_local_baseline",
    "source_inspected": "source_test_map_only",
    "partial_deferred": "managed_or_external_deployment_gate",
    "fresh_negative_control_20260630": "negative_control_runtime",
}


WHY_NOT_QUIC_GO_DEPTH = {
    "Cloudflare quiche": "Local migration tests and sample evidence are strong, but the target question for Cloudflare's managed edge is a separate deployment-layer claim.",
    "AWS s2n-quic": "Library tests and the local AWS-NLB-compatible CID proof are positive, but live forwarding still depends on the AWS identity gate.",
    "ngtcp2": "The library exposes migration/path-validation primitives, but this study did not need a second quic-go-style custom AddPath/Probe/Switch positive control.",
    "LiteSpeed lsquic": "Runtime demos reached app-level evidence, but production-like OpenLiteSpeed deployment needs a Linux/EC2 follow-up.",
    "MsQuic": "Selected NAT rebinding and path-validation tests passed, and the focused API audit shows constrained local-address control plus a QUIC-aware LB boundary rather than quic-go-style AddPath/Probe/Switch control.",
    "Quinn": "Rust test evidence is useful for maturity comparison, but the active migration surface is less direct than quic-go's controlled API in this corpus.",
    "Neqo": "Mozilla-adjacent tests provide broad migration evidence, but this did not become a browser runtime proof without Firefox/Necko controlled handover rows.",
    "XQUIC": "The NAT rebinding demo passed, and a fail-closed Linux full-suite replay runner is now packaged; the current macOS build path still hits unrelated AppleClang Werror toolchain friction.",
    "Chromium Chrome Cronet": "Source policy hooks, tests, and NetLog exist, but actual browser handover behavior is runtime-policy dependent and must be proven with browser rows.",
    "AWS CloudFront": "CloudFront is a managed viewer-edge deployment; it cannot be treated as end-to-end origin Connection Migration without a separate edge experiment.",
    "AWS NLB plus s2n-quic": "The local custom CID provider proof exists, but live target forwarding and path-change continuity are blocked until AWS identity opens.",
    "mvfst": "Source/test coverage is strong and a focused Linux runner is now packaged, but local build/test execution is still gated by Buck/getdeps/disk/toolchain cost.",
    "picoquic": "The test suite is rich and positive, but it is used here as an edge-case maturity comparison rather than the primary browser/deployment harness.",
    "nginx QUIC": "The server runtime demo is positive, but nginx is server-side only; Linux quic_bpf and browser handover are separate deployment claims.",
    "quicly": "The focused path-migration e2e subtest passed, while the full e2e run still has unrelated host-specific failures.",
    "aioquic": "The Python implementation is a readable passive/path-validation reference, not the strongest active-migration API candidate.",
    "HAProxy QUIC": "This is intentionally a negative control showing that HTTP/3 proxy availability does not imply active Connection Migration support.",
}


NEXT_NON_IPHONE_GATE = {
    "Cloudflare quiche": "Keep as cross-implementation evidence; only promote Cloudflare managed edge after a separate public edge experiment.",
    "AWS s2n-quic": "Refresh AWS credentials, rerun the s2n NLB readiness gate, then run forwarding echo before any path-change variant.",
    "ngtcp2": "Optional: build a focused ngtcp2 HTTP/3 migration runner if a second C-library positive control becomes necessary.",
    "LiteSpeed lsquic": "Run the OpenLiteSpeed or LSQUIC production-like demo on Linux/EC2.",
    "MsQuic": "Optional: build a small MsQuic runtime harness that changes QUIC_PARAM_CONN_LOCAL_ADDRESS after handshake confirmation and verifies peer-address-change plus payload continuity.",
    "Quinn": "Optional: add a small Quinn HTTP/3 or echo migration harness if Rust-stack runtime depth becomes reviewer-critical.",
    "Neqo": "Optional: run Firefox/Necko-adjacent controlled rows or keep Neqo as implementation maturity evidence.",
    "XQUIC": "Run harness/scripts/run-xquic-full-suite-linux.sh on Linux and accept only validation=ok with zero failed unit/case markers.",
    "Chromium Chrome Cronet": "Run Android/Cronet or desktop Chrome active network-change rows when a non-iPhone secondary path is available.",
    "AWS CloudFront": "Design a viewer-edge continuity experiment and explicitly label it non-end-to-end.",
    "AWS NLB plus s2n-quic": "Use the packaged live runner after AWS identity is valid; start with forwarding echo.",
    "mvfst": "Run harness/scripts/run-mvfst-focused-migration-tests-linux.sh on a Linux builder with buck2 and enough disk; accept only validation=ok for all three focused targets.",
    "picoquic": "Use as edge-case appendix evidence; no immediate deeper run is required unless reviewers ask for another active API baseline.",
    "nginx QUIC": "Run the Linux quic_bpf runner on EC2 or another Linux host with the required privileges.",
    "quicly": "Rerun full e2e on a Linux/upstream-compatible timing environment.",
    "aioquic": "Keep as readable reference evidence unless a Python passive rebind demonstration is needed.",
    "HAProxy QUIC": "Keep version-scoped negative control paired with HTTP/3 proxy support evidence.",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


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


def read_aws_readiness(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    if path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        gate = data.get("summary", {}).get("current_gate", {})
        local_proof_status = gate.get("local_proof_status", "unknown")
        return {
            "aws_identity_ok": gate.get("aws_identity_ok", "unknown"),
            "aws_identity_classification": gate.get("aws_identity_classification", "unknown"),
            "local_proof_status": local_proof_status,
            "local_proof_echo_matches": gate.get(
                "local_proof_echo_matches",
                "yes_from_pass" if local_proof_status == "PASS" else "unknown",
            ),
            "s2n_live_nlb_runner_ready": gate.get("s2n_live_nlb_runner_ready", "unknown"),
            "can_run_live_s2n_nlb_now": gate.get("can_run_live_s2n_nlb_now", "unknown"),
            "blocked_reason": gate.get("blocked_reason", "unknown"),
        }
    return read_env(path)


def depth_class(row: dict[str, str]) -> str:
    status = row.get("evidence_status", "")
    if row.get("name") == "HAProxy QUIC":
        return "negative_control_runtime"
    return DEPTH_BY_STATUS.get(status, "source_test_map_only")


def evidence_strength(row: dict[str, str], depth: str) -> str:
    active = row.get("active_migration_api", "")
    passive = row.get("passive_migration", "")
    tests = row.get("tests", "")
    if depth == "local_test_suite_rerun" and tests == "yes":
        return "strong_implementation_or_runtime_evidence"
    if depth == "local_runtime_or_app_demo":
        return "strong_runtime_or_app_evidence"
    if depth == "focused_partial_runtime":
        return "focused_positive_but_not_full_stack"
    if depth == "client_policy_source_plus_local_baseline":
        return "policy_dependent_client_evidence"
    if depth == "managed_or_external_deployment_gate":
        return "deployment_gate_pending"
    if depth == "negative_control_runtime":
        return "negative_control"
    if active == "yes" and passive == "yes":
        return "source_level_active_and_passive_evidence"
    return "source_or_partial_evidence"


def build_audit(survey_path: Path, aws_result_env: Path) -> dict[str, Any]:
    rows = [row for row in read_csv(survey_path) if row.get("name") != "quic-go"]
    aws = read_aws_readiness(aws_result_env)
    implementations: list[dict[str, str]] = []

    for row in rows:
        name = row.get("name", "")
        depth = depth_class(row)
        record = {
            "priority": row.get("priority", ""),
            "name": name,
            "category": row.get("category", ""),
            "current_level": row.get("current_level", ""),
            "evidence_status": row.get("evidence_status", ""),
            "depth_class": depth,
            "evidence_strength": evidence_strength(row, depth),
            "active_migration_api": row.get("active_migration_api", ""),
            "passive_migration": row.get("passive_migration", ""),
            "tests": row.get("tests", ""),
            "why_not_quic_go_depth": WHY_NOT_QUIC_GO_DEPTH.get(
                name,
                "This stack contributes maturity evidence, but was not selected as the deepest controllable positive control.",
            ),
            "next_non_iphone_gate": NEXT_NON_IPHONE_GATE.get(name, row.get("next_action", "")),
        }
        implementations.append(record)

    depth_counts = Counter(row["depth_class"] for row in implementations)
    strength_counts = Counter(row["evidence_strength"] for row in implementations)
    remaining_deepening = [
        row["name"]
        for row in implementations
        if row["depth_class"]
        in {
            "focused_partial_runtime",
            "client_policy_source_plus_local_baseline",
            "source_test_map_only",
            "managed_or_external_deployment_gate",
        }
    ]

    aws_summary = {
        "input_path": aws_result_env.as_posix(),
        "input_exists": aws_result_env.exists(),
        "aws_identity_ok": aws.get("aws_identity_ok", "unknown"),
        "aws_identity_classification": aws.get("aws_identity_classification", "unknown"),
        "local_proof_status": aws.get("local_proof_status", "unknown"),
        "local_proof_echo_matches": aws.get("local_proof_echo_matches", "unknown"),
        "s2n_live_nlb_runner_ready": aws.get("s2n_live_nlb_runner_ready", "unknown"),
        "can_run_live_s2n_nlb_now": aws.get("can_run_live_s2n_nlb_now", "unknown"),
        "blocked_reason": aws.get("blocked_reason", "unknown"),
    }

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "source_path": survey_path.as_posix(),
        "aws_readiness": aws_summary,
        "summary": {
            "survey_rows_excluding_quic_go": len(implementations),
            "depth_counts": {key: depth_counts.get(key, 0) for key in DEPTH_ORDER},
            "evidence_strength_counts": dict(sorted(strength_counts.items())),
            "remaining_deepening_candidates": remaining_deepening,
            "remaining_deepening_count": len(remaining_deepening),
            "interpretation": "quic-go is the deepest controllable positive control, but non-quic-go evidence is broad enough to show that CM is implemented across multiple stacks at different depths.",
        },
        "implementations": implementations,
        "reporting_boundary": {
            "safe_claim": "The non-quic-go corpus contains implementation, runtime, source, readiness, and negative-control evidence with explicit depth limits.",
            "unsafe_claim": "The non-quic-go corpus proves equal active migration control, browser handover, or managed deployment continuity across all stacks.",
            "professor_answer": "quic-go was used for the deepest controlled migration run because it exposes the cleanest AddPath/Probe/Switch-style control path; other implementations were still verified, but many are better used as maturity, runtime, deployment-readiness, or negative-control evidence.",
        },
    }


def emit_markdown(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    aws = audit["aws_readiness"]
    lines = [
        "# Non-quic-go Execution Depth Audit",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This public-safe audit explains why quic-go has the deepest controlled run while other implementations are still useful evidence. It is generated from `data/implementation-survey.csv` plus the latest AWS s2n readiness artifact when present.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| survey rows excluding quic-go | `{summary['survey_rows_excluding_quic_go']}` |",
        f"| depth counts | `{summary['depth_counts']}` |",
        f"| evidence strength counts | `{summary['evidence_strength_counts']}` |",
        f"| remaining deepening candidates | `{summary['remaining_deepening_candidates']}` |",
        f"| interpretation | {summary['interpretation']} |",
        "",
        "## Current AWS Gate",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| input exists | `{aws['input_exists']}` |",
        f"| aws identity ok | `{aws['aws_identity_ok']}` |",
        f"| aws identity classification | `{aws['aws_identity_classification']}` |",
        f"| local s2n proof | `{aws['local_proof_status']}` |",
        f"| local proof echo matches | `{aws['local_proof_echo_matches']}` |",
        f"| s2n live runner ready | `{aws['s2n_live_nlb_runner_ready']}` |",
        f"| can run live s2n NLB now | `{aws['can_run_live_s2n_nlb_now']}` |",
        f"| blocked reason | `{aws['blocked_reason']}` |",
        "",
        "## Professor-facing Answer",
        "",
        audit["reporting_boundary"]["professor_answer"],
        "",
        "## Implementation Depth Table",
        "",
        "| priority | implementation | depth class | strength | level | active API | passive | tests | why not quic-go depth | next non-iPhone gate |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in audit["implementations"]:
        lines.append(
            "| {priority} | {name} | `{depth}` | `{strength}` | `{level}` | `{active}` | `{passive}` | `{tests}` | {why} | {next_gate} |".format(
                priority=row["priority"],
                name=row["name"],
                depth=row["depth_class"],
                strength=row["evidence_strength"],
                level=row["current_level"],
                active=row["active_migration_api"],
                passive=row["passive_migration"],
                tests=row["tests"],
                why=row["why_not_quic_go_depth"],
                next_gate=row["next_non_iphone_gate"],
            )
        )

    lines.extend(
        [
            "",
            "## Reporting Boundary",
            "",
            f"- Safe claim: {audit['reporting_boundary']['safe_claim']}",
            f"- Unsafe claim: {audit['reporting_boundary']['unsafe_claim']}",
            "",
            "## Interpretation",
            "",
            "1. The result is not `only quic-go has Connection Migration`; the result is `quic-go is the cleanest controllable positive control`.",
            "2. Library/test-suite positives should be used to reject an implementation-absence explanation.",
            "3. Browser, CDN, LB, and server production claims require their own runtime gates because they add policy, routing, observability, and deployment constraints.",
            "4. The next non-iPhone experimental upgrade is still AWS NLB+s2n forwarding echo once credentials are valid; until then, this audit prevents overclaiming.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(markdown_path: Path, json_path: Path, csv_path: Path, audit: dict[str, Any]) -> None:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(emit_markdown(audit), encoding="utf-8")
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fieldnames = [
        "priority",
        "name",
        "category",
        "current_level",
        "evidence_status",
        "depth_class",
        "evidence_strength",
        "active_migration_api",
        "passive_migration",
        "tests",
        "why_not_quic_go_depth",
        "next_non_iphone_gate",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(audit["implementations"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--survey", default=DEFAULT_SURVEY)
    parser.add_argument("--aws-result-env", default=DEFAULT_AWS_RESULT_ENV)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    args = parser.parse_args()

    audit = build_audit(Path(args.survey), Path(args.aws_result_env))
    write_outputs(Path(args.output), Path(args.json_output), Path(args.csv_output), audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
