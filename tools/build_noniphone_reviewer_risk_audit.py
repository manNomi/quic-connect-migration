#!/usr/bin/env python3
"""Build a public-safe reviewer-risk and validity audit for the non-iPhone paper path."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_CLAIM_DASHBOARD = "data/noniphone-claim-readiness-dashboard-20260701.json"
DEFAULT_PROFESSOR_PACKET = "data/noniphone-professor-decision-packet-20260701.json"
DEFAULT_OUTPUT = "docs/results/noniphone-reviewer-risk-audit-20260701.md"
DEFAULT_JSON_OUTPUT = "data/noniphone-reviewer-risk-audit-20260701.json"


@dataclass(frozen=True)
class ReviewerRisk:
    id: str
    severity: str
    reviewer_objection: str
    current_evidence: tuple[str, ...]
    vulnerable_wording: str
    defensible_wording: str
    mitigation: str
    remaining_gap: str
    professor_decision_needed: str


RISKS = [
    ReviewerRisk(
        id="guarantee_overclaim",
        severity="critical",
        reviewer_objection="The paper may overstate that HTTP/3 Connection Migration guarantees web task continuity.",
        current_evidence=("noniphone-claim-readiness-dashboard", "noniphone-professor-decision-packet"),
        vulnerable_wording="HTTP/3 Connection Migration guarantees seamless work continuity.",
        defensible_wording="We evaluate where QUIC/HTTP/3 migration primitives, deployment routing, browser policy, and workload behavior do or do not support continuity.",
        mitigation="Use evaluate/assess/classify language, and keep transport continuity separate from application task completion.",
        remaining_gap="A positive public browser CM success row is still absent.",
        professor_decision_needed="Decide whether the paper is a maturity/gap analysis or must wait for a positive public/browser result.",
    ),
    ReviewerRisk(
        id="local_rebinding_external_validity",
        severity="high",
        reviewer_objection="Local UDP rebinding may not generalize to Wi-Fi/LTE, desktop interface handover, or public origin behavior.",
        current_evidence=("chrome-local-rebinding-workload-controls", "noniphone-workload-qoe-synthesis", "noniphone-desktop-path-change-readiness"),
        vulnerable_wording="Chrome handover works because local rebinding controls pass.",
        defensible_wording="Local rebinding controls are controlled browser/workload probes; public handover remains a separate gate.",
        mitigation="Label local results as controls and require public-origin active path-change rows for browser CM success.",
        remaining_gap="No active non-iPhone secondary desktop path and no H3-ready controlled public origin are available.",
        professor_decision_needed="Open public Chrome gates or keep local controls as methodological evidence only.",
    ),
    ReviewerRisk(
        id="public_positive_absence",
        severity="critical",
        reviewer_objection="The paper lacks a successful controlled-public Chrome single-session migration result.",
        current_evidence=("controlled-public-chrome-bridge-synthesis", "noniphone-public-workload-trial-packet", "controlled-public-origin-workload-deploy-packet"),
        vulnerable_wording="Chrome public-origin Connection Migration is validated.",
        defensible_wording="Tracked public Chrome rows currently provide H3 baselines and negative/gap evidence, not strong CM success.",
        mitigation="Report strong CM acceptance criteria and state that current strong success count is zero.",
        remaining_gap="Need application completion, client active path change, server tuple change, qlog path validation, and one target Chrome QUIC session in the same active row.",
        professor_decision_needed="Choose whether to run public Chrome trials after opening origin and desktop path gates.",
    ),
    ReviewerRisk(
        id="aws_s2n_scope_confusion",
        severity="high",
        reviewer_objection="AWS NLB+s2n readiness may be confused with live forwarding or active migration success.",
        current_evidence=("s2n-nlb-cid-provider-proof", "s2n-nlb-live-readiness", "aws-s2n-nlb-live-runner", "s2n-active-migration-api-audit"),
        vulnerable_wording="AWS NLB+s2n migration works.",
        defensible_wording="The repository has local CID-provider prerequisite evidence and a fail-closed live runner; live AWS forwarding is credential-blocked and active migration is a later design step.",
        mitigation="Split AWS claims into local prerequisite, live forwarding echo, and active path-change variant.",
        remaining_gap="AWS identity is invalid on the current host; live forwarding has not run.",
        professor_decision_needed="Refresh AWS credentials if AWS deployment evidence is required for the paper.",
    ),
    ReviewerRisk(
        id="streaming_completion_qoe_confound",
        severity="high",
        reviewer_objection="Streaming completion can hide rebuffering, retry/reconnect, and multiple QUIC sessions.",
        current_evidence=("chrome-desktop-noniphone-musiclike-local-refresh", "chrome-desktop-noniphone-buffered-media-local-refresh", "noniphone-workload-qoe-synthesis"),
        vulnerable_wording="Video and music workloads are continuous because playback completed.",
        defensible_wording="Streaming workloads are reported with QoE and session attribution; completion alone is not continuity.",
        mitigation="Always report rebuffer count, startup delay, retry count, target session count, tuple change, and qlog path evidence together.",
        remaining_gap="No public streaming handover rows exist yet.",
        professor_decision_needed="Decide whether streaming is a main evaluation axis or a QoE appendix.",
    ),
    ReviewerRisk(
        id="implementation_survey_heterogeneity",
        severity="medium",
        reviewer_objection="Implementation evidence mixes runtime tests, source audits, app demos, and readiness gates.",
        current_evidence=("cross-implementation-fresh-rerun", "sanitized-evidence-bundle-20260630", "implementation-survey.csv"),
        vulnerable_wording="All surveyed implementations are equally mature.",
        defensible_wording="The survey uses evidence levels and claim boundaries; runtime, source, app-demo, and readiness evidence are not treated as equal.",
        mitigation="Keep current_level/evidence_status columns visible and do not collapse them into a single binary support label.",
        remaining_gap="Some large production stacks still need Linux/build-focused execution.",
        professor_decision_needed="Decide whether additional implementation appendix depth is needed after the current broad survey.",
    ),
    ReviewerRisk(
        id="terminology_mobile_unstable",
        severity="high",
        reviewer_objection="Terms like unstable mobile network or mobile handover may be ambiguous or overbroad.",
        current_evidence=("noniphone-professor-decision-packet", "noniphone-claim-readiness-dashboard"),
        vulnerable_wording="Unstable mobile networks are evaluated.",
        defensible_wording="The current non-iPhone work evaluates controlled path-change readiness, local rebinding controls, public-origin gates, and workload continuity boundaries.",
        mitigation="Avoid claiming LTE/5G/Wi-Fi handover unless those rows exist; define path change, NAT rebinding, public-origin handover, and application recovery separately.",
        remaining_gap="No non-iPhone public active path-change row exists yet.",
        professor_decision_needed="Approve terminology before writing the final introduction and abstract.",
    ),
    ReviewerRisk(
        id="safari_claim_ceiling",
        severity="medium",
        reviewer_objection="Safari evidence has weaker observability than Chrome and is currently blocked at WebDriver session creation.",
        current_evidence=("safari-webdriver-session-readiness", "non-iphone-gate-rerun-20260701"),
        vulnerable_wording="Safari Connection Migration behavior is evaluated.",
        defensible_wording="Safari is a feasibility appendix candidate; current evidence is readiness-blocked and has lower browser-internal observability.",
        mitigation="Do not include Safari in main claims until session smoke and controlled-public baseline pass.",
        remaining_gap="Safari Allow remote automation is not enabled.",
        professor_decision_needed="Decide whether Safari should be excluded, deferred, or kept as a feasibility appendix.",
    ),
    ReviewerRisk(
        id="security_public_artifact_hygiene",
        severity="medium",
        reviewer_objection="Public artifacts may accidentally expose credentials, hosts, IPs, qlogs, NetLogs, or account data.",
        current_evidence=("sanitized-evidence-bundle-20260630", "reproducibility-manifest-20260630", "publication_bundle_validation"),
        vulnerable_wording="Raw artifacts are included for reproducibility.",
        defensible_wording="The public repository includes sanitized summaries, tools, manifests, and claim boundaries; raw sensitive artifacts remain excluded.",
        mitigation="Continue secret scan, publication bundle validation, and generated evidence-to-claim mapping before every push.",
        remaining_gap="Raw artifact archival policy for private review is separate from the public repository.",
        professor_decision_needed="Decide whether private raw artifacts need an offline appendix or institutional storage.",
    ),
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_audit(claim_dashboard: Path, professor_packet: Path) -> dict[str, Any]:
    dashboard = read_json(claim_dashboard)
    packet = read_json(professor_packet)
    risks = [asdict(risk) for risk in RISKS]
    critical = [risk["id"] for risk in risks if risk["severity"] == "critical"]
    high = [risk["id"] for risk in risks if risk["severity"] == "high"]
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "source_paths": {
            "claim_dashboard": claim_dashboard.as_posix(),
            "professor_packet": professor_packet.as_posix(),
        },
        "source_exists": {
            "claim_dashboard": claim_dashboard.exists(),
            "professor_packet": professor_packet.exists(),
        },
        "summary": {
            "risk_count": len(risks),
            "critical_count": len(critical),
            "high_count": len(high),
            "critical_risks": critical,
            "high_risks": high,
            "allowed_claim_count": dashboard.get("summary", {}).get("claim_allowed_count", 0),
            "blocked_claim_count": dashboard.get("summary", {}).get("claim_blocked_count", 0),
            "professor_questions": packet.get("professor_questions", []),
            "audit_decision": "The paper is defensible as a conservative maturity/gap analysis if critical overclaims are avoided; positive browser/AWS claims require opening external gates.",
        },
        "risks": risks,
    }


def emit_markdown(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    lines = [
        "# non-iPhone Reviewer Risk and Validity Audit",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This audit is public-safe. It converts the current non-iPhone claim dashboard and professor decision packet into reviewer-facing risks, defensive wording, and remaining evidence gaps.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| risk count | `{summary['risk_count']}` |",
        f"| critical risks | `{summary['critical_risks']}` |",
        f"| high risks | `{summary['high_risks']}` |",
        f"| allowed claim count | `{summary['allowed_claim_count']}` |",
        f"| blocked claim count | `{summary['blocked_claim_count']}` |",
        f"| audit decision | {summary['audit_decision']} |",
        "",
        "## Risk Register",
        "",
        "| risk | severity | reviewer objection | vulnerable wording | defensible wording | mitigation | remaining gap | professor decision |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for risk in audit["risks"]:
        lines.append(
            "| `{id}` | `{severity}` | {objection} | {vulnerable} | {defensible} | {mitigation} | {gap} | {decision} |".format(
                id=risk["id"],
                severity=risk["severity"],
                objection=risk["reviewer_objection"],
                vulnerable=risk["vulnerable_wording"],
                defensible=risk["defensible_wording"],
                mitigation=risk["mitigation"],
                gap=risk["remaining_gap"],
                decision=risk["professor_decision_needed"],
            )
        )

    lines.extend(
        [
            "",
            "## Reviewer-Safe Paper Posture",
            "",
            "- Treat implementation maturity, deployment routing, browser policy, and workload continuity as separate layers.",
            "- Present local Chrome rebinding rows as controlled probes, not public handover proof.",
            "- Keep public Chrome CM success, live AWS+s2n success, and Safari handover success out of the main claims until their gates open.",
            "- Use streaming workloads to discuss QoE and session attribution, not zero-impact continuity.",
            "- Ask the professor to choose between a conservative maturity/gap paper and additional positive-result gate work.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(output: Path, json_output: Path, audit: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(audit), encoding="utf-8")
    json_output.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim-dashboard", default=DEFAULT_CLAIM_DASHBOARD)
    parser.add_argument("--professor-packet", default=DEFAULT_PROFESSOR_PACKET)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    audit = build_audit(Path(args.claim_dashboard), Path(args.professor_packet))
    write_outputs(Path(args.output), Path(args.json_output), audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
