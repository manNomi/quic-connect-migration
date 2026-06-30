#!/usr/bin/env python3
"""Build a public-safe Quinn migration API boundary audit."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_OUTPUT = "docs/results/quinn-migration-api-boundary-audit-20260701.md"
DEFAULT_JSON_OUTPUT = "data/quinn-migration-api-boundary-audit-20260701.json"
DEFAULT_CLONE = "/private/tmp/quic-cm-scan-repos/quinn"
EXPECTED_COMMIT = "953b466747e667a9dfda0596b8051a0644f8333d"
GITHUB_BASE = f"https://github.com/quinn-rs/quinn/blob/{EXPECTED_COMMIT}"
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
        evidence_id="server-migration-default",
        source_path="quinn-proto/src/config/mod.rs",
        line=215,
        topic="ServerConfig migration policy",
        observation="ServerConfig documents client migration/NAT rebinding support and the default constructor sets migration to true.",
        implication="Quinn is not missing server-side support for client address changes; this weakens a pure implementation-absence explanation.",
    ),
    Evidence(
        evidence_id="server-migration-setter",
        source_path="quinn-proto/src/config/mod.rs",
        line=288,
        topic="Public server migration knob",
        observation="ServerConfig exposes a migration(value) setter that controls whether clients may migrate to new addresses.",
        implication="Migration is an explicit endpoint policy, so experiments must record whether the server permits it.",
    ),
    Evidence(
        evidence_id="connection-remote-address-doc",
        source_path="quinn/src/connection.rs",
        line=542,
        topic="Application-visible peer address",
        observation="Connection::remote_address documents that clients may change addresses when ServerConfig::migration is true.",
        implication="Applications can observe the peer address boundary, but this is not by itself a full workload-continuity proof.",
    ),
    Evidence(
        evidence_id="endpoint-rebind-api",
        source_path="quinn/src/endpoint.rs",
        line=265,
        topic="Endpoint socket rebind API",
        observation="Endpoint::rebind switches the endpoint to a new UDP socket and delegates to rebind_abstract.",
        implication="Quinn exposes a runtime mechanism that can trigger local-address change handling for all active connections.",
    ),
    Evidence(
        evidence_id="endpoint-rebind-scope",
        source_path="quinn/src/endpoint.rs",
        line=273,
        topic="Endpoint-wide rebind scope",
        observation="rebind_abstract updates the endpoint address live, affecting all active connections, and warns that unreachable connections may be lost.",
        implication="The public control surface is endpoint-wide socket rebind, not a per-connection AddPath/Probe/Switch API.",
    ),
    Evidence(
        evidence_id="abandoned-socket-during-active-migration",
        source_path="quinn/src/endpoint.rs",
        line=502,
        topic="Active migration receive path",
        observation="Endpoint state keeps an abandoned_socket during active migration until the first packet arrives on the new socket.",
        implication="The implementation accounts for in-flight traffic around endpoint rebind, but this remains a library/runtime behavior claim.",
    ),
    Evidence(
        evidence_id="migration-forbidden-drop",
        source_path="quinn-proto/src/connection/mod.rs",
        line=1103,
        topic="Remote migration policy enforcement",
        observation="A datagram from a new remote address is dropped when the side does not allow remote migration.",
        implication="Quinn enforces the disable/allow migration boundary, so experiments must avoid assuming every tuple change is accepted.",
    ),
    Evidence(
        evidence_id="server-migration-handler",
        source_path="quinn-proto/src/connection/mod.rs",
        line=3080,
        topic="Server-side migration detection",
        observation="When a non-probing data packet arrives from a new remote address on a server connection, Quinn calls migrate and updates the remote CID.",
        implication="Quinn has server-side passive/client-migration machinery with linkability-conscious CID handling.",
    ),
    Evidence(
        evidence_id="migrate-path-validation-state",
        source_path="quinn-proto/src/connection/mod.rs",
        line=3100,
        topic="New path setup",
        observation="migrate creates a new PathData, distinguishes NAT-rebinding-like same-IP moves, queues PATH_CHALLENGE, and arms a path-validation timer.",
        implication="The implementation models new-path validation rather than blindly accepting the new tuple.",
    ),
    Evidence(
        evidence_id="local-address-changed-hook",
        source_path="quinn-proto/src/connection/mod.rs",
        line=3141,
        topic="Local address change hook",
        observation="local_address_changed updates the remote CID and sends a ping after a local address change.",
        implication="Active local-address migration exists internally through endpoint rebind, but it differs from quic-go's explicit path probe/switch control.",
    ),
    Evidence(
        evidence_id="path-challenge-transmit",
        source_path="quinn-proto/src/connection/mod.rs",
        line=3268,
        topic="PATH_CHALLENGE transmission",
        observation="Outgoing data-space packets on an unvalidated path include PATH_CHALLENGE and update frame statistics.",
        implication="Quinn has observable path-validation frame accounting for migration/rebinding evidence.",
    ),
    Evidence(
        evidence_id="path-response-transmit",
        source_path="quinn-proto/src/connection/mod.rs",
        line=3283,
        topic="PATH_RESPONSE transmission",
        observation="Queued path responses are emitted on the relevant path and counted in frame statistics.",
        implication="Responder-side path validation is implemented, not merely recognized in the frame parser.",
    ),
    Evidence(
        evidence_id="preferred-address-config",
        source_path="quinn-proto/src/config/mod.rs",
        line=297,
        topic="Preferred address configuration",
        observation="ServerConfig exposes preferred IPv4 and IPv6 address setters, and the docs say clients switch if reachable.",
        implication="Quinn supports the preferred-address migration mode separately from generic rebinding.",
    ),
    Evidence(
        evidence_id="preferred-address-cid-receive",
        source_path="quinn-proto/src/connection/mod.rs",
        line=3519,
        topic="Preferred-address CID handling",
        observation="When a preferred address is received, Quinn inserts the preferred-address connection ID as sequence 1.",
        implication="Preferred-address support has concrete CID state handling, not just transport-parameter parsing.",
    ),
    Evidence(
        evidence_id="path-frame-stats",
        source_path="quinn-proto/src/connection/stats.rs",
        line=117,
        topic="Frame-level observability",
        observation="FrameStats includes NEW_CONNECTION_ID, PATH_CHALLENGE, PATH_RESPONSE, and RETIRE_CONNECTION_ID fields.",
        implication="Quinn exposes useful in-process counters for migration/path-validation tests.",
    ),
    Evidence(
        evidence_id="proto-migration-test",
        source_path="quinn-proto/src/tests/mod.rs",
        line=1351,
        topic="Focused migration test",
        observation="The migration test changes the client address, sends data, observes the server remote address update, and checks immediate ACK behavior.",
        implication="There is focused protocol-level test coverage for client migration/rebinding behavior.",
    ),
    Evidence(
        evidence_id="mtud-after-migration-test",
        source_path="quinn-proto/src/tests/mod.rs",
        line=2455,
        topic="Post-migration path property test",
        observation="The MTUD migration test changes the client port, observes the server remote address update, and verifies MTU behavior on the new path.",
        implication="Quinn tests post-migration path characteristics, not only tuple recognition.",
    ),
    Evidence(
        evidence_id="preferred-address-test",
        source_path="quinn-proto/src/tests/mod.rs",
        line=3590,
        topic="Preferred-address test",
        observation="The preferred_address test ensures a connection can be made when the server advertises a preferred address.",
        implication="Preferred-address behavior has a test hook, but the test is not a full production/browser workload.",
    ),
    Evidence(
        evidence_id="runtime-rebind-receive-test",
        source_path="quinn/src/tests.rs",
        line=691,
        topic="Runtime endpoint rebind test",
        observation="The rebind_recv Tokio test connects client/server endpoints, rebinds the client UDP socket, and receives a server unidirectional stream.",
        implication="There is runtime-level evidence that endpoint rebind can preserve a simple Quinn stream workload.",
    ),
    Evidence(
        evidence_id="local-rerun-summary",
        source_path="docs/results/implementation-rerun-results-20260630.md",
        line=337,
        topic="Fresh local rerun",
        observation="The study records cargo test -p quinn-proto migration and cargo test -p quinn rebind as passing at the audited commit.",
        implication="The current corpus has local test execution evidence, but not a custom HTTP/3 or browser deployment row for Quinn.",
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
        "implementation": "Quinn",
        "source_repository": "https://github.com/quinn-rs/quinn",
        "source_commit": EXPECTED_COMMIT,
        "local_clone": clone,
        "evidence_item_count": len(items),
        "summary": {
            "server_migration_default": "enabled",
            "endpoint_rebind_api": "present_endpoint_wide",
            "passive_client_migration": "implemented_and_tested",
            "active_local_address_control": "endpoint_rebind_plus_internal_local_address_changed_hook",
            "preferred_address": "implemented_with_config_and_tests",
            "path_validation": "PATH_CHALLENGE_RESPONSE_state_and_stats",
            "fresh_local_tests": "quinn-proto migration 1 passed; quinn rebind 1 passed",
            "quic_go_style_addpath_probe_switch": "not_established",
            "browser_or_http3_runtime_row": "absent",
        },
        "conclusion": {
            "implementation_status": "mature_for_server_allowed_client_migration_and_endpoint_rebind",
            "api_boundary": "endpoint_wide_socket_rebind_not_per_connection_addpath_probe_switch",
            "paper_use": "Use Quinn as Rust-stack migration/rebind maturity evidence and optional runtime-follow-up target, not as browser/deployment continuity proof.",
        },
        "safe_claim": "Quinn exposes server migration policy, endpoint-wide socket rebind, preferred-address support, path-validation machinery, frame stats, and fresh local migration/rebind tests.",
        "unsafe_claim": "Quinn currently provides the same per-connection AddPath/Probe/Switch control shape as quic-go or proves HTTP/3 browser/deployment workload continuity in this study.",
        "next_gap": "If reviewers require a Rust runtime row, build a small Quinn echo/HTTP workload harness that calls Endpoint::rebind mid-stream and records frame stats, peer address change, and payload continuity.",
        "evidence": items,
    }


def emit_markdown(audit: dict[str, Any]) -> str:
    clone = audit["local_clone"]
    lines = [
        "# Quinn Migration API Boundary Audit",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This public-safe audit narrows Quinn's role in the implementation survey. It explains why Quinn is strong Rust-stack migration/rebind evidence while still not being the same positive-control shape as quic-go.",
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
            "1. Quinn weakens an implementation-absence explanation because migration policy, rebind, preferred address, and path validation are present and tested.",
            "2. Quinn strengthens the API-shape explanation because the public runtime trigger is endpoint-wide socket rebind, not quic-go-style per-connection path control.",
            "3. Quinn should stay in the non-quic-go maturity section unless a dedicated Quinn echo/HTTP runtime harness is added.",
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
