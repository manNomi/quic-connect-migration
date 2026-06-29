#!/usr/bin/env python3
"""Build current-evidence manuscript Methods/Results sections in Korean and English."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from audit_final_browser_handover_trials import build_audit
from research_clock import utc_date_iso


DEFAULT_CLAIMS = "data/paper-claim-readiness-audit-20260629.csv"
DEFAULT_WORKLOADS = "data/workload-sensitivity-synthesis-20260629.csv"
DEFAULT_EXPERIMENTS = "data/experiment-results.csv"
DEFAULT_REQUIREMENTS = "data/final-browser-handover-required-trials.csv"
DEFAULT_IPHONE = "data/iphone-usb-latent-failover-live-rerun-20260629.json"
DEFAULT_ORIGIN = "data/controlled-public-origin-access-check-rerun-20260629.json"
DEFAULT_KO_OUTPUT = "docs/paper/current-evidence-methods-results-ko-20260629.md"
DEFAULT_EN_OUTPUT = "docs/paper/current-evidence-methods-results-en-20260629.md"


KO_CLAIM_WORDING = {
    "quic-cm-is-a-real-standard-feature": {
        "safe": "QUIC은 path validation과 client-initiated migration을 위한 표준 primitive를 제공하며, 일부 구현체는 이를 명시적 API로 노출한다.",
        "avoid": "HTTP/3 브라우저가 Wi-Fi/cellular 전환에서 이 primitive를 자동으로 사용한다고 단정하지 않는다.",
    },
    "controlled-implementations-can-migrate": {
        "safe": "통제된 QUIC client와 deployment path에서는 migration 또는 CID-aware continuity를 계측된 조건에서 재현할 수 있다.",
        "avoid": "CLI/library positive control을 Chrome/Safari 브라우저 handover 성공으로 일반화하지 않는다.",
    },
    "iphone-usb-path-change-trigger-is-ready": {
        "safe": "이 Mac에서는 Wi-Fi off 명령이 재현 가능한 latent iPhone USB failover를 만들며, 명확한 claim boundary 안에서 실제 client path-change trigger로 사용할 수 있다.",
        "avoid": "이를 simultaneous active multipath로 부르지 않는다. 이 결과는 Wi-Fi에서 iPhone USB로 넘어가는 delayed OS failover다.",
    },
    "public-origin-currently-blocks-final-runs": {
        "safe": "현재 final public trial을 실행하지 못하는 이유는 infrastructure readiness blocker이며, iPhone USB path change 실패 증거가 아니다.",
        "avoid": "controlled origin이 HTTPS/H3 connection을 받지 않는 상태에서 나온 실패를 browser CM 실패로 보고하지 않는다.",
    },
    "chrome-single-session-browser-cm-not-yet-proven": {
        "safe": "현재 Chrome 증거는 workload failure/recovery와 replacement-session behavior를 보여주지만, publishable single-session browser CM success claim은 아직 지원하지 않는다.",
        "avoid": "Chrome이 Wi-Fi에서 iPhone USB로 전환되는 동안 원래 HTTP/3 connection을 성공적으로 migration했다고 쓰지 않는다.",
    },
    "upload-download-app-recovery-is-strong": {
        "safe": "대용량 upload/download에서는 application retry 또는 byte-range recovery가 visible task failure를 completion으로 바꿀 수 있지만, 이는 single-session QUIC CM과 다르다.",
        "avoid": "retry로 완료된 row를 transport-layer CM 성공으로 사용하지 않는다.",
    },
    "streaming-continuity-needs-qoe-metrics": {
        "safe": "Streaming workload는 startup delay, rebuffer event, segment retry, session churn을 함께 측정해야 하며, completion만으로 mechanism을 설명할 수 없다.",
        "avoid": "session continuity와 path validation을 동시에 증명하지 못한 row에서 CM이 streaming을 개선했다고 말하지 않는다.",
    },
    "paper-direction-is-evidence-chain-and-workload-maturity": {
        "safe": "현재 논문 방향은 CM maturity와 workload-continuity study로 잡는 것이 방어 가능하다. 즉 CM이 왜 관측/배포하기 어려운지, 어떤 workload가 gap을 드러내는지, browser CM claim 전에 어떤 evidence chain이 필요한지를 다룬다.",
        "avoid": "논문을 이미 browser/mobile HTTP/3 CM success를 증명한 연구처럼 구성하지 않는다.",
    },
}


def load_csv(path: Path) -> list[dict[str, str]]:
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
        "| " + " | ".join(cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def claim_lookup(claims: list[dict[str, str]], claim_id: str) -> dict[str, str]:
    for row in claims:
        if row.get("claim_id") == claim_id:
            return row
    return {}


def compact_claims(claims: list[dict[str, str]]) -> list[list[str]]:
    ordered_ids = [
        "quic-cm-is-a-real-standard-feature",
        "controlled-implementations-can-migrate",
        "iphone-usb-path-change-trigger-is-ready",
        "public-origin-currently-blocks-final-runs",
        "chrome-single-session-browser-cm-not-yet-proven",
        "upload-download-app-recovery-is-strong",
        "streaming-continuity-needs-qoe-metrics",
        "paper-direction-is-evidence-chain-and-workload-maturity",
    ]
    rows: list[list[str]] = []
    for claim_id in ordered_ids:
        claim = claim_lookup(claims, claim_id)
        if claim:
            rows.append(
                [
                    claim["claim_id"],
                    claim["readiness"],
                    claim["safe_paper_wording"],
                    claim["do_not_claim"],
                ]
            )
    return rows


def compact_claims_ko(claims: list[dict[str, str]]) -> list[list[str]]:
    rows: list[list[str]] = []
    for claim_id, wording in KO_CLAIM_WORDING.items():
        claim = claim_lookup(claims, claim_id)
        if claim:
            rows.append([claim_id, claim["readiness"], wording["safe"], wording["avoid"]])
    return rows


def workload_rows(workloads: list[dict[str, str]]) -> list[list[str]]:
    return [
        [
            row["workload_class"],
            row["representative_task"],
            row["primary_result"],
            row["cm_evidence"],
            row["next_required_experiment"],
        ]
        for row in workloads
    ]


def experiment_counts(experiments: list[dict[str, str]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in experiments:
        status = row.get("status") or "unknown"
        counts[status] = counts.get(status, 0) + 1
    return counts


def format_counts(counts: dict[str, int]) -> str:
    return "; ".join(f"{key}={counts[key]}" for key in sorted(counts))


def origin_summary(origin: dict[str, Any]) -> str:
    tcp = origin.get("tcp", {}).get("classification", "missing")
    aws = origin.get("aws", {}).get("classification", "missing")
    recovery = origin.get("recovery_paths", {}).get("any_recovery_path_ready", False)
    return f"tcp={tcp}; aws={aws}; recovery_path_ready={recovery}"


def iphone_summary(iphone: dict[str, Any]) -> str:
    return (
        f"classification={iphone.get('classification', 'missing')}; "
        f"ready={iphone.get('ready')}; "
        f"ready_at_ms={iphone.get('ready_at_ms')}; "
        f"path={iphone.get('before', {}).get('default_interface', '-')}->{iphone.get('after', {}).get('default_interface', '-')}"
    )


def build_ko(payload: dict[str, Any]) -> str:
    final = payload["final"]
    lines = [
        "# 현재 증거 기반 Methods/Results 장 초안",
        "",
        f"생성일: `{payload['date']}`",
        "",
        "이 문서는 현재 repository에 남아 있는 재현 가능한 artifact만 기준으로 작성한 논문 본문용 초안이다. 결론을 미리 정하지 않기 위해, 각 주장은 `claim readiness`와 `do not claim` 경계를 함께 적는다.",
        "",
        "## 연구 질문",
        "",
        "1. QUIC Connection Migration은 구현체 관점에서 어느 정도 성숙했는가?",
        "2. 브라우저 HTTP/3 환경에서 Wi-Fi에서 iPhone USB/cellular로 전환될 때 single-session CM을 관찰할 수 있는가?",
        "3. 작업 연속성은 upload, download, polling, streaming workload별로 어떻게 다르게 나타나는가?",
        "",
        "## 방법",
        "",
        "본 연구는 세 층의 증거를 분리한다.",
        "",
        "- 구현체/배포 positive control: quic-go, quiche, AWS NLB/CID-aware path에서 path validation, tuple change, application completion을 확인한다.",
        "- 브라우저 evidence chain: application HTTP/3 사용, client path change, server tuple change, qlog path validation, browser session continuity, task completion을 한 row에서 함께 요구한다.",
        "- workload continuity: upload/download/polling/media를 동일한 성공/실패 기준으로 보지 않고, retry, Range resume, buffering, rebuffer, session churn을 분리해 측정한다.",
        "",
        "## 현재 실험 corpus",
        "",
        markdown_table(
            ["항목", "값"],
            [
                ["experiment status", format_counts(payload["experiment_counts"])],
                ["final browser protocol", f"{final['complete_count']}/{final['requirement_count']} requirements complete"],
                ["final blockers", "; ".join(final["blockers"]) if final["blockers"] else "-"],
                ["iPhone USB trigger", iphone_summary(payload["iphone"])],
                ["public origin", origin_summary(payload["origin"])],
            ],
        ),
        "",
        "## Claim Readiness",
        "",
        markdown_table(
            ["claim", "readiness", "논문에 쓸 수 있는 표현", "금지할 표현"],
            compact_claims_ko(payload["claims"]),
        ),
        "",
        "## Workload별 결과",
        "",
        markdown_table(
            ["workload", "대표 작업", "주요 결과", "CM evidence", "다음 실험"],
            workload_rows(payload["workloads"]),
        ),
        "",
        "## 현재 결과 해석",
        "",
        "현재 증거는 QUIC CM이 표준과 구현체 수준에서 실재하는 기능임을 보여준다. 특히 controlled implementation 및 deployment control에서는 path validation과 tuple change가 관찰되고, application task completion도 확인된다. 그러나 이 결과를 Chrome/Safari 브라우저의 Wi-Fi/cellular handover 성공으로 일반화할 수는 없다.",
        "",
        "브라우저 쪽에서는 iPhone USB failover trigger가 준비되었지만, controlled public origin이 현재 `connection_refused` 상태다. 따라서 지금 final Chrome active network-change row를 실행하면 CM 실패가 아니라 origin readiness 실패를 만들 가능성이 높다.",
        "",
        "작업 연속성 결과는 workload-dependent하다. 대용량 upload/download는 중단이 곧 task failure로 나타나며, retry나 Range resume이 completion을 회복할 수 있다. 반면 media workload는 segment retry와 buffer depth에 따라 completion, startup delay, rebuffer event가 분리된다. 따라서 streaming은 단순 completion이 아니라 QoE metric과 session attribution을 함께 보고해야 한다.",
        "",
        "## 한계",
        "",
        "- Chrome single-session browser CM 성공은 아직 증명되지 않았다.",
        "- iPhone USB trigger는 simultaneous active multipath가 아니라 delayed OS failover다.",
        "- local UDP rebinding control은 public Wi-Fi/cellular handover threshold로 직접 일반화할 수 없다.",
        "- controlled public origin 복구 후 fresh baseline이 필요하다.",
        "- Safari 또는 Android feasibility row가 아직 없다.",
        "",
        "## 다음 실행 순서",
        "",
        "1. AWS credential 또는 SSH를 복구해 controlled public origin을 다시 연다.",
        "2. fresh Chrome controlled public H3 baseline을 재실행한다.",
        "3. Chrome downlink no-heartbeat active path-change 3회를 수행한다.",
        "4. Chrome downlink heartbeat active path-change 3회를 수행한다.",
        "5. Range/resumable download와 buffered-media public handover를 추가한다.",
        "6. Safari 또는 Android Chrome feasibility row를 채운다.",
        "",
    ]
    return "\n".join(lines)


def build_en(payload: dict[str, Any]) -> str:
    final = payload["final"]
    lines = [
        "# Current-Evidence Methods/Results Draft",
        "",
        f"Generated: `{payload['date']}`",
        "",
        "This draft is derived only from reproducible artifacts currently present in the repository. To avoid result-first writing, each positive statement is paired with an explicit claim boundary.",
        "",
        "## Research Questions",
        "",
        "1. How mature is QUIC Connection Migration across implementations and deployments?",
        "2. Can browser HTTP/3 preserve a single QUIC session across Wi-Fi to iPhone USB/cellular failover?",
        "3. How does task continuity differ across upload, download, polling, and streaming workloads?",
        "",
        "## Method",
        "",
        "The study separates three evidence layers.",
        "",
        "- Implementation/deployment positive controls: quic-go, quiche, and AWS NLB/CID-aware paths are used to verify path validation, tuple change, and application completion under instrumented conditions.",
        "- Browser evidence chain: application HTTP/3 use, client path change, server tuple change, qlog path validation, browser session continuity, and task completion must align in the same row before a browser CM success claim is allowed.",
        "- Workload continuity: upload, download, polling, and media workloads are evaluated with workload-specific failure semantics, including retry, Range resume, buffering, rebuffering, and session churn.",
        "",
        "## Current Corpus",
        "",
        markdown_table(
            ["item", "value"],
            [
                ["experiment status", format_counts(payload["experiment_counts"])],
                ["final browser protocol", f"{final['complete_count']}/{final['requirement_count']} requirements complete"],
                ["final blockers", "; ".join(final["blockers"]) if final["blockers"] else "-"],
                ["iPhone USB trigger", iphone_summary(payload["iphone"])],
                ["public origin", origin_summary(payload["origin"])],
            ],
        ),
        "",
        "## Claim Readiness",
        "",
        markdown_table(
            ["claim", "readiness", "safe paper wording", "do not claim"],
            compact_claims(payload["claims"]),
        ),
        "",
        "## Workload Results",
        "",
        markdown_table(
            ["workload", "representative task", "primary result", "CM evidence", "next experiment"],
            workload_rows(payload["workloads"]),
        ),
        "",
        "## Interpretation",
        "",
        "The current evidence supports the existence and maturity of QUIC CM primitives in controlled implementations and deployments. Instrumented controls show path validation, tuple change, and application completion. However, those controls cannot be generalized to Chrome or Safari browser handover behavior.",
        "",
        "On the browser side, the iPhone USB failover trigger is ready, but the controlled public origin currently refuses TCP 443. Running final active Chrome rows in this state would create an origin-readiness failure artifact, not meaningful browser CM evidence.",
        "",
        "Task continuity is workload-dependent. Large upload and download expose path disruption as direct task failure, while retry or Range resume can restore completion. Media workloads can complete while shifting user-visible cost into startup delay, rebuffer events, segment retry, and session churn. Therefore streaming continuity must be evaluated with QoE metrics and session attribution, not completion alone.",
        "",
        "## Limitations",
        "",
        "- Chrome single-session browser CM success has not yet been demonstrated.",
        "- The iPhone USB trigger is delayed OS failover, not simultaneous active multipath.",
        "- Local UDP rebinding controls must not be converted into public Wi-Fi/cellular threshold claims.",
        "- A fresh controlled public H3 baseline is required after origin recovery.",
        "- Safari or Android feasibility evidence is still missing.",
        "",
        "## Next Execution Order",
        "",
        "1. Restore the controlled public origin through AWS credentials or SSH.",
        "2. Rerun a fresh Chrome controlled public H3 baseline.",
        "3. Run three Chrome downlink no-heartbeat active path-change rows.",
        "4. Run three Chrome downlink heartbeat active path-change rows.",
        "5. Add public Range/resumable download and buffered-media handover rows.",
        "6. Complete one Safari or Android Chrome feasibility row.",
        "",
    ]
    return "\n".join(lines)


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    experiments = load_csv(Path(args.experiments))
    return {
        "date": utc_date_iso(),
        "claims": load_csv(Path(args.claims)),
        "workloads": load_csv(Path(args.workloads)),
        "final": build_audit(Path(args.requirements), Path(args.experiments)),
        "iphone": load_json(Path(args.iphone)),
        "origin": load_json(Path(args.origin)),
        "experiment_counts": experiment_counts(experiments),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claims", default=DEFAULT_CLAIMS)
    parser.add_argument("--workloads", default=DEFAULT_WORKLOADS)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--requirements", default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--iphone", default=DEFAULT_IPHONE)
    parser.add_argument("--origin", default=DEFAULT_ORIGIN)
    parser.add_argument("--ko-output", default=DEFAULT_KO_OUTPUT)
    parser.add_argument("--en-output", default=DEFAULT_EN_OUTPUT)
    args = parser.parse_args()

    payload = build_payload(args)
    ko_output = Path(args.ko_output)
    en_output = Path(args.en_output)
    ko_output.parent.mkdir(parents=True, exist_ok=True)
    en_output.parent.mkdir(parents=True, exist_ok=True)
    ko_output.write_text(build_ko(payload), encoding="utf-8")
    en_output.write_text(build_en(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
