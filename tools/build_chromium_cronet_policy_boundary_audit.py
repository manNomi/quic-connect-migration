#!/usr/bin/env python3
"""Build a public-safe Chromium/Cronet migration policy boundary audit."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_OUTPUT = "docs/results/chromium-cronet-policy-boundary-audit-20260701.md"
DEFAULT_JSON_OUTPUT = "data/chromium-cronet-policy-boundary-audit-20260701.json"

CHROMIUM_COMMIT = "fd49b92dc0dc7d4353e2e79ad155e43ca7947ab7"
CHROMIUM_BLOB = f"https://chromium.googlesource.com/chromium/src/+/{CHROMIUM_COMMIT}"
ANDROID_CRONET_OPTIONS_URL = (
    "https://developer.android.com/develop/connectivity/cronet/reference/"
    "org/chromium/net/ConnectionMigrationOptions"
)
ANDROID_PLATFORM_OPTIONS_URL = (
    "https://developer.android.com/reference/android/net/http/"
    "ConnectionMigrationOptions.Builder"
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


def chromium_url(file: str, lines: str) -> str:
    start = lines.split("-")[0]
    return f"{CHROMIUM_BLOB}/{file}#{start}"


EVIDENCE = [
    Evidence(
        id="quicparams-default-network-migration-policy",
        source="Chromium source",
        file="net/quic/quic_context.h",
        lines="176-184",
        topic="QuicParams network-change migration flags",
        observation=(
            "QuicParams includes migrate_sessions_on_network_change_v2 and "
            "migrate_sessions_early_v2 fields for network-change and poor-path migration policy."
        ),
        implication="Chromium has browser-stack policy knobs for migration; support is not a missing primitive.",
        url=chromium_url("net/quic/quic_context.h", "176-184"),
    ),
    Evidence(
        id="quicparams-idle-and-port-migration-policy",
        source="Chromium source",
        file="net/quic/quic_context.h",
        lines="186-194",
        topic="Idle and port migration flags",
        observation=(
            "QuicParams includes migrate_idle_sessions and allow_port_migration fields "
            "that control idle-session and port-change behavior."
        ),
        implication="Migration behavior is intentionally configurable rather than universally enabled.",
        url=chromium_url("net/quic/quic_context.h", "186-194"),
    ),
    Evidence(
        id="client-session-migrate-to-socket",
        source="Chromium source",
        file="net/quic/quic_chromium_client_session.h",
        lines="930-936",
        topic="QuicChromiumClientSession::MigrateToSocket",
        observation="QuicChromiumClientSession declares MigrateToSocket with new socket reader/writer ownership.",
        implication="The Chrome client stack has an internal socket migration primitive.",
        url=chromium_url("net/quic/quic_chromium_client_session.h", "930-936"),
    ),
    Evidence(
        id="client-session-network-connected-callback",
        source="Chromium source",
        file="net/quic/quic_chromium_client_session.h",
        lines="938-941",
        topic="Network connected callback",
        observation="OnNetworkConnected can migrate a session to a newly connected network when pending migration exists.",
        implication="Network-change notifications can drive migration decisions inside the browser stack.",
        url=chromium_url("net/quic/quic_chromium_client_session.h", "938-941"),
    ),
    Evidence(
        id="client-session-disconnected-default-callbacks",
        source="Chromium source",
        file="net/quic/quic_chromium_client_session.h",
        lines="943-949",
        topic="Disconnected and default-network callbacks",
        observation=(
            "The session class has callbacks for disconnected networks and new default networks, "
            "including a comment that migration occurs if appropriate."
        ),
        implication="A browser handover claim must prove that the runtime policy actually chose these paths.",
        url=chromium_url("net/quic/quic_chromium_client_session.h", "943-949"),
    ),
    Evidence(
        id="client-session-path-degrading-callback",
        source="Chromium source",
        file="net/quic/quic_chromium_client_session.h",
        lines="797-805",
        topic="Path degrading callback",
        observation="QuicChromiumClientSession overrides OnPathDegrading and related forward-progress callbacks.",
        implication="Chromium can react to path-quality degradation, not only hard interface loss.",
        url=chromium_url("net/quic/quic_chromium_client_session.h", "797-805"),
    ),
    Evidence(
        id="netlog-migration-mode-trigger",
        source="Chromium source",
        file="net/log/net_log_event_type_list.h",
        lines="3168-3177",
        topic="NetLog migration mode and trigger events",
        observation="NetLog defines QUIC_CONNECTION_MIGRATION_MODE and QUIC_CONNECTION_MIGRATION_TRIGGERED events.",
        implication="Mode evidence is useful but must be paired with trigger/session evidence before claiming migration.",
        url=chromium_url("net/log/net_log_event_type_list.h", "3168-3177"),
    ),
    Evidence(
        id="netlog-migration-success-failure",
        source="Chromium source",
        file="net/log/net_log_event_type_list.h",
        lines="3179-3192",
        topic="NetLog migration failure and success events",
        observation="NetLog defines QUIC_CONNECTION_MIGRATION_FAILURE and QUIC_CONNECTION_MIGRATION_SUCCESS.",
        implication="A strong browser artifact should contain success/failure evidence for the target session.",
        url=chromium_url("net/log/net_log_event_type_list.h", "3179-3192"),
    ),
    Evidence(
        id="netlog-network-change-events",
        source="Chromium source",
        file="net/log/net_log_event_type_list.h",
        lines="3194-3228",
        topic="NetLog network-change migration events",
        observation=(
            "NetLog defines events for connected network, new default network, disconnected network, "
            "write error, waiting for a network, and path degrading."
        ),
        implication="Classifier logic should require event-chain evidence rather than tuple-change-only inference.",
        url=chromium_url("net/log/net_log_event_type_list.h", "3194-3228"),
    ),
    Evidence(
        id="netlog-probing-events",
        source="Chromium source",
        file="net/log/net_log_event_type_list.h",
        lines="3237-3247",
        topic="NetLog probing success/failure events",
        observation="NetLog defines post-probing migration success, failure, and waiting-for-network timeout events.",
        implication="Browser CM maturity includes observability for failed attempts, not just completed migrations.",
        url=chromium_url("net/log/net_log_event_type_list.h", "3237-3247"),
    ),
    Evidence(
        id="cronet-explicitly-disables-network-change-migration",
        source="Chromium source",
        file="components/cronet/url_request_context_config.cc",
        lines="918-924",
        topic="Cronet default network-change migration policy",
        observation=(
            "When QUIC is enabled, Cronet sets goaway_sessions_on_ip_change=false but explicitly "
            "sets migrate_sessions_on_network_change_v2=false."
        ),
        implication=(
            "Chromium-derived clients can suppress network-change migration by default, so Chrome, "
            "Cronet embedding, and Android platform behavior must be tested separately."
        ),
        url=chromium_url("components/cronet/url_request_context_config.cc", "918-924"),
    ),
    Evidence(
        id="android-cronet-connection-migration-options",
        source="Android Developers",
        file="ConnectionMigrationOptions",
        lines="n/a",
        topic="Cronet migration policy API",
        observation=(
            "The Android Cronet API exposes ConnectionMigrationOptions so applications can configure "
            "migration-related behavior."
        ),
        implication="Cronet migration is an embedding policy question, not a guaranteed browser-runtime outcome.",
        url=ANDROID_CRONET_OPTIONS_URL,
    ),
    Evidence(
        id="android-platform-connection-migration-options-builder",
        source="Android Developers",
        file="android.net.http.ConnectionMigrationOptions.Builder",
        lines="n/a",
        topic="Platform HTTP stack migration policy API",
        observation="The Android platform API exposes a builder for connection migration options.",
        implication="Android browser/app experiments must record client policy, platform stack, and defaults.",
        url=ANDROID_PLATFORM_OPTIONS_URL,
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
        "implementation": "Chromium Chrome Cronet",
        "source_repository": "https://chromium.googlesource.com/chromium/src",
        "source_commit": CHROMIUM_COMMIT,
        "source_ref": "refs/heads/main observed via git ls-remote on 2026-07-01",
        "summary": {
            "evidence_items": len(evidence),
            "client_socket_migration_hook_present": "yes",
            "network_change_policy_knobs_present": "yes",
            "netlog_migration_observability_present": "yes",
            "cronet_network_change_migration_default": "disabled_when_quic_enabled",
            "android_cronet_policy_api_present": "yes",
            "browser_runtime_handover_proven_by_this_audit": "no",
            "interpretation": (
                "Chromium/Cronet weakens an implementation-absence explanation because source hooks, "
                "policy knobs, and NetLog events exist; it strengthens the runtime-policy explanation "
                "because Cronet explicitly disables network-change migration by default in the inspected path."
            ),
        },
        "conclusion": {
            "transport_implementation_status": "client_stack_has_internal_migration_primitives",
            "runtime_policy_status": "policy_dependent_and_embedding_specific",
            "observability_status": "NetLog_can_expose_mode_trigger_success_failure_and_probing_events",
            "cronet_boundary": "network_change_migration_disabled_by_default_in_url_request_context_config",
            "paper_use": (
                "Use Chromium/Cronet as a high-usage client policy-boundary audit, not as proof that "
                "Chrome or Cronet migrated a live HTTP/3 browser workload."
            ),
        },
        "evidence": evidence,
        "reporting_boundary": {
            "safe_claim": (
                "Chromium/Cronet has migration hooks, policy knobs, and NetLog observability; "
                "Cronet's inspected default path disables network-change migration when QUIC is enabled."
            ),
            "unsafe_claim": (
                "Chrome browser, Android platform HTTP, or a Cronet-embedded app successfully performs "
                "single-session HTTP/3 Connection Migration in a live handover based on source hooks alone."
            ),
            "next_non_iphone_gate": (
                "When a non-iPhone secondary path or Android/Cronet device path is available, run a "
                "Chrome/Cronet active network-change trial and require target-session NetLog trigger/success, "
                "client path change, server tuple/qlog evidence, and workload completion."
            ),
        },
    }


def emit_markdown(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    conclusion = audit["conclusion"]
    lines = [
        "# Chromium/Cronet Policy Boundary Audit",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This public-safe audit tightens the browser/client part of the implementation survey. Chromium/Cronet is high-impact because Chrome and Android clients matter, but the source evidence must be separated from live browser handover evidence.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| implementation | `{audit['implementation']}` |",
        f"| source repository | [{audit['source_repository']}]({audit['source_repository']}) |",
        f"| source commit | `{audit['source_commit']}` |",
        f"| evidence items | `{summary['evidence_items']}` |",
        f"| socket migration hook present | `{summary['client_socket_migration_hook_present']}` |",
        f"| network-change policy knobs present | `{summary['network_change_policy_knobs_present']}` |",
        f"| NetLog migration observability present | `{summary['netlog_migration_observability_present']}` |",
        f"| Cronet network-change migration default | `{summary['cronet_network_change_migration_default']}` |",
        f"| Android Cronet policy API present | `{summary['android_cronet_policy_api_present']}` |",
        f"| browser runtime handover proven here | `{summary['browser_runtime_handover_proven_by_this_audit']}` |",
        f"| interpretation | {summary['interpretation']} |",
        "",
        "## Conclusion",
        "",
        "| claim axis | result |",
        "| --- | --- |",
        f"| transport implementation | `{conclusion['transport_implementation_status']}` |",
        f"| runtime policy | `{conclusion['runtime_policy_status']}` |",
        f"| observability | `{conclusion['observability_status']}` |",
        f"| Cronet boundary | `{conclusion['cronet_boundary']}` |",
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
            "1. Chromium/Cronet is too important to omit from the implementation survey because Chrome/Android client usage dominates the real deployment question.",
            "2. The source evidence shows migration capability and observability, so a pure `not implemented` explanation is too weak.",
            "3. Cronet's default policy boundary explains why a good transport mechanism can remain invisible to applications: a client runtime may deliberately suppress migration.",
            "4. The next defensible browser claim requires runtime artifacts, especially target-session NetLog trigger/success/failure evidence paired with server/qlog and workload completion evidence.",
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

    audit = build_audit()
    write_outputs(Path(args.output), Path(args.json_output), audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
