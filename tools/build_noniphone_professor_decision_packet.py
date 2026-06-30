#!/usr/bin/env python3
"""Build a Korean, public-safe decision packet for professor review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_CLAIM_DASHBOARD = "data/noniphone-claim-readiness-dashboard-20260701.json"
DEFAULT_DECISION = "data/non-iphone-next-research-decision-20260630.json"
DEFAULT_GATE_RERUN = "data/non-iphone-gate-rerun-20260701.json"
DEFAULT_OUTPUT = "docs/results/noniphone-professor-decision-packet-20260701.md"
DEFAULT_JSON_OUTPUT = "data/noniphone-professor-decision-packet-20260701.json"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def claim_lookup(dashboard: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row.get("id", ""): row for row in dashboard.get("claims", [])}


def build_packet(claim_dashboard: Path, decision_path: Path, gate_rerun_path: Path) -> dict[str, Any]:
    dashboard = read_json(claim_dashboard)
    decision = read_json(decision_path)
    gate = read_json(gate_rerun_path)
    claims = claim_lookup(dashboard)

    allowed_claims = dashboard.get("summary", {}).get("claim_allowed", [])
    blocked_claims = dashboard.get("summary", {}).get("claim_blocked", [])
    context = dashboard.get("context", {})

    meeting_decisions = [
        {
            "id": "scope_gap_paper",
            "label": "현재 근거로 논문 scope를 maturity/gap analysis로 확정할지",
            "recommendation": "recommended",
            "why": "구현체 primitive, deployment boundary, local workload/QoE evidence는 충분하지만 public browser/AWS positive claim은 아직 닫혀 있다.",
            "cost": "추가 외부 실험 없이도 초안/보고서 방향을 확정할 수 있다.",
            "risk": "positive public handover result가 없으므로 contribution wording을 보수적으로 유지해야 한다.",
        },
        {
            "id": "open_positive_public_browser_path",
            "label": "positive browser result를 얻기 위해 public H3 origin과 non-iPhone secondary path를 열지",
            "recommendation": "conditional",
            "why": "Chrome public-origin single-session CM 성공 claim을 열려면 현재 두 gate가 모두 필요하다.",
            "cost": "WebPKI+Alt-Svc H3 origin, workload endpoint, Ethernet/USB LAN 같은 non-iPhone secondary desktop path가 필요하다.",
            "risk": "실행 후에도 strong CM success가 나오지 않을 수 있으며, 그 경우 negative/gap evidence가 된다.",
        },
        {
            "id": "open_aws_s2n_path",
            "label": "AWS NLB+s2n live forwarding을 우선 열지",
            "recommendation": "conditional_high_value",
            "why": "교수님 decision 중 AWS 검증에 가장 직접적으로 대응한다.",
            "cost": "유효한 AWS credential이 필요하며, 첫 단계는 active migration이 아니라 live forwarding echo다.",
            "risk": "s2n public active migration API 한계 때문에 forwarding 이후 별도 active path-change 설계가 필요하다.",
        },
        {
            "id": "open_safari_feasibility",
            "label": "Safari를 cross-browser feasibility appendix로만 추가할지",
            "recommendation": "low_priority",
            "why": "Safari는 NetLog 같은 browser-internal evidence가 약해서 Chrome보다 claim ceiling이 낮다.",
            "cost": "Safari Allow remote automation 설정이 필요하다.",
            "risk": "성공해도 main contribution보다 feasibility appendix 성격이 강하다.",
        },
    ]

    blocked_summary = {
        "chrome_public_cm_success": {
            "blocked": "controlled_public_chrome_cm" in blocked_claims,
            "reason": claims.get("controlled_public_chrome_cm", {}).get("blockers", []),
        },
        "aws_s2n_live_success": {
            "blocked": "aws_s2n_live_claim" in blocked_claims,
            "reason": claims.get("aws_s2n_live_claim", {}).get("blockers", []),
        },
        "safari_handover_success": {
            "blocked": "safari_cross_browser_claim" in blocked_claims,
            "reason": claims.get("safari_cross_browser_claim", {}).get("blockers", []),
        },
    }

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "source_paths": {
            "claim_dashboard": claim_dashboard.as_posix(),
            "decision": decision_path.as_posix(),
            "gate_rerun": gate_rerun_path.as_posix(),
        },
        "source_exists": {
            "claim_dashboard": claim_dashboard.exists(),
            "decision": decision_path.exists(),
            "gate_rerun": gate_rerun_path.exists(),
        },
        "executive_summary": {
            "one_sentence": "현재 연구는 구현체 성숙도와 deployment/browser gap을 보수적으로 주장할 수 있지만, public Chrome CM 성공과 live AWS+s2n 성공은 아직 외부 gate 때문에 주장하면 안 된다.",
            "allowed_claim_count": len(allowed_claims),
            "blocked_claim_count": len(blocked_claims),
            "open_gates": gate.get("open_gates", []),
            "all_key_gates_blocked": gate.get("all_key_gates_blocked", None),
            "controlled_public_strong_cm_success_count": context.get("controlled_public_strong_cm_success_count", 0),
            "paper_decision": dashboard.get("summary", {}).get("paper_decision", "-"),
        },
        "allowed_claims": allowed_claims,
        "blocked_claims": blocked_claims,
        "blocked_summary": blocked_summary,
        "meeting_decisions": meeting_decisions,
        "next_research_priority": decision.get("recommendation", {}),
        "professor_questions": [
            "현재 논문을 CM implementation/deployment/browser maturity gap 분석으로 scope를 확정해도 되는가?",
            "positive result가 꼭 필요하다면 AWS NLB+s2n과 Chrome controlled-public workload 중 어느 gate를 먼저 열 것인가?",
            "Streaming workload는 main claim으로 둘 것인가, QoE/session-churn appendix로 둘 것인가?",
            "Safari는 main browser comparison이 아니라 feasibility appendix로 제한해도 되는가?",
        ],
        "do_not_say": [
            "HTTP/3 Connection Migration이 웹 작업 연속성을 보장한다고 말하지 않는다.",
            "Chrome public-origin single-session Connection Migration 성공을 주장하지 않는다.",
            "AWS NLB+s2n live success 또는 active migration success를 주장하지 않는다.",
            "Streaming completion을 zero-impact continuity나 single-session CM으로 해석하지 않는다.",
            "CDN/edge HTTP/3 continuity를 end-to-end origin CM으로 해석하지 않는다.",
        ],
    }


def emit_markdown(packet: dict[str, Any]) -> str:
    summary = packet["executive_summary"]
    lines = [
        "# non-iPhone Professor Decision Packet",
        "",
        f"Generated: `{packet['generated']}`",
        "",
        "이 문서는 교수님 논의용 public-safe decision packet이다. credential, 계정 ID, hostname, IP, qlog, keylog, pcap, NetLog 원문을 포함하지 않는다.",
        "",
        "## 한 문장 결론",
        "",
        summary["one_sentence"],
        "",
        "## 현재 판정",
        "",
        "| 항목 | 값 |",
        "| --- | --- |",
        f"| 허용 가능한 claim 수 | `{summary['allowed_claim_count']}` |",
        f"| 아직 막아야 할 claim 수 | `{summary['blocked_claim_count']}` |",
        f"| open gate | `{summary['open_gates']}` |",
        f"| all key gates blocked | `{summary['all_key_gates_blocked']}` |",
        f"| controlled-public strong CM success | `{summary['controlled_public_strong_cm_success_count']}` |",
        f"| paper decision | {summary['paper_decision']} |",
        "",
        "## 교수님께 받을 Decision",
        "",
        "| decision | 권장도 | 이유 | 비용 | 리스크 |",
        "| --- | --- | --- | --- | --- |",
    ]

    for row in packet["meeting_decisions"]:
        lines.append(
            f"| `{row['id']}`<br>{row['label']} | `{row['recommendation']}` | {row['why']} | {row['cost']} | {row['risk']} |"
        )

    lines.extend(
        [
            "",
            "## 현재 말해도 되는 Claim",
            "",
        ]
    )
    for claim in packet["allowed_claims"]:
        lines.append(f"- `{claim}`")

    lines.extend(
        [
            "",
            "## 아직 말하면 안 되는 Claim",
            "",
        ]
    )
    for key, value in packet["blocked_summary"].items():
        reasons = "; ".join(value.get("reason", [])) or "-"
        lines.append(f"- `{key}`: blocked=`{value.get('blocked')}`; reason={reasons}")

    lines.extend(
        [
            "",
            "## 교수님께 물어볼 질문",
            "",
        ]
    )
    for question in packet["professor_questions"]:
        lines.append(f"- {question}")

    lines.extend(
        [
            "",
            "## 말하면 안 되는 문장",
            "",
        ]
    )
    for item in packet["do_not_say"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## 권장 보고 방식",
            "",
            "현재는 positive success paper라기보다 maturity/gap paper로 잡는 것이 방어 가능하다. 교수님이 positive deployment/browser result를 요구하면, 먼저 AWS credential 또는 public H3 origin plus non-iPhone secondary path 중 하나를 열어야 한다.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(output: Path, json_output: Path, packet: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(packet), encoding="utf-8")
    json_output.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim-dashboard", default=DEFAULT_CLAIM_DASHBOARD)
    parser.add_argument("--decision", default=DEFAULT_DECISION)
    parser.add_argument("--gate-rerun", default=DEFAULT_GATE_RERUN)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    packet = build_packet(Path(args.claim_dashboard), Path(args.decision), Path(args.gate_rerun))
    write_outputs(Path(args.output), Path(args.json_output), packet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
