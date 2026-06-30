#!/usr/bin/env python3
"""Build a public-safe dashboard that separates paper-ready CM claims from open gates."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_BUNDLE = "data/sanitized-evidence-bundle-20260630.json"
DEFAULT_DECISION = "data/non-iphone-next-research-decision-20260630.json"
DEFAULT_GATE_RERUN = "data/non-iphone-gate-rerun-20260701.json"
DEFAULT_DESKTOP_PATH = "data/noniphone-desktop-path-change-readiness-20260701.json"
DEFAULT_BRIDGE = "data/controlled-public-chrome-bridge-synthesis-20260701.json"
DEFAULT_QOE = "data/noniphone-workload-qoe-continuity-synthesis-20260701.csv"
DEFAULT_OUTPUT = "docs/results/noniphone-claim-readiness-dashboard-20260701.md"
DEFAULT_JSON_OUTPUT = "data/noniphone-claim-readiness-dashboard-20260701.json"


@dataclass(frozen=True)
class ClaimRow:
    id: str
    label: str
    status: str
    claim_allowed: bool
    claim_strength: str
    paper_ready_wording: str
    evidence_ids: tuple[str, ...]
    blockers: tuple[str, ...]
    do_not_claim: str
    next_action: str


CLAIM_ROWS = [
    ClaimRow(
        id="implementation_maturity",
        label="Implementation-level CM maturity",
        status="supported",
        claim_allowed=True,
        claim_strength="paper_ready_limited",
        paper_ready_wording="Several major QUIC implementations expose or test path validation, rebinding, migration, preferred-address, or related primitives; CM is not merely an unimplemented idea.",
        evidence_ids=(
            "cross-implementation-fresh-rerun",
            "quiche-path-event-observability",
            "lsquic-preferred-address-app-demo",
            "lsquic-nat-rebinding-app-demo",
            "quicly-focused-e2e-path-migration",
            "nginx-active-client-migration-runtime",
            "s2n-active-migration-api-audit",
            "mvfst-source-audit",
        ),
        blockers=(),
        do_not_claim="Do not claim every implementation exposes the same active migration API or production deployment behavior.",
        next_action="Use this as the paper's implementation-maturity foundation, then shift attention to deployment and browser gates.",
    ),
    ClaimRow(
        id="deployment_routing_boundary",
        label="Deployment and routing boundary",
        status="partially_supported",
        claim_allowed=True,
        claim_strength="paper_ready_with_caveat",
        paper_ready_wording="Deployment support is separate from library support: CID-aware routing can preserve backend continuity, while proxy or mismatched-CID controls show that HTTP/3 availability alone is insufficient.",
        evidence_ids=(
            "aws-nlb-cid-aware-positive-control",
            "aws-nlb-negative-controls",
            "aws-nlb-http3-workload",
            "haproxy-http3-negative-control",
            "s2n-nlb-cid-provider-proof",
            "s2n-nlb-live-readiness",
            "aws-s2n-nlb-live-runner",
            "nginx-quic-bpf-readiness",
            "nginx-quic-bpf-linux-runner",
        ),
        blockers=(
            "AWS NLB+s2n live forwarding is still credential-blocked.",
            "nginx quic_bpf production-routing validation requires a Linux/root or capability environment.",
        ),
        do_not_claim="Do not claim live AWS NLB+s2n migration success, CDN end-to-end CM, or Linux quic_bpf success from the current host.",
        next_action="Refresh AWS credentials first; if unavailable, run nginx quic_bpf or OpenLiteSpeed on a suitable Linux/EC2 host.",
    ),
    ClaimRow(
        id="local_chrome_workload_controls",
        label="Local Chrome workload controls",
        status="supported_local_only",
        claim_allowed=True,
        claim_strength="local_control_only",
        paper_ready_wording="Local Chrome forced-H3 UDP-rebinding controls show that range/download and upload workloads can produce cleaner single-session evidence than streaming-like workloads, which require QoE and session-churn framing.",
        evidence_ids=(
            "chrome-local-rebinding-workload-controls",
            "chrome-desktop-noniphone-media-local-refresh",
            "chrome-desktop-noniphone-range-local-refresh",
            "chrome-desktop-noniphone-upload-local-refresh",
            "chrome-desktop-noniphone-musiclike-local-refresh",
            "chrome-desktop-noniphone-buffered-media-local-refresh",
            "noniphone-workload-qoe-synthesis",
        ),
        blockers=(
            "Local UDP rebinding is not the same as public Wi-Fi/LTE or desktop interface handover.",
        ),
        do_not_claim="Do not call local forced-H3 rebinding a public browser handover result.",
        next_action="Use local rows to prioritize public workload order: range/upload first, buffered/music-like streaming with QoE metrics after.",
    ),
    ClaimRow(
        id="controlled_public_chrome_cm",
        label="Controlled-public Chrome CM success",
        status="not_supported_yet",
        claim_allowed=False,
        claim_strength="gap_evidence",
        paper_ready_wording="The current controlled-public Chrome corpus supports a negative/gap statement: no tracked active row combines application completion, client active path change, server tuple change, qlog path validation, and single target Chrome QUIC session.",
        evidence_ids=(
            "controlled-public-chrome-bridge-synthesis",
            "user-provided-public-origin-readiness",
            "noniphone-desktop-path-change-readiness",
            "noniphone-public-workload-trial-packet",
            "controlled-public-origin-workload-deploy-packet",
            "non-iphone-gate-rerun-20260701",
        ),
        blockers=(
            "No controlled-public strong CM success row exists yet.",
            "The user-provided public HTTPS origin is not H3 Alt-Svc ready.",
            "The current desktop host lacks a non-iPhone active secondary path.",
        ),
        do_not_claim="Do not claim Chrome public-origin single-session Connection Migration success.",
        next_action="Open both gates: deploy an H3 Alt-Svc public origin and connect a non-iPhone secondary desktop path, then run the public workload trial packet.",
    ),
    ClaimRow(
        id="aws_s2n_live_claim",
        label="AWS NLB + s2n live claim",
        status="blocked",
        claim_allowed=False,
        claim_strength="readiness_only",
        paper_ready_wording="The repository has a dedicated AWS NLB+s2n runner and local CID-provider prerequisite evidence, but the current live AWS gate is blocked before resource creation.",
        evidence_ids=(
            "s2n-nlb-cid-provider-proof",
            "s2n-nlb-live-readiness",
            "aws-s2n-nlb-live-runner",
            "s2n-active-migration-api-audit",
            "non-iphone-gate-rerun-20260701",
        ),
        blockers=("AWS identity classifies as invalid_client_token on the current host.",),
        do_not_claim="Do not claim live AWS NLB+s2n forwarding or active migration success.",
        next_action="Refresh AWS credentials and run the fail-closed live forwarding runner before any active migration variant.",
    ),
    ClaimRow(
        id="safari_cross_browser_claim",
        label="Safari cross-browser feasibility",
        status="blocked_feasibility",
        claim_allowed=False,
        claim_strength="readiness_only",
        paper_ready_wording="Safari is currently a feasibility follow-up, not an evidence pillar: binaries exist, but WebDriver session creation is blocked by the local Safari remote-automation setting.",
        evidence_ids=("safari-webdriver-session-readiness", "non-iphone-gate-rerun-20260701"),
        blockers=("Safari Allow remote automation is not enabled.",),
        do_not_claim="Do not claim Safari H3 baseline, Safari handover, or Safari browser-internal session continuity.",
        next_action="Enable Safari Allow remote automation, rerun the session smoke, then treat Safari results as lower-ceiling feasibility evidence.",
    ),
    ClaimRow(
        id="streaming_qoe_claim",
        label="Streaming/QoE framing",
        status="supported_as_boundary",
        claim_allowed=True,
        claim_strength="paper_ready_local_qoe_boundary",
        paper_ready_wording="Streaming workloads should be reported with QoE and session attribution, because playback completion can hide rebuffering, retry/reconnect behavior, and multiple target QUIC sessions.",
        evidence_ids=(
            "chrome-desktop-noniphone-musiclike-local-refresh",
            "chrome-desktop-noniphone-buffered-media-local-refresh",
            "noniphone-workload-qoe-synthesis",
        ),
        blockers=("Public streaming handover has not been executed.",),
        do_not_claim="Do not claim zero-impact video or music continuity, or single-session CM, from completion alone.",
        next_action="For public trials, collect startup delay, rebuffer count, retry count, session count, tuple change, qlog path validation, and task completion together.",
    ),
    ClaimRow(
        id="paper_scope_decision",
        label="Paper scope decision",
        status="partial_ready",
        claim_allowed=True,
        claim_strength="scope_ready",
        paper_ready_wording="A defensible paper can now argue that CM maturity is multi-layered: implementation primitives are common, deployment/browser continuity remains gated, and workload-level continuity must be separated from transport/session continuity.",
        evidence_ids=(
            "cross-implementation-fresh-rerun",
            "haproxy-http3-negative-control",
            "controlled-public-chrome-bridge-synthesis",
            "noniphone-workload-qoe-synthesis",
            "non-iphone-gate-rerun-20260701",
        ),
        blockers=(
            "The paper should not yet present a successful public/browser CM result.",
            "The paper should not yet present live AWS NLB+s2n success.",
        ),
        do_not_claim="Do not frame the current work as proving that HTTP/3 CM guarantees web task continuity.",
        next_action="Ask for professor decision: either open AWS/public-origin/path gates for stronger positive results, or scope the paper around maturity gaps and conservative negative controls.",
    ),
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def evidence_index(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item.get("id", ""): item for item in bundle.get("items", [])}


def derive_context(
    gate: dict[str, Any],
    desktop_path: dict[str, Any],
    bridge: dict[str, Any],
    qoe_rows: list[dict[str, str]],
    decision: dict[str, Any],
) -> dict[str, Any]:
    return {
        "open_gates": gate.get("open_gates", []),
        "all_key_gates_blocked": gate.get("all_key_gates_blocked"),
        "aws_identity_classification": gate.get("aws", {}).get("identity_classification", "-"),
        "safari_session_ready": gate.get("safari", {}).get("safari_webdriver_session_ready", "-"),
        "public_origin_h3_alt_svc": gate.get("public_origin", {}).get("has_h3_alt_svc", "-"),
        "noniphone_desktop_path_ready": desktop_path.get("noniphone_desktop_path_ready", "-"),
        "noniphone_secondary_interfaces": desktop_path.get("noniphone_secondary_interfaces", []),
        "controlled_public_trial_count": bridge.get("trial_count", 0),
        "controlled_public_active_count": bridge.get("active_network_change_count", 0),
        "controlled_public_h3_baseline_count": bridge.get("baseline_h3_confirmed_count", 0),
        "controlled_public_strong_cm_success_count": bridge.get("strong_cm_success_count", 0),
        "qoe_workload_groups": [row.get("workload_group", "-") for row in qoe_rows],
        "next_decision_runnable_now": decision.get("runnable_now", []),
        "next_decision_blocked_track_count": decision.get("blocked_track_count", "-"),
    }


def build_dashboard(
    bundle_path: Path = Path(DEFAULT_BUNDLE),
    decision_path: Path = Path(DEFAULT_DECISION),
    gate_path: Path = Path(DEFAULT_GATE_RERUN),
    desktop_path: Path = Path(DEFAULT_DESKTOP_PATH),
    bridge_path: Path = Path(DEFAULT_BRIDGE),
    qoe_path: Path = Path(DEFAULT_QOE),
) -> dict[str, Any]:
    bundle = read_json(bundle_path)
    decision = read_json(decision_path)
    gate = read_json(gate_path)
    desktop = read_json(desktop_path)
    bridge = read_json(bridge_path)
    qoe_rows = read_csv_rows(qoe_path)
    evidence = evidence_index(bundle)

    rows: list[dict[str, Any]] = []
    for claim in CLAIM_ROWS:
        record = asdict(claim)
        ids = list(claim.evidence_ids)
        found = [evidence_id for evidence_id in ids if evidence_id in evidence]
        missing = [evidence_id for evidence_id in ids if evidence_id not in evidence]
        record["evidence_ids"] = ids
        record["evidence_found"] = found
        record["evidence_missing"] = missing
        rows.append(record)

    claim_allowed = [row["id"] for row in rows if row["claim_allowed"]]
    claim_blocked = [row["id"] for row in rows if not row["claim_allowed"]]
    context = derive_context(gate, desktop, bridge, qoe_rows, decision)
    missing_by_claim = {
        row["id"]: row["evidence_missing"]
        for row in rows
        if row["evidence_missing"]
    }

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "source_paths": {
            "bundle": bundle_path.as_posix(),
            "decision": decision_path.as_posix(),
            "gate_rerun": gate_path.as_posix(),
            "desktop_path": desktop_path.as_posix(),
            "controlled_public_bridge": bridge_path.as_posix(),
            "qoe_synthesis": qoe_path.as_posix(),
        },
        "source_exists": {
            "bundle": bundle_path.exists(),
            "decision": decision_path.exists(),
            "gate_rerun": gate_path.exists(),
            "desktop_path": desktop_path.exists(),
            "controlled_public_bridge": bridge_path.exists(),
            "qoe_synthesis": qoe_path.exists(),
        },
        "context": context,
        "summary": {
            "claim_count": len(rows),
            "claim_allowed_count": len(claim_allowed),
            "claim_blocked_count": len(claim_blocked),
            "claim_allowed": claim_allowed,
            "claim_blocked": claim_blocked,
            "bundle_item_count": bundle.get("item_count", 0),
            "missing_evidence_by_claim": missing_by_claim,
            "paper_decision": "The current corpus is ready for a conservative maturity/gap report, but not for Chrome public CM success or live AWS+s2n success claims.",
        },
        "claims": rows,
    }


def emit_markdown(dashboard: dict[str, Any]) -> str:
    summary = dashboard["summary"]
    context = dashboard["context"]
    lines = [
        "# non-iPhone Claim Readiness Dashboard",
        "",
        f"Generated: `{dashboard['generated']}`",
        "",
        "This dashboard is public-safe. It maps current evidence to paper wording boundaries without copying raw qlogs, pcaps, keylogs, NetLogs, private hosts, device IDs, account IDs, or credentials.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| claim count | `{summary['claim_count']}` |",
        f"| claim allowed count | `{summary['claim_allowed_count']}` |",
        f"| claim blocked count | `{summary['claim_blocked_count']}` |",
        f"| bundle item count | `{summary['bundle_item_count']}` |",
        f"| missing evidence by claim | `{summary['missing_evidence_by_claim']}` |",
        f"| paper decision | {summary['paper_decision']} |",
        "",
        "## Gate Context",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| open gates | `{context['open_gates']}` |",
        f"| all key gates blocked | `{context['all_key_gates_blocked']}` |",
        f"| AWS identity classification | `{context['aws_identity_classification']}` |",
        f"| Safari session ready | `{context['safari_session_ready']}` |",
        f"| public origin H3 Alt-Svc | `{context['public_origin_h3_alt_svc']}` |",
        f"| non-iPhone desktop path ready | `{context['noniphone_desktop_path_ready']}` |",
        f"| controlled-public active rows | `{context['controlled_public_active_count']}` |",
        f"| controlled-public H3 baselines | `{context['controlled_public_h3_baseline_count']}` |",
        f"| controlled-public strong CM successes | `{context['controlled_public_strong_cm_success_count']}` |",
        f"| QoE workload groups | `{context['qoe_workload_groups']}` |",
        "",
        "## Claim Readiness",
        "",
        "| claim | status | allowed | safe wording | blockers | do not claim | next action |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in dashboard["claims"]:
        blockers = "<br>".join(row["blockers"]) if row["blockers"] else "-"
        lines.append(
            "| `{id}`<br>{label} | `{status}` | `{allowed}` | {wording} | {blockers} | {do_not_claim} | {next_action} |".format(
                id=row["id"],
                label=row["label"],
                status=row["status"],
                allowed=str(row["claim_allowed"]).lower(),
                wording=row["paper_ready_wording"],
                blockers=blockers,
                do_not_claim=row["do_not_claim"],
                next_action=row["next_action"],
            )
        )

    lines.extend(
        [
            "",
            "## Evidence Trace",
            "",
            "| claim | evidence found | evidence missing |",
            "| --- | --- | --- |",
        ]
    )
    for row in dashboard["claims"]:
        lines.append(
            "| `{id}` | {found} | {missing} |".format(
                id=row["id"],
                found=", ".join(f"`{item}`" for item in row["evidence_found"]) or "-",
                missing=", ".join(f"`{item}`" for item in row["evidence_missing"]) or "-",
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The current corpus is strong enough for implementation-maturity, deployment-boundary, local workload, and QoE-framing claims.",
            "- It is not strong enough for controlled-public Chrome single-session CM success, Safari handover success, or live AWS NLB+s2n success.",
            "- The next professor decision should be whether to open external gates for positive public/browser/AWS results, or scope the paper around maturity gaps and conservative negative controls.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(output: Path, json_output: Path, dashboard: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(dashboard), encoding="utf-8")
    json_output.write_text(json.dumps(dashboard, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", default=DEFAULT_BUNDLE)
    parser.add_argument("--decision", default=DEFAULT_DECISION)
    parser.add_argument("--gate-rerun", default=DEFAULT_GATE_RERUN)
    parser.add_argument("--desktop-path", default=DEFAULT_DESKTOP_PATH)
    parser.add_argument("--controlled-public-bridge", default=DEFAULT_BRIDGE)
    parser.add_argument("--qoe-synthesis", default=DEFAULT_QOE)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    dashboard = build_dashboard(
        bundle_path=Path(args.bundle),
        decision_path=Path(args.decision),
        gate_path=Path(args.gate_rerun),
        desktop_path=Path(args.desktop_path),
        bridge_path=Path(args.controlled_public_bridge),
        qoe_path=Path(args.qoe_synthesis),
    )
    write_outputs(Path(args.output), Path(args.json_output), dashboard)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
