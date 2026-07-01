#!/usr/bin/env python3
"""Build a public-safe ngtcp2 migration API boundary audit."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_OUTPUT = "docs/results/ngtcp2-migration-api-boundary-audit-20260701.md"
DEFAULT_JSON_OUTPUT = "data/ngtcp2-migration-api-boundary-audit-20260701.json"
DEFAULT_CLONE = "/private/tmp/quic-cm-scan-repos/ngtcp2"
EXPECTED_COMMIT = "c24b12690c5bdf7ad2715ae427504e76bf5c6ffc"
GITHUB_BASE = f"https://github.com/ngtcp2/ngtcp2/blob/{EXPECTED_COMMIT}"
RESEARCH_REPO_BASE = "https://github.com/manNomi/quic-connect-migration/blob/docs/quinn-neqo-rerun-20260630"


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source_path: str
    line: int
    topic: str
    observation: str
    implication: str
    source_base: str = GITHUB_BASE

    @property
    def url(self) -> str:
        return f"{self.source_base}/{self.source_path}#L{self.line}"


EVIDENCE_ITEMS = [
    Evidence(
        evidence_id="transport-param-disable-active-migration",
        source_path="lib/includes/ngtcp2/ngtcp2.h",
        line=1595,
        topic="Transport-parameter migration policy",
        observation="ngtcp2_transport_params exposes disable_active_migration and documents it as the local endpoint not supporting active connection migration.",
        implication="ngtcp2 models the RFC migration policy boundary directly in its public transport-parameter surface.",
    ),
    Evidence(
        evidence_id="transport-param-preferred-address",
        source_path="lib/includes/ngtcp2/ngtcp2.h",
        line=1615,
        topic="Preferred-address transport parameter",
        observation="The public transport-parameter struct records whether a preferred_address is set.",
        implication="Preferred-address migration is represented as a public protocol primitive, not only as an internal parser detail.",
    ),
    Evidence(
        evidence_id="public-path-object",
        source_path="lib/includes/ngtcp2/ngtcp2.h",
        line=2142,
        topic="Public network path representation",
        observation="ngtcp2_path represents the local and remote endpoints where a packet is sent and received.",
        implication="Applications can pass explicit path objects to the connection APIs, which makes ngtcp2 a useful C-library comparison point.",
    ),
    Evidence(
        evidence_id="begin-path-validation-callback",
        source_path="lib/includes/ngtcp2/ngtcp2.h",
        line=3219,
        topic="Path-validation start callback",
        observation="ngtcp2_begin_path_validation notifies the application when validation starts and exposes the path plus fallback path.",
        implication="Migration/path probing can be observed at the application callback boundary.",
    ),
    Evidence(
        evidence_id="path-validation-result-callback",
        source_path="lib/includes/ngtcp2/ngtcp2.h",
        line=3241,
        topic="Path-validation result callback",
        observation="ngtcp2_path_validation reports success or failure for a validated path and optional fallback path.",
        implication="ngtcp2 gives applications a first-class completion signal for path validation.",
    ),
    Evidence(
        evidence_id="callback-table-path-validation",
        source_path="lib/includes/ngtcp2/ngtcp2.h",
        line=3800,
        topic="Callback table integration",
        observation="The public callback table includes an optional path_validation callback.",
        implication="Path-validation observability is part of the regular application integration surface.",
    ),
    Evidence(
        evidence_id="callback-table-begin-path-validation",
        source_path="lib/includes/ngtcp2/ngtcp2.h",
        line=3945,
        topic="Callback table integration",
        observation="The public callback table includes begin_path_validation as a versioned callback.",
        implication="Applications can observe both the start and the result of migration-related validation.",
    ),
    Evidence(
        evidence_id="testing-local-address-api",
        source_path="lib/includes/ngtcp2/ngtcp2.h",
        line=5912,
        topic="Local-address setter boundary",
        observation="ngtcp2_conn_set_local_addr changes the current path local endpoint address but is documented as testing-purpose only.",
        implication="The setter is useful for tests and NAT-rebinding simulation, but it should not be reported as the general production active-migration API.",
    ),
    Evidence(
        evidence_id="public-immediate-migration-api",
        source_path="lib/includes/ngtcp2/ngtcp2.h",
        line=6013,
        topic="Immediate client migration API",
        observation="ngtcp2_conn_initiate_immediate_migration starts client connection migration to a given path and performs path validation without waiting for success.",
        implication="ngtcp2 has a direct public client migration trigger, stronger than source-only or endpoint-wide-only evidence.",
    ),
    Evidence(
        evidence_id="public-validation-gated-migration-api",
        source_path="lib/includes/ngtcp2/ngtcp2.h",
        line=6039,
        topic="Validation-gated client migration API",
        observation="ngtcp2_conn_initiate_migration starts validation on a new path and migrates after successful validation.",
        implication="The public API exposes a safer validation-gated migration mode distinct from immediate migration.",
    ),
    Evidence(
        evidence_id="implementation-path-validation-start",
        source_path="lib/ngtcp2_conn.c",
        line=323,
        topic="Begin-path-validation callback dispatch",
        observation="Connection code calls begin_path_validation with flags, the validation path, and the fallback path when present.",
        implication="The public callback is wired into the migration/path-validation implementation.",
    ),
    Evidence(
        evidence_id="implementation-path-validation-result",
        source_path="lib/ngtcp2_conn.c",
        line=350,
        topic="Path-validation result dispatch",
        observation="Connection code calls path_validation with success, failure, or aborted results.",
        implication="A test or runtime harness can observe validation outcomes without inferring from packet logs alone.",
    ),
    Evidence(
        evidence_id="path-challenge-transmit",
        source_path="lib/ngtcp2_conn.c",
        line=5172,
        topic="PATH_CHALLENGE transmission",
        observation="conn_write_path_challenge constructs PATH_CHALLENGE frames for the path being validated and tracks probe entries.",
        implication="ngtcp2 implements active validation traffic rather than simply accepting tuple changes.",
    ),
    Evidence(
        evidence_id="path-response-validation-switch",
        source_path="lib/ngtcp2_conn.c",
        line=6130,
        topic="PATH_RESPONSE validation and path switch",
        observation="conn_recv_path_response validates the challenge data, updates the current DCID/path on success, resets path state, and reports success.",
        implication="Successful validation can promote the new path and reset transport state, which is core migration behavior.",
    ),
    Evidence(
        evidence_id="disable-active-migration-enforcement",
        source_path="lib/ngtcp2_conn.c",
        line=10027,
        topic="Disable-active-migration enforcement",
        observation="Server-side packet receive logic discards packets to a new local address when active migration is disabled unless the path matches preferred-address migration.",
        implication="The implementation enforces policy and preferred-address exceptions, so experiments must record server transport parameters.",
    ),
    Evidence(
        evidence_id="immediate-migration-implementation",
        source_path="lib/ngtcp2_conn.c",
        line=13846,
        topic="Immediate migration implementation",
        observation="ngtcp2_conn_initiate_immediate_migration stops PMTUD, retires the current DCID, installs a new path/DCID, resets congestion and ECN state, then begins validation.",
        implication="Immediate migration is implemented as a real path/DCID transition with follow-up validation.",
    ),
    Evidence(
        evidence_id="validation-gated-migration-implementation",
        source_path="lib/ngtcp2_conn.c",
        line=13921,
        topic="Validation-gated migration implementation",
        observation="ngtcp2_conn_initiate_migration creates a path-validation object for the new path, activates a DCID, and begins validation before switching.",
        implication="ngtcp2 can model validation-first migration semantics directly.",
    ),
    Evidence(
        evidence_id="client-migration-test-registered",
        source_path="tests/ngtcp2_conn_test.c",
        line=86,
        topic="Focused test registration",
        observation="The test suite registers test_ngtcp2_conn_client_connection_migration and related path challenge/disable-active-migration tests.",
        implication="Migration behavior is first-class in the unit test suite rather than incidental parser coverage.",
    ),
    Evidence(
        evidence_id="client-migration-test",
        source_path="tests/ngtcp2_conn_test.c",
        line=10813,
        topic="Client connection migration test",
        observation="The client migration test exercises immediate migration, validation-gated migration, PATH_RESPONSE handling, current-path update, and path-history reuse.",
        implication="The fresh local rerun covers both public migration APIs and validation behavior.",
    ),
    Evidence(
        evidence_id="disable-active-migration-test",
        source_path="tests/ngtcp2_conn_test.c",
        line=11169,
        topic="Disable-active-migration policy test",
        observation="The tests verify that PATH_CHALLENGE to a new local address is ignored when server disable_active_migration is set, while preferred-address migration is accepted.",
        implication="Policy and preferred-address exceptions are covered by focused tests.",
    ),
    Evidence(
        evidence_id="nat-rebinding-path-validation-test",
        source_path="tests/ngtcp2_conn_test.c",
        line=14268,
        topic="NAT rebinding path-validation test",
        observation="A server-side NAT rebinding scenario starts path validation after the remote port changes and checks fallback-path state.",
        implication="Passive rebinding and server-initiated validation are covered in addition to client active migration.",
    ),
    Evidence(
        evidence_id="example-client-active-versus-nat-rebinding",
        source_path="examples/client.cc",
        line=1347,
        topic="Example client local-address change",
        observation="The example client distinguishes NAT rebinding simulation from active migration: NAT rebinding updates the local address, while the non-NAT path calls ngtcp2_conn_initiate_immediate_migration.",
        implication="The sample application demonstrates the boundary between passive rebinding simulation and active client migration.",
    ),
    Evidence(
        evidence_id="example-client-cli-flags",
        source_path="examples/client.cc",
        line=2015,
        topic="Example CLI migration trigger",
        observation="The example client documents --change-local-addr and --nat-rebinding, with NAT rebinding described as changing local address without starting path validation.",
        implication="ngtcp2 ships runnable example controls that separate path-change modes for experiments.",
    ),
    Evidence(
        evidence_id="qlog-path-validation-frames",
        source_path="lib/ngtcp2_qlog.c",
        line=839,
        topic="qlog frame observability",
        observation="qlog frame writing includes PATH_CHALLENGE and PATH_RESPONSE frame types.",
        implication="Frame-level path-validation evidence can be captured in qlog when the application enables qlog_write.",
    ),
    Evidence(
        evidence_id="qlog-transport-params",
        source_path="lib/ngtcp2_qlog.c",
        line=946,
        topic="qlog transport-parameter observability",
        observation="qlog parameter output includes disable_active_migration and preferred_address when present.",
        implication="Policy and preferred-address state can be recorded in qlog artifacts.",
    ),
    Evidence(
        evidence_id="local-rerun-summary",
        source_path="docs/results/implementation-rerun-results-20260630.md",
        line=279,
        topic="Fresh local rerun",
        observation="The study reran ngtcp2 migration/path-validation focused tests, including client migration, path challenge receive, disable active migration, path validation, and PATH_CHALLENGE/PATH_RESPONSE frame encoding.",
        implication="The repository has executed local test evidence for the audited source commit, but not a custom ngtcp2 HTTP/3 browser/deployment workload row.",
        source_base=RESEARCH_REPO_BASE,
    ),
]


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
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
        "matches_expected_commit": "yes" if commit == EXPECTED_COMMIT else "no",
        "remote": remote,
    }


def build_audit(clone_path: Path = Path(DEFAULT_CLONE)) -> dict[str, Any]:
    clone = local_clone_state(clone_path)
    items = [asdict(item) | {"url": item.url} for item in EVIDENCE_ITEMS]
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "implementation": "ngtcp2",
        "source_repository": "https://github.com/ngtcp2/ngtcp2",
        "source_commit": EXPECTED_COMMIT,
        "local_clone": clone,
        "evidence_item_count": len(items),
        "summary": {
            "public_client_migration_api": "present_immediate_and_validation_gated",
            "active_api_boundary": "direct_client_path_api_not_quic_go_addpath_probe_switch_shape",
            "passive_rebinding": "server_path_validation_and_nat_rebinding_tests_present",
            "preferred_address": "transport_parameter_and_policy_exception_present",
            "disable_active_migration_policy": "implemented_and_tested",
            "path_validation": "begin_result_callbacks_plus_PATH_CHALLENGE_RESPONSE",
            "observability": "qlog_transport_params_and_path_frames",
            "fresh_local_tests": "focused_ngtcp2_migration_path_validation_tests_passed_in_corpus",
            "local_http3_runtime_row": "present_in_companion_runtime_trial_packet",
            "browser_or_deployment_runtime_row": "absent",
        },
        "conclusion": {
            "implementation_status": "mature_C_library_for_client_migration_path_validation_and_rebinding",
            "api_boundary": "direct_ngtcp2_path_api_but_no_browser_or_managed_deployment_claim",
            "paper_use": "Use ngtcp2 as source-linked C-library maturity evidence plus companion local HTTP/3 runtime positive control, not as browser or cloud deployment continuity proof.",
        },
        "safe_claim": "ngtcp2 exposes public immediate and validation-gated client migration APIs, path-validation callbacks, disable-active-migration/preferred-address policy handling, qlog observability, example controls, focused local test evidence, and a companion official-example local HTTP/3 runtime row.",
        "unsafe_claim": "ngtcp2 currently proves Chrome/Safari/Android browser handover, managed-CDN/LB continuity, or production application continuity in this study.",
        "next_gap": "Use the companion runtime packet as the second C-library positive control; repeat it on a clean host only if reviewers require independent replication.",
        "evidence": items,
    }


def emit_markdown(audit: dict[str, Any]) -> str:
    clone = audit["local_clone"]
    lines = [
        "# ngtcp2 Migration API Boundary Audit",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This public-safe audit narrows ngtcp2's role in the implementation survey. It explains why ngtcp2 is strong C-library migration/path-validation evidence while still not being browser or managed-deployment continuity evidence.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| implementation | `{audit['implementation']}` |",
        f"| source repository | [{audit['source_repository']}]({audit['source_repository']}) |",
        f"| source commit | `{audit['source_commit']}` |",
        f"| local clone observed | `{clone['observed']}` |",
        f"| local clone commit | `{clone['commit'] or '-'}` |",
        f"| local clone matches audit commit | `{clone['matches_expected_commit']}` |",
        f"| evidence items | `{audit['evidence_item_count']}` |",
    ]
    for key, value in audit["summary"].items():
        lines.append(f"| {key.replace('_', ' ')} | `{value}` |")

    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            "| claim axis | result |",
            "| --- | --- |",
        ]
    )
    for key, value in audit["conclusion"].items():
        lines.append(f"| {key.replace('_', ' ')} | `{value}` |")

    lines.extend(
        [
            "",
            "## Evidence Table",
            "",
            "| id | source | topic | observation | implication |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for item in audit["evidence"]:
        source = f"[{item['source_path']}:{item['line']}]({item['url']})"
        lines.append(
            f"| `{item['evidence_id']}` | {source} | `{item['topic']}` | {item['observation']} | {item['implication']} |"
        )

    lines.extend(
        [
            "",
            "## Reporting Boundary",
            "",
            f"- Safe claim: {audit['safe_claim']}",
            f"- Unsafe claim: {audit['unsafe_claim']}",
            f"- Next non-iPhone gap: {audit['next_gap']}",
            "",
            "## Paper Interpretation",
            "",
            "1. ngtcp2 weakens an implementation-absence explanation because active client migration, passive rebinding validation, preferred-address policy, and qlog evidence are present.",
            "2. ngtcp2 strengthens the API-shape explanation because it exposes direct path-based APIs, while the companion runtime packet shows the official examples can complete a local HTTP/3 migration row.",
            "3. ngtcp2 is now the second C-library positive control beyond quic-go, but browser and managed-deployment claims remain separate gates.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(output: Path, json_output: Path, audit: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    markdown = emit_markdown(audit)
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        if forbidden in markdown:
            raise ValueError(f"forbidden public text found: {forbidden}")
    output.write_text(markdown, encoding="utf-8")
    json_output.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clone", default=DEFAULT_CLONE)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    audit = build_audit(Path(args.clone))
    write_outputs(Path(args.output), Path(args.json_output), audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
