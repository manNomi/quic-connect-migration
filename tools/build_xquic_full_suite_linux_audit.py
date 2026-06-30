#!/usr/bin/env python3
"""Build a public-safe XQUIC full-suite Linux replay audit."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_XQUIC_DIR = "/private/tmp/quic-cm-scan-repos/xquic"
DEFAULT_NAT_RESULT_ENV = "harness/results/impl-rerun-20260630T070249Z/xquic-nat-rebinding/results.env"
DEFAULT_MACOS_BUILD_LOG = "harness/results/impl-rerun-20260630T070249Z/logs/xquic-build-tests.log"
DEFAULT_RUNNER = "harness/scripts/run-xquic-full-suite-linux.sh"
DEFAULT_OUTPUT = "docs/results/xquic-full-suite-linux-audit-20260701.md"
DEFAULT_JSON_OUTPUT = "data/xquic-full-suite-linux-audit-20260701.json"

XQUIC_COMMIT = "96155cffbde7f062fe45ac3f6899f47e25709d30"
XQUIC_BLOB = f"https://github.com/alibaba/xquic/blob/{XQUIC_COMMIT}"


@dataclass(frozen=True)
class Evidence:
    id: str
    file: str
    lines: str
    topic: str
    observation: str
    implication: str

    @property
    def url(self) -> str:
        start = self.lines.split("-")[0]
        return f"{XQUIC_BLOB}/{self.file}#L{start}"


EVIDENCE = [
    Evidence(
        id="official-requirements",
        file="README.md",
        lines="71-79",
        topic="Build and test dependencies",
        observation="The README lists CMake plus BoringSSL or BabaSSL for builds, and libevent plus CUnit for test cases.",
        implication="The full-suite replay must be treated as a Linux/toolchain gate, not merely a source scan.",
    ),
    Evidence(
        id="official-boringssl-quickstart",
        file="README.md",
        lines="85-118",
        topic="BoringSSL build path",
        observation="The README gives a BoringSSL build and XQUIC Debug/testing CMake path.",
        implication="The runner follows the documented BoringSSL route while keeping output public-safe.",
    ),
    Evidence(
        id="official-testcase-entrypoint",
        file="README.md",
        lines="153-157",
        topic="Testcase entrypoint",
        observation="The README documents running testcases through scripts/xquic_test.sh.",
        implication="A Linux replay packet should cover both unit tests and case tests when host prerequisites allow it.",
    ),
    Evidence(
        id="werror-cmake-flags",
        file="CMakeLists.txt",
        lines="108-114",
        topic="Compiler policy",
        observation="Non-MSVC builds add -Werror to common C flags.",
        implication="The observed macOS AppleClang failure is a host/toolchain strictness issue, not evidence that migration code failed at runtime.",
    ),
    Evidence(
        id="run-tests-target",
        file="tests/CMakeLists.txt",
        lines="77-134",
        topic="Unit test target",
        observation="The run_tests target includes transport, crypto, HTTP/3, QPACK, retry, datagram, and frame-type unit tests.",
        implication="A Linux full-suite PASS would materially deepen XQUIC beyond the current focused NAT rebinding demo.",
    ),
    Evidence(
        id="official-test-script",
        file="scripts/xquic_test.sh",
        lines="70-76",
        topic="Unit and case test execution",
        observation="The official test script runs tests/run_tests and scripts/case_test.sh.",
        implication="The replay runner mirrors this split and records separate unit/case exits and markers.",
    ),
    Evidence(
        id="peer-address-callback-api",
        file="include/xquic/xquic.h",
        lines="324-344",
        topic="Peer address change callbacks",
        observation="Public callbacks exist for connection-level and path-level peer address changes.",
        implication="XQUIC exposes passive migration/NAT rebinding observability to applications and tests.",
    ),
    Evidence(
        id="ready-to-create-path-api",
        file="include/xquic/xquic.h",
        lines="404-413",
        topic="Ready-to-create-path callback",
        observation="A ready-to-create-path callback is triggered after receiving a new connection ID.",
        implication="The demo can create an additional path when multipath prerequisites appear.",
    ),
    Evidence(
        id="callback-registration",
        file="include/xquic/xquic.h",
        lines="684-712",
        topic="Transport callback registration",
        observation="Transport callbacks register ready-to-create-path and peer-address-change hooks.",
        implication="The implementation has explicit callback surface for path and address transition evidence.",
    ),
    Evidence(
        id="nat-rebinding-validation",
        file="src/transport/xqc_frame.c",
        lines="1730-1773",
        topic="PATH_RESPONSE and rebinding validation",
        observation="PATH_RESPONSE data is checked against the prior PATH_CHALLENGE, then NAT rebinding address validation updates path or connection peer address and emits callbacks.",
        implication="The source implements the critical validation/notification logic behind the observed rebinding demo.",
    ),
    Evidence(
        id="test-client-rebind-socket",
        file="tests/test_client.c",
        lines="1518-1563",
        topic="Rebinding test socket",
        observation="Test cases 103/104 allocate and register a rebinding path socket.",
        implication="The example client can exercise a tuple-change-like path in local runtime tests.",
    ),
    Evidence(
        id="test-client-create-path",
        file="tests/test_client.c",
        lines="3795-3824",
        topic="Client path creation callback",
        observation="The client prints ready-to-create-path and creates a new path when multipath is enabled.",
        implication="The existing demo output can be tied to concrete source triggers.",
    ),
    Evidence(
        id="test-client-callback-registration",
        file="tests/test_client.c",
        lines="4600-4609",
        topic="Client callback registration",
        observation="The test client registers the ready-to-create-path callback in xqc_transport_callbacks_t.",
        implication="The observed demo path-creation marker is not a detached log string.",
    ),
    Evidence(
        id="test-server-peer-change-callback",
        file="tests/test_server.c",
        lines="1583-1594",
        topic="Server peer-address-change logs",
        observation="The test server prints connection-level and path-level peer address change notifications.",
        implication="The runtime demo can observe server-side rebinding acceptance.",
    ),
    Evidence(
        id="test-server-callback-registration",
        file="tests/test_server.c",
        lines="2438-2444",
        topic="Server callback registration",
        observation="The server registers connection and path peer-address-change callbacks.",
        implication="Server-side log evidence is rooted in registered transport callbacks.",
    ),
    Evidence(
        id="transport-parameter-boundary",
        file="src/transport/xqc_transport_params.h",
        lines="110-131",
        topic="Preferred address and disable active migration",
        observation="Transport parameters include preferred address and disable_active_migration fields.",
        implication="XQUIC tracks the RFC-level migration boundary conditions in transport parameters.",
    ),
]


FORBIDDEN_PUBLIC_TERMS = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AKIA",
    "ASIA",
    "arn:aws:" + "iam::",
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


def local_clone_state(xquic_dir: Path) -> dict[str, str | bool]:
    if not xquic_dir.exists():
        return {
            "path": xquic_dir.as_posix(),
            "exists": False,
            "commit": "not-observed",
            "matches_audit_commit": "unknown",
        }
    result = run(["git", "-C", xquic_dir.as_posix(), "rev-parse", "HEAD"])
    commit = result.stdout.strip() if result.returncode == 0 else "unknown"
    return {
        "path": xquic_dir.as_posix(),
        "exists": True,
        "commit": commit,
        "matches_audit_commit": "yes" if commit == XQUIC_COMMIT else "no",
    }


def macos_failure_summary(path: Path) -> dict[str, str | bool]:
    text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    return {
        "input_path": path.as_posix(),
        "input_exists": path.exists(),
        "status": "blocked_by_appleclang_werror" if "Wgnu-folding-constant" in text else "not_observed",
        "compiler": "AppleClang 17.0.0" if "AppleClang 17.0.0" in text else "not_observed",
        "failure_file": "tests/unittest/xqc_qpack_test.c:462" if "xqc_qpack_test.c:462" in text else "not_observed",
        "failure_flag": "-Werror,-Wgnu-folding-constant" if "Wgnu-folding-constant" in text else "not_observed",
    }


def nat_demo_summary(path: Path) -> dict[str, str | bool]:
    env = read_env(path)
    path0_ok = env.get("client0_exit") == "0" and env.get("path0_pass_count") == "2"
    path1_ok = env.get("client1_exit") == "0" and env.get("path1_pass_count") == "2"
    return {
        "input_path": path.as_posix(),
        "input_exists": path.exists(),
        "status": "PASS" if path0_ok and path1_ok else "not_observed",
        "client0_exit": env.get("client0_exit", "not-observed"),
        "path0_rebinding_evidence_count": env.get("path0_rebinding_evidence_count", "not-observed"),
        "path0_pass_count": env.get("path0_pass_count", "not-observed"),
        "client1_exit": env.get("client1_exit", "not-observed"),
        "path1_rebinding_evidence_count": env.get("path1_rebinding_evidence_count", "not-observed"),
        "path1_pass_count": env.get("path1_pass_count", "not-observed"),
    }


def runner_state(runner: Path) -> dict[str, str | bool]:
    text = runner.read_text(encoding="utf-8", errors="ignore") if runner.exists() else ""
    required_tokens = {
        "linux_gate": 'linux_required',
        "commit_gate": 'xquic_commit_mismatch',
        "boringssl_build": 'cmake --build "$BORINGSSL_DIR/build" --target ssl crypto',
        "xquic_build": 'cmake --build "$BUILD_DIR" --target run_tests test_client test_server',
        "run_tests": '"$BUILD_DIR/tests/run_tests"',
        "case_tests": 'sh "$XQUIC_DIR/scripts/case_test.sh"',
        "public_safe_readme": "This artifact is public-safe.",
    }
    token_status = {key: token in text for key, token in required_tokens.items()}
    return {
        "path": runner.as_posix(),
        "exists": runner.exists(),
        "required_tokens_present": all(token_status.values()),
        "token_status": token_status,
    }


def build_audit(xquic_dir: Path, nat_result_env: Path, macos_build_log: Path, runner: Path) -> dict[str, Any]:
    evidence = [asdict(item) | {"url": item.url} for item in EVIDENCE]
    nat_demo = nat_demo_summary(nat_result_env)
    macos_failure = macos_failure_summary(macos_build_log)
    runner_info = runner_state(runner)
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "implementation": "XQUIC",
        "source_commit": XQUIC_COMMIT,
        "source_repository": "https://github.com/alibaba/xquic",
        "local_clone": local_clone_state(xquic_dir),
        "summary": {
            "source_evidence_items": len(evidence),
            "nat_rebinding_demo_status": nat_demo["status"],
            "macos_full_suite_status": macos_failure["status"],
            "linux_runner_ready": "yes" if runner_info["exists"] and runner_info["required_tokens_present"] else "no",
            "paper_use": "Use XQUIC as focused NAT rebinding evidence with a packaged Linux full-suite replay gate; do not claim full-suite PASS until the Linux runner produces an ok artifact.",
            "interpretation": "XQUIC is not empty or purely theoretical: rebinding source callbacks and a local NAT rebinding demo exist. The remaining gap is full-suite replay on a Linux-compatible host.",
        },
        "existing_nat_rebinding_demo": nat_demo,
        "macos_full_suite_attempt": macos_failure,
        "linux_replay_runner": runner_info,
        "evidence": evidence,
        "reporting_boundary": {
            "safe_claim": "XQUIC has source-level path/address-change hooks, NAT rebinding validation logic, registered client/server demo callbacks, and a local NAT rebinding demo PASS artifact.",
            "unsafe_claim": "XQUIC full test-suite PASS, browser/mobile handover success, or production Alibaba deployment continuity.",
            "next_non_iphone_gate": "Run harness/scripts/run-xquic-full-suite-linux.sh on Linux with CMake, BoringSSL build prerequisites, libevent, and CUnit; accept only validation=ok with zero failed markers.",
        },
    }


def emit_markdown(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    local = audit["local_clone"]
    nat = audit["existing_nat_rebinding_demo"]
    macos = audit["macos_full_suite_attempt"]
    runner = audit["linux_replay_runner"]
    lines = [
        "# XQUIC Full-suite Linux Audit",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This public-safe audit closes the XQUIC gap left by the non-quic-go execution-depth audit. It separates the already-observed NAT rebinding demo from the still-pending Linux full-suite replay.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| implementation | `{audit['implementation']}` |",
        f"| source commit | `{audit['source_commit']}` |",
        f"| local clone observed | `{local['exists']}` |",
        f"| local clone commit | `{local['commit']}` |",
        f"| local clone matches audit commit | `{local['matches_audit_commit']}` |",
        f"| source evidence items | `{summary['source_evidence_items']}` |",
        f"| NAT rebinding demo status | `{summary['nat_rebinding_demo_status']}` |",
        f"| macOS full-suite status | `{summary['macos_full_suite_status']}` |",
        f"| Linux replay runner ready | `{summary['linux_runner_ready']}` |",
        f"| paper use | {summary['paper_use']} |",
        f"| interpretation | {summary['interpretation']} |",
        "",
        "## Existing NAT Rebinding Demo",
        "",
        "| field | value |",
        "| --- | --- |",
    ]
    for key, value in nat.items():
        lines.append(f"| {key} | `{value}` |")
    lines.extend(
        [
            "",
            "## macOS Full-suite Attempt",
            "",
            "| field | value |",
            "| --- | --- |",
        ]
    )
    for key, value in macos.items():
        lines.append(f"| {key} | `{value}` |")
    lines.extend(
        [
            "",
            "## Linux Replay Runner",
            "",
            "| field | value |",
            "| --- | --- |",
            f"| path | `{runner['path']}` |",
            f"| exists | `{runner['exists']}` |",
            f"| required tokens present | `{runner['required_tokens_present']}` |",
            "",
            "## Source Evidence",
            "",
            "| id | source | topic | observation | implication |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in audit["evidence"]:
        lines.append(
            f"| `{item['id']}` | [{item['file']}:{item['lines']}]({item['url']}) | {item['topic']} | {item['observation']} | {item['implication']} |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            f"- Safe claim: {audit['reporting_boundary']['safe_claim']}",
            f"- Unsafe claim: {audit['reporting_boundary']['unsafe_claim']}",
            f"- Next non-iPhone gate: {audit['reporting_boundary']['next_non_iphone_gate']}",
            "",
            "## Interpretation",
            "",
            "1. XQUIC should remain `focused_or_partial_positive` until the Linux replay runner produces an `ok` artifact.",
            "2. The existing NAT rebinding demo still matters because it ties callback source evidence to runtime client/server logs.",
            "3. The macOS full-suite interruption should be reported as toolchain friction caused by strict warning policy, not as a migration failure.",
            "4. A future paper row can promote XQUIC only after the Linux full-suite artifact passes the runner's fail-closed gates.",
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
    parser.add_argument("--xquic-dir", default=DEFAULT_XQUIC_DIR)
    parser.add_argument("--nat-result-env", default=DEFAULT_NAT_RESULT_ENV)
    parser.add_argument("--macos-build-log", default=DEFAULT_MACOS_BUILD_LOG)
    parser.add_argument("--runner", default=DEFAULT_RUNNER)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    audit = build_audit(
        xquic_dir=Path(args.xquic_dir),
        nat_result_env=Path(args.nat_result_env),
        macos_build_log=Path(args.macos_build_log),
        runner=Path(args.runner),
    )
    write_outputs(Path(args.output), Path(args.json_output), audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
