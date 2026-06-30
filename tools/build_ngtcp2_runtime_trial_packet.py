#!/usr/bin/env python3
"""Build a public-safe ngtcp2 example runtime trial packet."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_NGTCP2_DIR = "/private/tmp/quic-cm-scan-repos/ngtcp2"
DEFAULT_TEST_LOG = "harness/results/impl-rerun-20260630T070249Z/logs/ngtcp2-migration-tests.log"
DEFAULT_RUNNER = "harness/scripts/run-ngtcp2-example-migration-demo.sh"
DEFAULT_RUNNER_RESULT_ENV = "harness/results/ngtcp2-example-migration-demo-local-20260701/results/result.env"
DEFAULT_OUTPUT = "docs/results/ngtcp2-runtime-trial-packet-20260701.md"
DEFAULT_JSON_OUTPUT = "data/ngtcp2-runtime-trial-packet-20260701.json"

NGTCP2_COMMIT = "c24b12690c5bdf7ad2715ae427504e76bf5c6ffc"
NGTCP2_BLOB = f"https://github.com/ngtcp2/ngtcp2/blob/{NGTCP2_COMMIT}"
RESEARCH_REPO_BASE = "https://github.com/manNomi/quic-connect-migration/blob/docs/quinn-neqo-rerun-20260630"

FOCUSED_TESTS = [
    "/pkt/test_ngtcp2_pkt_encode_path_challenge_frame",
    "/pkt/test_ngtcp2_pkt_encode_path_response_frame",
    "/conn/test_ngtcp2_conn_client_connection_migration",
    "/conn/test_ngtcp2_conn_recv_path_challenge",
    "/conn/test_ngtcp2_conn_disable_active_migration",
    "/conn/test_ngtcp2_conn_path_validation",
]

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
    source_base: str = NGTCP2_BLOB

    @property
    def url(self) -> str:
        return f"{self.source_base}/{self.source}#L{self.line}"


EVIDENCE = [
    Evidence(
        id="examples-require-libev-nghttp3",
        source="README.rst",
        line=45,
        topic="Example dependency gate",
        observation="The ngtcp2 README states that sources under examples require libev and nghttp3.",
        implication="A runtime example-client/server migration row must record libev and nghttp3 readiness before claiming execution.",
    ),
    Evidence(
        id="examples-are-http3-client-server",
        source="README.rst",
        line=201,
        topic="Example runtime scope",
        observation="The README says the built client and server executables live under examples and speak HTTP/3.",
        implication="The examples are a legitimate runtime bridge between transport migration APIs and an HTTP/3 workload.",
    ),
    Evidence(
        id="openssl-example-binaries",
        source="README.rst",
        line=312,
        topic="OpenSSL example binaries",
        observation="The examples list includes osslclient and osslserver as OpenSSL-backed client/server binaries.",
        implication="A public-safe local runner can target osslclient/osslserver without adding a new ngtcp2 application.",
    ),
    Evidence(
        id="cmake-finds-example-dependencies",
        source="CMakeLists.txt",
        line=152,
        topic="CMake dependency discovery",
        observation="When ENABLE_LIB_ONLY is off, CMake searches for Libev and Libnghttp3.",
        implication="Missing libev is an example-runtime readiness blocker rather than evidence that migration primitives are absent.",
    ),
    Evidence(
        id="cmake-example-required-flags",
        source="CMakeLists.txt",
        line=252,
        topic="Example dependency flags",
        observation="CMake records HAVE_LIBEV and HAVE_LIBNGHTTP3 as example requirements.",
        implication="The trial packet can classify current local state before attempting a runtime run.",
    ),
    Evidence(
        id="ossl-example-build-condition",
        source="examples/CMakeLists.txt",
        line=414,
        topic="osslclient/osslserver build gate",
        observation="osslclient and osslserver are built only when Libev, OpenSSL helper support, and Libnghttp3 are found.",
        implication="The runtime row cannot be promoted until these dependency gates are open.",
    ),
    Evidence(
        id="example-active-versus-nat-rebinding",
        source="examples/client.cc",
        line=1347,
        topic="Example migration trigger",
        observation="The example client calls ngtcp2_conn_initiate_immediate_migration when changing local address without --nat-rebinding.",
        implication="The example can exercise active client migration semantics, not just passive NAT rebinding simulation.",
    ),
    Evidence(
        id="example-change-local-addr-flag",
        source="examples/client.cc",
        line=2015,
        topic="CLI trigger",
        observation="The --change-local-addr option changes the client local address after handshake completion.",
        implication="The runner has a documented trigger for a controlled post-handshake migration attempt.",
    ),
    Evidence(
        id="example-qlog-options",
        source="examples/client.cc",
        line=2047,
        topic="qlog capture",
        observation="The example client supports qlog-file and qlog-dir output.",
        implication="A future runtime PASS can be tied to path-validation frame evidence rather than exit code only.",
    ),
    Evidence(
        id="server-htdocs-qlog-options",
        source="examples/server.cc",
        line=2500,
        topic="HTTP/3 app and qlog capture",
        observation="The example server supports --htdocs and --qlog-dir.",
        implication="The runner can use a minimal static HTTP/3 object and collect server-side qlog-derived evidence.",
    ),
    Evidence(
        id="fresh-focused-test-log",
        source="docs/results/implementation-rerun-results-20260630.md",
        line=279,
        topic="Fresh local migration tests",
        observation="The study records six focused ngtcp2 migration/path-validation tests passing at the audited commit.",
        implication="The current missing runtime row is an example dependency/runtime gap, not an absence of migration tests.",
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


def pkg_version(module: str) -> str:
    proc = run(["pkg-config", "--modversion", module], timeout=5)
    if proc.returncode != 0:
        return "missing"
    return proc.stdout.strip().splitlines()[0] if proc.stdout.strip() else "unknown"


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
        "matches_expected_commit": "yes" if commit == NGTCP2_COMMIT else "no",
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


def focused_test_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "log_exists": False,
            "expected_tests": len(FOCUSED_TESTS),
            "passed_tests": 0,
            "all_expected_seen": "no",
            "summary_line": "",
        }
    text = path.read_text(encoding="utf-8", errors="ignore")
    passed = sum(1 for test in FOCUSED_TESTS if f"{test}[ OK" in text)
    summary_line = ""
    for line in text.splitlines():
        if "tests successful" in line:
            summary_line = line.strip()
            break
    return {
        "log_exists": True,
        "expected_tests": len(FOCUSED_TESTS),
        "passed_tests": passed,
        "all_expected_seen": "yes" if passed == len(FOCUSED_TESTS) else "no",
        "summary_line": summary_line,
    }


def example_binary_state(ngtcp2_dir: Path) -> dict[str, Any]:
    candidates = [
        ngtcp2_dir / "build-example-migration" / "examples" / "osslclient",
        ngtcp2_dir / "build-example-migration" / "examples" / "osslserver",
        ngtcp2_dir / "build-tests" / "examples" / "osslclient",
        ngtcp2_dir / "build-tests" / "examples" / "osslserver",
    ]
    present = [path.as_posix() for path in candidates if path.exists()]
    return {
        "candidate_count": len(candidates),
        "present_count": len(present),
        "present": present,
        "ossl_pair_present": "yes" if any(path.endswith("osslclient") for path in present) and any(path.endswith("osslserver") for path in present) else "no",
    }


def classify_runtime(pkg: dict[str, str], runner_env: dict[str, str]) -> tuple[str, str]:
    if runner_env:
        validation = runner_env.get("validation", "unknown")
        reason = runner_env.get("blocked_or_failed_reason", "unknown")
        if validation == "ok":
            return "ready_or_passed", "runner_validation_ok"
        if validation == "blocked":
            return "blocked", reason
        if validation == "failed":
            return "failed", reason
        return "unknown", reason
    if pkg["libev"] == "missing":
        return "blocked", "missing_pkg_config_libev"
    if pkg["libnghttp3"] == "missing":
        return "blocked", "missing_pkg_config_libnghttp3"
    if pkg["openssl"] == "missing":
        return "blocked", "missing_pkg_config_openssl"
    return "ready_not_run", "runner_result_env_missing"


def build_packet(
    ngtcp2_dir: Path,
    test_log: Path,
    runner: Path,
    runner_result_env: Path,
) -> dict[str, Any]:
    pkg = {
        "libev": pkg_version("libev"),
        "libnghttp3": pkg_version("libnghttp3"),
        "openssl": pkg_version("openssl"),
    }
    runner_env = parse_env(runner_result_env)
    runtime_status, runtime_reason = classify_runtime(pkg, runner_env)
    focused = focused_test_state(test_log)
    clone = local_clone_state(ngtcp2_dir)
    binary = example_binary_state(ngtcp2_dir)
    packet = {
        "generated": utc_date_iso(),
        "public_safe": True,
        "implementation": "ngtcp2",
        "source_commit": NGTCP2_COMMIT,
        "local_clone": clone,
        "dependency_state": pkg,
        "focused_test_state": focused,
        "example_binary_state": binary,
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
        "claim_boundary": {
            "safe_claim": "ngtcp2 has strong C-library migration/path-validation API and focused test evidence; a fail-closed example HTTP/3 runtime runner is now packaged, but current local execution is blocked unless dependency gates are open.",
            "unsafe_claim": "ngtcp2 runtime HTTP/3 workload continuity, browser handover, CDN/LB deployment continuity, or production app continuity.",
            "next_gap": "Install/provide libev with pkg-config visibility, then run harness/scripts/run-ngtcp2-example-migration-demo.sh with REQUIRE_READY=1 and require client exit 0 plus path-validation frame evidence.",
        },
        "evidence": [asdict(item) | {"url": item.url} for item in EVIDENCE],
    }
    text = json.dumps(packet, ensure_ascii=False)
    packet["public_safety_scan_ok"] = not any(token in text for token in FORBIDDEN_PUBLIC_TEXT)
    return packet


def emit_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# ngtcp2 Runtime Trial Packet",
        "",
        f"Generated: `{packet['generated']}`",
        "",
        "This public-safe packet turns the ngtcp2 gap into a reproducible runtime gate. It does not claim a runtime PASS unless the fail-closed runner records `validation=ok`.",
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
        f"| libev | `{packet['dependency_state']['libev']}` |",
        f"| libnghttp3 | `{packet['dependency_state']['libnghttp3']}` |",
        f"| openssl | `{packet['dependency_state']['openssl']}` |",
        f"| focused migration tests | `{packet['focused_test_state']['passed_tests']}/{packet['focused_test_state']['expected_tests']} expected seen` |",
        f"| example ossl binary pair present | `{packet['example_binary_state']['ossl_pair_present']}` |",
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
        f"| validation | `{packet['runner']['result_env_values'].get('validation', '-')}` |",
        f"| blocked or failed reason | `{packet['runner']['result_env_values'].get('blocked_or_failed_reason', '-')}` |",
        f"| client exit | `{packet['runner']['result_env_values'].get('client_exit', '-')}` |",
        f"| path challenge count | `{packet['runner']['result_env_values'].get('path_challenge_count', '-')}` |",
        f"| path response count | `{packet['runner']['result_env_values'].get('path_response_count', '-')}` |",
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
            "1. ngtcp2 should stay above source-only status because public migration APIs and focused local migration/path-validation tests are already present.",
            "2. The current local runtime blocker is dependency readiness for the official HTTP/3 examples, especially `libev`, not evidence that ngtcp2 lacks migration behavior.",
            "3. The new runner makes the next upgrade concrete: install the missing dependency, run with `REQUIRE_READY=1`, and promote only if qlog/log-derived path-validation evidence appears with a successful client exit.",
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
    parser.add_argument("--ngtcp2-dir", default=DEFAULT_NGTCP2_DIR)
    parser.add_argument("--test-log", default=DEFAULT_TEST_LOG)
    parser.add_argument("--runner", default=DEFAULT_RUNNER)
    parser.add_argument("--runner-result-env", default=DEFAULT_RUNNER_RESULT_ENV)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    packet = build_packet(
        Path(args.ngtcp2_dir),
        Path(args.test_log),
        Path(args.runner),
        Path(args.runner_result_env),
    )
    write_outputs(Path(args.output), Path(args.json_output), packet)
    print(f"wrote {args.output} and {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
