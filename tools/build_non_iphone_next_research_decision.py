#!/usr/bin/env python3
"""Build a public-safe decision brief for the next non-iPhone research step."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_EVIDENCE_BUNDLE = "data/sanitized-evidence-bundle-20260630.json"
DEFAULT_OUTPUT = "docs/results/non-iphone-next-research-decision-20260630.md"
DEFAULT_JSON_OUTPUT = "data/non-iphone-next-research-decision-20260630.json"


@dataclass(frozen=True)
class Track:
    rank: int
    id: str
    label: str
    current_state: str
    can_run_now: bool
    blocker: str
    needed_from_user_or_environment: str
    paper_value: str
    risk: str
    next_command_or_action: str
    supporting_evidence_ids: tuple[str, ...]
    decision: str


TRACKS = [
    Track(
        rank=1,
        id="aws-s2n-nlb-live-forwarding",
        label="AWS NLB + s2n-quic live forwarding echo",
        current_state="runner_ready_but_credential_blocked",
        can_run_now=False,
        blocker="AWS identity still classifies as invalid_client_token on the current host.",
        needed_from_user_or_environment="Refresh AWS credentials, then run the dedicated live NLB+s2n runner before designing active path-change.",
        paper_value="Highest: directly answers the deployment/AWS part of the professor decision without needing iPhone.",
        risk="The first live run only proves forwarding echo and target consistency; s2n public active migration API remains a separate limitation.",
        next_command_or_action="Refresh AWS credentials, then run `harness/scripts/run-aws-s2n-nlb-live-data-plane.sh`.",
        supporting_evidence_ids=(
            "s2n-nlb-cid-provider-proof",
            "s2n-nlb-live-readiness",
            "aws-s2n-nlb-live-runner",
            "s2n-active-migration-api-audit",
            "non-iphone-gate-rerun-20260701",
        ),
        decision="Primary next step once AWS credentials are valid.",
    ),
    Track(
        rank=2,
        id="chrome-controlled-public-workloads",
        label="Chrome desktop controlled-public media/range/upload handover",
        current_state="local_controls_pass_public_bridge_gap_user_origin_not_h3_ready",
        can_run_now=False,
        blocker="Tracked controlled-public Chrome rows are H3 baseline or negative-control evidence, not CM success; the user-provided public HTTPS origin is reachable but currently has no `Alt-Svc: h3`.",
        needed_from_user_or_environment="Configure the public domain or an AWS public origin with WebPKI TLS, HTTP/3, Alt-Svc, and workload endpoints, then run page-ready workload trials.",
        paper_value="High: bridges local browser evidence to real public-origin web workload continuity without iPhone.",
        risk="Even a PASS must prove single target QUIC session, path validation, path-change, and task completion together.",
        next_command_or_action="Prepare public origin, then run the controlled public Chrome media/range/upload wrappers.",
        supporting_evidence_ids=(
            "chromium-cronet-policy-evidence",
            "user-provided-public-origin-readiness",
            "non-iphone-gate-rerun-20260701",
            "controlled-public-chrome-bridge-synthesis",
            "chrome-desktop-noniphone-media-local-refresh",
            "chrome-desktop-noniphone-musiclike-local-refresh",
            "chrome-desktop-noniphone-buffered-media-local-refresh",
            "chrome-desktop-noniphone-range-local-refresh",
            "chrome-desktop-noniphone-upload-local-refresh",
            "noniphone-workload-qoe-synthesis",
            "noniphone-public-workload-trial-packet",
        ),
        decision="Best browser-facing next step after public origin is available.",
    ),
    Track(
        rank=3,
        id="nginx-quic-bpf-linux",
        label="nginx `quic_bpf` Linux production-routing check",
        current_state="linux_runner_ready_local_host_blocked",
        can_run_now=False,
        blocker="Current host is macOS; Linux/root/writable `/sys/fs/bpf` gate is required.",
        needed_from_user_or_environment="Run on Linux or EC2 with root/capability and writable bpffs.",
        paper_value="Medium-high: strengthens production server routing discussion and separates loopback runtime from deployment routing.",
        risk="It is server-side routing evidence, not browser handover evidence.",
        next_command_or_action="Run `harness/scripts/run-nginx-quic-bpf-linux-demo.sh` on a suitable Linux host.",
        supporting_evidence_ids=(
            "nginx-active-client-migration-runtime",
            "nginx-quic-bpf-readiness",
            "nginx-quic-bpf-linux-runner",
        ),
        decision="Good EC2/Linux follow-up if AWS is available but s2n live is deferred.",
    ),
    Track(
        rank=4,
        id="openlitespeed-production-like",
        label="OpenLiteSpeed production-like active-migration runtime",
        current_state="runner_ready_local_binary_disk_blocked",
        can_run_now=False,
        blocker="Local OpenLiteSpeed binary is missing and current macOS/disk conditions are not the right runtime environment.",
        needed_from_user_or_environment="Use Linux/EC2 or free/archive enough local artifact storage, then install/build OpenLiteSpeed.",
        paper_value="Medium: upgrades LSQUIC example app evidence toward a production-like server stack.",
        risk="Build/setup cost is high; result still remains server-stack evidence unless paired with browser workload.",
        next_command_or_action="Run `harness/scripts/run-openlitespeed-active-migration-demo.sh` on Linux/EC2.",
        supporting_evidence_ids=(
            "lsquic-preferred-address-app-demo",
            "lsquic-nat-rebinding-app-demo",
            "openlitespeed-runtime-runner",
        ),
        decision="Useful, but lower priority than AWS NLB+s2n for the professor's current decision.",
    ),
    Track(
        rank=5,
        id="safari-desktop-baseline",
        label="Safari desktop controlled-public baseline",
        current_state="binary_ready_session_blocked",
        can_run_now=False,
        blocker="Safari `Allow remote automation` is not enabled, so real WebDriver session creation fails.",
        needed_from_user_or_environment="Enable Safari Settings > Developer > Allow remote automation, then rerun session smoke.",
        paper_value="Medium: adds cross-browser feasibility, but claim ceiling remains lower than Chrome because there is no NetLog-equivalent artifact.",
        risk="A Safari PASS is feasibility evidence, not browser-internal single-session CM proof.",
        next_command_or_action="Rerun `tools/check_browser_cm_observability.py --safari-session-smoke`, then controlled-public Safari baseline.",
        supporting_evidence_ids=("safari-webdriver-session-readiness", "non-iphone-gate-rerun-20260701"),
        decision="Worth doing after one settings toggle, but not enough as the main paper contribution.",
    ),
    Track(
        rank=6,
        id="mvfst-focused-tests",
        label="mvfst focused migration tests on Linux/Buck",
        current_state="source_test_map_ready_build_blocked",
        can_run_now=False,
        blocker="Current host lacks the expected Buck/getdeps/disk setup for focused mvfst test execution.",
        needed_from_user_or_environment="Use a Linux builder with Buck/getdeps and sufficient disk.",
        paper_value="Medium-low for immediate paper direction: it strengthens implementation maturity, which is already fairly well covered.",
        risk="High build cost; still not browser/application continuity evidence.",
        next_command_or_action="Run focused BUCK targets identified by `tools/check_mvfst_migration_test_readiness.py`.",
        supporting_evidence_ids=("mvfst-source-audit", "mvfst-migration-test-readiness"),
        decision="Defer unless the paper needs one more large-scale implementation appendix.",
    ),
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def index_evidence(bundle: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item.get("id", ""): item for item in bundle.get("items", [])}


def build_decision(evidence_bundle_path: Path) -> dict[str, Any]:
    bundle = read_json(evidence_bundle_path)
    evidence = index_evidence(bundle)
    rows: list[dict[str, Any]] = []
    missing: dict[str, list[str]] = {}

    for track in TRACKS:
        track_dict = asdict(track)
        ids = list(track.supporting_evidence_ids)
        track_missing = [evidence_id for evidence_id in ids if evidence_id not in evidence]
        if track_missing:
            missing[track.id] = track_missing
        track_dict["supporting_evidence_ids"] = ids
        track_dict["supporting_evidence_found"] = [evidence_id for evidence_id in ids if evidence_id in evidence]
        track_dict["supporting_evidence_missing"] = track_missing
        rows.append(track_dict)

    runnable_now = [row["id"] for row in rows if row["can_run_now"]]
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "source_bundle": evidence_bundle_path.as_posix(),
        "source_bundle_exists": evidence_bundle_path.exists(),
        "source_bundle_item_count": bundle.get("item_count", 0),
        "track_count": len(rows),
        "runnable_now": runnable_now,
        "blocked_track_count": len(rows) - len(runnable_now),
        "missing_evidence_ids": missing,
        "recommendation": {
            "main": "Do not keep expanding generic implementation survey now; the next paper-critical gain is a deployment/browser bridge.",
            "first": "Refresh AWS credentials and run AWS NLB + s2n-quic live forwarding echo.",
            "second": "If AWS remains blocked, prepare a controlled public Chrome origin for media/range/upload page-ready trials.",
            "third": "Use Safari only as PASS_FEASIBILITY after Allow remote automation is enabled.",
        },
        "tracks": rows,
    }


def emit_markdown(decision: dict[str, Any]) -> str:
    lines = [
        "# Non-iPhone Next Research Decision Brief",
        "",
        f"Generated: `{decision['generated']}`",
        "",
        "This document chooses the next research step using only public-safe committed evidence IDs. It intentionally does not include credentials, IP addresses, hostnames, qlogs, pcaps, keylogs, or NetLogs.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| source bundle | `{decision['source_bundle']}` |",
        f"| source bundle exists | `{decision['source_bundle_exists']}` |",
        f"| source bundle item count | `{decision['source_bundle_item_count']}` |",
        f"| candidate tracks | `{decision['track_count']}` |",
        f"| runnable now | `{decision['runnable_now']}` |",
        f"| blocked track count | `{decision['blocked_track_count']}` |",
        f"| missing evidence IDs | `{decision['missing_evidence_ids']}` |",
        "",
        "## Recommendation",
        "",
        "| rank | recommendation |",
        "| ---: | --- |",
        f"| 1 | {decision['recommendation']['first']} |",
        f"| 2 | {decision['recommendation']['second']} |",
        f"| 3 | {decision['recommendation']['third']} |",
        "",
        "> Do not keep expanding generic implementation survey now; the next paper-critical gain is a deployment/browser bridge.",
        "",
        "## Candidate Tracks",
        "",
        "| rank | track | current state | can run now | blocker | paper value | decision |",
        "| ---: | --- | --- | --- | --- | --- | --- |",
    ]

    for row in decision["tracks"]:
        lines.append(
            "| {rank} | `{id}`<br>{label} | `{current_state}` | `{can_run_now}` | {blocker} | {paper_value} | {decision} |".format(
                rank=row["rank"],
                id=row["id"],
                label=row["label"],
                current_state=row["current_state"],
                can_run_now=str(row["can_run_now"]).lower(),
                blocker=row["blocker"],
                paper_value=row["paper_value"],
                decision=row["decision"],
            )
        )

    lines.extend(
        [
            "",
            "## Evidence Trace",
            "",
            "| track | evidence IDs | missing | next action |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in decision["tracks"]:
        evidence_ids = ", ".join(f"`{item}`" for item in row["supporting_evidence_ids"])
        missing = ", ".join(f"`{item}`" for item in row["supporting_evidence_missing"]) or "-"
        lines.append(f"| `{row['id']}` | {evidence_ids} | {missing} | {row['next_command_or_action']} |")

    lines.extend(
        [
            "",
            "## Interpretation For The Paper",
            "",
            "1. Implementation maturity is no longer the weakest section; the repository already has broad implementation tests, app demos, server runtime evidence, and negative controls.",
            "2. The next missing proof is whether the mature primitives survive a realistic deployment or browser public-origin boundary.",
            "3. AWS NLB+s2n is the most valuable non-iPhone path because it directly addresses the professor's AWS deployment decision, but it is blocked by credentials on this host.",
            "4. Chrome controlled-public workload trials are the best browser-facing fallback because local media/range/upload controls already define the artifact contract.",
            "5. Safari is worth adding for cross-browser feasibility only after WebDriver session creation is enabled, and its claim ceiling must stay below Chrome NetLog-based evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(markdown_path: Path, json_path: Path, decision: dict[str, Any]) -> None:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(emit_markdown(decision), encoding="utf-8")
    json_path.write_text(json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-bundle", default=DEFAULT_EVIDENCE_BUNDLE)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    decision = build_decision(Path(args.evidence_bundle))
    write_outputs(Path(args.output), Path(args.json_output), decision)
    print(f"wrote {args.output}")
    print(f"wrote {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
