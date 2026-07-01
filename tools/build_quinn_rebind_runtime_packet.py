#!/usr/bin/env python3
"""Build a public-safe Quinn endpoint rebind runtime packet."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_QUINN_DIR = "/private/tmp/quic-cm-scan-repos/quinn"
DEFAULT_RUNNER = "harness/scripts/run-quinn-rebind-runtime-demo.sh"
DEFAULT_RUNNER_RESULT_ENV = "harness/results/quinn-rebind-runtime-demo-local-20260701/results/result.env"
DEFAULT_OUTPUT = "docs/results/quinn-rebind-runtime-packet-20260701.md"
DEFAULT_JSON_OUTPUT = "data/quinn-rebind-runtime-packet-20260701.json"

QUINN_COMMIT = "953b466747e667a9dfda0596b8051a0644f8333d"
QUINN_BLOB = f"https://github.com/quinn-rs/quinn/blob/{QUINN_COMMIT}"
RESEARCH_REPO_BASE = "https://github.com/manNomi/quic-connect-migration/blob/docs/quinn-neqo-rerun-20260630"

FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


@dataclass(frozen=True)
class Evidence:
    id: str
    source: str
    line: int
    topic: str
    observation: str
    implication: str
    source_base: str = QUINN_BLOB

    @property
    def url(self) -> str:
        return f"{self.source_base}/{self.source}#L{self.line}"


EVIDENCE = [
    Evidence(
        id="endpoint-rebind-api",
        source="quinn/src/endpoint.rs",
        line=269,
        topic="Endpoint rebind API",
        observation="Endpoint::rebind switches a Quinn endpoint to a new UDP socket.",
        implication="Quinn has a public runtime control surface for endpoint-wide local address changes.",
    ),
    Evidence(
        id="endpoint-rebind-scope",
        source="quinn/src/endpoint.rs",
        line=279,
        topic="Endpoint-wide rebind scope",
        observation="rebind_abstract updates the endpoint address live and affects all active connections.",
        implication="Quinn's active local-address control is endpoint-wide rather than per-connection AddPath/Probe/Switch.",
    ),
    Evidence(
        id="runtime-rebind-recv-test",
        source="quinn/src/tests.rs",
        line=692,
        topic="Runtime rebind stream test",
        observation="The rebind_recv Tokio test connects client/server endpoints, rebinds the client UDP socket, and reads a server unidirectional stream.",
        implication="A simple Quinn stream workload can complete after endpoint rebind in the upstream test.",
    ),
    Evidence(
        id="proto-migration-test",
        source="quinn-proto/src/tests/mod.rs",
        line=1351,
        topic="Protocol migration test",
        observation="The migration test changes the client address, sends data, and observes the server remote address update.",
        implication="Quinn has protocol-level migration/rebinding evidence beyond the endpoint runtime test.",
    ),
    Evidence(
        id="path-challenge-transmit",
        source="quinn-proto/src/connection/mod.rs",
        line=3268,
        topic="PATH_CHALLENGE evidence",
        observation="Outgoing packets on an unvalidated path include PATH_CHALLENGE and update frame statistics.",
        implication="Runtime claims can be tied to path-validation frame evidence rather than only test exit code.",
    ),
    Evidence(
        id="path-response-transmit",
        source="quinn-proto/src/connection/mod.rs",
        line=3283,
        topic="PATH_RESPONSE evidence",
        observation="Queued path responses are emitted and counted in frame statistics.",
        implication="Quinn implements responder-side path-validation traffic.",
    ),
    Evidence(
        id="local-rerun-summary",
        source="docs/results/implementation-rerun-results-20260630.md",
        line=337,
        topic="Fresh local rerun",
        observation="The study records cargo test -p quinn-proto migration and cargo test -p quinn rebind as passing at the audited commit.",
        implication="The runtime packet deepens an existing Quinn row with a dedicated fail-closed artifact.",
        source_base=RESEARCH_REPO_BASE,
    ),
]


def run(args: list[str], timeout: int = 10) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def local_clone_state(path: Path) -> dict[str, str | bool]:
    if not path.exists():
        return {
            "observed": False,
            "commit": "",
            "matches_expected_commit": "no",
            "remote": "",
        }
    commit = run(["git", "-C", path.as_posix(), "rev-parse", "HEAD"]).stdout.strip()
    remote = run(["git", "-C", path.as_posix(), "remote", "get-url", "origin"]).stdout.strip()
    return {
        "observed": True,
        "commit": commit,
        "matches_expected_commit": "yes" if commit == QUINN_COMMIT else "no",
        "remote": remote,
    }


def parse_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def classify_runtime(runner_env: dict[str, str]) -> tuple[str, str]:
    if not runner_env:
        return "ready_not_run", "runner_result_env_missing"
    validation = runner_env.get("validation", "unknown")
    reason = runner_env.get("blocked_or_failed_reason", "unknown")
    if validation == "ok":
        return "ready_or_passed", "runner_validation_ok"
    if validation in {"blocked", "failed"}:
        return validation, reason
    return "unknown", reason


def build_claim_boundary(runner_env: dict[str, str]) -> dict[str, str]:
    if runner_env.get("validation") == "ok":
        return {
            "safe_claim": "Quinn has source/API evidence plus a local endpoint-rebind runtime PASS: the rebind_recv test passed, connected/got-conn/rebound logs appeared, the proto migration test passed, migration was initiated, PATH_CHALLENGE/PATH_RESPONSE counters were nonzero, and the new path was validated.",
            "unsafe_claim": "Quinn browser handover, HTTP/3 application continuity, managed deployment continuity, or quic-go-equivalent per-connection AddPath/Probe/Switch control.",
            "next_gap": "Use this as a Rust-stack endpoint-rebind runtime positive control; only build a custom Quinn HTTP/3 workload if reviewers require application-layer Rust evidence.",
        }
    return {
        "safe_claim": "Quinn has source/API evidence and a fail-closed endpoint-rebind runtime runner, but runtime PASS is not claimed until the runner records validation=ok.",
        "unsafe_claim": "Quinn endpoint-rebind workload continuity, browser handover, HTTP/3 application continuity, or managed deployment continuity.",
        "next_gap": "Run harness/scripts/run-quinn-rebind-runtime-demo.sh with REQUIRE_READY=1 and require rebind_recv plus proto path-validation evidence.",
    }


def build_packet(quinn_dir: Path, runner: Path, runner_result_env: Path) -> dict[str, Any]:
    runner_env = parse_env(runner_result_env)
    runtime_status, runtime_reason = classify_runtime(runner_env)
    packet = {
        "generated": utc_date_iso(),
        "public_safe": True,
        "implementation": "Quinn",
        "source_commit": QUINN_COMMIT,
        "local_clone": local_clone_state(quinn_dir),
        "runner": {
            "path": runner.as_posix(),
            "exists": runner.exists(),
            "result_env": runner_result_env.as_posix(),
            "result_env_exists": runner_result_env.exists(),
            "result_env_values": runner_env,
        },
        "runtime_trial": {
            "status": runtime_status,
            "reason": runtime_reason,
            "can_claim_runtime_pass": "yes" if runner_env.get("validation") == "ok" else "no",
            "can_claim_browser_or_deployment": "no",
        },
        "claim_boundary": build_claim_boundary(runner_env),
        "evidence": [asdict(item) | {"url": item.url} for item in EVIDENCE],
    }
    text = json.dumps(packet, ensure_ascii=False)
    packet["public_safety_scan_ok"] = not any(token in text for token in FORBIDDEN_PUBLIC_TEXT)
    return packet


def emit_markdown(packet: dict[str, Any]) -> str:
    runner_values = packet["runner"]["result_env_values"]
    if packet["runtime_trial"]["can_claim_runtime_pass"] == "yes":
        interpretation = [
            "1. Quinn should move above test-suite-only status because the dedicated runner records endpoint rebind, stream receive, protocol migration, and path-validation evidence.",
            "2. This strengthens the API-shape explanation: Quinn can preserve a simple stream workload through endpoint-wide rebind, but it is not a quic-go-style per-connection active path controller.",
            "3. Browser, HTTP/3 application, CDN/LB, and production continuity remain separate gates.",
        ]
    else:
        interpretation = [
            "1. Quinn remains strong Rust-stack source/test evidence, but this packet does not claim runtime PASS without validation=ok.",
            "2. The runner makes the next upgrade concrete: endpoint rebind test, proto migration test, path-validation counters, and stream receive logs must all appear.",
            "3. Browser, HTTP/3 application, CDN/LB, and production continuity remain separate gates.",
        ]
    lines = [
        "# Quinn Rebind Runtime Packet",
        "",
        f"Generated: `{packet['generated']}`",
        "",
        "This public-safe packet turns Quinn endpoint rebind into a reproducible runtime gate. It does not claim browser, HTTP/3 application, CDN/LB, or production deployment continuity.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| implementation | `{packet['implementation']}` |",
        f"| source commit | `{packet['source_commit']}` |",
        f"| local clone observed | `{packet['local_clone']['observed']}` |",
        f"| local clone commit | `{packet['local_clone']['commit'] or '-'}` |",
        f"| local clone matches audit commit | `{packet['local_clone']['matches_expected_commit']}` |",
        f"| runner exists | `{packet['runner']['exists']}` |",
        f"| runner result env exists | `{packet['runner']['result_env_exists']}` |",
        f"| runtime trial status | `{packet['runtime_trial']['status']}` |",
        f"| runtime trial reason | `{packet['runtime_trial']['reason']}` |",
        f"| can claim runtime PASS | `{packet['runtime_trial']['can_claim_runtime_pass']}` |",
        f"| public safety scan | `{'ok' if packet['public_safety_scan_ok'] else 'failed'}` |",
        "",
        "## Runner",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| path | `{packet['runner']['path']}` |",
        f"| result env | `{packet['runner']['result_env']}` |",
        f"| validation | `{runner_values.get('validation', '-')}` |",
        f"| blocked or failed reason | `{runner_values.get('blocked_or_failed_reason', '-')}` |",
        f"| rebind recv exit | `{runner_values.get('cargo_quinn_rebind_exit', '-')}` |",
        f"| proto migration exit | `{runner_values.get('cargo_quinn_proto_migration_exit', '-')}` |",
        f"| rebind recv ok count | `{runner_values.get('rebind_recv_ok_count', '-')}` |",
        f"| connected log count | `{runner_values.get('connected_log_count', '-')}` |",
        f"| got conn log count | `{runner_values.get('got_conn_log_count', '-')}` |",
        f"| rebound log count | `{runner_values.get('rebound_log_count', '-')}` |",
        f"| proto migration ok count | `{runner_values.get('proto_migration_ok_count', '-')}` |",
        f"| migration initiated count | `{runner_values.get('proto_migration_initiated_count', '-')}` |",
        f"| path challenge count | `{runner_values.get('path_challenge_count', '-')}` |",
        f"| path response count | `{runner_values.get('path_response_count', '-')}` |",
        f"| new path validated count | `{runner_values.get('new_path_validated_count', '-')}` |",
        "",
        "## Evidence Table",
        "",
        "| id | source | topic | observation | implication |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in packet["evidence"]:
        lines.append(
            f"| `{item['id']}` | [{item['source']}:{item['line']}]({item['url']}) | `{item['topic']}` | {item['observation']} | {item['implication']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Safe claim: {packet['claim_boundary']['safe_claim']}",
            f"- Unsafe claim: {packet['claim_boundary']['unsafe_claim']}",
            f"- Next gap: {packet['claim_boundary']['next_gap']}",
            "",
            "## Interpretation",
            "",
            *interpretation,
        ]
    )
    markdown = "\n".join(lines).rstrip() + "\n"
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        if forbidden in markdown:
            raise ValueError(f"public-safety token leaked: {forbidden}")
    return markdown


def write_outputs(output: Path, json_output: Path, packet: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(packet), encoding="utf-8")
    json_output.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quinn-dir", default=DEFAULT_QUINN_DIR)
    parser.add_argument("--runner", default=DEFAULT_RUNNER)
    parser.add_argument("--runner-result-env", default=DEFAULT_RUNNER_RESULT_ENV)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    packet = build_packet(
        Path(args.quinn_dir),
        Path(args.runner),
        Path(args.runner_result_env),
    )
    write_outputs(Path(args.output), Path(args.json_output), packet)
    print(f"wrote {args.output} and {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
