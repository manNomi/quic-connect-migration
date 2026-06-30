#!/usr/bin/env python3
"""Build a public-safe mvfst focused migration Linux runner audit."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_MVFST_DIR = "/private/tmp/quic-cm-scan-repos/mvfst"
DEFAULT_READINESS_JSON = "data/mvfst-migration-test-readiness-20260630.json"
DEFAULT_RUNNER = "harness/scripts/run-mvfst-focused-migration-tests-linux.sh"
DEFAULT_OUTPUT = "docs/results/mvfst-focused-linux-runner-audit-20260701.md"
DEFAULT_JSON_OUTPUT = "data/mvfst-focused-linux-runner-audit-20260701.json"

MVFST_COMMIT = "d9d65a3ab3e6ffba785d6605afe6f05b8db015ec"
MVFST_BLOB = f"https://github.com/facebook/mvfst/blob/{MVFST_COMMIT}"


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
        return f"{MVFST_BLOB}/{self.file}#L{start}"


EVIDENCE = [
    Evidence(
        id="path-manager-purpose",
        file="quic/state/QuicPathManager.h",
        lines="117-121",
        topic="Dedicated path manager",
        observation="QuicPathManager is documented as managing QUIC path probing and connection migration functionality.",
        implication="mvfst treats migration/path probing as a first-class state-management concern.",
    ),
    Evidence(
        id="client-start-path-probe",
        file="quic/client/QuicClientTransportLite.cpp",
        lines="1972-2064",
        topic="Client active path probe",
        observation="startPathProbe checks active-migration support, handshake state, socket binding, address family, adds a path, schedules PATH_CHALLENGE, and assigns a destination CID.",
        implication="mvfst has an explicit client active-probe flow that is richer than passive rebinding only.",
    ),
    Evidence(
        id="client-migrate-connection",
        file="quic/client/QuicClientTransportLite.cpp",
        lines="2071-2137",
        topic="Client active migration",
        observation="migrateConnection switches the current path, optionally resets congestion/RTT, emits qlog/stat migration hooks, and sends a ping to trigger migration.",
        implication="The client transport has an active path switch execution path.",
    ),
    Evidence(
        id="server-passive-migration",
        file="quic/server/state/ServerStateMachine.cpp",
        lines="812-878",
        topic="Server passive migration state machine",
        observation="Server-side migration handles validated/fallback paths, NAT rebinding detection, qlog update, congestion state, and current path switch.",
        implication="mvfst has server-side passive migration logic that must be tested separately from client active migration.",
    ),
    Evidence(
        id="buck-path-manager-target",
        file="quic/state/test/BUCK",
        lines="220-224",
        topic="Focused BUCK target",
        observation="BUCK defines quic_path_manager_test using QuicPathManagerTest.cpp.",
        implication="The path-manager primitive tests can be addressed as a focused target on a Buck-capable host.",
    ),
    Evidence(
        id="buck-client-migration-target",
        file="quic/client/test/BUCK",
        lines="101-105",
        topic="Focused BUCK target",
        observation="BUCK defines QuicClientTransportLiteMigrationTest using QuicClientTransportLiteMigrationTest.cpp.",
        implication="Client active migration can be tested without running the entire mvfst suite if Buck is available.",
    ),
    Evidence(
        id="buck-server-migration-target",
        file="quic/server/test/BUCK",
        lines="103-108",
        topic="Focused BUCK target",
        observation="BUCK defines QuicServerTransportMigrationTest using QuicServerTransportMigrationTest.cpp.",
        implication="Server passive migration can be tested as a focused target.",
    ),
    Evidence(
        id="path-manager-test-cases",
        file="quic/state/test/QuicPathManagerTest.cpp",
        lines="250-299",
        topic="PATH_CHALLENGE primitive tests",
        observation="Tests cover challenge lookup and challenge preparation, including nonexistent and already-validated path cases.",
        implication="Focused path-manager coverage includes path-validation primitives that underpin migration.",
    ),
    Evidence(
        id="client-migration-test-cases",
        file="quic/client/test/QuicClientTransportLiteMigrationTest.cpp",
        lines="181-287",
        topic="Client path probe and migration tests",
        observation="Tests cover path probe success with and without migration, current-path switch, and probe timeout.",
        implication="Focused client tests exercise the active probe/migrate boundary directly.",
    ),
    Evidence(
        id="server-nat-rebinding-test-cases",
        file="quic/server/test/QuicServerTransportMigrationTest.cpp",
        lines="1148-1263",
        topic="Server NAT rebinding tests",
        observation="Tests include client port-change NAT rebinding and client address-change NAT rebinding cases.",
        implication="Focused server tests cover passive migration and NAT rebinding behavior.",
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


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def local_clone_state(mvfst_dir: Path) -> dict[str, str | bool]:
    if not mvfst_dir.exists():
        return {
            "path": mvfst_dir.as_posix(),
            "exists": False,
            "commit": "not-observed",
            "matches_audit_commit": "unknown",
        }
    result = run(["git", "-C", mvfst_dir.as_posix(), "rev-parse", "HEAD"])
    commit = result.stdout.strip() if result.returncode == 0 else "unknown"
    return {
        "path": mvfst_dir.as_posix(),
        "exists": True,
        "commit": commit,
        "matches_audit_commit": "yes" if commit == MVFST_COMMIT else "no",
    }


def runner_state(runner: Path) -> dict[str, Any]:
    text = runner.read_text(encoding="utf-8", errors="ignore") if runner.exists() else ""
    required_tokens = {
        "linux_gate": "linux_required",
        "commit_gate": "mvfst_commit_mismatch",
        "buck_mode": 'RUNNER_MODE="${RUNNER_MODE:-buck}"',
        "focused_targets": "QuicClientTransportLiteMigrationTest",
        "buck_command": 'buck2 test "$target"',
        "getdeps_fallback": "getdeps.py --allow-system-packages",
        "public_safe_readme": "This artifact is public-safe.",
        "paper_ready_boundary": "A paper-ready focused PASS requires all three BUCK targets",
    }
    token_status = {key: token in text for key, token in required_tokens.items()}
    return {
        "path": runner.as_posix(),
        "exists": runner.exists(),
        "required_tokens_present": all(token_status.values()),
        "token_status": token_status,
    }


def summarize_readiness(readiness: dict[str, Any]) -> dict[str, Any]:
    focused = readiness.get("focused_targets", [])
    return {
        "input_present": bool(readiness),
        "source_commit": readiness.get("source_commit", "not-observed"),
        "remote_head_at_readiness": readiness.get("remote_head", "not-observed"),
        "validation": readiness.get("readiness", {}).get("validation", "not-observed"),
        "blocked_reasons": readiness.get("readiness", {}).get("blocked_reasons", []),
        "total_test_cases_observed": readiness.get("total_test_cases_observed", 0),
        "total_high_value_test_cases_observed": readiness.get("total_high_value_test_cases_observed", 0),
        "focused_target_count": len(focused),
        "focused_targets": [
            {
                "kind": item.get("kind", "-"),
                "file": item.get("file", "-"),
                "buck_target": item.get("buck_target", "-"),
                "test_case_count": item.get("test_case_count", 0),
                "high_value_test_count": item.get("high_value_test_count", 0),
            }
            for item in focused
        ],
    }


def build_audit(mvfst_dir: Path, readiness_json: Path, runner: Path) -> dict[str, Any]:
    readiness = summarize_readiness(read_json(readiness_json))
    runner_info = runner_state(runner)
    evidence = [asdict(item) | {"url": item.url} for item in EVIDENCE]
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "implementation": "mvfst",
        "source_commit": MVFST_COMMIT,
        "source_repository": "https://github.com/facebook/mvfst",
        "local_clone": local_clone_state(mvfst_dir),
        "summary": {
            "source_evidence_items": len(evidence),
            "focused_target_count": readiness["focused_target_count"],
            "test_cases_observed": readiness["total_test_cases_observed"],
            "high_value_test_cases_observed": readiness["total_high_value_test_cases_observed"],
            "readiness_validation": readiness["validation"],
            "linux_runner_ready": "yes" if runner_info["exists"] and runner_info["required_tokens_present"] else "no",
            "paper_use": "Use mvfst as production-relevant source/test maturity evidence with a packaged Linux focused-test gate; do not claim local mvfst execution until the runner produces an ok artifact.",
            "interpretation": "mvfst has strong migration-specific source/test structure, but the current study still lacks executed Linux Buck/getdeps results.",
        },
        "readiness_input": {
            "path": readiness_json.as_posix(),
            "exists": readiness_json.exists(),
            **readiness,
        },
        "linux_runner": runner_info,
        "evidence": evidence,
        "reporting_boundary": {
            "safe_claim": "mvfst has dedicated path manager, client active probe/migration, server passive migration/NAT rebinding logic, focused BUCK targets, and 106 observed migration/path-related test cases in the readiness map.",
            "unsafe_claim": "Local mvfst build/test PASS, browser handover success, production Meta deployment behavior, or equal controllability to the quic-go AddPath/Probe/Switch positive control.",
            "next_non_iphone_gate": "Run harness/scripts/run-mvfst-focused-migration-tests-linux.sh on a Linux host with buck2 and enough disk; accept only validation=ok with all three focused BUCK targets exiting 0.",
        },
    }


def emit_markdown(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    local = audit["local_clone"]
    readiness = audit["readiness_input"]
    runner = audit["linux_runner"]
    lines = [
        "# mvfst Focused Linux Runner Audit",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This public-safe audit narrows the mvfst gap from source/test-map evidence to a runnable Linux focused-test gate. It does not claim local mvfst execution success.",
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
        f"| focused target count | `{summary['focused_target_count']}` |",
        f"| test cases observed | `{summary['test_cases_observed']}` |",
        f"| high-value migration/path cases observed | `{summary['high_value_test_cases_observed']}` |",
        f"| readiness validation | `{summary['readiness_validation']}` |",
        f"| Linux runner ready | `{summary['linux_runner_ready']}` |",
        f"| paper use | {summary['paper_use']} |",
        f"| interpretation | {summary['interpretation']} |",
        "",
        "## Readiness Input",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| path | `{readiness['path']}` |",
        f"| exists | `{readiness['exists']}` |",
        f"| source commit | `{readiness['source_commit']}` |",
        f"| remote head at readiness | `{readiness['remote_head_at_readiness']}` |",
        f"| validation | `{readiness['validation']}` |",
        f"| blocked reasons | `{readiness['blocked_reasons']}` |",
        "",
        "## Focused Targets",
        "",
        "| kind | BUCK target | source file | tests | high-value tests |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for target in readiness["focused_targets"]:
        lines.append(
            "| {kind} | `{buck}` | `{file}` | `{tests}` | `{high}` |".format(
                kind=target["kind"],
                buck=target["buck_target"],
                file=target["file"],
                tests=target["test_case_count"],
                high=target["high_value_test_count"],
            )
        )
    lines.extend(
        [
            "",
            "## Linux Runner",
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
            "1. mvfst remains `source_test_map_only` until the Linux runner produces an `ok` artifact.",
            "2. The runner improves reproducibility by fixing the exact focused BUCK targets and getdeps fallback boundary.",
            "3. A future PASS can strengthen the paper's cross-implementation maturity argument without involving iPhone handover.",
            "4. This still would not prove Chrome/Safari/mobile browser continuity or managed deployment behavior.",
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
    parser.add_argument("--mvfst-dir", default=DEFAULT_MVFST_DIR)
    parser.add_argument("--readiness-json", default=DEFAULT_READINESS_JSON)
    parser.add_argument("--runner", default=DEFAULT_RUNNER)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    audit = build_audit(Path(args.mvfst_dir), Path(args.readiness_json), Path(args.runner))
    write_outputs(Path(args.output), Path(args.json_output), audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
