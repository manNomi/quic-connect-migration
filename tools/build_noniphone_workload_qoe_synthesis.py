#!/usr/bin/env python3
"""Build a non-iPhone workload continuity and QoE synthesis."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any

from research_clock import utc_kst_date_label


DEFAULT_OUTPUT = "docs/results/noniphone-workload-qoe-continuity-synthesis-20260701.md"
DEFAULT_CSV_OUTPUT = "data/noniphone-workload-qoe-continuity-synthesis-20260701.csv"


@dataclass(frozen=True)
class SourceSpec:
    path: str
    source_id: str
    workload_group: str
    kind: str


SOURCE_SPECS = [
    SourceSpec(
        "data/chrome-h3-rebinding-media-segment-replication-20260629.csv",
        "media-segment-replication-20260629",
        "video-like segment",
        "media",
    ),
    SourceSpec(
        "data/chrome-desktop-noniphone-media-local-refresh-20260630.csv",
        "media-segment-local-refresh-20260630",
        "video-like segment",
        "proxy_summary",
    ),
    SourceSpec(
        "data/chrome-h3-rebinding-music-like-media-control-20260629.csv",
        "music-like-control-20260629",
        "music-like segment",
        "media",
    ),
    SourceSpec(
        "data/chrome-desktop-noniphone-musiclike-local-refresh-20260701.csv",
        "music-like-local-refresh-20260701",
        "music-like segment",
        "media",
    ),
    SourceSpec(
        "data/chrome-h3-rebinding-buffered-media-control-20260629.csv",
        "buffered-media-control-20260629",
        "buffered video playback",
        "buffered",
    ),
    SourceSpec(
        "data/chrome-desktop-noniphone-buffered-media-local-refresh-20260701.csv",
        "buffered-media-local-refresh-20260701",
        "buffered video playback",
        "buffered",
    ),
    SourceSpec(
        "data/chrome-desktop-noniphone-range-local-refresh-20260630.csv",
        "range-download-local-refresh-20260630",
        "large byte-range download",
        "range",
    ),
    SourceSpec(
        "data/chrome-desktop-noniphone-upload-local-refresh-20260630.csv",
        "upload-local-refresh-20260630",
        "large upload",
        "upload",
    ),
]


CSV_FIELDS = [
    "workload_group",
    "sources",
    "rows",
    "pass_rows",
    "completion_rows",
    "completion_rate",
    "retry_profile",
    "drop_windows_ms",
    "chrome_sessions",
    "single_session_rows",
    "multi_session_rows",
    "path_validation_rows",
    "qoe_signal",
    "paper_use",
    "claim_boundary",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def as_int(value: Any, default: int = 0) -> int:
    try:
        raw = "" if value is None else str(value).strip()
        return int(raw) if raw else default
    except ValueError:
        return default


def yes(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "yes", "1", "pass"}


def path_validation_observed(row: dict[str, str]) -> bool:
    if yes(row.get("netlog_target_path_validation_observed")):
        return True
    return as_int(row.get("qlog_path_challenge")) > 0 and as_int(row.get("qlog_path_response")) > 0


def session_count(row: dict[str, str]) -> int:
    return as_int(row.get("chrome_quic_sessions") or row.get("netlog_target_quic_session_count"))


def completion_for(kind: str, row: dict[str, str]) -> bool:
    if kind == "media":
        return yes(row.get("media_complete"))
    if kind == "buffered":
        return yes(row.get("buffered_media_complete"))
    if kind == "range":
        return yes(row.get("range_complete"))
    if kind == "upload":
        return row.get("status") == "PASS" and as_int(row.get("upload_sink_request_bytes")) > 0
    if kind == "proxy_summary":
        return row.get("status") == "PASS"
    raise ValueError(f"unknown kind: {kind}")


def elapsed_for(kind: str, row: dict[str, str]) -> int:
    if kind == "media":
        return as_int(row.get("media_elapsed_ms"))
    if kind == "buffered":
        return as_int(row.get("elapsed_ms"))
    if kind == "range":
        return as_int(row.get("range_elapsed_ms"))
    return 0


def retry_for(kind: str, row: dict[str, str]) -> str:
    if kind in {"buffered", "media", "range"}:
        return row.get("retry_attempts") or "-"
    run_id = row.get("run_id") or row.get("trial_id") or ""
    match = re.search(r"retry([0-9]+)", run_id)
    if match:
        return match.group(1)
    return "-"


def drop_for(row: dict[str, str]) -> str:
    if row.get("drop_window_ms"):
        return str(row["drop_window_ms"])
    run_id = row.get("run_id") or row.get("trial_id") or ""
    match = re.search(r"drop([0-9]+)", run_id)
    if match:
        return match.group(1)
    return "unknown"


def source_rows(specs: list[SourceSpec]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for spec in specs:
        path = Path(spec.path)
        if not path.exists():
            continue
        for row in read_csv(path):
            normalized.append(
                {
                    "workload_group": spec.workload_group,
                    "source_id": spec.source_id,
                    "kind": spec.kind,
                    "status": row.get("status", ""),
                    "complete": completion_for(spec.kind, row),
                    "retry": retry_for(spec.kind, row),
                    "drop": drop_for(row),
                    "sessions": session_count(row),
                    "path_validation": path_validation_observed(row),
                    "elapsed_ms": elapsed_for(spec.kind, row),
                    "rebuffer_events": as_int(row.get("rebuffer_events")),
                    "startup_elapsed_ms": as_int(row.get("startup_elapsed_ms")),
                    "upload_bytes": as_int(row.get("upload_sink_request_bytes")),
                    "request_tuples": as_int(row.get("server_remote_addr_count")),
                }
            )
    return normalized


def format_counter(values: list[str]) -> str:
    counts = Counter(values)
    return ", ".join(f"{key}:{counts[key]}" for key in sorted(counts)) if counts else "-"


def format_range(values: list[int]) -> str:
    items = [value for value in values if value > 0]
    if not items:
        return "-"
    return f"{min(items)}-{max(items)}"


def format_median(values: list[int]) -> str:
    items = [value for value in values if value > 0]
    if not items:
        return "-"
    return str(int(median(items)))


def qoe_signal(group: str, rows: list[dict[str, Any]]) -> str:
    if group == "buffered video playback":
        return (
            f"rebuffer {format_range([int(row['rebuffer_events']) for row in rows])}; "
            f"startup median {format_median([int(row['startup_elapsed_ms']) for row in rows])}ms"
        )
    if group in {"video-like segment", "music-like segment", "large byte-range download"}:
        return f"elapsed median {format_median([int(row['elapsed_ms']) for row in rows])}ms"
    if group == "large upload":
        return f"upload bytes {format_range([int(row['upload_bytes']) for row in rows])}; request tuples {format_range([int(row['request_tuples']) for row in rows])}"
    return "-"


def paper_use(group: str) -> str:
    uses = {
        "video-like segment": "Use as local segment-continuity evidence; separate single-session local rows from multiple-session recovery.",
        "music-like segment": "Use as a retry/reconnect boundary: low-bitrate segment traffic still failed without retry under 6000ms loss.",
        "buffered video playback": "Use for QoE framing: playback completion can hide rebuffer cost and session churn.",
        "large byte-range download": "Use as the strongest local resumable-download control with single target-session path evidence.",
        "large upload": "Use as client-sending workload evidence and as a warning that request-level tuple logs can miss packet rebinding.",
    }
    return uses[group]


def claim_boundary(group: str) -> str:
    shared = "Do not claim public Wi-Fi/LTE handover or general browser CM deployment success."
    if group == "buffered video playback":
        return shared + " Do not claim zero-impact video continuity."
    if group == "music-like segment":
        return shared + " Do not call retry/reconnect recovery single-session CM."
    if group == "large upload":
        return shared + " Do not use request tuple count alone as packet-level path evidence."
    return shared


def build_synthesis(specs: list[SourceSpec] = SOURCE_SPECS) -> dict[str, Any]:
    rows = source_rows(specs)
    groups = sorted({str(row["workload_group"]) for row in rows})
    summaries: list[dict[str, str]] = []
    for group in groups:
        items = [row for row in rows if row["workload_group"] == group]
        pass_rows = sum(1 for row in items if row["status"] == "PASS")
        complete_rows = sum(1 for row in items if bool(row["complete"]))
        sessions = [int(row["sessions"]) for row in items if int(row["sessions"]) > 0]
        summary = {
            "workload_group": group,
            "sources": ", ".join(sorted({str(row["source_id"]) for row in items})),
            "rows": str(len(items)),
            "pass_rows": str(pass_rows),
            "completion_rows": str(complete_rows),
            "completion_rate": f"{complete_rows}/{len(items)}",
            "retry_profile": format_counter([str(row["retry"]) for row in items]),
            "drop_windows_ms": ", ".join(sorted({str(row["drop"]) for row in items}, key=lambda item: as_int(item, 10**9))),
            "chrome_sessions": format_range(sessions),
            "single_session_rows": str(sum(1 for row in items if int(row["sessions"]) == 1)),
            "multi_session_rows": str(sum(1 for row in items if int(row["sessions"]) > 1)),
            "path_validation_rows": str(sum(1 for row in items if bool(row["path_validation"]))),
            "qoe_signal": qoe_signal(group, items),
            "paper_use": paper_use(group),
            "claim_boundary": claim_boundary(group),
        }
        summaries.append(summary)
    return {
        "generated": utc_kst_date_label(),
        "public_safe": True,
        "source_count": len(specs),
        "row_count": len(rows),
        "groups": summaries,
        "interpretation": [
            "The strongest local non-iPhone browser evidence is not one uniform result: range and upload rows show cleaner single-session/path-validation signals than buffered or music-like rows.",
            "Streaming workloads must be reported with QoE and recovery mechanism fields, not only completion.",
            "Multiple Chrome target QUIC sessions convert many successful user-visible rows into application recovery or replacement-session evidence, not single-session browser Connection Migration evidence.",
        ],
        "next_public_trials": [
            "Recover or create an H3-ready public origin with Alt-Svc.",
            "Run public range-download and upload page-ready trials first because local controls already define crisp completion/path-validation gates.",
            "Run public buffered-media and music-like trials after that, reporting startup delay, rebuffer events, retry count, and Chrome session count together.",
        ],
    }


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def emit_markdown(payload: dict[str, Any], csv_output: str) -> str:
    summaries = payload["groups"]
    lines = [
        "# Non-iPhone Workload Continuity and QoE Synthesis",
        "",
        f"Generated: `{payload['generated']}`",
        "",
        "This public-safe synthesis normalizes the committed local Chrome/quic-go workload CSVs that do not require iPhone input. It compares video-like segment fetches, music-like segment fetches, buffered video playback, byte-range download, and upload controls under local UDP rebinding or local return-path loss.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| source CSV count | `{payload['source_count']}` |",
        f"| normalized rows | `{payload['row_count']}` |",
        f"| workload groups | `{len(summaries)}` |",
        "",
        "## Workload Comparison",
        "",
        markdown_table(
            [
                "workload",
                "rows",
                "PASS",
                "complete",
                "retry profile",
                "drop ms",
                "Chrome sessions",
                "single-session rows",
                "multi-session rows",
                "path validation rows",
                "QoE signal",
            ],
            [
                [
                    row["workload_group"],
                    row["rows"],
                    row["pass_rows"],
                    row["completion_rate"],
                    row["retry_profile"],
                    row["drop_windows_ms"],
                    row["chrome_sessions"],
                    row["single_session_rows"],
                    row["multi_session_rows"],
                    row["path_validation_rows"],
                    row["qoe_signal"],
                ]
                for row in summaries
            ],
        ),
        "",
        "## Paper Use",
        "",
        markdown_table(
            ["workload", "paper use", "claim boundary"],
            [[row["workload_group"], row["paper_use"], row["claim_boundary"]] for row in summaries],
        ),
        "",
        "## Interpretation",
        "",
    ]
    lines.extend(f"{idx}. {item}" for idx, item in enumerate(payload["interpretation"], start=1))
    lines.extend(
        [
            "",
            "## Next Public Trials",
            "",
        ]
    )
    lines.extend(f"{idx}. {item}" for idx, item in enumerate(payload["next_public_trials"], start=1))
    lines.extend(
        [
            "",
            "## Data",
            "",
            f"- CSV: `{csv_output}`",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(payload: dict[str, Any], markdown_path: Path, csv_path: Path) -> None:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    write_csv(payload["groups"], csv_path)
    markdown_path.write_text(emit_markdown(payload, csv_path.as_posix()), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    payload = build_synthesis()
    write_outputs(payload, Path(args.output), Path(args.csv_output))
    if args.format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"wrote {args.output}")
        print(f"wrote {args.csv_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
