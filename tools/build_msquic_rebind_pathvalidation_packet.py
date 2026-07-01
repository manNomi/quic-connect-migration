#!/usr/bin/env python3
"""Build a public-safe MsQuic rebind/path-validation runtime packet."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_MSQUIC_DIR = "/private/tmp/quic-cm-scan-repos/msquic"
DEFAULT_RUNNER = "harness/scripts/run-msquic-rebind-pathvalidation-demo.sh"
DEFAULT_RUNNER_RESULT_ENV = "harness/results/msquic-rebind-pathvalidation-local-20260701/results/result.env"
DEFAULT_OUTPUT = "docs/results/msquic-rebind-pathvalidation-packet-20260701.md"
DEFAULT_JSON_OUTPUT = "data/msquic-rebind-pathvalidation-packet-20260701.json"

MSQUIC_COMMIT = "51d449b7d2deb553d6503591f72a8e62d1071054"
MSQUIC_BLOB = f"https://github.com/microsoft/msquic/blob/{MSQUIC_COMMIT}"

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
    source_base: str = MSQUIC_BLOB

    @property
    def url(self) -> str:
        return f"{self.source_base}/{self.source}#L{self.line}"


EVIDENCE = [
    Evidence(
        id="migration-setting",
        source="docs/Settings.md",
        line=55,
        topic="Client migration setting",
        observation="MsQuic documents MigrationEnabled as client migration support for IP address and tuple changes with a cooperative load balancer or no load balancer.",
        implication="MsQuic treats migration as a configurable deployment-sensitive feature rather than unconditional application continuity.",
    ),
    Evidence(
        id="local-address-param-doc",
        source="docs/Settings.md",
        line=183,
        topic="Local address control parameter",
        observation="QUIC_PARAM_CONN_LOCAL_ADDRESS is settable on clients before start or after handshake confirmation.",
        implication="MsQuic exposes policy-constrained local-address control, unlike quic-go's AddPath/Probe/Switch shape.",
    ),
    Evidence(
        id="client-migration-deployment-doc",
        source="docs/Deployment.md",
        line=107,
        topic="Deployment boundary",
        observation="The deployment guide separates client migration from load-balancer routing requirements.",
        implication="A selected local MsQuic rebind PASS must not be promoted to generic LB/CDN deployment success.",
    ),
    Evidence(
        id="rebind-port-gtest",
        source="src/test/bin/quic_gtest.cpp",
        line=1868,
        topic="NAT port rebind test registration",
        observation="The RebindPort gtest invokes QuicTestNatPortRebind_NoPadding for user-mode tests.",
        implication="The local runner exercises MsQuic's selected NAT port rebinding test path.",
    ),
    Evidence(
        id="rebind-addr-gtest",
        source="src/test/bin/quic_gtest.cpp",
        line=1924,
        topic="NAT address rebind test registration",
        observation="The RebindAddr gtest invokes QuicTestNatAddrRebind_NoPadding for user-mode tests.",
        implication="The local runner exercises MsQuic's selected NAT address rebinding test path.",
    ),
    Evidence(
        id="path-validation-gtests",
        source="src/test/bin/quic_gtest.cpp",
        line=1973,
        topic="Path validation selected tests",
        observation="PathValidationTimeout and PathValidationLastPathClose are registered as WithFamilyArgs tests.",
        implication="The selected runner ties NAT rebinding evidence to path-validation failure handling.",
    ),
    Evidence(
        id="test-local-address-helper",
        source="src/test/lib/TestConnection.cpp",
        line=363,
        topic="Test local-address helper",
        observation="TestConnection::SetLocalAddr sets QUIC_PARAM_CONN_LOCAL_ADDRESS with retry handling after handshake confirmation.",
        implication="The tests use the documented local-address control surface rather than only parser-level checks.",
    ),
    Evidence(
        id="core-local-address-param",
        source="src/core/connection.c",
        line=6380,
        topic="Core local-address parameter handling",
        observation="The core connection parameter handler validates QUIC_PARAM_CONN_LOCAL_ADDRESS and rejects invalid states such as server-side use or pre-confirmation changes.",
        implication="MsQuic local-address control is real but policy-constrained.",
    ),
    Evidence(
        id="disable-active-migration-transport-param",
        source="src/core/connection.c",
        line=2412,
        topic="Disable active migration transport parameter",
        observation="Server transport parameters include disable_active_migration when MigrationEnabled is false.",
        implication="MsQuic migration behavior is explicitly controlled by policy and settings.",
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
        "matches_expected_commit": "yes" if commit == MSQUIC_COMMIT else "no",
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


def sanitize_runner_env(values: dict[str, str]) -> dict[str, str]:
    public_values = dict(values)
    run_id = public_values.get("run_id", "")
    if run_id:
        public_values["artifact_dir"] = f"harness/results/{run_id}"
    elif "artifact_dir" in public_values:
        public_values["artifact_dir"] = "harness/results/<run-id>"
    return public_values


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
            "safe_claim": "MsQuic has source/API evidence plus a local user-mode selected rebind/path-validation PASS: v4 and v6 RebindPort, RebindAddr, PathValidationTimeout, and PathValidationLastPathClose all passed under msquictest.",
            "unsafe_claim": "MsQuic browser handover, HTTP/3 application continuity, AWS NLB/CloudFront deployment success, or quic-go-equivalent AddPath/Probe/Switch control.",
            "next_gap": "Use this as selected MsQuic runtime-test evidence; build a separate application payload or live LB experiment only if reviewers require deployment/application continuity evidence.",
        }
    return {
        "safe_claim": "MsQuic has source/API evidence and a fail-closed selected rebind/path-validation runner, but runtime-test PASS is not claimed until the runner records validation=ok.",
        "unsafe_claim": "MsQuic selected rebind/path-validation success, browser handover, HTTP/3 application continuity, or managed deployment continuity.",
        "next_gap": "Run harness/scripts/run-msquic-rebind-pathvalidation-demo.sh with REQUIRE_READY=1 and require all eight selected v4/v6 tests to pass.",
    }


def build_packet(msquic_dir: Path, runner: Path, runner_result_env: Path) -> dict[str, Any]:
    runner_env = sanitize_runner_env(parse_env(runner_result_env))
    runtime_status, runtime_reason = classify_runtime(runner_env)
    packet = {
        "generated": utc_date_iso(),
        "public_safe": True,
        "implementation": "MsQuic",
        "source_commit": MSQUIC_COMMIT,
        "local_clone": local_clone_state(msquic_dir),
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
            "1. MsQuic should move above generic test-suite-only wording for the selected rebind/path-validation subset because the dedicated runner records v4 and v6 user-mode test PASS.",
            "2. This strengthens the API-shape explanation: MsQuic exposes a policy-constrained local-address parameter and deployment migration setting, not a quic-go-style AddPath/Probe/Switch controller.",
            "3. Browser, HTTP/3 application, CDN/LB, and production continuity remain separate gates.",
        ]
    else:
        interpretation = [
            "1. MsQuic remains strong source/test evidence, but this packet does not claim selected runtime-test PASS without validation=ok.",
            "2. The runner makes the next upgrade concrete: RebindPort, RebindAddr, PathValidationTimeout, and PathValidationLastPathClose must pass for both v4 and v6.",
            "3. Browser, HTTP/3 application, CDN/LB, and production continuity remain separate gates.",
        ]
    lines = [
        "# MsQuic Rebind Path Validation Packet",
        "",
        f"Generated: `{packet['generated']}`",
        "",
        "This public-safe packet turns MsQuic selected user-mode rebind/path-validation tests into a reproducible gate. It does not claim browser, HTTP/3 application, CDN/LB, or production deployment continuity.",
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
        f"| can claim selected runtime-test PASS | `{packet['runtime_trial']['can_claim_runtime_pass']}` |",
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
        f"| msquictest list exit | `{runner_values.get('msquictest_list_exit', '-')}` |",
        f"| msquictest v4 exit | `{runner_values.get('msquictest_v4_exit', '-')}` |",
        f"| msquictest v6 exit | `{runner_values.get('msquictest_v6_exit', '-')}` |",
        f"| listed rebind/path-validation count | `{runner_values.get('listed_rebind_pathvalidation_count', '-')}` |",
        f"| v4 ok count | `{runner_values.get('v4_ok_count', '-')}` |",
        f"| v6 ok count | `{runner_values.get('v6_ok_count', '-')}` |",
        f"| total ok count | `{runner_values.get('total_ok_count', '-')}` |",
        f"| passed summary count | `{runner_values.get('passed_summary_count', '-')}` |",
        f"| failed marker count | `{runner_values.get('failed_marker_count', '-')}` |",
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
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(output: Path, json_output: Path, packet: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(packet), encoding="utf-8")
    json_output.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--msquic-dir", default=DEFAULT_MSQUIC_DIR)
    parser.add_argument("--runner", default=DEFAULT_RUNNER)
    parser.add_argument("--runner-result-env", default=DEFAULT_RUNNER_RESULT_ENV)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    packet = build_packet(
        msquic_dir=Path(args.msquic_dir),
        runner=Path(args.runner),
        runner_result_env=Path(args.runner_result_env),
    )
    write_outputs(Path(args.output), Path(args.json_output), packet)
    print(f"wrote {args.output} and {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
