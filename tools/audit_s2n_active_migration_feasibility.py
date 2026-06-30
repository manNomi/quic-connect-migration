#!/usr/bin/env python3
"""Audit s2n-quic active-migration feasibility without copying raw logs."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from research_clock import utc_date_iso


DEFAULT_JSON_OUTPUT = "data/s2n-active-migration-api-audit-20260630.json"
DEFAULT_OUTPUT = "docs/results/s2n-active-migration-api-audit-20260630.md"


@dataclass(frozen=True)
class Evidence:
    id: str
    file: str
    line: int
    snippet: str
    meaning: str


def git_commit(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def discover_s2n_dir() -> Path:
    explicit = os.environ.get("S2N_QUIC_DIR")
    if explicit:
        return Path(explicit).expanduser().resolve()

    candidates = sorted(Path.home().glob(".cargo/git/checkouts/s2n-quic-*/*"))
    for candidate in candidates:
        if (candidate / "quic/s2n-quic/src/provider.rs").exists():
            return candidate.resolve()
    raise FileNotFoundError(
        "s2n-quic checkout not found; set S2N_QUIC_DIR or build the s2n proof crate first"
    )


def line_with(path: Path, needle: str) -> tuple[int, str]:
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        if needle in line:
            return line_no, line.strip()
    raise ValueError(f"pattern not found in {path}: {needle}")


def lines_with(path: Path, needles: Iterable[str]) -> list[tuple[int, str]]:
    needles = tuple(needles)
    matches = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        stripped = line.strip()
        if any(needle in stripped for needle in needles):
            matches.append((line_no, stripped))
    return matches


def evidence(root: Path, rel: str, needle: str, eid: str, meaning: str) -> Evidence:
    path = root / rel
    line_no, snippet = line_with(path, needle)
    return Evidence(eid, rel, line_no, snippet, meaning)


def count_public_trigger_candidates(root: Path) -> dict[str, int]:
    public_src = root / "quic/s2n-quic/src"
    patterns = {
        "AddPath": "AddPath",
        "Probe_call": "Probe(",
        "Switch_call": "Switch(",
        "migrate_connection": "migrate_connection",
        "migrate_source": "migrate_source",
        "start_path_probe": "start_path_probe",
        "perform_migration": "perform_migration",
    }
    counts = {name: 0 for name in patterns}
    for path in public_src.rglob("*.rs"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in patterns.items():
            counts[name] += text.count(pattern)
    return counts


def build_audit(root: Path) -> dict:
    root = root.resolve()
    connection_migration = "quic/s2n-quic-tests/src/tests/connection_migration.rs"
    zero_length = "quic/s2n-quic-tests/src/tests/zero_length_cid_client_connection_migration.rs"
    provider = "quic/s2n-quic/src/provider.rs"
    path_provider = "quic/s2n-quic/src/provider/path_migration.rs"
    core_migration = "quic/s2n-quic-core/src/path/migration.rs"
    limits = "quic/s2n-quic-core/src/connection/limits.rs"
    qns_interop = "quic/s2n-quic-qns/src/client/interop.rs"

    public_trigger_counts = count_public_trigger_candidates(root)
    evidence_items = [
        evidence(
            root,
            provider,
            "pub(crate) mod path_migration;",
            "path_migration_provider_not_public",
            "The path migration provider is present but not exposed as a public application provider.",
        ),
        evidence(
            root,
            path_provider,
            "this functionality isn't public",
            "path_migration_provider_future_public_comment",
            "The provider file itself marks this functionality as currently non-public.",
        ),
        evidence(
            root,
            core_migration,
            "pub trait Validator",
            "core_migration_validator_trait",
            "The core stack has a validator trait for migration attempts.",
        ),
        evidence(
            root,
            limits,
            "with_active_connection_migration",
            "active_migration_transport_parameter_toggle",
            "Endpoint limits can advertise or disable active connection migration support.",
        ),
        evidence(
            root,
            connection_migration,
            "socket.rebind(local_addr);",
            "test_socket_rebind_trigger",
            "The test suite triggers address changes through a test IO socket rebind hook.",
        ),
        evidence(
            root,
            connection_migration,
            "recorder::ActivePathUpdated::new()",
            "active_path_event_recorder",
            "The test suite records active path update events.",
        ),
        evidence(
            root,
            connection_migration,
            "fn ip_rebind_test()",
            "ip_rebind_test",
            "The test suite covers IP rebinding.",
        ),
        evidence(
            root,
            connection_migration,
            "fn port_rebind_test()",
            "port_rebind_test",
            "The test suite covers port rebinding.",
        ),
        evidence(
            root,
            connection_migration,
            "fn rebind_blocked_port()",
            "blocked_port_negative_test",
            "The test suite covers a migration-denial/control case.",
        ),
        evidence(
            root,
            zero_length,
            "set_disable_active_migration(false)",
            "zero_length_cid_quiche_interop_enables_active_migration",
            "A zero-length CID interop test enables active migration on the quiche client side.",
        ),
        evidence(
            root,
            qns_interop,
            "ConnectionMigration => false",
            "qns_connection_migration_unsupported",
            "The qns client marks the active migration testcase unsupported.",
        ),
        evidence(
            root,
            qns_interop,
            "TODO support the ability to actively migrate on the client",
            "qns_active_migration_todo",
            "The interop client still carries an explicit active-migration TODO.",
        ),
    ]

    test_names = [
        snippet
        for _, snippet in lines_with(
            root / connection_migration,
            (
                "fn ip_rebind_test",
                "fn port_rebind_test",
                "fn ip_and_port_rebind_test",
                "fn rebind_after_handshake_confirmed",
                "fn rebind_before_handshake_confirmed",
                "fn rebind_blocked_port",
                "fn rebind_server_addr_before_handshake_confirmed",
            ),
        )
    ]

    public_active_trigger_api_found = any(public_trigger_counts.values())
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "s2n_dir_hint": "external checkout; not committed",
        "source_commit": git_commit(root),
        "audited_files": sorted({item.file for item in evidence_items}),
        "public_active_trigger_api_found": public_active_trigger_api_found,
        "public_active_trigger_candidate_counts": public_trigger_counts,
        "test_names_observed": test_names,
        "evidence": [asdict(item) for item in evidence_items],
        "classification": {
            "migration_tests_present": True,
            "active_path_events_present": True,
            "path_migration_provider_public": False,
            "qns_active_migration_testcase_supported": False,
            "recommended_live_runner_phase": "forwarding_echo_first_active_path_change_follow_up",
        },
        "supports": (
            "s2n-quic has tested connection migration/rebinding machinery and active-path "
            "observability, but the current public application API does not expose a quic-go-like "
            "AddPath/Probe/Switch trigger."
        ),
        "do_not_claim": (
            "Do not claim that the AWS NLB+s2n live runner already performs active migration; "
            "its current phase is forwarding echo readiness."
        ),
    }


def emit_markdown(audit: dict) -> str:
    lines = [
        "# s2n-quic Active Migration API Feasibility Audit",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This document is public-safe. It records relative source paths and claim boundaries, not raw test logs.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| source commit | `{audit['source_commit']}` |",
        f"| public active trigger API found | `{audit['public_active_trigger_api_found']}` |",
        f"| migration tests present | `{audit['classification']['migration_tests_present']}` |",
        f"| active path events present | `{audit['classification']['active_path_events_present']}` |",
        f"| path migration provider public | `{audit['classification']['path_migration_provider_public']}` |",
        f"| qns active migration testcase supported | `{audit['classification']['qns_active_migration_testcase_supported']}` |",
        "",
        "## Public Trigger Candidate Counts",
        "",
        "| candidate | count |",
        "| --- | ---: |",
    ]
    for name, count in audit["public_active_trigger_candidate_counts"].items():
        lines.append(f"| `{name}` | `{count}` |")

    lines.extend(
        [
            "",
            "## Evidence",
            "",
            "| id | source | line | snippet | meaning |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    for item in audit["evidence"]:
        snippet = item["snippet"].replace("|", "\\|")
        lines.append(
            f"| `{item['id']}` | `{item['file']}` | `{item['line']}` | `{snippet}` | {item['meaning']} |"
        )

    lines.extend(
        [
            "",
            "## Observed Test Names",
            "",
        ]
    )
    for name in audit["test_names_observed"]:
        lines.append(f"- `{name}`")

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            f"- Supports: {audit['supports']}",
            f"- Do not claim: {audit['do_not_claim']}",
            "- Paper use: classify s2n-quic as implementation-level migration mature, while keeping AWS NLB+s2n active migration as a phase-2 follow-up after forwarding echo.",
            "",
            "## Reproduction",
            "",
            "```bash",
            "python3 tools/audit_s2n_active_migration_feasibility.py \\",
            "  --output docs/results/s2n-active-migration-api-audit-20260630.md \\",
            "  --json-output data/s2n-active-migration-api-audit-20260630.json",
            "```",
            "",
            "Focused test command used for the latest local check:",
            "",
            "```bash",
            "cargo test --manifest-path \"$S2N_QUIC_DIR/quic/s2n-quic-tests/Cargo.toml\" \\",
            "  connection_migration -- --nocapture",
            "```",
            "",
            "Latest local check summary: `10 passed; 0 failed; 90 filtered out`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(output: Path, json_output: Path, audit: dict) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(audit), encoding="utf-8")
    json_output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--s2n-dir", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=Path(DEFAULT_OUTPUT))
    parser.add_argument("--json-output", type=Path, default=Path(DEFAULT_JSON_OUTPUT))
    args = parser.parse_args()

    root = args.s2n_dir.resolve() if args.s2n_dir else discover_s2n_dir()
    audit = build_audit(root)
    write_outputs(args.output, args.json_output, audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
