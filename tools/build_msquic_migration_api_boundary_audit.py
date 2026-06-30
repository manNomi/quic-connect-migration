#!/usr/bin/env python3
"""Build a public-safe MsQuic migration API/deployment boundary audit."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_MSQUIC_DIR = "/private/tmp/quic-cm-scan-repos/msquic"
DEFAULT_OUTPUT = "docs/results/msquic-migration-api-boundary-audit-20260701.md"
DEFAULT_JSON_OUTPUT = "data/msquic-migration-api-boundary-audit-20260701.json"

MSQUIC_COMMIT = "51d449b7d2deb553d6503591f72a8e62d1071054"
MSQUIC_BLOB = f"https://github.com/microsoft/msquic/blob/{MSQUIC_COMMIT}"


@dataclass(frozen=True)
class Evidence:
    id: str
    file: str
    lines: str
    symbol_or_topic: str
    observation: str
    implication: str

    @property
    def url(self) -> str:
        start = self.lines.split("-")[0]
        return f"{MSQUIC_BLOB}/{self.file}#L{start}"


EVIDENCE = [
    Evidence(
        id="load-balancing-mode-enum",
        file="src/inc/msquic.h",
        lines="90-96",
        symbol_or_topic="QUIC_LOAD_BALANCING_MODE",
        observation="Public API defines disabled, server-id-by-IP, and fixed-server-id load balancing modes.",
        implication="MsQuic has explicit CID/load-balancing support, but it is deployment configuration rather than per-connection migration proof.",
    ),
    Evidence(
        id="migration-setting-public-api",
        file="src/inc/msquic.h",
        lines="789-843",
        symbol_or_topic="QUIC_SETTINGS.MigrationEnabled",
        observation="The public settings struct exposes a MigrationEnabled bit.",
        implication="Client migration support is a first-class setting in the public API surface.",
    ),
    Evidence(
        id="default-migration-enabled",
        file="src/core/quicdef.h",
        lines="441-448",
        symbol_or_topic="QUIC_DEFAULT_MIGRATION_ENABLED",
        observation="Migration defaults to TRUE while load balancing defaults to disabled.",
        implication="The implementation is not missing migration support, but production LB routing is not enabled by default.",
    ),
    Evidence(
        id="settings-doc-migration-lb-boundary",
        file="docs/Settings.md",
        lines="51-55",
        symbol_or_topic="Settings documentation",
        observation="Docs list load balancing as disabled by default and client migration as enabled by default, requiring a cooperative load balancer or no load balancer.",
        implication="A paper claim must separate endpoint support from QUIC-aware deployment routing.",
    ),
    Evidence(
        id="deployment-doc-lb-configuration",
        file="docs/Deployment.md",
        lines="90-105",
        symbol_or_topic="Deployment load balancing modes",
        observation="Docs state load-balancing encoding is not enabled by default and describe modes 1 and 2.",
        implication="Managed or multi-server deployment evidence requires explicit LoadBalancingMode configuration and routing validation.",
    ),
    Evidence(
        id="local-address-connection-param",
        file="src/inc/msquic.h",
        lines="1035-1039",
        symbol_or_topic="QUIC_PARAM_CONN_LOCAL_ADDRESS",
        observation="The connection parameter table exposes local and remote address parameters.",
        implication="Applications can influence local address binding, but this is not the same shape as quic-go AddPath/Probe/Switch.",
    ),
    Evidence(
        id="settings-doc-local-address-limits",
        file="docs/Settings.md",
        lines="180-186",
        symbol_or_topic="QUIC_PARAM_CONN_LOCAL_ADDRESS docs",
        observation="Docs say local address is client-only and must be set before start or after handshake confirmation.",
        implication="There is a controlled local-address hook, but it has state and endpoint limits that must be respected in experiments.",
    ),
    Evidence(
        id="local-address-set-state-check",
        file="src/core/connection.c",
        lines="6380-6405",
        symbol_or_topic="Set QUIC_PARAM_CONN_LOCAL_ADDRESS",
        observation="The setter rejects server use and rejects use between start and handshake confirmation.",
        implication="MsQuic exposes a policy-constrained address-setting API rather than a generic active-path switch primitive.",
    ),
    Evidence(
        id="peer-address-changed-event-api",
        file="src/inc/msquic.h",
        lines="1344-1394",
        symbol_or_topic="QUIC_CONNECTION_EVENT_PEER_ADDRESS_CHANGED",
        observation="The public connection event enum includes local and peer address changed notifications.",
        implication="MsQuic has application-visible observability for tuple change events.",
    ),
    Evidence(
        id="peer-address-changed-implementation",
        file="src/core/connection.c",
        lines="5561-5568",
        symbol_or_topic="Indicate peer address changed",
        observation="Core connection code emits the peer-address-changed event when the remote path changes.",
        implication="Passive rebinding/migration can be observed at the application callback layer.",
    ),
    Evidence(
        id="nat-port-rebind-test",
        file="src/test/lib/HandshakeTest.cpp",
        lines="685-735",
        symbol_or_topic="QuicTestNatPortRebind",
        observation="The test changes the observed client port and waits for the server-side peer address change event.",
        implication="There is concrete NAT port rebinding test coverage.",
    ),
    Evidence(
        id="nat-address-rebind-test",
        file="src/test/lib/HandshakeTest.cpp",
        lines="739-790",
        symbol_or_topic="QuicTestNatAddrRebind",
        observation="The test changes the observed client address and waits for the peer address change event.",
        implication="There is concrete NAT address rebinding test coverage.",
    ),
]


FORBIDDEN_PUBLIC_TERMS = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AKIA",
    "ASIA",
    "arn:aws:iam::",
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


def local_clone_state(msquic_dir: Path) -> dict[str, str | bool]:
    if not msquic_dir.exists():
        return {
            "path": msquic_dir.as_posix(),
            "exists": False,
            "commit": "not-observed",
            "matches_audit_commit": "unknown",
        }
    result = run(["git", "-C", msquic_dir.as_posix(), "rev-parse", "HEAD"])
    commit = result.stdout.strip() if result.returncode == 0 else "unknown"
    return {
        "path": msquic_dir.as_posix(),
        "exists": True,
        "commit": commit,
        "matches_audit_commit": "yes" if commit == MSQUIC_COMMIT else "no",
    }


def build_audit(msquic_dir: Path) -> dict[str, Any]:
    evidence = [asdict(item) | {"url": item.url} for item in EVIDENCE]
    conclusion = {
        "migration_support_status": "implemented_and_tested_for_client_migration_rebinding",
        "active_api_boundary": "policy_constrained_local_address_control_not_quic_go_style_addpath_probe_switch",
        "deployment_boundary": "requires_no_load_balancer_or_cooperative_quic_aware_load_balancer",
        "observability_status": "public_address_changed_events_and_internal_logs_available",
        "paper_use": "Use MsQuic as production-relevant NAT rebinding and deployment-boundary evidence, not as the deepest controllable active-migration positive control.",
    }
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "implementation": "MsQuic",
        "source_commit": MSQUIC_COMMIT,
        "source_repository": "https://github.com/microsoft/msquic",
        "local_clone": local_clone_state(msquic_dir),
        "summary": {
            "evidence_items": len(evidence),
            "migration_enabled_default": "TRUE",
            "load_balancing_default": "QUIC_LOAD_BALANCING_DISABLED",
            "nat_rebinding_tests_present": "yes",
            "peer_address_changed_event_present": "yes",
            "local_address_param_present": "yes",
            "quic_go_style_addpath_probe_switch_public_api": "not_established_by_public_header_scan",
            "interpretation": "MsQuic is mature for client migration/NAT rebinding and QUIC-aware LB deployments, but its public control surface differs from quic-go's direct AddPath/Probe/Switch experiment API.",
        },
        "conclusion": conclusion,
        "evidence": evidence,
        "reporting_boundary": {
            "safe_claim": "MsQuic exposes migration settings, address-change events, constrained local-address control, and NAT rebinding tests.",
            "unsafe_claim": "MsQuic has the same direct application-triggered active migration API shape as quic-go or proves managed-LB continuity without a QUIC-aware routing experiment.",
            "next_non_iphone_gate": "If MsQuic must be promoted beyond maturity evidence, build a small client/server runtime harness that changes QUIC_PARAM_CONN_LOCAL_ADDRESS after handshake confirmation and captures peer-address-change plus payload continuity.",
        },
    }


def emit_markdown(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    conclusion = audit["conclusion"]
    local = audit["local_clone"]
    lines = [
        "# MsQuic Migration API Boundary Audit",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This public-safe audit narrows the remaining MsQuic question from the non-quic-go execution-depth audit: MsQuic clearly has migration/rebinding support, but the claim boundary differs from the quic-go active AddPath/Probe/Switch positive control.",
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
        f"| migration enabled default | `{summary['migration_enabled_default']}` |",
        f"| load balancing default | `{summary['load_balancing_default']}` |",
        f"| NAT rebinding tests present | `{summary['nat_rebinding_tests_present']}` |",
        f"| peer address changed event present | `{summary['peer_address_changed_event_present']}` |",
        f"| local address param present | `{summary['local_address_param_present']}` |",
        f"| quic-go-style AddPath/Probe/Switch API | `{summary['quic_go_style_addpath_probe_switch_public_api']}` |",
        f"| interpretation | {summary['interpretation']} |",
        "",
        "## Conclusion",
        "",
        "| claim axis | result |",
        "| --- | --- |",
        f"| migration support | `{conclusion['migration_support_status']}` |",
        f"| active API boundary | `{conclusion['active_api_boundary']}` |",
        f"| deployment boundary | `{conclusion['deployment_boundary']}` |",
        f"| observability | `{conclusion['observability_status']}` |",
        f"| paper use | {conclusion['paper_use']} |",
        "",
        "## Evidence Table",
        "",
        "| id | source | topic | observation | implication |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in audit["evidence"]:
        source = f"[{item['file']}:{item['lines']}]({item['url']})"
        lines.append(
            f"| `{item['id']}` | {source} | `{item['symbol_or_topic']}` | {item['observation']} | {item['implication']} |"
        )

    boundary = audit["reporting_boundary"]
    lines.extend(
        [
            "",
            "## Reporting Boundary",
            "",
            f"- Safe claim: {boundary['safe_claim']}",
            f"- Unsafe claim: {boundary['unsafe_claim']}",
            f"- Next non-iPhone gate: {boundary['next_non_iphone_gate']}",
            "",
            "## Paper Interpretation",
            "",
            "1. MsQuic weakens an `implementation absence` explanation because client migration is enabled by default and NAT rebind tests exist.",
            "2. MsQuic strengthens the `deployment friction` explanation because load-balancing support requires explicit mode selection and cooperative routing.",
            "3. MsQuic should not replace quic-go as the deepest controlled positive control unless a focused runtime harness proves local-address switching, peer-address-change observation, and payload continuity in one artifact.",
        ]
    )
    text = "\n".join(lines).rstrip() + "\n"
    for forbidden in FORBIDDEN_PUBLIC_TERMS:
        if forbidden in text:
            raise ValueError(f"public output contains forbidden term: {forbidden}")
    return text


def write_outputs(markdown_path: Path, json_path: Path, audit: dict[str, Any]) -> None:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(emit_markdown(audit), encoding="utf-8")
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--msquic-dir", default=DEFAULT_MSQUIC_DIR)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    audit = build_audit(Path(args.msquic_dir))
    write_outputs(Path(args.output), Path(args.json_output), audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
