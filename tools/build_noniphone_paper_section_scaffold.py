#!/usr/bin/env python3
"""Build a public-safe paper section scaffold from non-iPhone evidence."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_BUNDLE = "data/sanitized-evidence-bundle-20260630.json"
DEFAULT_WORDING_GUARD = "data/noniphone-paper-wording-guard-20260701.json"
DEFAULT_OUTPUT = "docs/results/noniphone-paper-section-scaffold-20260701.md"
DEFAULT_JSON_OUTPUT = "data/noniphone-paper-section-scaffold-20260701.json"


@dataclass(frozen=True)
class SectionRow:
    id: str
    section: str
    purpose: str
    use_en: str
    use_ko: str
    evidence_ids: tuple[str, ...]
    wording_sections: tuple[str, ...]
    do_not_claim: str
    next_gap: str


SECTIONS = [
    SectionRow(
        id="abstract_positioning",
        section="Abstract",
        purpose="State the paper as a conservative maturity/gap evaluation instead of a guarantee claim.",
        use_en="We assess how QUIC/HTTP/3 migration primitives, deployment routing, browser behavior, and workload design shape application-level continuity.",
        use_ko="QUIC/HTTP/3 migration primitive, 배포 라우팅, 브라우저 동작, workload 설계가 애플리케이션 수준 작업 연속성에 만드는 경계를 평가한다고 쓴다.",
        evidence_ids=("noniphone-paper-wording-guard", "noniphone-reviewer-risk-audit"),
        wording_sections=("abstract",),
        do_not_claim="Do not claim that HTTP/3 CM guarantees seamless continuity.",
        next_gap="If a stronger abstract is desired, open public Chrome or AWS positive-result gates first.",
    ),
    SectionRow(
        id="introduction_problem_framing",
        section="Introduction",
        purpose="Separate path change, local rebinding, deployment routing, browser policy, and app recovery terminology.",
        use_en="Motivate the problem as a layer-boundary question: transport migration support does not automatically imply browser-visible task continuity.",
        use_ko="문제 제기는 계층 경계 문제로 잡는다. transport migration 지원이 곧 browser-visible task continuity를 뜻하지 않는다고 설명한다.",
        evidence_ids=("noniphone-paper-wording-guard", "noniphone-reviewer-risk-audit"),
        wording_sections=("introduction",),
        do_not_claim="Do not use broad unstable mobile network wording without defining the tested path-change class.",
        next_gap="Finalize terminology with the professor before writing the abstract and introduction.",
    ),
    SectionRow(
        id="method_implementation_maturity",
        section="Method",
        purpose="Explain implementation maturity as evidence-level classification rather than a binary support label.",
        use_en="Classify implementation evidence into runtime controls, app demos, source/test audits, deployment gates, and negative controls.",
        use_ko="구현체 근거를 runtime control, app demo, source/test audit, deployment gate, negative control로 나누어 설명한다.",
        evidence_ids=("cross-implementation-fresh-rerun", "quiche-path-event-observability", "nginx-active-client-migration-runtime", "haproxy-http3-negative-control"),
        wording_sections=("method",),
        do_not_claim="Do not state that all surveyed implementations are equally mature.",
        next_gap="Run large production-stack focused tests only if the appendix needs more implementation depth.",
    ),
    SectionRow(
        id="method_public_cm_acceptance",
        section="Method",
        purpose="Define conservative strong-CM acceptance criteria for public Chrome rows.",
        use_en="Require application completion, client active path change, target tuple change, qlog path validation, and one Chrome target QUIC session in the same active row.",
        use_ko="동일 active row에서 application completion, client active path change, target tuple change, qlog path validation, Chrome target QUIC session 1개를 모두 요구한다.",
        evidence_ids=("noniphone-public-workload-trial-packet", "controlled-public-origin-workload-deploy-packet", "controlled-public-chrome-bridge-synthesis", "controlled-public-chrome-artifact-classifier-contract", "controlled-public-chrome-contract-application-audit"),
        wording_sections=("method",),
        do_not_claim="Do not count task completion alone as Connection Migration success.",
        next_gap="Open public H3 origin and non-iPhone desktop path gates before claiming public Chrome CM success.",
    ),
    SectionRow(
        id="results_implementation_layer",
        section="Results",
        purpose="Report that implementation primitives exist across stacks while behavior and deployability differ.",
        use_en="Implementation evidence shows CM-related primitives are present across multiple stacks, but API exposure, observability, and deployment readiness differ.",
        use_ko="여러 구현체에 CM 관련 primitive는 존재하지만 API 노출, 관찰성, 배포 readiness는 구현체마다 다르다고 보고한다.",
        evidence_ids=("cross-implementation-fresh-rerun", "lsquic-preferred-address-app-demo", "lsquic-nat-rebinding-app-demo", "s2n-active-migration-api-audit", "mvfst-source-audit"),
        wording_sections=("results",),
        do_not_claim="Do not generalize a quic-go positive control to all stacks or browser behavior.",
        next_gap="Use implementation evidence as foundation, not as final web-continuity proof.",
    ),
    SectionRow(
        id="results_deployment_boundary",
        section="Results",
        purpose="Report CID-aware deployment and proxy negative-control boundaries.",
        use_en="Deployment results should distinguish CID-aware routing, proxy termination boundaries, local prerequisites, and blocked live AWS execution.",
        use_ko="배포 결과는 CID-aware routing, proxy termination boundary, local prerequisite, blocked live AWS execution을 분리해 쓴다.",
        evidence_ids=("aws-nlb-cid-aware-positive-control", "aws-nlb-negative-controls", "aws-nlb-http3-workload", "s2n-nlb-cid-provider-proof", "s2n-nlb-live-readiness", "aws-s2n-nlb-live-runner"),
        wording_sections=("results",),
        do_not_claim="Do not claim live AWS NLB+s2n forwarding or active migration success yet.",
        next_gap="Refresh AWS credentials to run live forwarding before any AWS positive claim.",
    ),
    SectionRow(
        id="results_browser_workloads",
        section="Results",
        purpose="Use local Chrome controls to prioritize workloads while avoiding public handover overclaim.",
        use_en="Local Chrome forced-H3 controls show that range/download and upload provide cleaner single-session local evidence than streaming-like workloads.",
        use_ko="Local Chrome forced-H3 control에서는 range/download와 upload가 streaming형 workload보다 단일 session local evidence가 더 선명하다고 쓴다.",
        evidence_ids=("chrome-local-rebinding-workload-controls", "chrome-desktop-noniphone-range-local-refresh", "chrome-desktop-noniphone-upload-local-refresh", "noniphone-workload-qoe-synthesis"),
        wording_sections=("results",),
        do_not_claim="Do not call local rebinding a public Wi-Fi/LTE or desktop-interface handover result.",
        next_gap="Run controlled-public range/upload trials first once public-origin and path-change gates open.",
    ),
    SectionRow(
        id="results_streaming_qoe",
        section="Results",
        purpose="Frame streaming as QoE/session-attribution evidence rather than zero-impact continuity.",
        use_en="Streaming outcomes must include rebuffering, startup delay, retry behavior, and Chrome target session count.",
        use_ko="Streaming 결과는 rebuffering, startup delay, retry behavior, Chrome target session count를 함께 보고한다.",
        evidence_ids=("chrome-desktop-noniphone-musiclike-local-refresh", "chrome-desktop-noniphone-buffered-media-local-refresh", "noniphone-workload-qoe-synthesis"),
        wording_sections=("results",),
        do_not_claim="Do not treat playback completion alone as continuity or single-session CM.",
        next_gap="Public streaming trials need QoE metrics and session attribution together.",
    ),
    SectionRow(
        id="limitations_future_work",
        section="Limitations",
        purpose="Make blocked public Chrome, AWS, Safari, and terminology gaps explicit.",
        use_en="Limitations should state that no tracked active public Chrome row satisfies strong CM success, live AWS+s2n is credential-blocked, and Safari remains feasibility-only.",
        use_ko="한계에서는 tracked active public Chrome strong CM success가 없고, live AWS+s2n은 credential-blocked이며, Safari는 feasibility-only라고 명시한다.",
        evidence_ids=("noniphone-claim-readiness-dashboard", "noniphone-professor-decision-packet", "noniphone-reviewer-risk-audit"),
        wording_sections=("limitations",),
        do_not_claim="Do not hide the absence of public/browser positive rows.",
        next_gap="Professor decision should choose maturity/gap scope or external positive-result gate work.",
    ),
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def evidence_index(bundle: dict[str, Any]) -> set[str]:
    return {item.get("id", "") for item in bundle.get("items", [])}


def wording_sections(guard: dict[str, Any]) -> set[str]:
    return {rule.get("section", "") for rule in guard.get("rules", [])}


def build_scaffold(bundle_path: Path, wording_guard_path: Path) -> dict[str, Any]:
    bundle = read_json(bundle_path)
    guard = read_json(wording_guard_path)
    evidence_ids = evidence_index(bundle)
    sections_available = wording_sections(guard)
    rows: list[dict[str, Any]] = []
    missing_evidence: dict[str, list[str]] = {}
    missing_wording: dict[str, list[str]] = {}

    for section in SECTIONS:
        record = asdict(section)
        record["evidence_ids"] = list(section.evidence_ids)
        record["wording_sections"] = list(section.wording_sections)
        evidence_missing = [item for item in section.evidence_ids if item not in evidence_ids]
        wording_missing = [item for item in section.wording_sections if item not in sections_available]
        if evidence_missing:
            missing_evidence[section.id] = evidence_missing
        if wording_missing:
            missing_wording[section.id] = wording_missing
        rows.append(record)

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "source_paths": {
            "evidence_bundle": bundle_path.as_posix(),
            "wording_guard": wording_guard_path.as_posix(),
        },
        "source_exists": {
            "evidence_bundle": bundle_path.exists(),
            "wording_guard": wording_guard_path.exists(),
        },
        "summary": {
            "section_count": len(rows),
            "paper_sections": sorted({row["section"] for row in rows}),
            "missing_evidence_ids": missing_evidence,
            "missing_wording_sections": missing_wording,
            "bundle_item_count": bundle.get("item_count", 0),
            "scaffold_decision": "Use this scaffold to draft a conservative maturity/gap paper before opening public browser or AWS positive-result gates.",
        },
        "sections": rows,
    }


def emit_markdown(scaffold: dict[str, Any]) -> str:
    summary = scaffold["summary"]
    lines = [
        "# non-iPhone Paper Section Scaffold",
        "",
        f"Generated: `{scaffold['generated']}`",
        "",
        "This public-safe scaffold maps the current evidence corpus and wording guard into paper sections. It does not include raw qlogs, pcaps, keylogs, NetLogs, private hosts, device IDs, account IDs, or credentials.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| section count | `{summary['section_count']}` |",
        f"| paper sections | `{summary['paper_sections']}` |",
        f"| bundle item count | `{summary['bundle_item_count']}` |",
        f"| missing evidence ids | `{summary['missing_evidence_ids']}` |",
        f"| missing wording sections | `{summary['missing_wording_sections']}` |",
        f"| scaffold decision | {summary['scaffold_decision']} |",
        "",
        "## Section Plan",
        "",
        "| id | section | purpose | EN seed | KO seed | evidence ids | do not claim | next gap |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in scaffold["sections"]:
        evidence = ", ".join(f"`{item}`" for item in row["evidence_ids"])
        lines.append(
            "| `{id}` | {section} | {purpose} | {use_en} | {use_ko} | {evidence} | {do_not_claim} | {next_gap} |".format(
                id=row["id"],
                section=row["section"],
                purpose=row["purpose"],
                use_en=row["use_en"],
                use_ko=row["use_ko"],
                evidence=evidence,
                do_not_claim=row["do_not_claim"],
                next_gap=row["next_gap"],
            )
        )
    lines.extend(
        [
            "",
            "## Drafting Order",
            "",
            "1. Write the abstract and introduction from the boundary framing, not from a guarantee claim.",
            "2. Write methods around evidence levels and strong-CM acceptance criteria.",
            "3. Present implementation, deployment, browser workload, and streaming/QoE results as separate layers.",
            "4. Put public Chrome, live AWS+s2n, and Safari gaps in limitations/future work unless their gates open.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(output: Path, json_output: Path, scaffold: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(scaffold), encoding="utf-8")
    json_output.write_text(json.dumps(scaffold, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--evidence-bundle", default=DEFAULT_BUNDLE)
    parser.add_argument("--wording-guard", default=DEFAULT_WORDING_GUARD)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    scaffold = build_scaffold(Path(args.evidence_bundle), Path(args.wording_guard))
    write_outputs(Path(args.output), Path(args.json_output), scaffold)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
