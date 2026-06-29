#!/usr/bin/env python3
"""Build current-evidence paper skeletons in Korean and English."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_CLAIMS = "data/paper-claim-readiness-audit-20260629.csv"
DEFAULT_WORKLOADS = "data/workload-sensitivity-synthesis-20260629.csv"
DEFAULT_IPHONE = "data/iphone-usb-latent-failover-live-rerun-20260629.json"
DEFAULT_ORIGIN = "data/controlled-public-origin-access-check-rerun-20260629.json"
DEFAULT_KO_OUTPUT = "docs/paper/current-evidence-paper-skeleton-ko-20260629.md"
DEFAULT_EN_OUTPUT = "docs/paper/current-evidence-paper-skeleton-en-20260629.md"


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def claim(claims: list[dict[str, str]], claim_id: str, field: str) -> str:
    for row in claims:
        if row.get("claim_id") == claim_id:
            return row.get(field, "")
    return ""


def workload_result(workloads: list[dict[str, str]], workload_class: str) -> str:
    for row in workloads:
        if row.get("workload_class") == workload_class:
            return row.get("primary_result", "")
    return ""


def iphone_line(iphone: dict[str, Any]) -> str:
    return (
        f"{iphone.get('classification', 'missing')}, "
        f"{iphone.get('before', {}).get('default_interface', '-')} -> "
        f"{iphone.get('after', {}).get('default_interface', '-')}, "
        f"{iphone.get('ready_at_ms', '-')} ms"
    )


def origin_line(origin: dict[str, Any]) -> str:
    return (
        f"TCP {origin.get('tcp', {}).get('classification', 'missing')}, "
        f"AWS {origin.get('aws', {}).get('classification', 'missing')}"
    )


def build_ko(claims: list[dict[str, str]], workloads: list[dict[str, str]], iphone: dict[str, Any], origin: dict[str, Any]) -> str:
    date = utc_date_iso()
    upload = workload_result(workloads, "large_upload")
    download = workload_result(workloads, "large_download")
    media = workload_result(workloads, "media_segments")
    music = workload_result(workloads, "music_like_buffered")
    lines = [
        "# 현재 증거 기반 논문 Skeleton",
        "",
        f"생성일: `{date}`",
        "",
        "## 추천 제목",
        "",
        "HTTP/3/QUIC Connection Migration의 구현 성숙도와 웹 작업 연속성: Evidence Chain 및 Workload-Sensitive Recovery 분석",
        "",
        "## 대체 제목",
        "",
        "- Wi-Fi-to-Cellular Failover 환경에서 HTTP/3/QUIC Connection Migration 성숙도와 웹 작업 연속성 평가",
        "- QUIC Connection Migration은 왜 웹에서 잘 보이지 않는가: 구현체 성숙도, 배포 friction, 작업 연속성 분석",
        "",
        "## 초록 초안",
        "",
        "QUIC Connection Migration은 endpoint의 IP 주소나 포트가 바뀌어도 connection continuity를 유지할 수 있도록 설계된 transport 기능이다. 그러나 HTTP/3 웹 애플리케이션에서 이 기능이 실제 작업 연속성으로 이어지는지는 구현체, 브라우저 runtime policy, endpoint discovery, load balancer routing, proxy/CDN termination, client path-change proof, application recovery strategy에 의해 달라진다. 본 연구는 QUIC 구현체와 배포 경로의 CM 성숙도를 조사하고, Chrome HTTP/3 workload에서 upload, download, polling, streaming 작업이 path disruption과 application-level recovery에 어떻게 반응하는지 분석한다. 현재 증거는 controlled QUIC implementation과 deployment에서는 path validation과 tuple change가 재현 가능함을 보여주지만, Chrome single-session browser CM 성공은 아직 증명하지 못한다. 반면 대용량 upload/download, Range resume, media buffering 실험은 작업 연속성이 transport CM뿐 아니라 retry, replacement session, buffering, QoE tradeoff에 의해 결정됨을 보여준다. 따라서 본 연구는 HTTP/3 CM 평가가 단순 connection 유지 여부가 아니라 evidence chain과 workload semantics를 함께 포함해야 한다고 주장한다.",
        "",
        "## 핵심 기여",
        "",
        "1. QUIC CM 구현체 성숙도를 active/passive migration, API 노출, qlog/trace, test, deployment suitability 기준으로 정리했다.",
        "2. browser CM claim에 필요한 evidence chain을 application H3, client path change, server tuple, qlog path validation, browser session continuity, task completion으로 정의했다.",
        "3. CM이 덜 쓰이는 이유를 구현체 부재가 아니라 runtime policy, endpoint discovery, session attribution, CID-aware routing, proxy/CDN, middlebox, security, workload recovery, observability friction으로 분해했다.",
        "4. upload/download/Range/media workload 결과를 통해 작업 연속성이 retry, Range resume, buffering, replacement-session behavior와 결합되어 나타남을 보였다.",
        "5. 현재 Mac+iPhone 실험에서는 `latent Wi-Fi-loss-to-iPhone-USB cellular failover` trigger가 준비됐지만, controlled public origin 복구 전까지 final browser CM success claim은 보류해야 함을 명확히 했다.",
        "",
        "## 현재 주요 결과",
        "",
        f"- iPhone USB trigger: `{iphone_line(iphone)}`",
        f"- public origin blocker: `{origin_line(origin)}`",
        f"- upload: {upload}",
        f"- download: {download}",
        f"- media segments/buffered playback: {media}",
        f"- music-like buffered media: {music}",
        f"- Chrome single-session browser CM: {claim(claims, 'chrome-single-session-browser-cm-not-yet-proven', 'readiness')}",
        "",
        "## 권장 논문 구조",
        "",
        "1. Introduction",
        "   - QUIC CM의 promise와 HTTP/3 웹 작업 연속성 gap",
        "   - 왜 `HTTP/3 지원`과 `CM 지원`을 분리해야 하는가",
        "2. Background",
        "   - RFC 9000 CM, Connection ID, path validation",
        "   - HTTP/3 discovery와 browser/runtime policy",
        "3. Implementation And Deployment Maturity",
        "   - 구현체 survey",
        "   - quic-go/quiche/AWS NLB positive controls",
        "4. Evidence Chain Methodology",
        "   - CM success 판정 기준",
        "   - negative controls와 overclaim 방지",
        "5. Workload Continuity Experiments",
        "   - upload/download",
        "   - Range/resumable download",
        "   - polling/dashboard",
        "   - media segments/buffered playback",
        "6. Why CM Is Underused",
        "   - layered friction matrix",
        "   - browser/session/deployment/application/observability 원인",
        "7. Discussion",
        "   - application recovery와 transport CM의 관계",
        "   - managed CDN/LB 환경의 claim boundary",
        "8. Limitations And Future Work",
        "   - public origin recovery, fresh baseline, final active rows",
        "   - Safari/Android/Cronet follow-up",
        "",
        "## 표/그림 후보",
        "",
        "- Table 1: QUIC implementation CM maturity survey",
        "- Table 2: Browser CM evidence chain rubric",
        "- Table 3: Operational friction matrix",
        "- Table 4: Workload sensitivity synthesis",
        "- Figure 1: Transport CM vs application-level recovery boundary",
        "- Figure 2: Browser final handover evidence chain",
        "- Figure 3: Streaming buffer depth vs rebuffer/startup tradeoff",
        "",
        "## 지금 쓰면 안 되는 문장",
        "",
        "- Chrome은 Wi-Fi-to-cellular failover 중 HTTP/3 connection migration에 성공했다.",
        "- HTTP/3를 지원하는 서버는 Connection Migration도 지원한다.",
        "- tuple이 바뀌었으므로 CM이 성공했다.",
        "- streaming workload completion은 CM이 잘 작동한다는 증거다.",
        "",
        "## 다음 실험이 채워야 할 빈칸",
        "",
        "- controlled public origin fresh baseline",
        "- Chrome no-heartbeat active path-change 3회",
        "- Chrome heartbeat active path-change 3회",
        "- public Range handover",
        "- public buffered-media handover",
        "- Safari 또는 Android feasibility row",
        "",
    ]
    return "\n".join(lines)


def build_en(claims: list[dict[str, str]], workloads: list[dict[str, str]], iphone: dict[str, Any], origin: dict[str, Any]) -> str:
    date = utc_date_iso()
    upload = workload_result(workloads, "large_upload")
    download = workload_result(workloads, "large_download")
    media = workload_result(workloads, "media_segments")
    music = workload_result(workloads, "music_like_buffered")
    lines = [
        "# Current-Evidence Paper Skeleton",
        "",
        f"Generated: `{date}`",
        "",
        "## Recommended Title",
        "",
        "QUIC Connection Migration Maturity and Web Task Continuity: An Evidence-Chain and Workload-Sensitive Recovery Study",
        "",
        "## Alternate Titles",
        "",
        "- Evaluating HTTP/3/QUIC Connection Migration Maturity and Web Task Continuity under Wi-Fi-to-Cellular Failover",
        "- Why QUIC Connection Migration Remains Hard To Observe On The Web: Implementation Maturity, Deployment Friction, and Workload Continuity",
        "",
        "## Abstract Draft",
        "",
        "QUIC Connection Migration is designed to preserve connection continuity when an endpoint's IP address or port changes. In HTTP/3 web applications, however, whether this transport feature becomes user-visible task continuity depends on implementation maturity, browser runtime policy, endpoint discovery, load-balancer routing, proxy/CDN termination, client path-change proof, and application recovery strategy. This study surveys QUIC CM maturity across implementations and deployment paths, and evaluates how Chrome HTTP/3 workloads such as upload, download, polling, and streaming respond to path disruption and application-level recovery. Current evidence shows that controlled QUIC implementations and deployments can reproduce path validation and tuple changes, but it does not yet prove Chrome single-session browser CM success. Large upload/download, Range resume, and media buffering results instead show that task continuity is shaped by retry, replacement sessions, buffering, and QoE tradeoffs. The paper therefore argues that HTTP/3 CM evaluation requires an evidence chain and workload semantics, not only a binary connection-continuity test.",
        "",
        "## Contributions",
        "",
        "1. A maturity survey of QUIC CM implementations across active/passive migration, API exposure, qlog/tracing, tests, and deployment suitability.",
        "2. A browser CM evidence chain requiring application H3 use, client path change, server tuple change, qlog path validation, browser session continuity, and task completion.",
        "3. A layered explanation for why CM is underused: runtime policy, endpoint discovery, session attribution, CID-aware routing, proxy/CDN termination, middleboxes, security risk, workload recovery, and observability.",
        "4. A workload-continuity analysis showing that upload/download, Range resume, and media buffering expose different failure and recovery mechanisms.",
        "5. A clear boundary for the current Mac+iPhone setup: the latent Wi-Fi-loss-to-iPhone-USB cellular failover trigger is ready, but final browser CM success remains pending until the controlled public origin is restored and final rows are completed.",
        "",
        "## Current Key Results",
        "",
        f"- iPhone USB trigger: `{iphone_line(iphone)}`",
        f"- public origin blocker: `{origin_line(origin)}`",
        f"- upload: {upload}",
        f"- download: {download}",
        f"- media segments/buffered playback: {media}",
        f"- music-like buffered media: {music}",
        f"- Chrome single-session browser CM: {claim(claims, 'chrome-single-session-browser-cm-not-yet-proven', 'readiness')}",
        "",
        "## Recommended Paper Structure",
        "",
        "1. Introduction",
        "2. Background",
        "3. Implementation And Deployment Maturity",
        "4. Evidence Chain Methodology",
        "5. Workload Continuity Experiments",
        "6. Why CM Is Underused",
        "7. Discussion",
        "8. Limitations And Future Work",
        "",
        "## Candidate Tables And Figures",
        "",
        "- Table 1: QUIC implementation CM maturity survey",
        "- Table 2: Browser CM evidence chain rubric",
        "- Table 3: Operational friction matrix",
        "- Table 4: Workload sensitivity synthesis",
        "- Figure 1: Transport CM vs application-level recovery boundary",
        "- Figure 2: Browser final handover evidence chain",
        "- Figure 3: Streaming buffer depth vs rebuffer/startup tradeoff",
        "",
        "## Sentences To Avoid For Now",
        "",
        "- Chrome successfully migrated the HTTP/3 connection during Wi-Fi-to-cellular failover.",
        "- Servers that support HTTP/3 also support Connection Migration.",
        "- The tuple changed, therefore CM succeeded.",
        "- Streaming workload completion proves that CM works well.",
        "",
        "## Remaining Experiment Gaps",
        "",
        "- Fresh controlled public origin baseline.",
        "- Three Chrome no-heartbeat active path-change rows.",
        "- Three Chrome heartbeat active path-change rows.",
        "- Public Range handover.",
        "- Public buffered-media handover.",
        "- One Safari or Android feasibility row.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claims", default=DEFAULT_CLAIMS)
    parser.add_argument("--workloads", default=DEFAULT_WORKLOADS)
    parser.add_argument("--iphone", default=DEFAULT_IPHONE)
    parser.add_argument("--origin", default=DEFAULT_ORIGIN)
    parser.add_argument("--ko-output", default=DEFAULT_KO_OUTPUT)
    parser.add_argument("--en-output", default=DEFAULT_EN_OUTPUT)
    args = parser.parse_args()

    claims = load_csv(Path(args.claims))
    workloads = load_csv(Path(args.workloads))
    iphone = load_json(Path(args.iphone))
    origin = load_json(Path(args.origin))
    ko_output = Path(args.ko_output)
    en_output = Path(args.en_output)
    ko_output.parent.mkdir(parents=True, exist_ok=True)
    en_output.parent.mkdir(parents=True, exist_ok=True)
    ko_output.write_text(build_ko(claims, workloads, iphone, origin), encoding="utf-8")
    en_output.write_text(build_en(claims, workloads, iphone, origin), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
