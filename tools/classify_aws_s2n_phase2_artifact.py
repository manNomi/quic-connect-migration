#!/usr/bin/env python3
"""Classify AWS NLB + s2n-quic phase-1/phase-2 live artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_OUTPUT = "docs/results/aws-s2n-phase2-artifact-classifier-contract-20260701.md"
DEFAULT_JSON_OUTPUT = "data/aws-s2n-phase2-artifact-classifier-contract-20260701.json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_summary(artifact_dir: Path, summary_path: Path | None = None) -> Path:
    if summary_path:
        return summary_path
    candidate = artifact_dir / "results" / "summary.json"
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"missing summary.json under {artifact_dir}")


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"true", "yes", "1", "ok", "pass"}
    return bool(value)


def int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def gate(name: str, ok: bool, evidence: str, why: str) -> dict[str, Any]:
    return {"name": name, "ok": ok, "evidence": evidence, "why": why}


def classify_summary(summary: dict[str, Any]) -> dict[str, Any]:
    mode = str(summary.get("path_change_mode") or "forwarding_echo")
    proxy = summary.get("rebinding_proxy") if isinstance(summary.get("rebinding_proxy"), dict) else {}
    client_echo = bool_value(summary.get("client_echo_matches"))
    server_success_count = int_value(summary.get("server_success_count"))
    successful_target = str(summary.get("successful_target") or "")
    status = str(summary.get("status") or "")

    common_gates = [
        gate("summary_status_pass", status == "PASS", f"status={status or '-'}", "Runner summary must be PASS."),
        gate("client_echo_matches", client_echo, f"client_echo_matches={client_echo}", "Client must receive the deterministic echo."),
        gate(
            "single_successful_target",
            server_success_count == 1 and bool(successful_target),
            f"server_success_count={server_success_count}; successful_target={successful_target or '-'}",
            "Exactly one NLB target should complete the workload.",
        ),
    ]

    if mode == "forwarding_echo":
        ok = all(item["ok"] for item in common_gates)
        return {
            "generated": utc_date_iso(),
            "mode": mode,
            "classification": "phase1_forwarding_echo_positive" if ok else "phase1_forwarding_echo_not_positive",
            "accepted": ok,
            "claim_strength": "aws_s2n_forwarding_echo_only" if ok else "not_claimable",
            "safe_claim": "AWS NLB forwarded a deterministic s2n-quic echo workload to exactly one CID-routed target in this setup." if ok else "",
            "do_not_claim": "Do not claim NAT-rebinding continuity, application-triggered active migration, browser handover, or general AWS NLB behavior.",
            "gates": common_gates,
            "next_action": "If this passes, run PATH_CHANGE_MODE=rebinding_proxy with chunked client traffic.",
        }

    if mode != "rebinding_proxy":
        return {
            "generated": utc_date_iso(),
            "mode": mode,
            "classification": "unknown_path_change_mode",
            "accepted": False,
            "claim_strength": "not_claimable",
            "safe_claim": "",
            "do_not_claim": "Unknown mode cannot support paper claims.",
            "gates": common_gates + [gate("known_mode", False, f"path_change_mode={mode}", "Mode must be forwarding_echo or rebinding_proxy.")],
            "next_action": "Use PATH_CHANGE_MODE=forwarding_echo or PATH_CHANGE_MODE=rebinding_proxy.",
        }

    proxy_switched = bool_value(proxy.get("switched"))
    server_packets_a = int_value(proxy.get("server_packets_a"))
    server_packets_b = int_value(proxy.get("server_packets_b"))
    upstream_a = str(proxy.get("upstream_a_addr") or "")
    upstream_b = str(proxy.get("upstream_b_addr") or "")
    client_packets = int_value(proxy.get("client_packets"))
    payload_chunks = int_value(summary.get("client_payload_chunks"))
    chunk_delay_ms = int_value(summary.get("client_chunk_delay_ms"))
    proxy_rebind_observed = bool_value(summary.get("proxy_rebind_observed"))

    phase2_gates = common_gates + [
        gate(
            "proxy_rebind_observed",
            proxy_rebind_observed,
            f"proxy_rebind_observed={proxy_rebind_observed}",
            "Runner summary must record proxy-observed rebinding.",
        ),
        gate(
            "proxy_switched_to_b",
            proxy_switched,
            f"switched={proxy_switched}",
            "Proxy must switch client-to-server traffic to upstream socket B.",
        ),
        gate(
            "proxy_has_client_packets",
            client_packets > 0,
            f"client_packets={client_packets}",
            "Proxy must observe client packets.",
        ),
        gate(
            "proxy_has_a_and_b_server_packets",
            server_packets_a > 0 and server_packets_b > 0,
            f"server_packets_a={server_packets_a}; server_packets_b={server_packets_b}",
            "Server-to-client traffic should be observed on both upstream paths.",
        ),
        gate(
            "upstream_tuple_changed",
            bool(upstream_a and upstream_b and upstream_a != upstream_b),
            f"upstream_a={upstream_a or '-'}; upstream_b={upstream_b or '-'}",
            "Proxy upstream A and B must be distinct source tuples.",
        ),
        gate(
            "chunked_client_after_switch",
            payload_chunks > 1 and chunk_delay_ms > 0,
            f"client_payload_chunks={payload_chunks}; client_chunk_delay_ms={chunk_delay_ms}",
            "Client workload must be configured to keep traffic alive after the proxy switch.",
        ),
    ]
    ok = all(item["ok"] for item in phase2_gates)
    missing = [item["name"] for item in phase2_gates if not item["ok"]]
    return {
        "generated": utc_date_iso(),
        "mode": mode,
        "classification": "phase2_nat_rebinding_proxy_positive" if ok else "phase2_nat_rebinding_proxy_not_positive",
        "accepted": ok,
        "claim_strength": "aws_s2n_nat_rebinding_proxy_continuity" if ok else "not_claimable",
        "safe_claim": "AWS NLB+s2n tolerated a controlled NAT-rebinding-style path change for the tested echo/stream workload." if ok else "",
        "do_not_claim": "Do not claim public s2n application-triggered active migration API support, browser handover, mobile Wi-Fi/LTE handover, or general production guarantee.",
        "gates": phase2_gates,
        "missing_gates": missing,
        "next_action": "If accepted, archive sanitized client/proxy/server/result artifacts and keep the claim scoped to NAT-rebinding proxy continuity.",
    }


def contract() -> dict[str, Any]:
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "classifier": "tools/classify_aws_s2n_phase2_artifact.py",
        "summary_schema_source": "harness/scripts/run-aws-s2n-nlb-live-data-plane.sh",
        "phase1_required_gates": [
            "summary_status_pass",
            "client_echo_matches",
            "single_successful_target",
        ],
        "phase2_required_gates": [
            "summary_status_pass",
            "client_echo_matches",
            "single_successful_target",
            "proxy_rebind_observed",
            "proxy_switched_to_b",
            "proxy_has_client_packets",
            "proxy_has_a_and_b_server_packets",
            "upstream_tuple_changed",
            "chunked_client_after_switch",
        ],
        "safe_boundaries": {
            "phase1": "Forwarding echo only; not active migration.",
            "phase2": "Controlled NAT-rebinding proxy continuity only; not public s2n active migration API support.",
        },
        "paper_use": "Use this classifier before turning any future AWS live artifact into a paper result row.",
    }


def emit_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# AWS s2n Phase-2 Artifact Classifier Contract",
        "",
        f"Generated: `{result['generated']}`",
        "",
        "This public-safe document defines how future AWS NLB+s2n forwarding-echo and NAT-rebinding proxy artifacts must be classified before they are used in the paper.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| classifier | `{result['classifier']}` |",
        f"| summary schema source | `{result['summary_schema_source']}` |",
        f"| paper use | {result['paper_use']} |",
        "",
        "## Required Gates",
        "",
        "| phase | required gates | safe boundary |",
        "| --- | --- | --- |",
        f"| phase 1 forwarding echo | `{', '.join(result['phase1_required_gates'])}` | {result['safe_boundaries']['phase1']} |",
        f"| phase 2 NAT-rebinding proxy | `{', '.join(result['phase2_required_gates'])}` | {result['safe_boundaries']['phase2']} |",
        "",
        "## Interpretation",
        "",
        "1. A forwarding-echo PASS is only an AWS routing prerequisite.",
        "2. A phase-2 PASS requires client continuity, exactly one successful target, proxy-observed A/B tuples, B-side server packets, and chunked client traffic after switch.",
        "3. Even a phase-2 PASS must not be described as public s2n AddPath/Probe/Switch-style active migration.",
        "",
    ]
    return "\n".join(lines)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-dir")
    parser.add_argument("--summary")
    parser.add_argument("--contract", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--json-output")
    parser.add_argument("--require-accepted", action="store_true")
    args = parser.parse_args()

    if args.contract:
        result = contract()
        output = args.output or DEFAULT_OUTPUT
        json_output = args.json_output or DEFAULT_JSON_OUTPUT
        write_text(Path(output), emit_markdown(result))
        write_text(Path(json_output), json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print(f"wrote {output}")
        print(f"wrote {json_output}")
        return 0

    if not args.artifact_dir and not args.summary:
        print("expected --contract, --summary, or --artifact-dir", file=sys.stderr)
        return 2
    summary_path = find_summary(Path(args.artifact_dir or "."), Path(args.summary) if args.summary else None)
    result = classify_summary(read_json(summary_path))
    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else emit_classification_markdown(result, summary_path)
    if args.output:
        write_text(Path(args.output), text)
    else:
        print(text, end="")
    if args.require_accepted and not result["accepted"]:
        return 1
    return 0


def emit_classification_markdown(result: dict[str, Any], summary_path: Path) -> str:
    lines = [
        "# AWS s2n Phase-2 Artifact Classification",
        "",
        f"Generated: `{result['generated']}`",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| summary | `{summary_path.as_posix()}` |",
        f"| mode | `{result['mode']}` |",
        f"| classification | `{result['classification']}` |",
        f"| accepted | `{str(result['accepted']).lower()}` |",
        f"| claim strength | `{result['claim_strength']}` |",
        f"| safe claim | {result['safe_claim'] or '-'} |",
        f"| do not claim | {result['do_not_claim']} |",
        "",
        "## Gates",
        "",
        "| gate | ok | evidence | why |",
        "| --- | --- | --- | --- |",
    ]
    for item in result["gates"]:
        lines.append(f"| `{item['name']}` | `{str(item['ok']).lower()}` | `{item['evidence']}` | {item['why']} |")
    missing = result.get("missing_gates") or []
    lines.extend(["", f"Missing gates: `{', '.join(missing) if missing else '-'}`", ""])
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
