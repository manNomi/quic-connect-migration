#!/usr/bin/env python3
"""Build a public-safe contract for future controlled-public Chrome CM artifacts."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_OUTPUT = "docs/results/controlled-public-chrome-artifact-classifier-contract-20260701.md"
DEFAULT_JSON_OUTPUT = "data/controlled-public-chrome-artifact-classifier-contract-20260701.json"


@dataclass(frozen=True)
class Gate:
    name: str
    required_for: str
    artifact_source: str
    accept_when: str
    why: str


@dataclass(frozen=True)
class ResultClass:
    id: str
    claim_strength: str
    accept_when: str
    safe_claim: str
    do_not_claim: str


@dataclass(frozen=True)
class WorkloadRule:
    workload: str
    primary_use: str
    strong_cm_extra_requirement: str
    fallback_interpretation: str


GATES = [
    Gate(
        name="public_origin_https_ok",
        required_for="baseline_h3",
        artifact_source="public-origin-readiness.json",
        accept_when="HTTPS reachability is true and the target origin is controlled by the experiment.",
        why="A browser CM row is meaningless if the public origin itself is not reachable.",
    ),
    Gate(
        name="public_origin_alt_svc_h3",
        required_for="baseline_h3",
        artifact_source="public-origin-readiness.json",
        accept_when="Alt-Svc advertises h3 for the same WebPKI origin.",
        why="Chrome must be offered an ordinary HTTP/3 route without forced local-only overrides.",
    ),
    Gate(
        name="server_application_h3_confirmed",
        required_for="baseline_h3",
        artifact_source="server.json + server qlog",
        accept_when="Server request log and qlog show application HTTP/3 for the target workload.",
        why="H3 discovery alone is not enough; the application request must actually use HTTP/3.",
    ),
    Gate(
        name="chrome_target_quic_session_observed",
        required_for="baseline_h3",
        artifact_source="Chrome NetLog",
        accept_when="Chrome NetLog contains target-origin QUIC session or application QUIC job evidence.",
        why="Server-side H3 should be paired with browser-side attribution when Chrome is the client.",
    ),
    Gate(
        name="expected_workload_requests_reached",
        required_for="baseline_h3",
        artifact_source="server.json",
        accept_when="Expected workload request count is reached for the selected route.",
        why="A partial request sequence should not be promoted to workload continuity evidence.",
    ),
    Gate(
        name="application_completion_metric_true",
        required_for="active_strong_cm",
        artifact_source="DOM dump / application-summary",
        accept_when="The workload-specific completion metric is true.",
        why="Connection continuity claims must not ignore whether the user-visible task completed.",
    ),
    Gate(
        name="network_change_command_executed",
        required_for="active_strong_cm",
        artifact_source="network-change.json",
        accept_when="The non-iPhone network-change command is present and exits 0 or an explicitly accepted no-exit condition.",
        why="No-change rows are controls, not active migration trials.",
    ),
    Gate(
        name="client_active_path_changed",
        required_for="active_strong_cm",
        artifact_source="client-path-change-summary.json",
        accept_when="Before/after route snapshots classify an active client path change.",
        why="Server tuple movement alone can be misleading without client-side path evidence.",
    ),
    Gate(
        name="server_target_h3_tuple_changed",
        required_for="active_strong_cm",
        artifact_source="server.json",
        accept_when="Target H3 remote tuple count is greater than one for the workload.",
        why="A single observed tuple cannot prove path migration at the server endpoint.",
    ),
    Gate(
        name="server_qlog_path_validation",
        required_for="active_strong_cm",
        artifact_source="server qlog",
        accept_when="PATH_CHALLENGE and/or PATH_RESPONSE evidence is present for the active row.",
        why="Tuple changes without QUIC path validation are not enough for CM.",
    ),
    Gate(
        name="chrome_single_target_quic_session",
        required_for="active_strong_cm",
        artifact_source="Chrome NetLog",
        accept_when="Target-origin Chrome QUIC session count is exactly one.",
        why="Multiple target sessions indicate reconnect/session churn rather than single-session CM.",
    ),
]


RESULT_CLASSES = [
    ResultClass(
        id="public_h3_baseline_positive",
        claim_strength="baseline_only",
        accept_when="baseline_h3 gates pass and no active network-change command is part of the row.",
        safe_claim="The controlled public origin can serve the selected Chrome workload over HTTP/3.",
        do_not_claim="Do not claim Connection Migration from a no-change or baseline row.",
    ),
    ResultClass(
        id="strong_single_session_cm_positive",
        claim_strength="browser_deployment_positive",
        accept_when="All active_strong_cm gates pass in the same row.",
        safe_claim="For this controlled public Chrome workload, task completion coincided with client path change, server tuple change, qlog path validation, and a single Chrome target QUIC session.",
        do_not_claim="Do not generalize to mobile Wi-Fi/LTE, other browsers, CDNs, or all workloads.",
    ),
    ResultClass(
        id="application_recovery_or_reconnect",
        claim_strength="task_recovery_not_cm",
        accept_when="Application completion is true but Chrome target sessions are greater than one, retry is used, or qlog path validation is absent.",
        safe_claim="The application task recovered or completed under disruption.",
        do_not_claim="Do not describe this as single-session QUIC Connection Migration.",
    ),
    ResultClass(
        id="negative_control_record",
        claim_strength="gap_or_negative_control",
        accept_when="The row maps to a PASS_NEGATIVE_CONTROL classification from the source classifier.",
        safe_claim="The row documents a missing gate or conservative failure mode.",
        do_not_claim="Do not count it as public browser CM success.",
    ),
    ResultClass(
        id="not_claimable",
        claim_strength="not_claimable",
        accept_when="The row lacks the H3 precondition, server artifact, or workload completion evidence needed for interpretation.",
        safe_claim="No paper result claim should be made from this row.",
        do_not_claim="Do not use incomplete infrastructure rows as CM evidence.",
    ),
]


NEGATIVE_CONTROL_CLASSES = [
    "controlled_public_network_change_not_executed",
    "path_snapshot_missing",
    "no_client_active_path_change_observed",
    "application_task_incomplete_without_quic_path_validation",
    "application_task_incomplete_despite_quic_path_validation",
    "application_task_failed_without_quic_path_validation",
    "application_task_failed_despite_quic_path_validation",
    "tuple_changed_without_path_validation",
    "reconnect_or_multiple_sessions",
    "path_validation_without_observed_tuple_change",
    "application_task_succeeded_without_observed_quic_migration",
    "no_path_change_after_trigger",
    "controlled_public_network_change_inconclusive",
]


WORKLOAD_RULES = [
    WorkloadRule(
        workload="large byte-range download",
        primary_use="First active public workload because byte accounting and completion are crisp.",
        strong_cm_extra_requirement="Range complete, expected byte count reached, no application retry, and one Chrome target QUIC session.",
        fallback_interpretation="If range completes with multiple sessions or no qlog path validation, report recovery/reconnect rather than CM.",
    ),
    WorkloadRule(
        workload="large upload",
        primary_use="Second active public workload because it tests client-sending continuity.",
        strong_cm_extra_requirement="Upload complete, received bytes match intended payload, and packet/path evidence is not inferred from request tuple alone.",
        fallback_interpretation="If upload completes but request-level tuple stays one, use qlog/NetLog/proxy evidence before making any path claim.",
    ),
    WorkloadRule(
        workload="buffered video playback",
        primary_use="QoE workload that can hide disruption behind startup buffer or rebuffering.",
        strong_cm_extra_requirement="Playback complete plus startup delay, rebuffer count, target session count, tuple change, and qlog path validation.",
        fallback_interpretation="Playback completion alone is QoE/recovery evidence, not CM.",
    ),
    WorkloadRule(
        workload="music-like segment",
        primary_use="Streaming-like boundary workload that separates retry recovery from transport continuity.",
        strong_cm_extra_requirement="Segment completion without retry/reconnect and with all active strong CM gates in one row.",
        fallback_interpretation="Retry-based segment completion should be framed as application recovery.",
    ),
]


def contract() -> dict[str, Any]:
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "contract_id": "controlled-public-chrome-artifact-classifier-contract",
        "source_classifier": "tools/classify_controlled_public_h3_network_change.py",
        "source_trial_packet": "docs/results/noniphone-public-workload-trial-packet-20260701.md",
        "source_bridge_synthesis": "docs/results/controlled-public-chrome-bridge-synthesis-20260701.md",
        "baseline_h3_required_gates": [asdict(gate) for gate in GATES if gate.required_for == "baseline_h3"],
        "active_strong_cm_required_gates": [asdict(gate) for gate in GATES if gate.required_for == "active_strong_cm"],
        "negative_control_classes_to_preserve": NEGATIVE_CONTROL_CLASSES,
        "result_classes": [asdict(row) for row in RESULT_CLASSES],
        "workload_rules": [asdict(row) for row in WORKLOAD_RULES],
        "safe_boundary": {
            "baseline": "A public H3 baseline proves only that the controlled origin and Chrome can speak HTTP/3 for the workload.",
            "active": "A strong active CM row requires application completion, client active path change, server target tuple change, qlog path validation, and exactly one Chrome target QUIC session in the same row.",
            "streaming": "Streaming completion must be reported with QoE and session attribution; completion alone is not CM.",
        },
        "paper_use": "Run the source classifier on each future controlled-public Chrome row, then use this contract to decide whether the row is baseline evidence, strong single-session CM evidence, task recovery, or a negative control.",
    }


def emit_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Controlled Public Chrome Artifact Classifier Contract",
        "",
        f"Generated: `{result['generated']}`",
        "",
        "This public-safe contract defines how future controlled-public Chrome HTTP/3 workload artifacts must be interpreted before they are used as paper evidence.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| source classifier | `{result['source_classifier']}` |",
        f"| source trial packet | `{result['source_trial_packet']}` |",
        f"| source bridge synthesis | `{result['source_bridge_synthesis']}` |",
        f"| paper use | {result['paper_use']} |",
        "",
        "## Baseline H3 Gates",
        "",
        "| gate | artifact source | accept when | why |",
        "| --- | --- | --- | --- |",
    ]
    for gate in result["baseline_h3_required_gates"]:
        lines.append(f"| `{gate['name']}` | `{gate['artifact_source']}` | {gate['accept_when']} | {gate['why']} |")

    lines.extend(
        [
            "",
            "## Active Strong CM Gates",
            "",
            "| gate | artifact source | accept when | why |",
            "| --- | --- | --- | --- |",
        ]
    )
    for gate in result["active_strong_cm_required_gates"]:
        lines.append(f"| `{gate['name']}` | `{gate['artifact_source']}` | {gate['accept_when']} | {gate['why']} |")

    lines.extend(
        [
            "",
            "## Result Classes",
            "",
            "| class | claim strength | accept when | safe claim | do not claim |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for row in result["result_classes"]:
        lines.append(
            f"| `{row['id']}` | `{row['claim_strength']}` | {row['accept_when']} | {row['safe_claim']} | {row['do_not_claim']} |"
        )

    lines.extend(
        [
            "",
            "## Negative-Control Classes To Preserve",
            "",
            ", ".join(f"`{item}`" for item in result["negative_control_classes_to_preserve"]),
            "",
            "## Workload Rules",
            "",
            "| workload | primary use | strong CM extra requirement | fallback interpretation |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in result["workload_rules"]:
        lines.append(
            f"| {row['workload']} | {row['primary_use']} | {row['strong_cm_extra_requirement']} | {row['fallback_interpretation']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "1. No-change and baseline rows are infrastructure controls, not CM success rows.",
            "2. Application completion alone is insufficient because retry, reconnect, and multiple Chrome QUIC sessions can also complete a task.",
            "3. A strong public Chrome CM row must carry the full single-row evidence chain: task completion, client active path change, target H3 tuple change, qlog path validation, and one Chrome target QUIC session.",
            "4. Streaming rows must include startup delay, rebuffer count, retry count, completion, tuple/path evidence, and Chrome session count.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(output: Path, json_output: Path, result: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(result), encoding="utf-8")
    json_output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()
    result = contract()
    write_outputs(Path(args.output), Path(args.json_output), result)
    print(f"wrote {args.output}")
    print(f"wrote {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
