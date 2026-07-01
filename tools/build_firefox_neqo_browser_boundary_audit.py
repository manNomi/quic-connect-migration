#!/usr/bin/env python3
"""Build a public-safe Firefox/Neqo browser-runtime boundary audit."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_OUTPUT = "docs/results/firefox-neqo-browser-boundary-audit-20260701.md"
DEFAULT_JSON_OUTPUT = "data/firefox-neqo-browser-boundary-audit-20260701.json"

NEQO_COMMIT = "3ba227d37f46a5684e984ead831b73344d9fec63"
NEQO_BLOB = f"https://github.com/mozilla/neqo/blob/{NEQO_COMMIT}"
FIREFOX_NEQO_GLUE_URL = (
    "https://github.com/mozilla-firefox/firefox/blob/main/netwerk/socket/neqo_glue/Cargo.toml"
)


@dataclass(frozen=True)
class Evidence:
    id: str
    source: str
    file: str
    lines: str
    topic: str
    observation: str
    implication: str
    url: str


def neqo_url(file: str, lines: str) -> str:
    start = lines.split("-")[0]
    return f"{NEQO_BLOB}/{file}#L{start}"


EVIDENCE = [
    Evidence(
        id="neqo-firefox-implementation-claim",
        source="Neqo README",
        file="README.md",
        lines="5-12",
        topic="Firefox adjacency",
        observation=(
            "Neqo describes itself as the QUIC implementation used by Mozilla in Firefox and "
            "other products, and as a QUIC transport, HTTP/3, and QPACK library."
        ),
        implication=(
            "Neqo is a legitimate Firefox-adjacent implementation maturity target, not an "
            "unrelated toy stack."
        ),
        url=neqo_url("README.md", "5-12"),
    ),
    Evidence(
        id="neqo-server-experimental-boundary",
        source="Neqo README",
        file="README.md",
        lines="15-24",
        topic="Server maturity boundary",
        observation="The README warns that Neqo server functionality is experimental and not for production use.",
        implication=(
            "A Neqo server result should be treated as test/debug implementation evidence, not "
            "production Firefox-server deployment evidence."
        ),
        url=neqo_url("README.md", "15-24"),
    ),
    Evidence(
        id="neqo-firefox-version-linkage",
        source="Neqo SECURITY",
        file="SECURITY.md",
        lines="7-17",
        topic="Firefox release linkage",
        observation=(
            "Neqo support is tied to Firefox versions where it has landed, and active Firefox "
            "versions point to vendored Neqo versions."
        ),
        implication=(
            "Firefox relevance is real, but the exact browser behavior depends on the Firefox "
            "vendored version and runtime integration."
        ),
        url=neqo_url("SECURITY.md", "7-17"),
    ),
    Evidence(
        id="neqo-firefox-local-server-recipe",
        source="Neqo README",
        file="README.md",
        lines="154-162",
        topic="Firefox test integration recipe",
        observation=(
            "The README includes a recipe for connecting Firefox to a local neqo-server with "
            "HTTP/3 testing preferences and optional logging/profiling."
        ),
        implication=(
            "Firefox-adjacent runtime experiments are possible, but they require explicit "
            "browser setup and separate execution artifacts."
        ),
        url=neqo_url("README.md", "154-162"),
    ),
    Evidence(
        id="neqo-firefox-vendor-glue",
        source="Neqo README",
        file="README.md",
        lines="179-186",
        topic="Firefox vendoring path",
        observation=(
            "The Neqo release process tells maintainers to update Firefox-side neqo dependency "
            "versions in neqo_glue and HTTP/3 test-server Cargo manifests."
        ),
        implication=(
            "The Firefox browser claim must bind the observed Firefox build/version, not only the "
            "standalone Neqo repository commit."
        ),
        url=neqo_url("README.md", "179-186"),
    ),
    Evidence(
        id="neqo-migrate-api",
        source="Neqo source",
        file="neqo-transport/src/connection/mod.rs",
        lines="2068-2140",
        topic="Active migration API",
        observation=(
            "Connection::migrate accepts local/remote address choices, supports immediate or "
            "post-probe migration, rejects disabled/invalid migration, probes the candidate path, "
            "and emits a path-migrated event."
        ),
        implication="Neqo has explicit transport-level active migration machinery.",
        url=neqo_url("neqo-transport/src/connection/mod.rs", "2068-2140"),
    ),
    Evidence(
        id="neqo-peer-migration-handler",
        source="Neqo source",
        file="neqo-transport/src/connection/mod.rs",
        lines="2198-2218",
        topic="Passive peer migration handling",
        observation="Server-side peer migration handling can ensure a permanent path, update path state, and emit migration events.",
        implication="Neqo covers passive migration/rebinding handling as well as client-initiated migration.",
        url=neqo_url("neqo-transport/src/connection/mod.rs", "2198-2218"),
    ),
    Evidence(
        id="neqo-path-probe-and-primary-selection",
        source="Neqo source",
        file="neqo-transport/src/path.rs",
        lines="200-220",
        topic="Probe before path promotion",
        observation=(
            "The path manager starts ECN validation, promotes a path immediately only when forced "
            "or already valid, otherwise records it as a migration target and probes it."
        ),
        implication="Neqo implements the path-validation gate expected by QUIC migration.",
        url=neqo_url("neqo-transport/src/path.rs", "200-220"),
    ),
    Evidence(
        id="neqo-path-response-validation",
        source="Neqo source",
        file="neqo-transport/src/path.rs",
        lines="792-801",
        topic="PATH_RESPONSE validation",
        observation=(
            "A matching PATH_RESPONSE marks the path valid and can trigger the next probe stage "
            "for full-MTU probing."
        ),
        implication="The implementation has explicit validation state for a candidate migrated path.",
        url=neqo_url("neqo-transport/src/path.rs", "792-801"),
    ),
    Evidence(
        id="neqo-qlog-transport-parameters",
        source="Neqo source",
        file="neqo-transport/src/qlog.rs",
        lines="59-99",
        topic="qlog for migration-related transport parameters",
        observation=(
            "Neqo qlog output includes disable_active_migration and preferred_address transport "
            "parameter fields."
        ),
        implication="Neqo has observability hooks for migration-relevant policy/configuration evidence.",
        url=neqo_url("neqo-transport/src/qlog.rs", "59-99"),
    ),
    Evidence(
        id="neqo-rebinding-tests",
        source="Neqo tests",
        file="neqo-transport/src/connection/tests/migration.rs",
        lines="320-339",
        topic="NAT rebinding tests",
        observation=(
            "The migration tests include port rebinding and address+port rebinding, with and "
            "without zero-length connection IDs."
        ),
        implication="Neqo has focused tests for rebinding cases that matter in mobility-like scenarios.",
        url=neqo_url("neqo-transport/src/connection/tests/migration.rs", "320-339"),
    ),
    Evidence(
        id="neqo-immediate-migration-test",
        source="Neqo tests",
        file="neqo-transport/src/connection/tests/migration.rs",
        lines="428-446",
        topic="Immediate active migration test",
        observation="The immediate migration test calls migrate(..., true, ...) and expects a PathMigrated event and PATH_CHALLENGE.",
        implication="Neqo tests active migration at the transport layer.",
        url=neqo_url("neqo-transport/src/connection/tests/migration.rs", "428-446"),
    ),
    Evidence(
        id="neqo-graceful-migration-test",
        source="Neqo tests",
        file="neqo-transport/src/connection/tests/migration.rs",
        lines="638-720",
        topic="Graceful migration test",
        observation=(
            "The graceful migration test probes the new path, keeps data on the old path until "
            "validation, switches after PATH_RESPONSE, and confirms server traffic on the new path."
        ),
        implication=(
            "Neqo's test suite covers more than API presence; it checks path validation and data "
            "continuity across the migration sequence."
        ),
        url=neqo_url("neqo-transport/src/connection/tests/migration.rs", "638-720"),
    ),
    Evidence(
        id="neqo-preferred-address-test",
        source="Neqo tests",
        file="neqo-transport/src/connection/tests/migration.rs",
        lines="741-830",
        topic="Preferred address test",
        observation=(
            "The preferred-address test probes the server's preferred address after handshake, "
            "keeps data on the original path during probing, then sends data on the preferred path."
        ),
        implication="Neqo exercises the preferred-address migration path separately from generic rebinding.",
        url=neqo_url("neqo-transport/src/connection/tests/migration.rs", "741-830"),
    ),
    Evidence(
        id="neqo-disable-migration-test",
        source="Neqo tests",
        file="neqo-transport/src/connection/tests/migration.rs",
        lines="1011-1020",
        topic="disable_active_migration test",
        observation="The migration_disabled test expects InvalidMigration when the peer disables migration.",
        implication="Neqo tests the policy boundary where a peer forbids active migration.",
        url=neqo_url("neqo-transport/src/connection/tests/migration.rs", "1011-1020"),
    ),
    Evidence(
        id="neqo-pmtud-migration-test",
        source="Neqo tests",
        file="neqo-transport/src/connection/tests/pmtud.rs",
        lines="120-150",
        topic="PMTUD after migration",
        observation="The PMTUD test documents VPN-like migration to a lower MTU path and checks PMTUD behavior.",
        implication="Neqo covers post-migration path property changes, not just tuple switching.",
        url=neqo_url("neqo-transport/src/connection/tests/pmtud.rs", "120-150"),
    ),
    Evidence(
        id="neqo-ecn-migration-test",
        source="Neqo tests",
        file="neqo-transport/src/connection/tests/ecn.rs",
        lines="436-456",
        topic="ECN after migration",
        observation="The ECN migration tests vary path marking behavior and assert migrated/non-migrated outcomes.",
        implication="Neqo tests migration interaction with path-quality transport state.",
        url=neqo_url("neqo-transport/src/connection/tests/ecn.rs", "436-456"),
    ),
    Evidence(
        id="neqo-local-rerun-summary",
        source="Current research repo",
        file="docs/results/implementation-rerun-results-20260630.md",
        lines="37-40",
        topic="Fresh local rerun result",
        observation=(
            "The research rerun records cargo test -p neqo-transport migration at commit "
            f"{NEQO_COMMIT} with 53 passed and 0 failed."
        ),
        implication="The study has local test-suite evidence for Neqo, but this is not a Firefox browser handover row.",
        url="https://github.com/manNomi/quic-connect-migration/blob/docs/quinn-neqo-rerun-20260630/docs/results/implementation-rerun-results-20260630.md",
    ),
]


FORBIDDEN_PUBLIC_TERMS = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AKIA",
    "ASIA",
    "arn:aws:" + "iam::",
]


def build_audit() -> dict[str, Any]:
    evidence = [asdict(item) for item in EVIDENCE]
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "implementation": "Neqo",
        "browser_runtime": "Firefox",
        "source_repository": "https://github.com/mozilla/neqo",
        "source_commit": NEQO_COMMIT,
        "firefox_glue_reference": FIREFOX_NEQO_GLUE_URL,
        "summary": {
            "evidence_items": len(evidence),
            "firefox_adjacency_supported": "yes",
            "transport_migration_api_present": "yes",
            "passive_rebinding_handling_present": "yes",
            "preferred_address_tests_present": "yes",
            "migration_policy_boundary_tests_present": "yes",
            "qlog_migration_parameter_observability_present": "yes",
            "local_neqo_transport_migration_rerun": "53_passed_0_failed_recorded_20260630",
            "firefox_browser_runtime_handover_proven_by_this_audit": "no",
            "firefox_browser_runtime_rows_in_current_study": "absent",
            "interpretation": (
                "Neqo is strong Mozilla/Firefox-adjacent implementation maturity evidence, "
                "but standalone Neqo transport tests must not be promoted to a Firefox browser "
                "HTTP/3 network-change continuity claim."
            ),
        },
        "conclusion": {
            "implementation_status": "transport_migration_mature_in_source_and_tests",
            "firefox_status": "browser_runtime_claim_not_executed",
            "paper_use": (
                "Use Neqo to rebut a pure implementation-absence explanation for CM underuse; "
                "keep Firefox browser handover as a separate runtime gate."
            ),
        },
        "evidence": evidence,
        "reporting_boundary": {
            "safe_claim": (
                "Neqo has explicit migration API/source support, rebinding handling, preferred-address "
                "coverage, qlog transport-parameter observability, and a fresh local migration test rerun."
            ),
            "unsafe_claim": (
                "Firefox desktop or mobile has been shown by this study to preserve a single HTTP/3 "
                "browser session across Wi-Fi/cellular or interface handover."
            ),
            "next_non_iphone_gate": (
                "Install/run Firefox desktop against a controlled H3 origin or local neqo-server, capture "
                "Firefox/Necko logging plus server qlog/tuple evidence, and require target session attribution, "
                "client path change, server path validation, and workload completion before claiming Firefox CM."
            ),
        },
    }


def emit_markdown(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    conclusion = audit["conclusion"]
    lines = [
        "# Firefox/Neqo Browser Boundary Audit",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This public-safe audit tightens the Mozilla/Firefox part of the implementation survey. Neqo is important because it is Firefox-adjacent, but Neqo transport tests are not the same as a Firefox browser network-change experiment.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| implementation | `{audit['implementation']}` |",
        f"| browser runtime | `{audit['browser_runtime']}` |",
        f"| source repository | [{audit['source_repository']}]({audit['source_repository']}) |",
        f"| source commit | `{audit['source_commit']}` |",
        f"| Firefox glue reference | [{audit['firefox_glue_reference']}]({audit['firefox_glue_reference']}) |",
        f"| evidence items | `{summary['evidence_items']}` |",
        f"| Firefox adjacency supported | `{summary['firefox_adjacency_supported']}` |",
        f"| transport migration API present | `{summary['transport_migration_api_present']}` |",
        f"| passive rebinding handling present | `{summary['passive_rebinding_handling_present']}` |",
        f"| preferred-address tests present | `{summary['preferred_address_tests_present']}` |",
        f"| migration policy boundary tests present | `{summary['migration_policy_boundary_tests_present']}` |",
        f"| qlog migration parameter observability present | `{summary['qlog_migration_parameter_observability_present']}` |",
        f"| local Neqo transport migration rerun | `{summary['local_neqo_transport_migration_rerun']}` |",
        f"| Firefox browser runtime handover proven here | `{summary['firefox_browser_runtime_handover_proven_by_this_audit']}` |",
        f"| Firefox browser runtime rows in current study | `{summary['firefox_browser_runtime_rows_in_current_study']}` |",
        f"| interpretation | {summary['interpretation']} |",
        "",
        "## Conclusion",
        "",
        "| claim axis | result |",
        "| --- | --- |",
        f"| implementation status | `{conclusion['implementation_status']}` |",
        f"| Firefox status | `{conclusion['firefox_status']}` |",
        f"| paper use | {conclusion['paper_use']} |",
        "",
        "## Evidence Table",
        "",
        "| id | source | topic | observation | implication |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in audit["evidence"]:
        location = item["file"] if item["lines"] == "n/a" else f"{item['file']}:{item['lines']}"
        source = f"[{location}]({item['url']})"
        lines.append(
            f"| `{item['id']}` | {source} | `{item['topic']}` | {item['observation']} | {item['implication']} |"
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
            "1. Neqo should remain in the high-value implementation survey because it is the Mozilla/Firefox-adjacent QUIC stack.",
            "2. The fresh Neqo rerun and source audit are enough to say CM is implemented and tested in this stack.",
            "3. They are not enough to say Firefox browser requests survive a live network handover; that requires Firefox runtime logs and server-side path evidence.",
            "4. This distinction helps the paper answer why CM is underused: implementation support exists, but browser integration, policy, observability, and workload evidence still form separate gates.",
        ]
    )
    text = "\n".join(lines).rstrip() + "\n"
    for forbidden in FORBIDDEN_PUBLIC_TERMS:
        if forbidden in text:
            raise ValueError(f"public output contains forbidden term: {forbidden}")
    return text


def write_outputs(output: Path, json_output: Path, audit: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(audit), encoding="utf-8")
    json_output.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    write_outputs(Path(args.output), Path(args.json_output), build_audit())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
