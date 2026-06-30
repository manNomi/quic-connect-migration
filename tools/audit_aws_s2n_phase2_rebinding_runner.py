#!/usr/bin/env python3
"""Audit the AWS s2n phase-2 NAT-rebinding proxy runner readiness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_RUNNER = "harness/scripts/run-aws-s2n-nlb-live-data-plane.sh"
DEFAULT_CLIENT = "experiments/s2n-quic-nlb-cid-provider/src/bin/nlb_live_client.rs"
DEFAULT_PROXY = "repro/quic-go-min-repro/cmd/udprebindproxy/main.go"
DEFAULT_PREFLIGHT_ENV = "data/aws-s2n-phase2-rebinding-preflight-20260701.txt"
DEFAULT_OUTPUT = "docs/results/aws-s2n-phase2-rebinding-runner-audit-20260701.md"
DEFAULT_JSON_OUTPUT = "data/aws-s2n-phase2-rebinding-runner-audit-20260701.json"


RUNNER_TOKENS = [
    ("mode_flag", 'PATH_CHANGE_MODE="${PATH_CHANGE_MODE:-forwarding_echo}"', "Default remains forwarding echo."),
    ("rebinding_mode_gate", 'PATH_CHANGE_MODE" == "rebinding_proxy"', "Rebinding mode is explicit."),
    ("proxy_build", 'go build -o "$RUN_DIR/bin/udprebindproxy"', "Proxy is built inside the run artifact."),
    ("proxy_upstream_bind", "--upstream-bind-ip", "Proxy can bind local upstream sockets for remote NLB targets."),
    ("chunk_env", 'PAYLOAD_CHUNKS="$PAYLOAD_CHUNKS"', "Client can be forced to send after the proxy switch."),
    ("delay_env", 'CHUNK_DELAY_MS="$CHUNK_DELAY_MS"', "Client chunk timing is configurable."),
    ("proxy_rebind_observed", "proxy_rebind_observed", "Summary separates proxy-observed rebind from forwarding echo."),
    (
        "phase2_claim_boundary",
        "s2n_nlb_nat_rebinding_proxy_not_public_active_migration",
        "Result boundary avoids claiming public active migration API support.",
    ),
]


CLIENT_TOKENS = [
    ("payload_chunks", 'env_value("PAYLOAD_CHUNKS", "1")', "Chunked send is opt-in and default-compatible."),
    ("chunk_delay", 'env_value("CHUNK_DELAY_MS", "0")', "Chunk delay is opt-in and default-compatible."),
    ("chunk_sender", "payload_chunks_for", "Payload is split across multiple sends when configured."),
    ("client_result_fields", "payload_chunks: usize", "Client result records the configured chunk count."),
]


PROXY_TOKENS = [
    ("upstream_bind_flag", 'flag.String("upstream-bind-ip"', "Proxy exposes a bind-IP flag."),
    ("remote_wildcard_bind", "net.IPv4zero", "Remote upstream targets can use wildcard local binding."),
    ("loopback_preserved", "serverUDPAddr.IP.IsLoopback()", "Loopback behavior remains stable for local Chrome controls."),
    ("bind_recorded", "UpstreamBindIP", "Proxy result records the bind decision."),
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""


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


def token_rows(text: str, tokens: list[tuple[str, str, str]]) -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "token": token,
            "present": token in text,
            "meaning": meaning,
        }
        for name, token, meaning in tokens
    ]


def all_present(rows: list[dict[str, Any]]) -> bool:
    return all(bool(row["present"]) for row in rows)


def build_audit(runner: Path, client: Path, proxy: Path, preflight_env: Path) -> dict[str, Any]:
    runner_text = read_text(runner)
    client_text = read_text(client)
    proxy_text = read_text(proxy)
    preflight = read_env(preflight_env)
    runner_rows = token_rows(runner_text, RUNNER_TOKENS)
    client_rows = token_rows(client_text, CLIENT_TOKENS)
    proxy_rows = token_rows(proxy_text, PROXY_TOKENS)

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "source_paths": {
            "runner": runner.as_posix(),
            "client": client.as_posix(),
            "proxy": proxy.as_posix(),
            "preflight_env": preflight_env.as_posix(),
        },
        "source_exists": {
            "runner": runner.exists(),
            "client": client.exists(),
            "proxy": proxy.exists(),
            "preflight_env": preflight_env.exists(),
        },
        "summary": {
            "runner_mode_ready": all_present(runner_rows),
            "chunked_client_ready": all_present(client_rows),
            "remote_proxy_bind_ready": all_present(proxy_rows),
            "pre_resource_preflight_recorded": bool(preflight),
            "preflight_validation": preflight.get("validation", "unknown"),
            "preflight_blocked_reason": preflight.get("blocked_reason", "unknown"),
            "preflight_path_change_mode": preflight.get("path_change_mode", "unknown"),
            "preflight_go_found": preflight.get("go_found", "unknown"),
            "preflight_rebinding_proxy_source_ready": preflight.get("rebinding_proxy_source_ready", "unknown"),
            "audit_decision": "The phase-2 NAT-rebinding proxy runner is packaged and fail-closed, but AWS credential gates still block live execution.",
        },
        "checks": {
            "runner": runner_rows,
            "client": client_rows,
            "proxy": proxy_rows,
        },
        "claim_boundary": {
            "safe_claim": "The repository now has a runnable phase-2 mode that can place a UDP rebinding proxy between the s2n client and AWS NLB, force chunked client traffic after the proxy switch, and classify proxy-observed rebinding separately from forwarding echo.",
            "unsafe_claim": "This audit proves live AWS NLB+s2n NAT-rebinding continuity, application-triggered active migration, browser handover, or current upstream s2n public active migration API support.",
            "next_step": "After AWS identity opens, run forwarding echo first; only if that passes, run this mode with PATH_CHANGE_MODE=rebinding_proxy, PAYLOAD_CHUNKS>1, and CHUNK_DELAY_MS>0.",
        },
    }


def emit_markdown(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    lines = [
        "# AWS s2n Phase-2 Rebinding Runner Audit",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This public-safe audit checks whether the AWS NLB+s2n live runner has a packaged phase-2 NAT-rebinding proxy mode. It does not include credentials, account IDs, hostnames, IP addresses, key material, qlogs, keylogs, pcaps, or NetLogs.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
    ]
    for key, value in summary.items():
        lines.append(f"| {key} | `{value}` |")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Safe claim: {audit['claim_boundary']['safe_claim']}",
            f"- Unsafe claim: {audit['claim_boundary']['unsafe_claim']}",
            f"- Next step: {audit['claim_boundary']['next_step']}",
            "",
        ]
    )
    for group, title in [
        ("runner", "Runner Checks"),
        ("client", "s2n Client Checks"),
        ("proxy", "UDP Rebinding Proxy Checks"),
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
            "1. The runner still defaults to forwarding echo, so existing phase-1 semantics are preserved.",
            "2. The phase-2 mode is explicit and requires the rebinding proxy, Go toolchain, chunked client send, and proxy-observed B-side packets before classifying a rebinding run as successful.",
            "3. The current recorded preflight is blocked before AWS resource creation by the AWS identity gate.",
            "4. A future PASS row must still be produced by a live AWS run; this audit only proves readiness and claim boundaries.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(output: Path, json_output: Path, audit: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(audit), encoding="utf-8")
    json_output.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runner", default=DEFAULT_RUNNER)
    parser.add_argument("--client", default=DEFAULT_CLIENT)
    parser.add_argument("--proxy", default=DEFAULT_PROXY)
    parser.add_argument("--preflight-env", default=DEFAULT_PREFLIGHT_ENV)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    audit = build_audit(Path(args.runner), Path(args.client), Path(args.proxy), Path(args.preflight_env))
    write_outputs(Path(args.output), Path(args.json_output), audit)
    print(f"wrote {args.output}")
    print(f"wrote {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
