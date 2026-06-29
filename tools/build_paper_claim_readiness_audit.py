#!/usr/bin/env python3
"""Build a paper-claim readiness audit from current research artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from audit_final_browser_handover_trials import build_audit
from research_clock import utc_date_iso


DEFAULT_REQUIREMENTS = "data/final-browser-handover-required-trials.csv"
DEFAULT_EXPERIMENTS = "data/experiment-results.csv"
DEFAULT_WORKLOAD_SYNTHESIS = "data/workload-sensitivity-synthesis-20260629.csv"
DEFAULT_IPHONE_FAILOVER = "data/iphone-usb-latent-failover-live-rerun-20260629.json"
DEFAULT_ORIGIN_ACCESS = "data/controlled-public-origin-access-check-rerun-20260629.json"
DEFAULT_OUTPUT = "docs/results/paper-claim-readiness-audit-20260629.md"
DEFAULT_CSV_OUTPUT = "data/paper-claim-readiness-audit-20260629.csv"


@dataclass(frozen=True)
class ClaimRow:
    claim_id: str
    readiness: str
    evidence: str
    safe_paper_wording: str
    do_not_claim: str
    next_step: str


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def count_where(rows: list[dict[str, str]], *needles: str) -> int:
    lowered = [needle.lower() for needle in needles]
    count = 0
    for row in rows:
        text = " ".join(str(value).lower() for value in row.values())
        if all(needle in text for needle in lowered):
            count += 1
    return count


def truthy(value: str) -> bool:
    return value.strip().lower() in {"true", "yes", "1"}


def count_instrumented_path_change_rows(rows: list[dict[str, str]]) -> int:
    return sum(
        1
        for row in rows
        if row.get("status") == "PASS"
        and truthy(row.get("path_validation_observed", ""))
        and truthy(row.get("tuple_change_observed", ""))
    )


def status_counts(rows: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        status = row.get("status", "") or "unknown"
        counts[status] = counts.get(status, 0) + 1
    return dict(sorted(counts.items()))


def workload_summary(rows: list[dict[str, str]], workload_class: str) -> dict[str, str]:
    for row in rows:
        if row.get("workload_class") == workload_class:
            return row
    return {}


def final_blocker_text(audit: dict[str, Any]) -> str:
    blockers = audit.get("blockers") or []
    return "; ".join(str(blocker) for blocker in blockers) or "-"


def build_rows(
    *,
    final_audit: dict[str, Any],
    experiments: list[dict[str, str]],
    workloads: list[dict[str, str]],
    iphone: dict[str, Any],
    origin: dict[str, Any],
) -> list[ClaimRow]:
    upload = workload_summary(workloads, "large_upload")
    download = workload_summary(workloads, "large_download")
    media = workload_summary(workloads, "media_segments")
    music = workload_summary(workloads, "music_like_buffered")
    final_complete = bool(final_audit.get("complete"))
    complete_count = int(final_audit.get("complete_count", 0))
    requirement_count = int(final_audit.get("requirement_count", 0))
    iphone_ready = bool(iphone.get("ready")) and iphone.get("classification") == "latent_iphone_usb_failover_observed"
    ready_at = iphone.get("ready_at_ms")
    origin_tcp = origin.get("tcp", {}).get("classification", "missing")
    aws_classification = origin.get("aws", {}).get("classification", "missing")
    recovery_ready = origin.get("recovery_paths", {}).get("any_recovery_path_ready", False)

    controlled_impl_count = count_instrumented_path_change_rows(experiments)
    nlb_count = count_where(experiments, "aws nlb")
    public_iphone_count = count_where(experiments, "iphone usb", "network-change")

    return [
        ClaimRow(
            claim_id="quic-cm-is-a-real-standard-feature",
            readiness="source-backed",
            evidence="RFC 9000 defines path validation and connection migration; quic-go documents AddPath/Probe/Switch as client-side path migration primitives.",
            safe_paper_wording="QUIC provides standardized primitives for path validation and client-initiated migration, and at least some implementations expose explicit migration APIs.",
            do_not_claim="Do not infer that HTTP/3 browsers automatically use those primitives during Wi-Fi/cellular handover.",
            next_step="Use RFC 9000 and implementation docs as background, then rely on local artifacts for runtime behavior.",
        ),
        ClaimRow(
            claim_id="controlled-implementations-can-migrate",
            readiness="supported-scoped",
            evidence=f"{controlled_impl_count} PASS rows have both path validation and tuple-change evidence; AWS NLB/CID-related evidence rows={nlb_count}. Key rows include quic-go direct origin and quiche local migration controls.",
            safe_paper_wording="Controlled QUIC clients and deployment paths can demonstrate migration or CID-aware continuity under instrumented conditions.",
            do_not_claim="Do not generalize controlled CLI/library success to Chrome/Safari browser handover.",
            next_step="Keep controlled implementation results as positive controls and contrast them with browser/runtime policy evidence.",
        ),
        ClaimRow(
            claim_id="controlled-public-browser-h3-baseline-exists",
            readiness="supported-historical",
            evidence="Final audit still has the controlled public Chrome application H3 baseline requirement complete; no-change downlink baselines are also complete.",
            safe_paper_wording="The study already established that the controlled public origin was previously usable for Chrome HTTP/3 application traffic and no-change comparisons.",
            do_not_claim="Do not treat the previous baseline as proof that the public origin is currently online.",
            next_step="After origin recovery, rerun a fresh baseline before final active path-change rows.",
        ),
        ClaimRow(
            claim_id="iphone-usb-path-change-trigger-is-ready",
            readiness="supported-scoped" if iphone_ready else "not-supported",
            evidence=f"Rerun classification={iphone.get('classification', 'missing')}; ready={iphone.get('ready')}; ready_at_ms={ready_at}; before={iphone.get('before', {}).get('default_interface', '-')}; after={iphone.get('after', {}).get('default_interface', '-')}.",
            safe_paper_wording="On this Mac, Wi-Fi-off can trigger a reproducible latent iPhone USB failover, suitable as a real client path-change trigger with an explicit claim boundary.",
            do_not_claim="Do not call this simultaneous active multipath; it is delayed OS failover from Wi-Fi to iPhone USB.",
            next_step="Use NETWORK_CHANGE_CMD=\"networksetup -setairportpower 'en0' off\" in page-ready public trials once the origin is reachable.",
        ),
        ClaimRow(
            claim_id="public-origin-currently-blocks-final-runs",
            readiness="blocked-by-origin",
            evidence=f"Origin TCP classification={origin_tcp}; AWS identity classification={aws_classification}; any recovery path ready={recovery_ready}.",
            safe_paper_wording="The current inability to run final public trials is an infrastructure readiness blocker, not evidence that iPhone USB path change failed.",
            do_not_claim="Do not report a failed final browser CM trial when the controlled origin did not accept HTTPS/H3 connections.",
            next_step="Refresh AWS credentials or provide SSH/cert access, restart the controlled origin, and rerun baseline plus active trials.",
        ),
        ClaimRow(
            claim_id="chrome-single-session-browser-cm-not-yet-proven",
            readiness="not-supported-yet",
            evidence=f"Final protocol complete={final_complete}; complete requirements={complete_count}/{requirement_count}; blockers={final_blocker_text(final_audit)}; public iPhone network-change rows observed={public_iphone_count}.",
            safe_paper_wording="The current Chrome evidence supports workload failure/recovery and replacement-session observations, but not a publishable single-session browser CM success claim.",
            do_not_claim="Do not state that Chrome successfully migrated the original HTTP/3 connection across Wi-Fi-to-iPhone-USB.",
            next_step="Complete 3 no-heartbeat active rows, 3 heartbeat active rows, and one Safari/Android feasibility row with the full evidence chain.",
        ),
        ClaimRow(
            claim_id="upload-download-app-recovery-is-strong",
            readiness="supported",
            evidence=f"Upload: {upload.get('primary_result', '-')}; Download: {download.get('primary_result', '-')}.",
            safe_paper_wording="For large upload/download, application retry or byte-range recovery can convert visible task failure into task completion, but this is not the same as single-session QUIC CM.",
            do_not_claim="Do not use retry-completed rows as transport-layer CM success.",
            next_step="When public origin is restored, rerun page-ready upload/download with retry0 and retry1/range variants.",
        ),
        ClaimRow(
            claim_id="streaming-continuity-needs-qoe-metrics",
            readiness="supported-local-control",
            evidence=f"Media: {media.get('primary_result', '-')}; Music-like: {music.get('primary_result', '-')}.",
            safe_paper_wording="Streaming workloads require startup delay, rebuffer events, segment retry, and session churn metrics; completion alone hides the mechanism.",
            do_not_claim="Do not say CM helps streaming unless the row also proves session continuity and path validation.",
            next_step="Run public page-ready buffered-media handover after origin recovery and compare it against local buffered-media controls.",
        ),
        ClaimRow(
            claim_id="paper-direction-is-evidence-chain-and-workload-maturity",
            readiness="supported-as-framing",
            evidence="Implementation positives, browser negative controls, iPhone path-change readiness, workload recovery controls, and origin readiness gates now form a coherent evidence-boundary story.",
            safe_paper_wording="The defensible paper direction is a maturity and workload-continuity study: why CM is hard to observe/deploy, which workloads expose the gap, and what evidence is required before claiming browser CM.",
            do_not_claim="Do not frame the paper as already proving browser/mobile HTTP/3 CM success.",
            next_step="Write the paper around evidence chain, workload sensitivity, and controlled recovery; add final public handover rows when infrastructure is restored.",
        ),
    ]


def build_audit_payload(args: argparse.Namespace) -> dict[str, Any]:
    final_audit = build_audit(Path(args.requirements), Path(args.experiments))
    experiments = load_csv(Path(args.experiments))
    workloads = load_csv(Path(args.workload_synthesis))
    iphone = load_json(Path(args.iphone_failover))
    origin = load_json(Path(args.origin_access))
    rows = build_rows(
        final_audit=final_audit,
        experiments=experiments,
        workloads=workloads,
        iphone=iphone,
        origin=origin,
    )
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "requirements": args.requirements,
        "experiments": args.experiments,
        "workload_synthesis": args.workload_synthesis,
        "iphone_failover": args.iphone_failover,
        "origin_access": args.origin_access,
        "experiment_status_counts": status_counts(experiments),
        "final_protocol": {
            "complete": final_audit.get("complete"),
            "complete_count": final_audit.get("complete_count"),
            "requirement_count": final_audit.get("requirement_count"),
            "blockers": final_audit.get("blockers"),
        },
        "claims": [asdict(row) for row in rows],
        "source_anchors": [
            {
                "label": "RFC 9000, QUIC transport",
                "url": "https://datatracker.ietf.org/doc/html/rfc9000",
                "use": "Normative connection migration and path validation semantics.",
            },
            {
                "label": "quic-go connection migration docs",
                "url": "https://quic-go.net/docs/quic/connection-migration/",
                "use": "Implementation-level AddPath/Probe/Switch control model.",
            },
            {
                "label": "curl issue 7695",
                "url": "https://github.com/curl/curl/issues/7695",
                "use": "Practitioner report that HTTP/3 support did not imply automatic connection migration in curl.",
            },
            {
                "label": "An Analysis of QUIC Connection Migration in the Wild",
                "url": "https://arxiv.org/abs/2410.06066",
                "use": "Measurement anchor for uneven Internet CM support among HTTP/3-capable destinations.",
            },
        ],
    }


def emit_markdown(payload: dict[str, Any]) -> str:
    protocol = payload["final_protocol"]
    status_counts_text = "; ".join(f"{key}={value}" for key, value in payload["experiment_status_counts"].items())
    lines = [
        "# Paper Claim Readiness Audit",
        "",
        f"Generated: `{payload['generated']}`",
        "",
        "This audit records what the current evidence can and cannot support. It is intentionally conservative: application recovery, tuple change, or task completion is not upgraded to browser single-session QUIC Connection Migration unless the full evidence chain is present.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| final browser protocol complete | `{'yes' if protocol['complete'] else 'no'}` |",
        f"| final browser requirements | `{protocol['complete_count']}/{protocol['requirement_count']}` |",
        f"| final blockers | `{'; '.join(protocol['blockers']) if protocol['blockers'] else '-'}` |",
        f"| experiment status counts | `{status_counts_text}` |",
        "",
        "## Claim Audit",
        "",
        "| claim | readiness | safe paper wording | do not claim | next step |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in payload["claims"]:
        lines.append(
            f"| `{row['claim_id']}` | `{row['readiness']}` | {row['safe_paper_wording']} | {row['do_not_claim']} | {row['next_step']} |"
        )
    lines.extend(["", "## Evidence Notes", ""])
    for row in payload["claims"]:
        lines.append(f"- `{row['claim_id']}`: {row['evidence']}")
    lines.extend(["", "## Source Anchors", ""])
    for source in payload["source_anchors"]:
        lines.append(f"- [{source['label']}]({source['url']}): {source['use']}")
    lines.extend(
        [
            "",
            "## Paper Decision",
            "",
            "Proceed with the paper as a workload-sensitive CM maturity study, not as a success-only browser CM paper. The current evidence is strong enough to argue that HTTP/3 application continuity depends on workload semantics and recovery policy, while browser single-session CM remains unproven until the controlled public handover rows are completed.",
            "",
        ]
    )
    return "\n".join(lines)


def write_claim_csv(payload: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "claim_id",
        "readiness",
        "evidence",
        "safe_paper_wording",
        "do_not_claim",
        "next_step",
    ]
    with output.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for row in payload["claims"]:
            writer.writerow({field: row[field] for field in fieldnames})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--workload-synthesis", default=DEFAULT_WORKLOAD_SYNTHESIS)
    parser.add_argument("--iphone-failover", default=DEFAULT_IPHONE_FAILOVER)
    parser.add_argument("--origin-access", default=DEFAULT_ORIGIN_ACCESS)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    parser.add_argument("--json-output")
    args = parser.parse_args()

    payload = build_audit_payload(args)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(payload), encoding="utf-8")
    write_claim_csv(payload, Path(args.csv_output))
    if args.json_output:
        json_output = Path(args.json_output)
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
