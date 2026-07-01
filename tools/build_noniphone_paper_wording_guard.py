#!/usr/bin/env python3
"""Build a public-safe bilingual wording guard for the non-iPhone paper path."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_RISK_AUDIT = "data/noniphone-reviewer-risk-audit-20260701.json"
DEFAULT_CLAIM_DASHBOARD = "data/noniphone-claim-readiness-dashboard-20260701.json"
DEFAULT_OUTPUT = "docs/results/noniphone-paper-wording-guard-20260701.md"
DEFAULT_JSON_OUTPUT = "data/noniphone-paper-wording-guard-20260701.json"


@dataclass(frozen=True)
class WordingRule:
    section: str
    risk_ids: tuple[str, ...]
    avoid: str
    use_en: str
    use_ko: str
    evidence_boundary: str


RULES = [
    WordingRule(
        section="abstract",
        risk_ids=("guarantee_overclaim", "public_positive_absence"),
        avoid="HTTP/3 Connection Migration guarantees seamless task continuity under unstable mobile networks.",
        use_en="This study assesses how QUIC/HTTP/3 connection-migration primitives, deployment routing, browser behavior, and workload design shape application-level continuity.",
        use_ko="본 연구는 QUIC/HTTP/3 Connection Migration primitive, 배포 라우팅, 브라우저 동작, workload 설계가 애플리케이션 수준 작업 연속성에 어떤 경계를 만드는지 평가한다.",
        evidence_boundary="Do not claim public Chrome CM success or guarantee language.",
    ),
    WordingRule(
        section="introduction",
        risk_ids=("terminology_mobile_unstable", "local_rebinding_external_validity"),
        avoid="We evaluate unstable mobile networks such as Wi-Fi/LTE handover.",
        use_en="We distinguish controlled local UDP rebinding, public-origin active path change, deployment routing, and application recovery, because these layers expose different failure modes.",
        use_ko="본 연구는 local UDP rebinding, public-origin active path change, 배포 라우팅, 애플리케이션 복구를 구분한다. 각 계층은 서로 다른 실패 원인을 드러내기 때문이다.",
        evidence_boundary="Do not use LTE/5G/Wi-Fi handover wording unless those rows are actually collected.",
    ),
    WordingRule(
        section="method",
        risk_ids=("implementation_survey_heterogeneity",),
        avoid="Each implementation was tested equivalently.",
        use_en="Implementation evidence is classified by level: runtime positive controls, app demos, source/test audits, deployment gates, and negative controls are reported separately.",
        use_ko="구현체 근거는 runtime positive control, app demo, source/test audit, deployment gate, negative control로 구분해 보고한다.",
        evidence_boundary="Do not collapse source audits and runtime results into one binary support label.",
    ),
    WordingRule(
        section="method",
        risk_ids=("public_positive_absence",),
        avoid="A public Chrome migration run is successful if the task completes.",
        use_en="A strong public Chrome CM row requires application completion, client active path change, target server tuple change, qlog path validation, and one target Chrome QUIC session in the same active trial.",
        use_ko="강한 public Chrome CM row는 동일 active trial 안에서 application completion, client active path change, target server tuple change, qlog path validation, Chrome target QUIC session 1개를 모두 요구한다.",
        evidence_boundary="Task completion alone is not a CM success criterion.",
    ),
    WordingRule(
        section="results",
        risk_ids=("local_rebinding_external_validity",),
        avoid="Chrome handover succeeds in our experiments.",
        use_en="Local Chrome forced-H3 rebinding controls show workload-sensitive behavior under a controlled path perturbation, but they do not substitute for public-origin handover evidence.",
        use_ko="Local Chrome forced-H3 rebinding control은 통제된 path perturbation에서 workload-sensitive behavior를 보여주지만, public-origin handover 근거를 대체하지 않는다.",
        evidence_boundary="Keep local controls separate from public browser claims.",
    ),
    WordingRule(
        section="results",
        risk_ids=("aws_s2n_scope_confusion",),
        avoid="AWS NLB+s2n migration is validated.",
        use_en="The AWS path currently contains local CID-provider prerequisite evidence and a fail-closed live runner; live forwarding and active migration remain blocked or future steps.",
        use_ko="AWS 경로는 현재 local CID-provider prerequisite evidence와 fail-closed live runner를 확보한 상태이며, live forwarding과 active migration은 아직 blocked 또는 future step이다.",
        evidence_boundary="Do not claim live AWS forwarding or active migration before credentials and trial rows exist.",
    ),
    WordingRule(
        section="results",
        risk_ids=("streaming_completion_qoe_confound",),
        avoid="Video and music workloads remain continuous because playback completes.",
        use_en="Streaming completion is reported together with rebuffering, startup delay, retry behavior, and Chrome target session count; completion alone is treated as insufficient continuity evidence.",
        use_ko="Streaming completion은 rebuffering, startup delay, retry behavior, Chrome target session count와 함께 보고하며, completion만으로는 연속성 근거가 부족하다고 본다.",
        evidence_boundary="Do not interpret multi-session retry recovery as single-session CM.",
    ),
    WordingRule(
        section="limitations",
        risk_ids=("public_positive_absence", "safari_claim_ceiling"),
        avoid="The browser behavior section is complete.",
        use_en="The current public/browser evidence is intentionally conservative: no tracked active public Chrome row satisfies strong CM success, and Safari remains a lower-observability feasibility follow-up.",
        use_ko="현재 public/browser 근거는 의도적으로 보수적으로 해석한다. tracked active public Chrome row 중 strong CM success를 만족한 것은 없고, Safari는 낮은 관찰성의 feasibility follow-up으로 남아 있다.",
        evidence_boundary="State the absence of strong public success as a limitation, not as hidden success.",
    ),
    WordingRule(
        section="artifact_policy",
        risk_ids=("security_public_artifact_hygiene",),
        avoid="Raw artifacts are published for reproducibility.",
        use_en="The public artifact includes sanitized summaries, reproducible tools, manifests, and claim boundaries; raw sensitive traces are excluded from the public repository.",
        use_ko="공개 artifact에는 sanitized summary, 재현 도구, manifest, claim boundary를 포함하고, 민감한 raw trace는 공개 저장소에서 제외한다.",
        evidence_boundary="Continue publication-bundle validation and secret scanning before push.",
    ),
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def build_guard(risk_audit_path: Path, claim_dashboard_path: Path) -> dict[str, Any]:
    risk_audit = read_json(risk_audit_path)
    claim_dashboard = read_json(claim_dashboard_path)
    risks = {risk.get("id", ""): risk for risk in risk_audit.get("risks", [])}
    rows: list[dict[str, Any]] = []
    missing_risk_ids: dict[str, list[str]] = {}

    for rule in RULES:
        record = asdict(rule)
        missing = [risk_id for risk_id in rule.risk_ids if risk_id not in risks]
        if missing:
            missing_risk_ids[f"{rule.section}:{rule.avoid}"] = missing
        record["risk_ids"] = list(rule.risk_ids)
        record["risk_severities"] = {
            risk_id: risks.get(risk_id, {}).get("severity", "missing")
            for risk_id in rule.risk_ids
        }
        rows.append(record)

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "source_paths": {
            "risk_audit": risk_audit_path.as_posix(),
            "claim_dashboard": claim_dashboard_path.as_posix(),
        },
        "source_exists": {
            "risk_audit": risk_audit_path.exists(),
            "claim_dashboard": claim_dashboard_path.exists(),
        },
        "summary": {
            "rule_count": len(rows),
            "sections": sorted({row["section"] for row in rows}),
            "missing_risk_ids": missing_risk_ids,
            "allowed_claim_count": claim_dashboard.get("summary", {}).get("claim_allowed_count", 0),
            "blocked_claim_count": claim_dashboard.get("summary", {}).get("claim_blocked_count", 0),
            "critical_risks": risk_audit.get("summary", {}).get("critical_risks", []),
            "guard_decision": "Use conservative evaluate/classify wording unless public browser or AWS positive gates are opened.",
        },
        "rules": rows,
    }


def emit_markdown(guard: dict[str, Any]) -> str:
    summary = guard["summary"]
    lines = [
        "# non-iPhone Paper Wording Guard",
        "",
        f"Generated: `{guard['generated']}`",
        "",
        "This public-safe guard converts reviewer risks into bilingual wording rules for the abstract, introduction, method, results, limitations, and artifact policy sections.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| rule count | `{summary['rule_count']}` |",
        f"| sections | `{summary['sections']}` |",
        f"| allowed claim count | `{summary['allowed_claim_count']}` |",
        f"| blocked claim count | `{summary['blocked_claim_count']}` |",
        f"| critical risks | `{summary['critical_risks']}` |",
        f"| missing risk ids | `{summary['missing_risk_ids']}` |",
        f"| guard decision | {summary['guard_decision']} |",
        "",
        "## Wording Rules",
        "",
        "| section | risk ids | avoid | use EN | use KO | evidence boundary |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in guard["rules"]:
        risk_ids = ", ".join(f"`{risk_id}`" for risk_id in row["risk_ids"])
        lines.append(
            "| `{section}` | {risk_ids} | {avoid} | {use_en} | {use_ko} | {boundary} |".format(
                section=row["section"],
                risk_ids=risk_ids,
                avoid=row["avoid"],
                use_en=row["use_en"],
                use_ko=row["use_ko"],
                boundary=row["evidence_boundary"],
            )
        )

    lines.extend(
        [
            "",
            "## Safe Writing Posture",
            "",
            "- Prefer evaluate, assess, classify, separate, and boundary wording.",
            "- Avoid guarantee, prove, validated, seamless, and works unless the specific strong evidence row exists.",
            "- Keep local rebinding, public path change, AWS deployment, browser behavior, and application recovery in separate paragraphs.",
            "- Put unresolved public Chrome, AWS+s2n, and Safari claims in limitations or future work.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(output: Path, json_output: Path, guard: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(guard), encoding="utf-8")
    json_output.write_text(json.dumps(guard, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--risk-audit", default=DEFAULT_RISK_AUDIT)
    parser.add_argument("--claim-dashboard", default=DEFAULT_CLAIM_DASHBOARD)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    guard = build_guard(Path(args.risk_audit), Path(args.claim_dashboard))
    write_outputs(Path(args.output), Path(args.json_output), guard)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
