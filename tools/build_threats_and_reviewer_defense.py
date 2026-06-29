#!/usr/bin/env python3
"""Build threats-to-validity and reviewer-defense chapters for the CM paper."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


CLAIMS = Path("data/paper-claim-readiness-audit-20260629.csv")
WORKLOADS = Path("data/workload-sensitivity-synthesis-20260629.csv")
FINAL_PACKET = Path("data/final-handover-trial-packet-current-20260629.json")
RECOVERY_PLAN = Path("data/public-origin-recovery-plan-20260629.json")
MATRIX_OUTPUT = Path("data/reviewer-defense-matrix-20260629.csv")
KO_OUTPUT = Path("docs/paper/threats-to-validity-and-reviewer-defense-ko-20260629.md")
EN_OUTPUT = Path("docs/paper/threats-to-validity-and-reviewer-defense-en-20260629.md")


MATRIX_FIELDS = [
    "reviewer_question_id",
    "reviewer_question",
    "current_answer",
    "current_evidence",
    "claim_boundary",
    "remaining_gap",
    "next_action",
]


REVIEWER_ROWS = [
    {
        "reviewer_question_id": "RQ-claim-browser-cm",
        "reviewer_question": "Can the study claim Chrome successfully performs HTTP/3 QUIC Connection Migration during Wi-Fi-to-cellular failover?",
        "current_answer": "No. The current evidence supports workload failure/recovery and replacement-session behavior, not publishable single-session browser CM success.",
        "current_evidence": "final protocol 3/6; Chrome no-heartbeat active rows 0/3; Chrome heartbeat active rows 0/3; public origin currently not live",
        "claim_boundary": "Do not claim Chrome single-session CM until application H3, client path change, server tuple change, qlog path validation, one Chrome target QUIC session, and task completion are present in the same row.",
        "remaining_gap": "Fresh public origin baseline and six Chrome active path-change rows.",
        "next_action": "Recover public origin, rerun baseline, then execute no-heartbeat and heartbeat active rows.",
    },
    {
        "reviewer_question_id": "RQ-implementation-maturity",
        "reviewer_question": "Is CM unused because it is not implemented?",
        "current_answer": "No. The implementation survey and controls show CM primitives exist, but deployment/runtime/observability friction limits visible web use.",
        "current_evidence": "implementation survey, quic-go/quiche positive controls, AWS NLB/CID-aware evidence, CM underuse chapter",
        "claim_boundary": "Do not collapse underuse into a single cause such as missing implementation.",
        "remaining_gap": "Broader production operator interviews or CDN/browser internal policy data would strengthen external validity.",
        "next_action": "Use the current friction matrix as paper framing and add final browser rows when infrastructure is restored.",
    },
    {
        "reviewer_question_id": "RQ-iphone-usb-generalization",
        "reviewer_question": "Does Mac+iPhone USB failover represent mobile network handover in general?",
        "current_answer": "No. It is a reproducible real client path-change trigger, but it is delayed OS failover rather than simultaneous active multipath or a complete mobile-network model.",
        "current_evidence": "iPhone USB rerun: latent_iphone_usb_failover_observed; en0 -> en8; about 1.3 s",
        "claim_boundary": "Name the setup as latent Wi-Fi-loss-to-iPhone-USB cellular failover.",
        "remaining_gap": "Android Chrome or Safari/iOS feasibility row for a more platform-diverse result.",
        "next_action": "Fill Safari or Android feasibility after public origin recovery.",
    },
    {
        "reviewer_question_id": "RQ-workload-continuity",
        "reviewer_question": "Why evaluate upload, download, Range, media, and polling instead of only connection survival?",
        "current_answer": "Because user-visible continuity is workload-dependent and can be produced by application retry, range resume, buffering, or replacement sessions.",
        "current_evidence": "upload retry0 failed 3/3 and retry1 passed 3/3; download retry and Range controls; buffered media startup/rebuffer tradeoff",
        "claim_boundary": "Task completion is not transport CM unless session continuity and path evidence also align.",
        "remaining_gap": "Public Range and buffered-media handover rows after origin recovery.",
        "next_action": "Run public page-ready Range and buffered-media trials after the first Chrome active rows.",
    },
    {
        "reviewer_question_id": "RQ-streaming",
        "reviewer_question": "Is streaming the most important CM use case?",
        "current_answer": "It is important, but it is also the easiest workload to misinterpret because buffering and segment retry can hide transport disruption.",
        "current_evidence": "buffered playback completed 12/12 locally while all rows used multiple Chrome target QUIC sessions; low buffer had rebuffer events, high buffer had startup delay",
        "claim_boundary": "Do not state CM improves streaming unless single-session evidence and QoE metrics are both present.",
        "remaining_gap": "Public buffered-media handover with startup delay, rebuffer, retry, session count, and qlog evidence.",
        "next_action": "Treat media as a QoE-aware workload after upload/download active rows.",
    },
    {
        "reviewer_question_id": "RQ-public-origin-blocker",
        "reviewer_question": "Does the current inability to run final public trials weaken the result?",
        "current_answer": "It limits browser CM success claims but does not invalidate controlled implementation results or local workload-recovery controls.",
        "current_evidence": "public origin recovery planner: DNS resolved, TCP 443 connection_refused, AWS invalid_client_token, final protocol 3/6",
        "claim_boundary": "Do not report origin-readiness failure as browser CM failure.",
        "remaining_gap": "Recover public origin and repeat fresh baseline before final active rows.",
        "next_action": "Import valid AWS credentials or restore SSH access, then rerun recovery planner.",
    },
    {
        "reviewer_question_id": "RQ-third-party-sites",
        "reviewer_question": "Can public H3 sites such as Google or Cloudflare replace a controlled origin?",
        "current_answer": "No. They can show browser H3 discovery/capability, but they cannot provide server qlog, tuple, workload, or path validation evidence.",
        "current_evidence": "public Alt-Svc scans and Chrome public discovery controls",
        "claim_boundary": "Use third-party sites only as discovery/capability controls.",
        "remaining_gap": "Controlled public origin must be live for final CM claims.",
        "next_action": "Keep third-party results out of CM success table.",
    },
    {
        "reviewer_question_id": "RQ-cdn-lb-scope",
        "reviewer_question": "How should CDN/LB deployments be interpreted?",
        "current_answer": "Managed CDN/LB environments can terminate QUIC at the edge or route by CID, so continuity claims may be edge-level or deployment-scoped rather than end-to-end browser-origin CM.",
        "current_evidence": "AWS NLB/CID controls and operational friction matrix",
        "claim_boundary": "Distinguish end-to-end QUIC CM from edge-level connection continuity or CID-aware data-plane continuity.",
        "remaining_gap": "Additional provider-specific deployment tests would broaden scope.",
        "next_action": "Present CDN/LB as deployment discussion, not final browser CM proof.",
    },
]


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    def cell(value: object) -> str:
        return str(value if value is not None else "").replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def claim_rows(claims: list[dict[str, str]]) -> list[list[str]]:
    return [
        [
            row.get("claim_id", ""),
            row.get("readiness", ""),
            row.get("safe_paper_wording", ""),
            row.get("do_not_claim", ""),
        ]
        for row in claims
    ]


def workload_rows(workloads: list[dict[str, str]]) -> list[list[str]]:
    return [
        [
            row.get("workload_class", ""),
            row.get("primary_result", ""),
            row.get("cm_evidence", ""),
            row.get("next_required_experiment", ""),
        ]
        for row in workloads
    ]


def reviewer_rows() -> list[list[str]]:
    return [
        [
            row["reviewer_question_id"],
            row["reviewer_question"],
            row["current_answer"],
            row["claim_boundary"],
            row["next_action"],
        ]
        for row in REVIEWER_ROWS
    ]


def final_state(packet: dict[str, Any], recovery: dict[str, Any]) -> list[list[str]]:
    final_completion = packet.get("final_completion") or {}
    next_step = recovery.get("next_step") or {}
    public_origin = recovery.get("public_origin") or {}
    return [
        ["final protocol", f"{final_completion.get('complete_count', '-')}/{final_completion.get('requirement_count', '-')}"],
        ["next trial", (packet.get("next_trial") or {}).get("trial_id", "-")],
        ["packet state", packet.get("state", "-")],
        ["missing gate", "; ".join(packet.get("missing_required_gates") or ["-"])],
        ["public origin", public_origin.get("classification", "-")],
        ["next recovery step", next_step.get("step_id", "-")],
    ]


def write_matrix() -> None:
    MATRIX_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with MATRIX_OUTPUT.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=MATRIX_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(REVIEWER_ROWS)


def build_ko(claims: list[dict[str, str]], workloads: list[dict[str, str]], packet: dict[str, Any], recovery: dict[str, Any]) -> str:
    date = utc_date_iso()
    return "\n".join(
        [
            "# Threats To Validity 및 Reviewer Defense",
            "",
            f"생성일: `{date}`",
            "",
            "## 목적",
            "",
            "이 장은 현재 연구 결과를 더 강하게 보이도록 포장하기 위한 문서가 아니다. 반대로, 논문 심사자가 물을 가능성이 높은 질문을 먼저 적고, 현재 증거가 허용하는 주장과 허용하지 않는 주장을 분리하기 위한 방어선이다.",
            "",
            "현재 논문의 방어 가능한 중심 주장은 다음이다.",
            "",
            "> HTTP/3/QUIC Connection Migration은 표준과 일부 구현체에서는 성숙한 primitive로 존재하지만, 웹 브라우저와 실제 작업 연속성에서는 구현체 성숙도, runtime policy, deployment path, workload semantics, application recovery가 함께 작동한다. 따라서 CM 평가는 단일 connection survival이 아니라 evidence chain과 workload-sensitive recovery로 설계되어야 한다.",
            "",
            "## 현재 최종 Gate 상태",
            "",
            markdown_table(["항목", "값"], final_state(packet, recovery)),
            "",
            "## Reviewer Defense Matrix",
            "",
            markdown_table(
                ["id", "리뷰어 질문", "현재 답변", "claim boundary", "다음 행동"],
                reviewer_rows(),
            ),
            "",
            "## Claim Readiness 요약",
            "",
            markdown_table(
                ["claim", "readiness", "쓸 수 있는 표현", "쓰면 안 되는 표현"],
                claim_rows(claims),
            ),
            "",
            "## Workload별 Threats",
            "",
            markdown_table(
                ["workload", "현재 결과", "CM evidence", "다음 실험"],
                workload_rows(workloads),
            ),
            "",
            "## Threats To Validity",
            "",
            "### Construct Validity",
            "",
            "Connection Migration 성공을 server remote tuple 변화나 작업 완료만으로 정의하면 과대해석이 된다. 본 연구는 application HTTP/3, client path change, server tuple, qlog path validation, browser session continuity, task completion을 분리해 보고한다.",
            "",
            "### Internal Validity",
            "",
            "local UDP rebinding, iPhone USB failover, application retry는 서로 다른 mechanism이다. 따라서 각 row는 `single-session CM`, `replacement-session continuity`, `application-level recovery`, `origin-readiness failure`로 분류해야 한다.",
            "",
            "### External Validity",
            "",
            "Mac+iPhone USB failover는 실제 client path-change trigger이지만 일반적인 모든 mobile handover를 대표하지 않는다. Safari 또는 Android feasibility row가 필요하며, public origin 복구 후 fresh baseline을 먼저 실행해야 한다.",
            "",
            "### Measurement Validity",
            "",
            "Chrome NetLog, server qlog, server request log, DOM dataset은 서로 다른 계층을 관찰한다. 하나의 계층만 성공해도 CM 성공이라고 말하지 않는다. 특히 streaming은 completion, startup delay, rebuffer, retry, session churn을 함께 본다.",
            "",
            "### Infrastructure Validity",
            "",
            "현재 public origin `connection_refused`와 AWS `invalid_client_token`은 final browser CM 실험의 blocker다. 이 상태에서 실행한 실패는 browser CM 실패가 아니라 origin readiness 실패다.",
            "",
            "## Reviewer에게 먼저 인정할 한계",
            "",
            "- Chrome single-session browser CM success는 아직 증명되지 않았다.",
            "- 현재 iPhone USB trigger는 delayed OS failover이지 simultaneous multipath가 아니다.",
            "- local rebinding proxy 결과는 public Wi-Fi/cellular handover로 직접 일반화하지 않는다.",
            "- managed CDN/LB 환경은 edge-level continuity와 end-to-end CM을 분리해야 한다.",
            "- streaming completion은 QoE continuity evidence일 수 있지만 transport CM success evidence는 아니다.",
            "",
            "## 논문에 넣을 안전한 결론",
            "",
            "현재까지 가장 방어 가능한 결론은 `CM이 쓸모없다`도, `Chrome에서 CM이 된다`도 아니다. 결론은 `CM을 웹 작업 연속성으로 평가하려면 구현체 성숙도와 workload recovery를 함께 봐야 하며, single-session browser CM claim에는 더 강한 evidence chain이 필요하다`이다.",
            "",
            "## Source Anchors",
            "",
            "- RFC 9000: <https://datatracker.ietf.org/doc/html/rfc9000>",
            "- RFC 9114: <https://datatracker.ietf.org/doc/html/rfc9114>",
            "- ACM CCR 2025, `An Analysis of QUIC Connection Migration in the Wild`: <https://dl.acm.org/doi/10.1145/3727063.3727066>",
            "- IETF Media over QUIC WG: <https://datatracker.ietf.org/wg/moq/about/>",
            "",
            f"재생성 명령: `python3 tools/{Path(__file__).name}`",
            "",
        ]
    )


def build_en(claims: list[dict[str, str]], workloads: list[dict[str, str]], packet: dict[str, Any], recovery: dict[str, Any]) -> str:
    date = utc_date_iso()
    return "\n".join(
        [
            "# Threats To Validity And Reviewer Defense",
            "",
            f"Generated: `{date}`",
            "",
            "## Purpose",
            "",
            "This chapter is not meant to make the current results look stronger than they are. It does the opposite: it lists likely reviewer questions and separates what the current evidence supports from what it does not yet support.",
            "",
            "The defensible central claim is:",
            "",
            "> HTTP/3/QUIC Connection Migration exists as a mature standard primitive in some implementations, but web-browser task continuity depends on implementation maturity, runtime policy, deployment path, workload semantics, and application recovery. CM evaluation therefore needs an evidence chain and workload-sensitive recovery analysis, not a single connection-survival check.",
            "",
            "## Current Final Gate State",
            "",
            markdown_table(["item", "value"], final_state(packet, recovery)),
            "",
            "## Reviewer Defense Matrix",
            "",
            markdown_table(
                ["id", "reviewer question", "current answer", "claim boundary", "next action"],
                reviewer_rows(),
            ),
            "",
            "## Claim Readiness Summary",
            "",
            markdown_table(
                ["claim", "readiness", "safe wording", "do not claim"],
                claim_rows(claims),
            ),
            "",
            "## Workload-Specific Threats",
            "",
            markdown_table(
                ["workload", "current result", "CM evidence", "next experiment"],
                workload_rows(workloads),
            ),
            "",
            "## Threats To Validity",
            "",
            "### Construct Validity",
            "",
            "Defining CM success using only server tuple changes or task completion would overclaim the result. This study separates application HTTP/3, client path change, server tuple changes, qlog path validation, browser session continuity, and task completion.",
            "",
            "### Internal Validity",
            "",
            "Local UDP rebinding, iPhone USB failover, and application retry are different mechanisms. Rows must therefore be classified as single-session CM, replacement-session continuity, application-level recovery, or origin-readiness failure.",
            "",
            "### External Validity",
            "",
            "Mac+iPhone USB failover is a real client path-change trigger, but it does not represent all mobile handover behavior. Safari or Android feasibility is still needed, and a fresh public baseline must precede final active rows.",
            "",
            "### Measurement Validity",
            "",
            "Chrome NetLog, server qlog, server request logs, and DOM datasets observe different layers. A single layer cannot prove CM success alone. Streaming especially requires completion, startup delay, rebuffering, retry, and session-churn metrics.",
            "",
            "### Infrastructure Validity",
            "",
            "The current public-origin `connection_refused` and AWS `invalid_client_token` states block final browser CM trials. A failure observed under this condition would be an origin-readiness failure, not a browser CM failure.",
            "",
            "## Limitations To Acknowledge Up Front",
            "",
            "- Chrome single-session browser CM success is not yet proven.",
            "- The current iPhone USB trigger is delayed OS failover, not simultaneous multipath.",
            "- Local rebinding proxy rows should not be directly generalized to public Wi-Fi/cellular handover.",
            "- Managed CDN/LB deployments require separating edge-level continuity from end-to-end CM.",
            "- Streaming completion can be QoE-continuity evidence without being transport-CM evidence.",
            "",
            "## Safe Conclusion For The Paper",
            "",
            "The strongest current conclusion is neither that CM is useless nor that Chrome already performs CM successfully. The safe conclusion is that evaluating CM as web task continuity requires implementation maturity and workload recovery analysis, and that single-session browser CM claims require a stronger evidence chain.",
            "",
            "## Source Anchors",
            "",
            "- RFC 9000: <https://datatracker.ietf.org/doc/html/rfc9000>",
            "- RFC 9114: <https://datatracker.ietf.org/doc/html/rfc9114>",
            "- ACM CCR 2025, `An Analysis of QUIC Connection Migration in the Wild`: <https://dl.acm.org/doi/10.1145/3727063.3727066>",
            "- IETF Media over QUIC WG: <https://datatracker.ietf.org/wg/moq/about/>",
            "",
            f"Regenerate with: `python3 tools/{Path(__file__).name}`",
            "",
        ]
    )


def main() -> int:
    claims = load_csv(CLAIMS)
    workloads = load_csv(WORKLOADS)
    packet = load_json(FINAL_PACKET)
    recovery = load_json(RECOVERY_PLAN)
    write_matrix()
    KO_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    KO_OUTPUT.write_text(build_ko(claims, workloads, packet, recovery), encoding="utf-8")
    EN_OUTPUT.write_text(build_en(claims, workloads, packet, recovery), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
