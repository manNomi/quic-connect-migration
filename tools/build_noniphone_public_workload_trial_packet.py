#!/usr/bin/env python3
"""Build the next non-iPhone controlled-public workload trial packet."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_kst_date_label


DEFAULT_SYNTHESIS_CSV = "data/noniphone-workload-qoe-continuity-synthesis-20260701.csv"
DEFAULT_OUTPUT = "docs/results/noniphone-public-workload-trial-packet-20260701.md"
DEFAULT_JSON_OUTPUT = "data/noniphone-public-workload-trial-packet-20260701.json"


@dataclass(frozen=True)
class TrialTemplate:
    rank: int
    trial_id_pattern: str
    phase: str
    workload: str
    repetitions: int
    target_path: str
    expected_requests: int
    ready_expression: str
    runner: str
    primary_metric: str
    local_evidence_group: str
    why_now: str
    interpretation_if_success: str
    interpretation_if_not_strong_cm: str


TRIALS = [
    TrialTemplate(
        rank=0,
        trial_id_pattern="controlled-public-chrome-h3-baseline-001",
        phase="baseline",
        workload="public H3 bootstrap",
        repetitions=1,
        target_path="/browser-slow?duration_ms=3000&chunks=3&label=public-h3-baseline",
        expected_requests=2,
        ready_expression="",
        runner="run-controlled-public-h3-browser-baseline.sh",
        primary_metric="controlled-public application H3 baseline PASS",
        local_evidence_group="baseline",
        why_now="Every public workload trial depends on a fresh H3/Alt-Svc baseline.",
        interpretation_if_success="The public origin is usable for controlled Chrome HTTP/3 workload trials.",
        interpretation_if_not_strong_cm="A failed baseline is infrastructure evidence, not Connection Migration evidence.",
    ),
    TrialTemplate(
        rank=1,
        trial_id_pattern="controlled-public-chrome-range-nochange-001",
        phase="no-change-baseline",
        workload="large byte-range download",
        repetitions=1,
        target_path="/browser-range-download?bytes=1048576&range_bytes=131072&range_duration_ms=250&range_chunks=2&retry_attempts=0&retry_delay_ms=500&label=public-range-nochange",
        expected_requests=9,
        ready_expression="",
        runner="run-controlled-public-h3-browser-baseline.sh",
        primary_metric="range_complete=true; range_completed_bytes=1048576",
        local_evidence_group="large byte-range download",
        why_now="Local range rows have the cleanest single-session path-validation evidence among browser workloads.",
        interpretation_if_success="The public origin can serve the resumable-download workload before active path-change trials.",
        interpretation_if_not_strong_cm="No-change rows are controls and must not be used as migration success evidence.",
    ),
    TrialTemplate(
        rank=2,
        trial_id_pattern="controlled-public-chrome-range-network-change-00{1..3}",
        phase="active-network-change",
        workload="large byte-range download",
        repetitions=3,
        target_path="/browser-range-download?bytes=1048576&range_bytes=131072&range_duration_ms=250&range_chunks=2&retry_attempts=0&retry_delay_ms=500&label=public-range-active",
        expected_requests=9,
        ready_expression='Number(document.body.dataset.rangeCompletedChunks || "0") >= 1',
        runner="run-controlled-public-h3-network-change.sh",
        primary_metric="range_complete, completed bytes, Chrome target sessions, qlog path validation",
        local_evidence_group="large byte-range download",
        why_now="Range is the first active public workload because its completion and byte accounting are crisp.",
        interpretation_if_success="A strong row can support public browser single-session CM only if the full evidence chain passes.",
        interpretation_if_not_strong_cm="Multiple sessions or missing qlog path validation should be reported as recovery/reconnect or negative-control evidence.",
    ),
    TrialTemplate(
        rank=3,
        trial_id_pattern="controlled-public-chrome-upload-nochange-001",
        phase="no-change-baseline",
        workload="large upload",
        repetitions=1,
        target_path="/browser-upload?bytes=131072&duration_ms=3000&chunks=6&retry_attempts=0&retry_delay_ms=500&label=public-upload-nochange",
        expected_requests=2,
        ready_expression="",
        runner="run-controlled-public-h3-browser-baseline.sh",
        primary_metric="upload_complete=true; upload_response_bytes=131072",
        local_evidence_group="large upload",
        why_now="Upload is user-visible task continuity and request tuple logs can miss packet-level rebinding.",
        interpretation_if_success="The public origin can receive upload workloads before active path-change trials.",
        interpretation_if_not_strong_cm="No-change upload rows are public workload baselines, not CM rows.",
    ),
    TrialTemplate(
        rank=4,
        trial_id_pattern="controlled-public-chrome-upload-network-change-00{1..3}",
        phase="active-network-change",
        workload="large upload",
        repetitions=3,
        target_path="/browser-upload?bytes=131072&duration_ms=3000&chunks=6&retry_attempts=0&retry_delay_ms=500&label=public-upload-active",
        expected_requests=2,
        ready_expression='Number(document.body.dataset.uploadBytes || "0") > 0',
        runner="run-controlled-public-h3-network-change.sh",
        primary_metric="upload_complete, received bytes, Chrome target sessions, qlog path validation",
        local_evidence_group="large upload",
        why_now="Upload is the second active workload because it tests client-sending continuity.",
        interpretation_if_success="A strong row can support public browser upload continuity under single-session CM.",
        interpretation_if_not_strong_cm="If upload completes with replacement sessions, report task recovery separately from CM.",
    ),
    TrialTemplate(
        rank=5,
        trial_id_pattern="controlled-public-chrome-buffered-low-network-change-00{1..3}",
        phase="active-network-change",
        workload="buffered video playback",
        repetitions=3,
        target_path="/browser-buffered-media?count=8&bytes=8192&segment_duration_ms=50&segment_chunks=1&playback_interval_ms=1000&startup_buffer_segments=1&max_buffer_segments=1&retry_attempts=0&retry_delay_ms=500&label=public-buffered-low-active",
        expected_requests=9,
        ready_expression='Number(document.body.dataset.bufferedMediaFetchedCount || "0") >= 1',
        runner="run-controlled-public-h3-network-change.sh",
        primary_metric="playback complete, startup delay, rebuffer events, Chrome target sessions",
        local_evidence_group="buffered video playback",
        why_now="Low-buffer playback exposes visible QoE cost instead of hiding disruption behind startup delay.",
        interpretation_if_success="A complete row is QoE continuity evidence; it is CM evidence only if the single-session chain also passes.",
        interpretation_if_not_strong_cm="Playback completion with multiple sessions is replacement-session or application-level continuity evidence.",
    ),
    TrialTemplate(
        rank=6,
        trial_id_pattern="controlled-public-chrome-buffered-high-network-change-00{1..3}",
        phase="active-network-change",
        workload="buffered video playback",
        repetitions=3,
        target_path="/browser-buffered-media?count=8&bytes=8192&segment_duration_ms=50&segment_chunks=1&playback_interval_ms=1000&startup_buffer_segments=4&max_buffer_segments=6&retry_attempts=0&retry_delay_ms=500&label=public-buffered-high-active",
        expected_requests=9,
        ready_expression='Number(document.body.dataset.bufferedMediaFetchedCount || "0") >= 1',
        runner="run-controlled-public-h3-network-change.sh",
        primary_metric="playback complete, startup delay, rebuffer events, Chrome target sessions",
        local_evidence_group="buffered video playback",
        why_now="High-buffer playback checks whether buffering hides disruption while changing startup/rebuffer tradeoffs.",
        interpretation_if_success="Use as QoE comparison against low-buffer playback, not as automatic CM success.",
        interpretation_if_not_strong_cm="If sessions churn, report buffer-masked recovery rather than transport continuity.",
    ),
    TrialTemplate(
        rank=7,
        trial_id_pattern="controlled-public-chrome-musiclike-retry0-network-change-00{1..3}",
        phase="active-network-change",
        workload="music-like segment",
        repetitions=3,
        target_path="/browser-media-segments?count=8&interval_ms=1000&bytes=8192&segment_duration_ms=50&segment_chunks=1&retry_attempts=0&retry_delay_ms=500&label=public-musiclike-retry0-active",
        expected_requests=9,
        ready_expression='Number(document.body.dataset.mediaCompletedCount || "0") >= 1',
        runner="run-controlled-public-h3-network-change.sh",
        primary_metric="media_complete, completed segments, elapsed time, Chrome target sessions",
        local_evidence_group="music-like segment",
        why_now="The local corpus shows music-like retry0 is a useful failure/control boundary.",
        interpretation_if_success="Unexpected retry0 success should be examined for path timing, buffering, and session count.",
        interpretation_if_not_strong_cm="Failure without retry is still useful workload-boundary evidence.",
    ),
    TrialTemplate(
        rank=8,
        trial_id_pattern="controlled-public-chrome-musiclike-retry1-network-change-00{1..3}",
        phase="active-network-change",
        workload="music-like segment",
        repetitions=3,
        target_path="/browser-media-segments?count=8&interval_ms=1000&bytes=8192&segment_duration_ms=50&segment_chunks=1&retry_attempts=1&retry_delay_ms=500&label=public-musiclike-retry1-active",
        expected_requests=9,
        ready_expression='Number(document.body.dataset.mediaCompletedCount || "0") >= 1',
        runner="run-controlled-public-h3-network-change.sh",
        primary_metric="media_complete, retries used, elapsed time, Chrome target sessions",
        local_evidence_group="music-like segment",
        why_now="Retry1 should follow retry0 to separate application recovery from transport continuity.",
        interpretation_if_success="Completion with retry should be framed as application recovery unless the single-session chain passes.",
        interpretation_if_not_strong_cm="Multiple sessions or retries must not be described as pure QUIC CM success.",
    ),
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def synthesis_by_workload(path: Path) -> dict[str, dict[str, str]]:
    return {row["workload_group"]: row for row in read_csv(path) if row.get("workload_group")}


def local_summary(workload: str, synthesis: dict[str, dict[str, str]]) -> str:
    row = synthesis.get(workload)
    if not row:
        return "-"
    return (
        f"{row.get('completion_rate', '-')}; sessions {row.get('chrome_sessions', '-')}; "
        f"single {row.get('single_session_rows', '-')}; multi {row.get('multi_session_rows', '-')}; "
        f"path-validation {row.get('path_validation_rows', '-')}; {row.get('qoe_signal', '-')}"
    )


def build_target_url_expression(trial: TrialTemplate) -> str:
    return f"${{PUBLIC_ORIGIN_BASE:?set PUBLIC_ORIGIN_BASE like https://h3.example.com}}{trial.target_path}"


def sample_trial_id(trial: TrialTemplate) -> str:
    return trial.trial_id_pattern.replace("00{1..3}", "001")


def active_command(trial: TrialTemplate) -> str:
    ready = trial.ready_expression.replace("'", "'\"'\"'")
    run_id = sample_trial_id(trial)
    return "\n".join(
        [
            "cd repro/quic-go-min-repro",
            f"RUN_ID={run_id} \\",
            f"ARTIFACT_DIR=artifacts/{run_id} \\",
            'PUBLIC_ORIGIN_URL="' + build_target_url_expression(trial) + '" \\',
            'PUBLIC_ORIGIN_BOOTSTRAP_URL="${PUBLIC_ORIGIN_BOOTSTRAP_URL:-$PUBLIC_ORIGIN_BASE/browser-slow?duration_ms=3000&chunks=3&label=public-bootstrap}" \\',
            'CONTROLLED_PUBLIC_BASELINE_SUMMARY="${CONTROLLED_PUBLIC_BASELINE_SUMMARY:?set a prior PASS baseline summary}" \\',
            'NETWORK_CHANGE_CMD="${NETWORK_CHANGE_CMD:?set a non-iPhone active path-change command}" \\',
            f"CONTROLLED_PUBLIC_EXPECTED_REQUESTS={trial.expected_requests} \\",
            "REQUIRE_H3_ALT_SVC=1 \\",
            "CHROME_RUNNER=cdp \\",
            "CHROME_HOLD_SECONDS=45 \\",
            "CHROME_TIMEOUT_SECONDS=70 \\",
            f"NETWORK_CHANGE_READY_EXPR='{ready}' \\",
            "./scripts/run-controlled-public-h3-network-change.sh",
        ]
    )


def baseline_command(trial: TrialTemplate) -> str:
    return "\n".join(
        [
            "cd repro/quic-go-min-repro",
            f"RUN_ID={trial.trial_id_pattern} \\",
            f"ARTIFACT_DIR=artifacts/{trial.trial_id_pattern} \\",
            'PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_BOOTSTRAP_URL:-$PUBLIC_ORIGIN_BASE/browser-slow?duration_ms=3000&chunks=3&label=public-bootstrap}" \\',
            'SECOND_URL="' + build_target_url_expression(trial) + '" \\',
            f"CONTROLLED_PUBLIC_EXPECTED_REQUESTS={trial.expected_requests} \\",
            "REQUIRE_H3_ALT_SVC=1 \\",
            "RUN_CONTROLLED_PUBLIC_CLASSIFIER=1 \\",
            "CHROME_RUNNER=cdp \\",
            "CHROME_HOLD_SECONDS=25 \\",
            "CHROME_TIMEOUT_SECONDS=45 \\",
            "./scripts/run-controlled-public-h3-browser-baseline.sh",
        ]
    )


def command_for(trial: TrialTemplate) -> str:
    if trial.phase == "active-network-change":
        return active_command(trial)
    return baseline_command(trial)


def acceptance_for(trial: TrialTemplate) -> str:
    if trial.phase == "baseline":
        return "PASS baseline with application H3 confirmed by server log/qlog and Chrome NetLog."
    if trial.phase == "no-change-baseline":
        return "PASS no-change workload baseline; no active path-change claim."
    return (
        "Strong CM row requires application completion, client active path change, target H3 tuple change, "
        "server qlog PATH_CHALLENGE/PATH_RESPONSE, and one Chrome target QUIC session."
    )


def build_packet(synthesis_csv: Path = Path(DEFAULT_SYNTHESIS_CSV)) -> dict[str, Any]:
    synthesis = synthesis_by_workload(synthesis_csv)
    trials: list[dict[str, Any]] = []
    for trial in TRIALS:
        record = asdict(trial)
        record["target_url_expression"] = build_target_url_expression(trial)
        record["acceptance_gate"] = acceptance_for(trial)
        record["local_synthesis"] = local_summary(trial.local_evidence_group, synthesis)
        record["command"] = command_for(trial)
        trials.append(record)
    return {
        "generated": utc_kst_date_label(),
        "public_safe": True,
        "synthesis_csv": synthesis_csv.as_posix(),
        "trial_count": len(trials),
        "active_trial_repetitions": sum(trial["repetitions"] for trial in trials if trial["phase"] == "active-network-change"),
        "preconditions": [
            "PUBLIC_ORIGIN_BASE points to a WebPKI HTTPS origin that advertises Alt-Svc h3.",
            "PUBLIC_ORIGIN_BOOTSTRAP_URL reaches the same origin and passes controlled-public H3 baseline.",
            "CONTROLLED_PUBLIC_BASELINE_SUMMARY points to a prior PASS baseline summary.",
            "NETWORK_CHANGE_CMD performs a non-iPhone active path change on the desktop client.",
            "Raw qlog, NetLog, pcap, keylog, private hosts, and credentials remain outside committed files.",
        ],
        "strong_cm_acceptance": [
            "application task completion is true for the workload-specific DOM metric",
            "client active path changed according to before/after route snapshots",
            "server target H3 remote tuple count changed",
            "server qlog records PATH_CHALLENGE and PATH_RESPONSE",
            "Chrome target QUIC session count is one",
        ],
        "trials": trials,
        "claim_boundary": "This packet is a run plan. It is not evidence that any public workload or browser Connection Migration trial has succeeded.",
    }


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(value.replace("|", "\\|").replace("\n", "<br>") for value in row) + " |")
    return "\n".join(lines)


def emit_markdown(packet: dict[str, Any]) -> str:
    trials = packet["trials"]
    lines = [
        "# Non-iPhone Public Workload Trial Packet",
        "",
        f"Generated: `{packet['generated']}`",
        "",
        "This public-safe packet converts the local non-iPhone workload/QoE synthesis into the next controlled-public Chrome trial order. It intentionally excludes iPhone-based triggers and does not include hostnames, IP addresses, credentials, qlogs, NetLogs, pcaps, or keylogs.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| synthesis CSV | `{packet['synthesis_csv']}` |",
        f"| trial templates | `{packet['trial_count']}` |",
        f"| active trial repetitions | `{packet['active_trial_repetitions']}` |",
        f"| claim boundary | {packet['claim_boundary']} |",
        "",
        "## Preconditions",
        "",
    ]
    lines.extend(f"{idx}. {item}" for idx, item in enumerate(packet["preconditions"], start=1))
    lines.extend(
        [
            "",
            "## Strong CM Acceptance",
            "",
        ]
    )
    lines.extend(f"{idx}. {item}" for idx, item in enumerate(packet["strong_cm_acceptance"], start=1))
    lines.extend(
        [
            "",
            "## Trial Order",
            "",
            markdown_table(
                [
                    "rank",
                    "trial id pattern",
                    "phase",
                    "workload",
                    "runs",
                    "expected requests",
                    "ready expression",
                    "local synthesis",
                    "acceptance",
                ],
                [
                    [
                        str(trial["rank"]),
                        trial["trial_id_pattern"],
                        trial["phase"],
                        trial["workload"],
                        str(trial["repetitions"]),
                        str(trial["expected_requests"]),
                        trial["ready_expression"] or "-",
                        trial["local_synthesis"],
                        trial["acceptance_gate"],
                    ]
                    for trial in trials
                ],
            ),
            "",
            "## Command Templates",
            "",
            "Set `PUBLIC_ORIGIN_BASE`, `PUBLIC_ORIGIN_BOOTSTRAP_URL`, `CONTROLLED_PUBLIC_BASELINE_SUMMARY`, and `NETWORK_CHANGE_CMD` in an ignored shell or terminal session before using the active templates.",
            "",
        ]
    )
    for trial in trials:
        lines.extend(
            [
                f"### {trial['trial_id_pattern']}",
                "",
                f"Why now: {trial['why_now']}",
                "",
                "```bash",
                trial["command"],
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Interpretation Rules",
            "",
        ]
    )
    for trial in trials:
        lines.extend(
            [
                f"- `{trial['trial_id_pattern']}` success: {trial['interpretation_if_success']}",
                f"- `{trial['trial_id_pattern']}` non-strong-CM: {trial['interpretation_if_not_strong_cm']}",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_outputs(packet: dict[str, Any], output: Path, json_output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(packet), encoding="utf-8")
    json_output.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--synthesis-csv", default=DEFAULT_SYNTHESIS_CSV)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    packet = build_packet(Path(args.synthesis_csv))
    write_outputs(packet, Path(args.output), Path(args.json_output))
    print(f"wrote {args.output}")
    print(f"wrote {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
