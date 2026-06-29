#!/usr/bin/env python3
"""Build a literature-to-claim positioning matrix for the QUIC CM paper."""

from __future__ import annotations

import csv
from pathlib import Path

from research_clock import utc_date_iso


MATRIX_OUTPUT = Path("data/literature-claim-positioning-20260629.csv")
KO_OUTPUT = Path("docs/results/literature-claim-positioning-20260629.md")
EN_OUTPUT = Path("docs/paper/literature-claim-positioning-en-20260629.md")


MATRIX_FIELDS = [
    "source_id",
    "grade",
    "claim_axis",
    "source",
    "year",
    "source_type",
    "url",
    "paper_use",
    "supports",
    "does_not_support",
    "experiment_gap",
    "next_experiment_or_analysis",
]


SOURCE_ROWS = [
    {
        "source_id": "ccr2025-wild-cm",
        "grade": "A",
        "claim_axis": "deployment reality / support unevenness",
        "source": "An Analysis of QUIC Connection Migration in the Wild",
        "year": "2025",
        "source_type": "peer-reviewed measurement paper",
        "url": "https://dl.acm.org/doi/10.1145/3727063.3727066",
        "paper_use": "Primary related-work anchor and gap statement.",
        "supports": "Internet-wide QUIC CM support is uneven, so a failure-layer study is justified.",
        "does_not_support": "It does not prove why each endpoint fails, nor does it prove browser workload continuity.",
        "experiment_gap": "Need controlled decomposition into application H3, path change, path validation, session continuity, and task completion.",
        "next_experiment_or_analysis": "Use this as the opening related-work anchor and compare our evidence-chain protocol against its support-scanning boundary.",
    },
    {
        "source_id": "rfc9000-cm",
        "grade": "A",
        "claim_axis": "standard primitive",
        "source": "QUIC: A UDP-Based Multiplexed and Secure Transport",
        "year": "2021",
        "source_type": "IETF standard",
        "url": "https://datatracker.ietf.org/doc/html/rfc9000",
        "paper_use": "Normative background for CID, path validation, NAT rebinding, and client migration.",
        "supports": "QUIC has standardized primitives that allow a connection to survive address changes when endpoint and deployment conditions permit.",
        "does_not_support": "Path validation is necessary but not sufficient for HTTP/3 browser task continuity.",
        "experiment_gap": "Need qlog path-validation evidence plus browser session and workload evidence in the same row.",
        "next_experiment_or_analysis": "Keep qlog PATH_CHALLENGE/PATH_RESPONSE as a necessary evidence-chain column, not the final success criterion.",
    },
    {
        "source_id": "rfc9114-h3-discovery",
        "grade": "A",
        "claim_axis": "HTTP/3 endpoint discovery",
        "source": "HTTP/3",
        "year": "2022",
        "source_type": "IETF standard",
        "url": "https://datatracker.ietf.org/doc/html/rfc9114",
        "paper_use": "Explains why application H3 baseline is a separate gate before CM testing.",
        "supports": "A browser must first discover and choose an HTTP/3 endpoint before transport migration can matter for a web workload.",
        "does_not_support": "It does not imply that an HTTP/3-capable origin or Alt-Svc advertisement enables migration.",
        "experiment_gap": "Need fresh public application-H3 baseline after origin recovery.",
        "next_experiment_or_analysis": "Run a no-change controlled public Chrome H3 baseline before active network-change rows.",
    },
    {
        "source_id": "rfc9308-rfc9312-ops",
        "grade": "A",
        "claim_axis": "operational manageability",
        "source": "RFC 9308 and RFC 9312",
        "year": "2022",
        "source_type": "IETF operational RFCs",
        "url": "https://www.rfc-editor.org/rfc/rfc9308.html",
        "paper_use": "Operational caution for UDP timeouts, NAT rebinding, CID choices, and manageability limits.",
        "supports": "Deployment maturity is separate from transport feature existence.",
        "does_not_support": "It does not measure browser behavior or quantify CM adoption by itself.",
        "experiment_gap": "Need deployment controls: direct origin, CID-aware load balancer, CDN/edge distinction, proxy negative controls.",
        "next_experiment_or_analysis": "Use operational RFCs to justify the maturity-axis rubric and threat model.",
    },
    {
        "source_id": "chromium-cronet-policy",
        "grade": "A",
        "claim_axis": "browser/runtime policy",
        "source": "Chromium QUIC migration parameters and Android Cronet ConnectionMigrationOptions",
        "year": "2026",
        "source_type": "official source/API documentation",
        "url": "https://developer.android.com/develop/connectivity/cronet/reference/org/chromium/net/ConnectionMigrationOptions",
        "paper_use": "Shows that client runtime policy exists and must be separated from transport capability.",
        "supports": "Browser-family stacks expose migration-related policy knobs for network change, path degradation, idle migration, and non-default network use.",
        "does_not_support": "API/source hooks do not prove that Chrome or Safari actually migrated a live browser HTTP/3 session in our scenario.",
        "experiment_gap": "Need NetLog migration trigger/success/failure evidence and controlled Android/Cronet feasibility rows.",
        "next_experiment_or_analysis": "Prioritize Chrome NetLog active rows, then Android/Cronet after a device and policy artifact are available.",
    },
    {
        "source_id": "quic-go-docs",
        "grade": "A",
        "claim_axis": "implementation positive control",
        "source": "quic-go Connection Migration documentation",
        "year": "2026",
        "source_type": "implementation documentation",
        "url": "https://quic-go.net/docs/quic/connection-migration/",
        "paper_use": "Positive-control implementation model for explicit path add/probe/switch behavior.",
        "supports": "Some QUIC implementations expose concrete migration controls and path probing behavior.",
        "does_not_support": "A library positive control does not generalize to browser HTTP/3 handover behavior.",
        "experiment_gap": "Need to contrast local quic-go positive controls with browser runtime and deployment evidence.",
        "next_experiment_or_analysis": "Keep quic-go as controlled implementation evidence and avoid using it as browser CM proof.",
    },
    {
        "source_id": "ietf-multipath",
        "grade": "A",
        "claim_axis": "standards trajectory",
        "source": "Managing multiple paths for a QUIC connection",
        "year": "2026",
        "source_type": "IETF QUIC WG draft",
        "url": "https://datatracker.ietf.org/doc/draft-ietf-quic-multipath/",
        "paper_use": "Future-work and scoping source.",
        "supports": "QUIC path work is moving toward richer multipath/path-management mechanisms rather than abandoning mobility.",
        "does_not_support": "Multipath support does not prove RFC 9000 single-path browser CM in today's Chrome/Safari.",
        "experiment_gap": "Need to keep the paper scoped to single-path browser CM unless using a multipath-enabled stack.",
        "next_experiment_or_analysis": "Use as future work and terminology boundary, not as evidence for current browser success.",
    },
    {
        "source_id": "swiftshift-2026",
        "grade": "B",
        "claim_axis": "interactive media / QoE sensitivity",
        "source": "SwiftShift: Accelerating QUIC Migration for Ultra-Low-Latency Interactive Media",
        "year": "2026",
        "source_type": "peer-reviewed media systems paper",
        "url": "https://dl.acm.org/doi/10.1145/3798065.3798080",
        "paper_use": "Motivation for media QoE metrics and migration overhead discussion.",
        "supports": "Even when QUIC migration exists, migration delay and recovery behavior can matter for low-latency media.",
        "does_not_support": "It does not prove vanilla browser HTTP/3 media continuity or our specific iPhone USB handover behavior.",
        "experiment_gap": "Need media rows with startup delay, rebuffering, retry, session count, and path evidence.",
        "next_experiment_or_analysis": "Treat streaming as QoE-aware workload after upload/download active rows, not as the first CM proof target.",
    },
    {
        "source_id": "encor-2026",
        "grade": "B",
        "claim_axis": "mobile handover / application continuity",
        "source": "EnCoR: An end-to-end architecture for simplifying cellular networks",
        "year": "2026",
        "source_type": "preprint / architecture paper",
        "url": "https://arxiv.org/html/2605.22524v2",
        "paper_use": "Mobile-network adjacent evidence that application behavior can matter after handover.",
        "supports": "Handover and application continuity can fail in edge cases when endpoint traffic and detection timing do not align.",
        "does_not_support": "It does not replace direct browser Wi-Fi/cellular HTTP/3 CM measurement.",
        "experiment_gap": "Need silent-client downlink and heartbeat variants under active path change.",
        "next_experiment_or_analysis": "Keep no-heartbeat vs heartbeat rows as P1 because they directly test this failure mode.",
    },
    {
        "source_id": "qasm-2026",
        "grade": "B",
        "claim_axis": "middlebox manageability",
        "source": "QASM: A Novel Framework for QUIC-Aware Stateful Middleboxes",
        "year": "2026",
        "source_type": "preprint / middlebox systems paper",
        "url": "https://arxiv.org/abs/2602.03354",
        "paper_use": "Explains operational reluctance and middlebox state tracking friction.",
        "supports": "QUIC encryption and address migration complicate middlebox state, NAT, rate limiting, load balancing, and service tracking.",
        "does_not_support": "It does not measure our browser workloads or prove a specific public-origin failure cause.",
        "experiment_gap": "Need to classify failures as browser policy, deployment routing, middlebox/proxy, or application recovery rather than one CM failure bucket.",
        "next_experiment_or_analysis": "Use in the 'why CM may not be widely enabled' section and the deployment-maturity rubric.",
    },
    {
        "source_id": "quicstep-2026",
        "grade": "B",
        "claim_axis": "security / censorship circumvention",
        "source": "QUICstep: Evaluating connection migration based QUIC censorship circumvention",
        "year": "2026",
        "source_type": "privacy/security paper",
        "url": "https://petsymposium.org/popets/2026/popets-2026-0014.php",
        "paper_use": "Shows that CM can be a valuable and sensitive primitive beyond mobility.",
        "supports": "Connection migration has security/privacy use cases and can be used as a support-measurement signal.",
        "does_not_support": "It does not imply operators should always enable CM or that browsers expose it for web workloads.",
        "experiment_gap": "Need a neutral maturity framing that includes value, abuse risk, and operational caution.",
        "next_experiment_or_analysis": "Use in related work and reviewer defense, not as continuity evidence.",
    },
    {
        "source_id": "quic-exfil-2025",
        "grade": "B",
        "claim_axis": "security misuse / preferred address",
        "source": "QUIC-Exfil: Exploiting QUIC's Server Preferred Address Feature to Perform Data Exfiltration Attacks",
        "year": "2025",
        "source_type": "peer-reviewed security paper / preprint available",
        "url": "https://arxiv.org/abs/2505.05292",
        "paper_use": "Operational caution for preferred-address and server-side migration features.",
        "supports": "Migration-related features can create monitoring and policy risks, explaining some deployment caution.",
        "does_not_support": "Preferred-address misuse is not the same mechanism as RFC 9000 client Wi-Fi/cellular migration.",
        "experiment_gap": "Need to distinguish client migration, server preferred address, server-initiated migration, and multipath in terminology.",
        "next_experiment_or_analysis": "Use for security discussion and terminology boundaries only.",
    },
    {
        "source_id": "aws-nlb-quic",
        "grade": "A",
        "claim_axis": "managed deployment / CID-aware routing",
        "source": "AWS Network Load Balancer QUIC protocol support",
        "year": "2025",
        "source_type": "cloud provider documentation/blog",
        "url": "https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-quic-protocol-support-for-network-load-balancer-accelerating-mobile-first-applications/",
        "paper_use": "Deployment control for CID-aware routing and managed cloud feasibility.",
        "supports": "Managed deployments may need QUIC-aware CID routing to preserve continuity across tuple changes.",
        "does_not_support": "A load balancer's CID-aware behavior is not the same as end-to-end browser-origin single-session migration.",
        "experiment_gap": "Need to separate direct-origin, LB, CDN edge, and third-party public H3 cases.",
        "next_experiment_or_analysis": "Use after public-origin recovery for cloud deployment discussion, not as a substitute for Chrome active rows.",
    },
]


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    def cell(value: object) -> str:
        return str(value if value is not None else "").replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def write_matrix() -> None:
    MATRIX_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with MATRIX_OUTPUT.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=MATRIX_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(SOURCE_ROWS)


def compact_rows() -> list[list[str]]:
    return [
        [
            row["source_id"],
            row["grade"],
            row["claim_axis"],
            row["paper_use"],
            row["supports"],
            row["does_not_support"],
            row["experiment_gap"],
        ]
        for row in SOURCE_ROWS
    ]


def source_list() -> list[str]:
    return [f"- `{row['source_id']}`: [{row['source']}]({row['url']})" for row in SOURCE_ROWS]


def build_ko() -> str:
    date = utc_date_iso()
    return "\n".join(
        [
            "# Literature Claim Positioning Matrix",
            "",
            f"생성일: `{date}`",
            "",
            "## 목적",
            "",
            "이 문서는 QUIC Connection Migration 관련 최신 문헌을 현재 실험 결과와 연결한다. 결론을 먼저 정하고 문헌을 끼워 맞추지 않기 위해, 각 source마다 `supports`, `does_not_support`, `experiment_gap`을 분리했다.",
            "",
            "현재 논문 방향에서 가장 중요한 판단은 다음이다.",
            "",
            "1. CM은 표준과 일부 구현체에서 실재하고, multipath/media/edge/security 연구로 계속 확장되는 active topic이다.",
            "2. 하지만 그 사실만으로 Chrome/Safari HTTP/3 single-session handover 성공을 주장할 수는 없다.",
            "3. CM이 덜 쓰이거나 덜 보이는 이유는 구현 부재 하나가 아니라 browser runtime policy, deployment routing, middlebox manageability, security concern, application recovery가 겹친 문제다.",
            "4. 따라서 본 연구의 기여는 `CM이 된다/안 된다`가 아니라 `어느 계층의 어떤 증거가 있어야 browser web task continuity를 주장할 수 있는가`를 계측하는 쪽이 더 방어 가능하다.",
            "",
            "## Positioning Matrix",
            "",
            markdown_table(
                ["source", "grade", "claim axis", "paper use", "supports", "does not support", "experiment gap"],
                compact_rows(),
            ),
            "",
            "## 논문 주장에 주는 영향",
            "",
            "### 강해진 주장",
            "",
            "- QUIC CM은 버려진 기능이 아니다. RFC 9000의 primitive, IETF multipath draft, SwiftShift 같은 media migration 연구, cloud/LB 문서가 모두 active path-management 흐름을 보여준다.",
            "- `왜 안 쓰이는가`는 구현 여부보다 deployment/runtime/observability 질문으로 바꿔야 한다. QASM, RFC 9308/9312, AWS NLB, QUIC-Exfil은 운영자가 CM을 조심스럽게 다룰 이유를 제공한다.",
            "- streaming은 중요한 use case지만, completion만 보면 오해하기 쉽다. buffer, segment retry, startup delay, rebuffer, session churn을 같이 측정해야 한다.",
            "",
            "### 약해졌거나 아직 보류해야 할 주장",
            "",
            "- Chrome/Safari가 Wi-Fi에서 iPhone USB/cellular로 바뀌는 동안 원래 HTTP/3 connection을 single-session으로 migration했다는 주장은 아직 보류한다.",
            "- third-party public H3 site 또는 CDN edge support는 controlled origin의 qlog/tuple/workload evidence를 대체하지 못한다.",
            "- multipath, server preferred address, server-initiated migration은 RFC 9000 client active migration과 구분해야 한다.",
            "",
            "## 다음 실험 우선순위",
            "",
            "1. controlled public origin을 복구하고 no-change Chrome H3 baseline을 다시 얻는다.",
            "2. Chrome downlink no-heartbeat 3회와 heartbeat 3회를 page-ready active path-change로 실행한다.",
            "3. upload/download retry와 Range resume public rows를 추가해 application recovery와 CM을 분리한다.",
            "4. streaming은 그 다음 단계에서 QoE row로 확장한다. 이때 startup delay, rebuffer event, retry count, Chrome target QUIC session count를 함께 보고한다.",
            "5. Safari는 feasibility, Android/Cronet은 true mobile-platform follow-up으로 분리한다.",
            "",
            "## Source Links",
            "",
            *source_list(),
            "",
            "## 재생성",
            "",
            f"`python3 tools/{Path(__file__).name}`",
            "",
        ]
    )


def build_en() -> str:
    date = utc_date_iso()
    return "\n".join(
        [
            "# Literature Claim Positioning Matrix",
            "",
            f"Generated: `{date}`",
            "",
            "## Purpose",
            "",
            "This document connects the current QUIC Connection Migration literature to the experiment corpus without deciding the conclusion in advance. Each source is separated into what it supports, what it does not support, and what experimental gap remains.",
            "",
            "The current paper direction should be:",
            "",
            "1. CM is a real standard feature and an active research topic, extending into multipath, media, edge, and security work.",
            "2. That does not prove Chrome/Safari HTTP/3 single-session handover in the web workload setting.",
            "3. Underuse or low visibility is a layered deployment/runtime/observability problem, not simply a missing-implementation problem.",
            "4. The defensible contribution is an evidence-chain and workload-continuity study for browser-visible CM claims.",
            "",
            "## Positioning Matrix",
            "",
            markdown_table(
                ["source", "grade", "claim axis", "paper use", "supports", "does not support", "experiment gap"],
                compact_rows(),
            ),
            "",
            "## Implications For The Paper",
            "",
            "### Strengthened Claims",
            "",
            "- QUIC CM is not abandoned. RFC 9000, the multipath draft, media-migration work, and cloud/LB documentation all point to active path-management work.",
            "- The underuse question should be framed around deployment, runtime policy, and observability rather than implementation existence alone.",
            "- Streaming is a meaningful workload, but it needs QoE and mechanism metrics, not only completion.",
            "",
            "### Claims To Keep On Hold",
            "",
            "- Do not claim that Chrome/Safari migrated the original HTTP/3 connection across Wi-Fi-to-cellular/iPhone-USB until the full evidence chain is present.",
            "- Do not treat third-party H3 sites or CDN edge support as substitutes for controlled-origin qlog, tuple, workload, and session evidence.",
            "- Do not conflate multipath, server preferred address, server-initiated migration, and RFC 9000 client active migration.",
            "",
            "## Next Experimental Priority",
            "",
            "1. Recover the controlled public origin and rerun a no-change Chrome H3 baseline.",
            "2. Run three Chrome downlink no-heartbeat rows and three heartbeat rows with page-ready active path change.",
            "3. Add upload/download retry and Range-resume public rows to separate application recovery from CM.",
            "4. Expand streaming after that as a QoE workload with startup delay, rebuffer events, retries, and Chrome target QUIC-session count.",
            "5. Treat Safari as feasibility and Android/Cronet as the true mobile-platform follow-up.",
            "",
            "## Source Links",
            "",
            *source_list(),
            "",
            "## Regenerate",
            "",
            f"`python3 tools/{Path(__file__).name}`",
            "",
        ]
    )


def main() -> int:
    write_matrix()
    KO_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    KO_OUTPUT.write_text(build_ko(), encoding="utf-8")
    EN_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    EN_OUTPUT.write_text(build_en(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
