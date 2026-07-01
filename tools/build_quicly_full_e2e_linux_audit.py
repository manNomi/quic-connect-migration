#!/usr/bin/env python3
"""Build a public-safe quicly full-e2e Linux runner audit."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_QUICLY_DIR = "/private/tmp/quic-cm-scan-repos/quicly"
DEFAULT_FOCUSED_RESULT_ENV = "harness/results/quicly-e2e-path-migration-local-20260630/results/result.env"
DEFAULT_RUNNER = "harness/scripts/run-quicly-full-e2e-linux.sh"
DEFAULT_OUTPUT = "docs/results/quicly-full-e2e-linux-audit-20260701.md"
DEFAULT_JSON_OUTPUT = "data/quicly-full-e2e-linux-audit-20260701.json"

QUICLY_COMMIT = "ed83c7c7d545a01650651c9523466f561ec5d4bb"
QUICLY_BLOB = f"https://github.com/h2o/quicly/blob/{QUICLY_COMMIT}"


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
        return f"{QUICLY_BLOB}/{self.file}#L{start}"


EVIDENCE = [
    Evidence(
        id="official-build-instructions",
        file="README.md",
        lines="8-18",
        topic="Build prerequisites",
        observation="The README documents submodule initialization, CMake/make builds, and OpenSSL as a build dependency.",
        implication="A full e2e replay needs a real build gate, not only a source scan or prebuilt local binary.",
    ),
    Evidence(
        id="official-test-instructions",
        file="README.md",
        lines="24-42",
        topic="Perl dependency and make check path",
        observation="The README documents Perl dependency installation before running make check.",
        implication="The runner must fail closed when Net::EmptyPort or other Perl-side prerequisites are missing.",
    ),
    Evidence(
        id="frame-primitive",
        file="lib/frame.c",
        lines="28-30",
        topic="PATH_CHALLENGE/PATH_RESPONSE frame encoding",
        observation="The frame encoder selects PATH_RESPONSE or PATH_CHALLENGE and copies the 8-byte challenge payload.",
        implication="quicly contains the RFC path-validation frame primitive used by the e2e migration test.",
    ),
    Evidence(
        id="path-validation-state",
        file="lib/quicly.c",
        lines="226-240",
        topic="Path challenge/response state",
        observation="Each path tracks PATH_CHALLENGE scheduling/data and PATH_RESPONSE data.",
        implication="Path validation is represented in connection path state, not only in stateless frame parsing.",
    ),
    Evidence(
        id="promote-path",
        file="lib/quicly.c",
        lines="2091-2096",
        topic="Path promotion",
        observation="promote_path logs a promote_path event and promotes a validated path index.",
        implication="The e2e test's promote_path log checks are tied to a concrete path switch implementation point.",
    ),
    Evidence(
        id="path-challenge-send-logging",
        file="lib/quicly.c",
        lines="5317-5330",
        topic="PATH_CHALLENGE/PATH_RESPONSE send logging",
        observation="Sending path challenge/response frames updates stats and emits path_challenge_send/path_response_send logs.",
        implication="The implementation can expose migration evidence through stats/log events.",
    ),
    Evidence(
        id="path-response-validation",
        file="lib/quicly.c",
        lines="6615-6630",
        topic="PATH_RESPONSE receive validation",
        observation="PATH_RESPONSE data is compared against the outstanding PATH_CHALLENGE and path validation is completed when it matches.",
        implication="The e2e path-migration PASS covers the same validation mechanism that decides whether a path can be promoted.",
    ),
    Evidence(
        id="disable-active-migration-boundary",
        file="lib/quicly.c",
        lines="7687-7689",
        topic="disable_active_migration policy",
        observation="The receive path respects the peer's disable_active_migration transport parameter after TLS handshake completion.",
        implication="quicly has policy boundaries; implementation support does not mean every peer/path migration is allowed.",
    ),
    Evidence(
        id="path-migration-e2e",
        file="t/e2e.t",
        lines="371-430",
        topic="Focused path-migration e2e test",
        observation="The e2e test respawns a UDP forwarder twice, checks two promote_path events, and verifies CID sequence 1 is used for the first path probe in the CID-enabled case.",
        implication="The focused local PASS is migration-specific and stronger than primitive-only evidence.",
    ),
    Evidence(
        id="slow-start-boundary",
        file="t/e2e.t",
        lines="432-546",
        topic="Unrelated full e2e timing caveat",
        observation="The slow-start subtest is a separate congestion-control timing test after path-migration.",
        implication="The observed macOS full-e2e failure should not be reported as a path-migration failure, but it also prevents a full e2e PASS claim.",
    ),
    Evidence(
        id="stats-surface",
        file="include/quicly.h",
        lines="785-790",
        topic="Path stats",
        observation="Public stats include validated paths, validation failures, migration-elicited paths, promoted paths, and closed-no-DCID paths.",
        implication="quicly exposes migration/path state as measurable counters useful for implementation maturity reporting.",
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


def local_clone_state(quicly_dir: Path) -> dict[str, str | bool]:
    if not quicly_dir.exists():
        return {
            "path": quicly_dir.as_posix(),
            "exists": False,
            "commit": "not-observed",
            "matches_audit_commit": "unknown",
        }
    result = run(["git", "-C", quicly_dir.as_posix(), "rev-parse", "HEAD"])
    commit = result.stdout.strip() if result.returncode == 0 else "unknown"
    return {
        "path": quicly_dir.as_posix(),
        "exists": True,
        "commit": commit,
        "matches_audit_commit": "yes" if commit == QUICLY_COMMIT else "no",
    }


def focused_e2e_summary(path: Path) -> dict[str, str | bool]:
    env = read_env(path)
    return {
        "input_path": path.as_posix(),
        "input_exists": path.exists(),
        "status": "PASS_FOCUSED_E2E"
        if env.get("validation") == "ok_path_migration"
        and env.get("path_subtest_ok") == "yes"
        and env.get("cid_seq_check_ok") == "yes"
        else "not_observed",
        "ready": env.get("ready", "not-observed"),
        "prove_exit": env.get("prove_exit", "not-observed"),
        "path_subtest_seen": env.get("path_subtest_seen", "not-observed"),
        "path_subtest_ok": env.get("path_subtest_ok", "not-observed"),
        "cid_seq_check_ok": env.get("cid_seq_check_ok", "not-observed"),
        "slow_start_failed": env.get("slow_start_failed", "not-observed"),
        "validation": env.get("validation", "not-observed"),
    }


def runner_state(runner: Path) -> dict[str, Any]:
    text = runner.read_text(encoding="utf-8", errors="ignore") if runner.exists() else ""
    required_tokens = {
        "linux_gate": "linux_required",
        "commit_gate": "quicly_commit_mismatch",
        "net_empty_port_gate": "missing_perl_net_empty_port",
        "submodule_update": "git submodule update --init --recursive",
        "cmake_configure": 'cmake -S "$QUICLY_DIR" -B "$QUICLY_BUILD_DIR"',
        "build_targets": "cmake --build \"$QUICLY_BUILD_DIR\" --target test.t cli udpfw",
        "unit_test": '"$QUICLY_BUILD_DIR/test.t"',
        "prove_e2e": "prove -v t/e2e.t",
        "full_pass_boundary": "ok_full_e2e",
        "public_safe_readme": "This artifact is public-safe.",
    }
    token_status = {key: token in text for key, token in required_tokens.items()}
    return {
        "path": runner.as_posix(),
        "exists": runner.exists(),
        "required_tokens_present": all(token_status.values()),
        "token_status": token_status,
    }


def build_audit(quicly_dir: Path, focused_result_env: Path, runner: Path) -> dict[str, Any]:
    focused = focused_e2e_summary(focused_result_env)
    runner_info = runner_state(runner)
    evidence = [asdict(item) | {"url": item.url} for item in EVIDENCE]
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "implementation": "quicly",
        "source_commit": QUICLY_COMMIT,
        "source_repository": "https://github.com/h2o/quicly",
        "local_clone": local_clone_state(quicly_dir),
        "summary": {
            "source_evidence_items": len(evidence),
            "focused_e2e_status": focused["status"],
            "focused_path_subtest_ok": focused["path_subtest_ok"],
            "focused_cid_seq_check_ok": focused["cid_seq_check_ok"],
            "focused_full_prove_exit": focused["prove_exit"],
            "focused_slow_start_failed": focused["slow_start_failed"],
            "linux_runner_ready": "yes" if runner_info["exists"] and runner_info["required_tokens_present"] else "no",
            "paper_use": "Use quicly as focused e2e path-migration evidence plus a fail-closed Linux full-e2e replay gate; do not claim full e2e PASS until validation=ok_full_e2e exists.",
            "interpretation": "quicly has concrete path validation/promotion internals and a focused e2e PASS, but the current study still lacks a clean full t/e2e.t PASS artifact.",
        },
        "focused_e2e_input": focused,
        "linux_runner": runner_info,
        "evidence": evidence,
        "reporting_boundary": {
            "safe_claim": "quicly's focused path-migration e2e subtest passed locally, including CID sequence 1 first path probe evidence, and the repository now has a Linux full-e2e replay gate.",
            "unsafe_claim": "quicly full t/e2e.t PASS, production H2O deployment continuity, browser handover success, or quic-go-equivalent public AddPath/Probe/Switch control.",
            "next_non_iphone_gate": "Run harness/scripts/run-quicly-full-e2e-linux.sh on Linux; accept full-e2e promotion only when validation=ok_full_e2e with unit_test_exit=0, prove_exit=0, path_subtest_ok=yes, and cid_seq_check_ok=yes.",
        },
    }


def emit_markdown(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    local = audit["local_clone"]
    focused = audit["focused_e2e_input"]
    runner = audit["linux_runner"]
    lines = [
        "# quicly Full e2e Linux Runner Audit",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This public-safe audit narrows the remaining quicly gap from focused e2e path-migration evidence to a reproducible Linux full-e2e gate. It does not claim full quicly e2e success.",
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
        f"| focused e2e status | `{summary['focused_e2e_status']}` |",
        f"| focused path subtest ok | `{summary['focused_path_subtest_ok']}` |",
        f"| focused CID sequence check ok | `{summary['focused_cid_seq_check_ok']}` |",
        f"| focused full prove exit | `{summary['focused_full_prove_exit']}` |",
        f"| focused slow-start failed | `{summary['focused_slow_start_failed']}` |",
        f"| Linux runner ready | `{summary['linux_runner_ready']}` |",
        f"| paper use | {summary['paper_use']} |",
        f"| interpretation | {summary['interpretation']} |",
        "",
        "## Focused e2e Input",
        "",
        "| field | value |",
        "| --- | --- |",
    ]
    for key, value in focused.items():
        lines.append(f"| {key} | `{value}` |")
    lines.extend(
        [
            "",
            "## Linux Full-e2e Runner",
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
            "1. quicly remains `focused_e2e_positive_with_full_e2e_gate` until the Linux runner produces `validation=ok_full_e2e`.",
            "2. The existing focused PASS is useful because it checks path promotion and CID use for the first path probe.",
            "3. The previous `slow-start` caveat is outside the path-migration subtest, but it still prevents a full e2e PASS claim.",
            "4. A future Linux PASS would strengthen implementation maturity evidence without requiring iPhone handover.",
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
    parser.add_argument("--quicly-dir", default=DEFAULT_QUICLY_DIR)
    parser.add_argument("--focused-result-env", default=DEFAULT_FOCUSED_RESULT_ENV)
    parser.add_argument("--runner", default=DEFAULT_RUNNER)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    audit = build_audit(Path(args.quicly_dir), Path(args.focused_result_env), Path(args.runner))
    write_outputs(Path(args.output), Path(args.json_output), audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
