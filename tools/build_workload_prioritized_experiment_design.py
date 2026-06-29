#!/usr/bin/env python3
"""Build a workload-prioritized experiment design for the CM paper."""

from __future__ import annotations

import csv
from pathlib import Path

from research_clock import utc_date_iso


WORKLOAD_SYNTHESIS = Path("data/workload-sensitivity-synthesis-20260629.csv")
STREAMING_CASES = Path("data/streaming-workload-case-analysis-20260629.csv")
MATRIX_OUTPUT = Path("data/workload-prioritized-next-experiments-20260629.csv")
KO_OUTPUT = Path("docs/paper/workload-prioritized-experiment-design-ko-20260629.md")
EN_OUTPUT = Path("docs/paper/workload-prioritized-experiment-design-en-20260629.md")


MATRIX_FIELDS = [
    "experiment_id",
    "priority",
    "workload",
    "question",
    "variant",
    "minimum_runs",
    "ready_condition",
    "success_evidence",
    "failure_interpretation",
    "claim_unlocked",
]


NEXT_EXPERIMENTS = [
    {
        "experiment_id": "P0-fresh-public-h3-baseline",
        "priority": "0",
        "workload": "baseline",
        "question": "Is the controlled public origin currently reachable and serving application HTTP/3?",
        "variant": "Chrome no-change public origin",
        "minimum_runs": "1 PASS",
        "ready_condition": "public origin TCP/TLS/H3 reachable; Alt-Svc present; controlled baseline summary PASS",
        "success_evidence": "server request log, qlog, Chrome NetLog application using_quic=true",
        "failure_interpretation": "infrastructure blocker, not CM evidence",
        "claim_unlocked": "public origin is ready for active handover rows",
    },
    {
        "experiment_id": "P1-downlink-noheartbeat-active",
        "priority": "1",
        "workload": "large_download/downlink",
        "question": "Does a silent long response survive Wi-Fi-to-iPhone-USB failover without application help?",
        "variant": "heartbeat=false, page-ready trigger after first bytes",
        "minimum_runs": "3",
        "ready_condition": "fresh baseline PASS; latent iPhone USB trigger observed; NETWORK_CHANGE_CMD set",
        "success_evidence": "task completion, client path change, server tuple change, qlog path validation, one Chrome target QUIC session",
        "failure_interpretation": "if origin ready, failure suggests browser/runtime/workload continuity gap",
        "claim_unlocked": "strongest browser CM positive or negative row for long downlink",
    },
    {
        "experiment_id": "P1-downlink-heartbeat-active",
        "priority": "2",
        "workload": "large_download/downlink",
        "question": "Does post-change client traffic help recovery, and is it CM or a replacement session?",
        "variant": "heartbeat=true after path change",
        "minimum_runs": "3",
        "ready_condition": "same as no-heartbeat active row",
        "success_evidence": "same evidence chain plus heartbeat request timing and Chrome session count",
        "failure_interpretation": "heartbeat cannot recover the workload under this browser/origin/runtime condition",
        "claim_unlocked": "separates active client probing/application traffic from true single-session CM",
    },
    {
        "experiment_id": "P2-upload-retry-boundary-public",
        "priority": "3",
        "workload": "large_upload",
        "question": "Can application retry restore upload task continuity after active path failover?",
        "variant": "retry0 vs retry1, page-ready trigger after upload starts",
        "minimum_runs": "3 per variant",
        "ready_condition": "public origin recovered; upload sink reachable; page-ready trigger stable",
        "success_evidence": "uploadComplete, upload bytes received, retry count, session count, qlog path evidence",
        "failure_interpretation": "task failure boundary remains visible even with retry budget",
        "claim_unlocked": "application recovery benefit and session-continuity cost for user-generated content upload",
    },
    {
        "experiment_id": "P2-range-download-public",
        "priority": "4",
        "workload": "large_download/range",
        "question": "Does byte-range resume improve task completion relative to full-response retry?",
        "variant": "Range retry0/retry2 under active path change",
        "minimum_runs": "3 per variant",
        "ready_condition": "public range endpoint and page-ready trigger available",
        "success_evidence": "downloadComplete, recovered byte ranges, total bytes, session count, qlog path evidence",
        "failure_interpretation": "browser/application recovery budget is insufficient for resumable transfer",
        "claim_unlocked": "resumable transfer design guidance for HTTP/3 workloads",
    },
    {
        "experiment_id": "P3-buffered-media-public",
        "priority": "5",
        "workload": "video/music streaming",
        "question": "Does buffering hide transport disruption, and what QoE cost appears?",
        "variant": "low buffer vs high buffer; retry0 vs retry2",
        "minimum_runs": "3 per profile",
        "ready_condition": "public media endpoint reachable; page-ready trigger after first segment",
        "success_evidence": "playbackComplete, startup delay, rebuffer events, segment retries, session count, qlog path evidence",
        "failure_interpretation": "visible playback continuity needs app recovery or buffer budget",
        "claim_unlocked": "QoE-aware streaming continuity result without overclaiming CM",
    },
    {
        "experiment_id": "P4-safari-feasibility",
        "priority": "6",
        "workload": "browser feasibility",
        "question": "Can Safari complete the same public workload across active path change?",
        "variant": "Safari/WebDriver downlink or buffered-media feasibility",
        "minimum_runs": "1",
        "ready_condition": "public origin recovered; Safari WebDriver ready",
        "success_evidence": "task completion, client path snapshot, server/qlog tuple/path evidence",
        "failure_interpretation": "feasibility gap or insufficient observability; not directly comparable to Chrome NetLog",
        "claim_unlocked": "cross-browser feasibility row with weaker browser-internal observability",
    },
    {
        "experiment_id": "P4-android-chrome-feasibility",
        "priority": "7",
        "workload": "mobile browser feasibility",
        "question": "Can Android Chrome expose a real mobile Wi-Fi/cellular handover row?",
        "variant": "Android Chrome public downlink/media",
        "minimum_runs": "1",
        "ready_condition": "ADB device connected; Android network-change command available; public origin recovered",
        "success_evidence": "task completion, Android path snapshot, server/qlog tuple/path evidence",
        "failure_interpretation": "device/runtime feasibility gap; needs Android-specific rerun",
        "claim_unlocked": "true mobile-platform feasibility beyond Mac+iPhone tethered failover",
    },
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    def cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def write_matrix() -> None:
    MATRIX_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with MATRIX_OUTPUT.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=MATRIX_FIELDS)
        writer.writeheader()
        writer.writerows(NEXT_EXPERIMENTS)


def compact_existing_workloads(rows: list[dict[str, str]]) -> list[list[str]]:
    output: list[list[str]] = []
    for row in rows:
        output.append(
            [
                row.get("workload_class", "-"),
                row.get("primary_result", "-"),
                row.get("cm_evidence", "-"),
                row.get("paper_use", "-"),
            ]
        )
    return output


def compact_streaming_cases(rows: list[dict[str, str]]) -> list[list[str]]:
    output: list[list[str]] = []
    for row in rows:
        output.append(
            [
                row.get("case_name", "-"),
                row.get("priority", "-"),
                row.get("network_pattern", "-"),
                row.get("next_experiment", "-"),
                row.get("interpretation_risk", "-"),
            ]
        )
    return output


def next_experiment_rows() -> list[list[str]]:
    return [
        [
            row["experiment_id"],
            row["priority"],
            row["workload"],
            row["minimum_runs"],
            row["claim_unlocked"],
        ]
        for row in NEXT_EXPERIMENTS
    ]


def build_ko(date: str, workloads: list[dict[str, str]], streaming_cases: list[dict[str, str]]) -> str:
    return "\n".join(
        [
            "# Workload 우선순위 기반 다음 실험 설계",
            "",
            f"생성일: `{date}`",
            "",
            "## 핵심 판단",
            "",
            "Connection Migration 연구에서 스트리밍은 중요하다. 다만 논문에서 가장 먼저 증명해야 할 대상은 `동영상이 끝까지 재생됐다`가 아니라, 어떤 계층이 연속성을 만들었는지다. QUIC CM은 transport continuity이고, 브라우저/웹 애플리케이션의 작업 연속성은 retry, Range resume, segment fetch, buffer depth, replacement session, CDN/proxy termination이 함께 만든다.",
            "",
            "따라서 실험 우선순위는 다음처럼 잡는 것이 안전하다.",
            "",
            "1. 대용량 upload/download: 중단이 사용자 작업 실패로 바로 드러나므로 CM gap을 가장 선명하게 보여준다.",
            "2. Range/resumable download: 같은 download라도 전체 재시도와 부분 재시도를 분리한다.",
            "3. live/low-latency video: buffer가 작아 path disruption이 rebuffer로 드러나기 쉽다.",
            "4. VOD/video-on-demand: buffer가 커서 transport failure가 가려질 수 있으므로 QoE metric이 필요하다.",
            "5. music-like streaming: 낮은 bitrate와 큰 effective buffer 때문에 negative/control workload로 유용하다.",
            "",
            "## 기존 증거 요약",
            "",
            markdown_table(
                ["workload", "주요 결과", "CM evidence", "논문 사용"],
                compact_existing_workloads(workloads),
            ),
            "",
            "## 스트리밍/대용량 Case 분해",
            "",
            markdown_table(
                ["case", "priority", "network pattern", "다음 실험", "해석 위험"],
                compact_streaming_cases(streaming_cases),
            ),
            "",
            "## 다음 실험 Matrix",
            "",
            markdown_table(
                ["experiment", "priority", "workload", "minimum runs", "claim unlocked"],
                next_experiment_rows(),
            ),
            "",
            "## 가설",
            "",
            "- H1: Chrome 브라우저에서 active Wi-Fi-to-iPhone-USB failover가 발생해도, 긴 downlink/upload는 application recovery 없이 안정적으로 single-session continuity를 보장하지 못할 가능성이 높다.",
            "- H2: retry, Range resume, segment retry는 task completion을 올릴 수 있지만, Chrome target QUIC session churn과 completion latency를 함께 증가시킬 수 있다.",
            "- H3: buffered media는 transport CM이 실패하거나 관찰되지 않아도 playback completion을 달성할 수 있다. 이때 논문 결과는 `CM 성공`이 아니라 startup delay/rebuffer/session churn의 QoE tradeoff로 써야 한다.",
            "- H4: low-latency video는 VOD/music보다 CM 또는 application recovery의 효과가 더 잘 드러날 가능성이 높다. 그러나 현재 local result에서는 small/music-like segment도 no-retry에서 실패했으므로, bitrate만으로 민감도를 단정하면 안 된다.",
            "",
            "## Evidence Ladder",
            "",
            markdown_table(
                ["level", "의미", "필수 증거", "논문 표현"],
                [
                    ["L0", "HTTP/3 capability", "Alt-Svc 또는 Chrome NetLog application H3", "H3 baseline"],
                    ["L1", "task continuity", "DOM completion 또는 upload/download/media complete", "작업이 완료됐다"],
                    ["L2", "path-change continuity", "client path snapshot + server tuple/qlog 변화", "경로 변화 중 작업 완료"],
                    ["L3", "single-session browser CM", "L2 + Chrome target QUIC session count 1 + qlog path validation", "브라우저 single-session CM evidence"],
                    ["L4", "workload/QoE impact", "L3 또는 L2 + latency/rebuffer/retry/session churn", "workload별 사용자 영향"],
                ],
            ),
            "",
            "## 실험별 판정 규칙",
            "",
            "- upload/download row는 task completion, retry count, bytes received, completion latency, Chrome session count를 같이 보고한다.",
            "- Range row는 전체 응답 재시도와 byte-range 재시도를 분리한다.",
            "- media row는 completion만 보지 않고 startup delay, rebuffer event, fetched/played segment count, retry count를 필수 metric으로 둔다.",
            "- third-party public site는 H3 discovery/control로만 사용한다. 서버 qlog와 tuple을 볼 수 없으면 CM success claim에는 쓰지 않는다.",
            "- iPhone USB trigger는 `latent Wi-Fi-loss-to-iPhone-USB cellular failover`로 명명한다. simultaneous active multipath라고 쓰지 않는다.",
            "",
            "## 왜 스트리밍만으로 시작하지 않는가",
            "",
            "스트리밍은 실제 사용자 영향이 큰 workload지만, buffer와 segment retry가 transport failure를 쉽게 가린다. 따라서 스트리밍 결과만 먼저 보면 `재생 완료`와 `CM 성공`을 혼동하기 쉽다. 논문 설득력을 위해서는 upload/download로 transport continuity gap을 먼저 잡고, 그 다음 streaming에서 application recovery와 QoE tradeoff를 보여주는 순서가 더 강하다.",
            "",
            "## Source Anchors",
            "",
            "- RFC 9000: QUIC transport의 connection migration/path validation 기준. <https://datatracker.ietf.org/doc/html/rfc9000>",
            "- RFC 9114: HTTP/3는 QUIC 위의 HTTP mapping이며 application recovery semantics 자체를 보장하지 않는다. <https://datatracker.ietf.org/doc/html/rfc9114>",
            "- ACM CCR 2025 `An Analysis of QUIC Connection Migration in the Wild`: wild/deployment 관점의 CM 관측 경계 참고. <https://dl.acm.org/doi/10.1145/3727063.3727066>",
            "- IETF Media over QUIC WG: media delivery가 QUIC 위에서 새롭게 논의되고 있으나, 본 연구의 browser HTTP/3 segment-fetch model과는 claim boundary를 분리한다. <https://datatracker.ietf.org/wg/moq/about/>",
            "",
            "## 다음 실행",
            "",
            "현재 즉시 필요한 외부 조건은 public origin 복구다. origin이 살아나면 `P0 -> P1 no-heartbeat -> P1 heartbeat -> P2 upload/range -> P3 buffered media -> P4 Safari/Android` 순서로 간다.",
            "",
            f"재생성 명령: `python3 tools/{Path(__file__).name}`",
        ]
    ) + "\n"


def build_en(date: str, workloads: list[dict[str, str]], streaming_cases: list[dict[str, str]]) -> str:
    return "\n".join(
        [
            "# Workload-Prioritized Experiment Design",
            "",
            f"Generated: `{date}`",
            "",
            "## Core Decision",
            "",
            "Streaming is important for a Connection Migration study, but the paper should not treat playback completion as transport-layer success. QUIC CM is transport continuity. Web task continuity is also shaped by retry, Range resume, segment fetches, buffer depth, replacement sessions, and CDN/proxy termination.",
            "",
            "The safest experiment order is therefore:",
            "",
            "1. Large upload/download, because interruption maps directly to user-task failure.",
            "2. Range/resumable download, because full retry and partial retry are different recovery semantics.",
            "3. Live or low-latency video, because small buffers expose disruption as rebuffering.",
            "4. Video on demand, because larger buffers can hide transport disruption.",
            "5. Music-like streaming, because lower bitrate and larger effective buffers make it useful as a low-sensitivity control.",
            "",
            "## Existing Evidence",
            "",
            markdown_table(
                ["workload", "primary result", "CM evidence", "paper use"],
                compact_existing_workloads(workloads),
            ),
            "",
            "## Streaming And Large-Transfer Case Split",
            "",
            markdown_table(
                ["case", "priority", "network pattern", "next experiment", "interpretation risk"],
                compact_streaming_cases(streaming_cases),
            ),
            "",
            "## Next Experiment Matrix",
            "",
            markdown_table(
                ["experiment", "priority", "workload", "minimum runs", "claim unlocked"],
                next_experiment_rows(),
            ),
            "",
            "## Hypotheses",
            "",
            "- H1: During active Wi-Fi-to-iPhone-USB failover, Chrome may not reliably preserve a long upload/downlink as a single HTTP/3 QUIC session without application recovery.",
            "- H2: retry, Range resume, and segment retry can improve task completion while increasing session churn and completion latency.",
            "- H3: buffered media can complete even when transport CM is absent or unproven; the paper should report startup delay, rebuffering, retry, and session churn rather than only completion.",
            "- H4: low-latency video should be more sensitive than VOD/music, but bitrate alone is not enough to predict sensitivity; the current music-like no-retry control failed under a 6000 ms disruption.",
            "",
            "## Evidence Ladder",
            "",
            markdown_table(
                ["level", "meaning", "required evidence", "paper wording"],
                [
                    ["L0", "HTTP/3 capability", "Alt-Svc or Chrome NetLog application H3", "H3 baseline"],
                    ["L1", "task continuity", "DOM completion or upload/download/media complete", "the task completed"],
                    ["L2", "path-change continuity", "client path snapshot plus server tuple/qlog change", "task completion during path change"],
                    ["L3", "single-session browser CM", "L2 plus one Chrome target QUIC session and qlog path validation", "browser single-session CM evidence"],
                    ["L4", "workload/QoE impact", "L3 or L2 plus latency/rebuffer/retry/session churn", "workload-specific user impact"],
                ],
            ),
            "",
            "## Classification Rules",
            "",
            "- Upload/download rows must report task completion, retry count, received bytes, completion latency, and Chrome session count.",
            "- Range rows must separate whole-response retry from byte-range recovery.",
            "- Media rows must include startup delay, rebuffer events, fetched/played segment counts, and retry counts.",
            "- Third-party public sites are only H3 discovery/control evidence. Without server qlog and tuple evidence they cannot support CM success claims.",
            "- The iPhone USB trigger should be named `latent Wi-Fi-loss-to-iPhone-USB cellular failover`, not simultaneous active multipath.",
            "",
            "## Why Not Start With Streaming Only",
            "",
            "Streaming is user-important, but buffering and segment retry can hide transport failure. Starting with streaming alone risks confusing playback completion with CM success. A stronger paper first establishes the transport continuity gap with upload/download, then uses streaming to show application recovery and QoE tradeoffs.",
            "",
            "## Source Anchors",
            "",
            "- RFC 9000 for QUIC connection migration and path validation. <https://datatracker.ietf.org/doc/html/rfc9000>",
            "- RFC 9114 for HTTP/3 as an HTTP mapping over QUIC, without application recovery guarantees. <https://datatracker.ietf.org/doc/html/rfc9114>",
            "- ACM CCR 2025 `An Analysis of QUIC Connection Migration in the Wild` for deployment/wild-measurement boundaries. <https://dl.acm.org/doi/10.1145/3727063.3727066>",
            "- IETF Media over QUIC WG for emerging QUIC-based media delivery, kept separate from this study's browser HTTP/3 segment-fetch model. <https://datatracker.ietf.org/wg/moq/about/>",
            "",
            "## Next Execution",
            "",
            "The immediate external dependency is public-origin recovery. Once it is reachable, run `P0 -> P1 no-heartbeat -> P1 heartbeat -> P2 upload/range -> P3 buffered media -> P4 Safari/Android`.",
            "",
            f"Regenerate with: `python3 tools/{Path(__file__).name}`",
        ]
    ) + "\n"


def main() -> int:
    date = utc_date_iso()
    workloads = read_csv(WORKLOAD_SYNTHESIS)
    streaming_cases = read_csv(STREAMING_CASES)
    write_matrix()
    KO_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    KO_OUTPUT.write_text(build_ko(date, workloads, streaming_cases), encoding="utf-8")
    EN_OUTPUT.write_text(build_en(date, workloads, streaming_cases), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
