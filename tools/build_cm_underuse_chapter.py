#!/usr/bin/env python3
"""Build paper-facing chapters explaining why QUIC CM is underused."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from research_clock import utc_date_iso


DEFAULT_FRICTION = "data/cm-operational-friction-matrix-20260624.csv"
DEFAULT_IMPLEMENTATIONS = "data/implementation-survey.csv"
DEFAULT_KO_OUTPUT = "docs/paper/cm-underuse-and-deployment-friction-ko-20260629.md"
DEFAULT_EN_OUTPUT = "docs/paper/cm-underuse-and-deployment-friction-en-20260629.md"


KO_LAYER = {
    "implementation": "구현체/런타임 정책",
    "browser": "브라우저/HTTP/3 discovery",
    "network": "클라이언트 path-change 증명",
    "load-balancer": "로드밸런서/CID routing",
    "proxy": "프록시/중간자 termination",
    "cdn": "CDN edge scope",
    "middlebox": "방화벽/NAT/운영 middlebox",
    "security": "보안/운영 민감도",
    "application": "애플리케이션 workload",
    "methods": "관찰성/측정 방법",
    "adoption": "도입/측정 gap",
    "performance": "성능/QoE 비용",
}

KO_LAYER_BY_ID = {
    "application-h3-discovery": "브라우저/HTTP/3 discovery",
    "session-attribution": "브라우저/session attribution",
}


KO_FRICTION = {
    "implementation-policy": {
        "claim": "CM primitive는 존재하지만 구현체와 runtime policy에 따라 실제 사용 여부가 달라진다.",
        "meaning": "QUIC stack이 migration API를 제공해도 browser, application API, default policy가 runtime migration을 막을 수 있다.",
    },
    "application-h3-discovery": {
        "claim": "HTTP/3 application request가 실제로 성립해야 CM 실험이 가능하다.",
        "meaning": "Alt-Svc나 DNS hint만으로는 충분하지 않으며, target request가 HTTP/3로 갔는지 server log와 qlog로 확인해야 한다.",
    },
    "active-path-proof": {
        "claim": "network-change 명령이 실제 active client path를 바꾸지 않을 수 있다.",
        "meaning": "interface toggle은 성공해도 route/interface/public IP가 바뀌지 않으면 CM evidence가 아니다.",
    },
    "session-attribution": {
        "claim": "tuple 변화는 CM이 아니라 replacement session일 수 있다.",
        "meaning": "브라우저는 실제 path migration 없이도 새 QUIC session을 열 수 있으므로 session continuity가 필요하다.",
    },
    "cid-load-balancing": {
        "claim": "로드밸런서는 tuple 변화 후에도 같은 logical backend로 라우팅해야 한다.",
        "meaning": "5-tuple 기반 라우팅은 migration packet을 다른 backend로 보낼 수 있어 CID-aware routing이 필요하다.",
    },
    "proxy-termination": {
        "claim": "HTTP/3 proxy 지원은 CM 지원을 의미하지 않는다.",
        "meaning": "proxy가 QUIC을 terminate하거나 path validation을 전달하지 못하면 end-to-end CM semantics가 깨진다.",
    },
    "cdn-edge-scope": {
        "claim": "CDN의 HTTP/3 CM은 origin end-to-end가 아니라 viewer-edge continuity일 수 있다.",
        "meaning": "managed CDN은 edge에서 QUIC을 terminate하므로 origin까지의 CM과 구분해야 한다.",
    },
    "middlebox-manageability": {
        "claim": "CM은 middlebox와 운영 모니터링의 5-tuple 가정을 흔든다.",
        "meaning": "NAT, firewall, rate limiter, Kubernetes service tracking은 IP/port 변화와 encrypted control plane 때문에 어려워진다.",
    },
    "security-risk": {
        "claim": "CM과 preferred address는 보안/운영 정책상 민감할 수 있다.",
        "meaning": "IP masking, censorship circumvention, exfiltration, state-table abuse 가능성 때문에 operator가 보수적으로 설정할 수 있다.",
    },
    "silent-client-downlink": {
        "claim": "downlink-dominant workload는 migration recovery를 제때 유도하지 못할 수 있다.",
        "meaning": "path change 후 client가 보낼 데이터가 없으면 detection/validation이 늦어지고 heartbeat나 retry가 recovery mechanism을 바꾼다.",
    },
    "observability-gap": {
        "claim": "browser CM evidence는 단일 artifact로 판정하기 어렵다.",
        "meaning": "NetLog, qlog, server tuple, route snapshot은 각각 빈틈이 있으므로 combined evidence chain이 필요하다.",
    },
    "measurement-gap": {
        "claim": "HTTP/3 adoption은 CM adoption이 아니다.",
        "meaning": "인터넷-wide scan에서 HTTP/3 capable server라도 CM support는 provider configuration과 deployment path에 따라 달라진다.",
    },
    "performance-risk": {
        "claim": "CM이 성공해도 stall, retransmission, QoE 비용이 남을 수 있다.",
        "meaning": "특히 media나 interactive workload는 completion뿐 아니라 startup delay, rebuffer, recovery time을 봐야 한다.",
    },
}


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    def cell(value: object) -> str:
        return str(value if value is not None else "").replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(cell(value) for value in row) + " |")
    return "\n".join(lines)


def implementation_summary(rows: list[dict[str, str]]) -> list[list[object]]:
    levels: dict[str, int] = {}
    active_yes = 0
    passive_yes = 0
    tests_yes = 0
    for row in rows:
        levels[row["current_level"]] = levels.get(row["current_level"], 0) + 1
        active_yes += 1 if row.get("active_migration_api") == "yes" else 0
        passive_yes += 1 if row.get("passive_migration") == "yes" else 0
        tests_yes += 1 if row.get("tests") == "yes" else 0
    return [
        ["surveyed implementations", len(rows)],
        ["active migration API = yes", active_yes],
        ["passive migration = yes", passive_yes],
        ["tests = yes", tests_yes],
        ["level distribution", "; ".join(f"{key}={value}" for key, value in sorted(levels.items()))],
    ]


def ko_rows(friction_rows: list[dict[str, str]]) -> list[list[object]]:
    rows: list[list[object]] = []
    for row in friction_rows:
        ko = KO_FRICTION.get(row["friction_id"], {})
        rows.append(
                [
                KO_LAYER_BY_ID.get(row["friction_id"], KO_LAYER.get(row["layer"], row["layer"])),
                ko.get("claim", row["friction"]),
                ko.get("meaning", row["why_it_discourages_or_blocks_cm"]),
                row["experiment_match_count"],
                row["literature_match_count"],
                row["paper_use"],
            ]
        )
    return rows


def en_rows(friction_rows: list[dict[str, str]]) -> list[list[object]]:
    return [
        [
            row["layer"],
            row["friction"],
            row["why_it_discourages_or_blocks_cm"],
            row["experiment_match_count"],
            row["literature_match_count"],
            row["paper_use"],
        ]
        for row in friction_rows
    ]


def build_ko(friction_rows: list[dict[str, str]], implementations: list[dict[str, str]]) -> str:
    generated = utc_date_iso()
    lines = [
        "# 왜 QUIC Connection Migration은 덜 쓰이는가",
        "",
        f"생성일: `{generated}`",
        "",
        "## 핵심 답변",
        "",
        "현재 증거 기준으로 CM이 덜 쓰이는 이유는 기술이 아예 없어서가 아니다. 주요 QUIC 구현체에는 path validation, NAT rebinding 대응, active/passive migration primitive, qlog/trace, test가 상당히 존재한다. 문제는 이 primitive가 브라우저 runtime policy, HTTP/3 discovery, 실제 client path change, load balancer routing, proxy/CDN termination, middlebox 운영, application recovery와 동시에 맞아야 user-visible continuity로 나타난다는 점이다.",
        "",
        "따라서 논문에서는 `CM 미사용 = 구현 부재`로 단순화하지 않는다. 더 정확한 framing은 다음과 같다.",
        "",
        "> QUIC CM is implemented unevenly and deployed conservatively because transport support is only one layer. Browser policy, endpoint discovery, routing, observability, workload semantics, and operational risk decide whether CM becomes visible application continuity.",
        "",
        "## 구현체 성숙도 요약",
        "",
        markdown_table(["metric", "value"], implementation_summary(implementations)),
        "",
        "## Layer별 friction",
        "",
        markdown_table(
            ["layer", "논문용 주장", "의미", "repo evidence rows", "literature matches", "paper use"],
            ko_rows(friction_rows),
        ),
        "",
        "## 논문에서 사용할 결론",
        "",
        "1. CM은 표준과 구현체 수준에서 존재한다.",
        "2. HTTP/3 지원은 CM 지원과 다르다.",
        "3. 브라우저에서는 application H3 baseline, client path change, tuple change, qlog path validation, session continuity, task completion을 한 row에서 동시에 보여야 한다.",
        "4. Load balancer/CDN/proxy는 CM을 end-to-end로 보존하지 않을 수 있다.",
        "5. 많은 웹 workload는 retry, Range resume, buffering, reconnect로 사용자 경험을 복구하므로 transport CM 부재가 숨겨질 수 있다.",
        "6. 반대로 upload/download 같은 long-lived task는 CM 부재가 직접 task failure로 드러난다.",
        "",
        "## 현재 연구와의 연결",
        "",
        "본 repo의 실험은 이 friction을 직접 반영한다. quic-go/quiche/AWS NLB positive control은 transport/deployment CM 가능성을 보여준다. HAProxy, browser Alt-Svc, inactive interface toggle, multiple-session, return-path outage, public iPhone USB rows는 HTTP/3 또는 tuple 변화만으로 browser CM을 주장할 수 없음을 보여준다. Upload/download/Range/media 결과는 application-level recovery와 workload semantics가 작업 연속성의 핵심 변수임을 보여준다.",
        "",
        "## 아직 필요한 증거",
        "",
        "- controlled public origin 복구 후 fresh Chrome H3 baseline",
        "- Chrome no-heartbeat active path-change 3회",
        "- Chrome heartbeat active path-change 3회",
        "- Safari 또는 Android feasibility 1회",
        "- public Range 및 buffered-media handover row",
        "",
    ]
    return "\n".join(lines)


def build_en(friction_rows: list[dict[str, str]], implementations: list[dict[str, str]]) -> str:
    generated = utc_date_iso()
    lines = [
        "# Why QUIC Connection Migration Is Underused",
        "",
        f"Generated: `{generated}`",
        "",
        "## Core Answer",
        "",
        "The current evidence does not support the simple answer that CM is unused because it is unimplemented. Major QUIC stacks expose path validation, NAT rebinding handling, active or passive migration primitives, qlog/tracing, and tests. The harder problem is that those transport primitives must align with browser runtime policy, HTTP/3 endpoint discovery, real client path change, load-balancer routing, proxy/CDN termination, middlebox operations, and application recovery before users see continuity.",
        "",
        "The paper should therefore use this framing:",
        "",
        "> QUIC CM is implemented unevenly and deployed conservatively because transport support is only one layer. Browser policy, endpoint discovery, routing, observability, workload semantics, and operational risk decide whether CM becomes visible application continuity.",
        "",
        "## Implementation Maturity Summary",
        "",
        markdown_table(["metric", "value"], implementation_summary(implementations)),
        "",
        "## Layered Friction",
        "",
        markdown_table(
            ["layer", "friction", "why it blocks or discourages CM", "repo evidence rows", "literature matches", "paper use"],
            en_rows(friction_rows),
        ),
        "",
        "## Paper-Level Conclusion",
        "",
        "1. CM exists in the standard and in mature implementations.",
        "2. HTTP/3 support is not equivalent to CM support.",
        "3. Browser evidence requires application H3 use, client path change, tuple change, qlog path validation, session continuity, and task completion in the same row.",
        "4. Load balancers, CDNs, and proxies may not preserve end-to-end CM semantics.",
        "5. Many web workloads hide missing transport CM through retry, Range resume, buffering, reconnect, or replacement sessions.",
        "6. Long-lived upload/download tasks expose missing transport continuity more directly as task failure.",
        "",
        "## Link To Current Evidence",
        "",
        "The repository mirrors these frictions. quic-go, quiche, and AWS NLB controls show transport/deployment feasibility. HAProxy, browser Alt-Svc, inactive interface toggles, multiple-session rows, return-path outage controls, and public iPhone USB rows show why HTTP/3 or tuple change alone is insufficient. Upload, download, Range, and media results show that application-level recovery and workload semantics dominate task continuity.",
        "",
        "## Remaining Evidence Needed",
        "",
        "- Fresh Chrome H3 baseline after controlled public origin recovery.",
        "- Three Chrome no-heartbeat active path-change rows.",
        "- Three Chrome heartbeat active path-change rows.",
        "- One Safari or Android feasibility row.",
        "- Public Range and buffered-media handover rows.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--friction", default=DEFAULT_FRICTION)
    parser.add_argument("--implementations", default=DEFAULT_IMPLEMENTATIONS)
    parser.add_argument("--ko-output", default=DEFAULT_KO_OUTPUT)
    parser.add_argument("--en-output", default=DEFAULT_EN_OUTPUT)
    args = parser.parse_args()

    friction_rows = load_csv(Path(args.friction))
    implementations = load_csv(Path(args.implementations))

    ko_output = Path(args.ko_output)
    en_output = Path(args.en_output)
    ko_output.parent.mkdir(parents=True, exist_ok=True)
    en_output.parent.mkdir(parents=True, exist_ok=True)
    ko_output.write_text(build_ko(friction_rows, implementations), encoding="utf-8")
    en_output.write_text(build_en(friction_rows, implementations), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
