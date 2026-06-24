#!/usr/bin/env python3
"""Summarize Chrome local UDP rebinding timing-sensitivity runs."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import summarize_chrome_rebinding_proxy_matrix as downlink
import summarize_chrome_rebinding_upload_matrix as upload
from research_clock import utc_date_iso


CSV_FIELDS = [
    "workload",
    "timing",
    "rebinding_after",
    "run_id",
    "heartbeat",
    "status",
    "classification",
    "server_remote_addr_count",
    "netlog_target_quic_session_count",
    "netlog_target_using_quic_job_count",
    "netlog_target_path_challenge_received",
    "netlog_target_path_response_sent",
    "netlog_target_path_validation_observed",
    "qlog_path_challenge",
    "qlog_path_response",
    "qlog_path_validation_observed",
    "upload_sink_request_count",
    "upload_sink_request_bytes",
    "proxy_switched",
    "proxy_client_packets_a",
    "proxy_client_packets_b",
    "proxy_client_packet_share_b",
    "proxy_client_bytes_a",
    "proxy_client_bytes_b",
    "proxy_packet_rebind_observed",
    "artifact_dir",
]


def parse_run_spec(raw: str) -> tuple[str, str, str, Path]:
    parts = raw.split(":", 3)
    if len(parts) != 4:
        raise ValueError(
            "run specs must use workload:timing:rebinding_after:artifact_dir, "
            f"got {raw!r}"
        )
    workload, timing, rebinding_after, artifact_dir = parts
    if workload not in {"downlink", "upload"}:
        raise ValueError(f"unsupported workload {workload!r}")
    if not timing:
        raise ValueError("timing must not be empty")
    if not rebinding_after:
        raise ValueError("rebinding_after must not be empty")
    return workload, timing, rebinding_after, Path(artifact_dir)


def packet_share_b(row: dict[str, str]) -> str:
    packets_a = int(row.get("proxy_client_packets_a") or 0)
    packets_b = int(row.get("proxy_client_packets_b") or 0)
    total = packets_a + packets_b
    if total == 0:
        return "0.000"
    return f"{packets_b / total:.3f}"


def qlog_path_validation_observed(row: dict[str, str]) -> str:
    challenge = int(row.get("qlog_path_challenge") or 0)
    response = int(row.get("qlog_path_response") or 0)
    return str(challenge > 0 and response > 0).lower()


def row_from_spec(raw: str) -> dict[str, str]:
    workload, timing, rebinding_after, artifact_dir = parse_run_spec(raw)
    if workload == "downlink":
        base = downlink.row_from_artifact(artifact_dir)
        heartbeat = base["heartbeat"]
        upload_count = ""
        upload_bytes = ""
    else:
        base = upload.row_from_artifact(artifact_dir)
        heartbeat = "n/a"
        upload_count = base["upload_sink_request_count"]
        upload_bytes = base["upload_sink_request_bytes"]

    return {
        "workload": workload,
        "timing": timing,
        "rebinding_after": rebinding_after,
        "run_id": artifact_dir.name,
        "heartbeat": heartbeat,
        "status": base["status"],
        "classification": base["classification"],
        "server_remote_addr_count": base["server_remote_addr_count"],
        "netlog_target_quic_session_count": base["netlog_target_quic_session_count"],
        "netlog_target_using_quic_job_count": base["netlog_target_using_quic_job_count"],
        "netlog_target_path_challenge_received": base["netlog_target_path_challenge_received"],
        "netlog_target_path_response_sent": base["netlog_target_path_response_sent"],
        "netlog_target_path_validation_observed": base["netlog_target_path_validation_observed"],
        "qlog_path_challenge": base["qlog_path_challenge"],
        "qlog_path_response": base["qlog_path_response"],
        "qlog_path_validation_observed": qlog_path_validation_observed(base),
        "upload_sink_request_count": upload_count,
        "upload_sink_request_bytes": upload_bytes,
        "proxy_switched": base["proxy_switched"],
        "proxy_client_packets_a": base["proxy_client_packets_a"],
        "proxy_client_packets_b": base["proxy_client_packets_b"],
        "proxy_client_packet_share_b": packet_share_b(base),
        "proxy_client_bytes_a": base["proxy_client_bytes_a"],
        "proxy_client_bytes_b": base["proxy_client_bytes_b"],
        "proxy_packet_rebind_observed": base["proxy_packet_rebind_observed"],
        "artifact_dir": artifact_dir.as_posix(),
    }


def count_by(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(row[key] for row in rows).items()))


def count_true(rows: list[dict[str, str]], key: str) -> str:
    total = len(rows)
    true_count = sum(1 for row in rows if row[key] == "true")
    return f"{true_count}/{total}"


def avg_b_share(rows: list[dict[str, str]]) -> str:
    if not rows:
        return "0.000"
    values = [float(row["proxy_client_packet_share_b"]) for row in rows]
    return f"{sum(values) / len(values):.3f}"


def grouped_rows(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], list[dict[str, str]]]:
    groups: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        groups[(row["workload"], row["timing"], row["rebinding_after"])].append(row)
    return dict(sorted(groups.items()))


def emit_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Chrome H3 Local Rebinding Timing Sensitivity Summary",
        "",
        f"Generated: `{utc_date_iso()}`",
        "",
        "This summary aggregates local Chrome forced-H3 UDP rebinding runs with early and late proxy switch timing. It is a local NAT-rebinding control, not a public Wi-Fi/LTE handover result.",
        "",
        "## Aggregate",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| runs | `{len(rows)}` |",
        f"| status counts | `{count_by(rows, 'status')}` |",
        f"| workload counts | `{count_by(rows, 'workload')}` |",
        f"| timing counts | `{count_by(rows, 'timing')}` |",
        f"| packet rebinding observed | `{count_true(rows, 'proxy_packet_rebind_observed')}` |",
        f"| qlog path validation observed | `{count_true(rows, 'qlog_path_validation_observed')}` |",
        f"| NetLog target path validation observed | `{count_true(rows, 'netlog_target_path_validation_observed')}` |",
        "",
        "## Timing Groups",
        "",
        "| workload | timing | rebind after | runs | status counts | classification counts | heartbeat counts | qlog path validation | NetLog target path validation | packet rebind | avg B packet share |",
        "| --- | --- | --- | ---: | --- | --- | --- | --- | --- | --- | ---: |",
    ]
    for (workload, timing, rebinding_after), group in grouped_rows(rows).items():
        lines.append(
            "| {workload} | {timing} | {rebinding_after} | {runs} | `{status}` | `{classification}` | "
            "`{heartbeat}` | {qlog} | {netlog} | {packet} | {share} |".format(
                workload=workload,
                timing=timing,
                rebinding_after=rebinding_after,
                runs=len(group),
                status=count_by(group, "status"),
                classification=count_by(group, "classification"),
                heartbeat=count_by(group, "heartbeat"),
                qlog=count_true(group, "qlog_path_validation_observed"),
                netlog=count_true(group, "netlog_target_path_validation_observed"),
                packet=count_true(group, "proxy_packet_rebind_observed"),
                share=avg_b_share(group),
            )
        )

    lines.extend(
        [
            "",
            "## Runs",
            "",
            "| workload | timing | run | heartbeat | status | classification | remote tuples | Chrome QUIC sessions | qlog PATH C/R | NetLog target PATH C/R | proxy packets A/B | B packet share | upload bytes |",
            "| --- | --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- | ---: | ---: |",
        ]
    )
    for row in rows:
        upload_bytes = row["upload_sink_request_bytes"] or "-"
        lines.append(
            "| {workload} | {timing} | {run_id} | {heartbeat} | {status} | `{classification}` | "
            "{server_remote_addr_count} | {netlog_target_quic_session_count} | "
            "{qlog_path_challenge}/{qlog_path_response} | "
            "{netlog_target_path_challenge_received}/{netlog_target_path_response_sent} | "
            "{proxy_client_packets_a}/{proxy_client_packets_b} | "
            "{proxy_client_packet_share_b} | {upload_bytes} |".format(**row, upload_bytes=upload_bytes)
        )

    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "All timing-sensitivity rows completed and recorded proxy packet rebinding, qlog path validation, and Chrome target NetLog path-validation frames. Early rebinding shifts more packets to upstream B, while late rebinding leaves fewer B-side packets but still produces path-validation evidence. The heartbeat rows show that workload timing can change whether extra request/session evidence appears, so heartbeat-based recovery must be evaluated with browser session attribution rather than tuple counts alone.",
            "",
            "These rows strengthen the local NAT-rebinding evidence boundary. They still do not complete the controlled-public active browser handover protocol because no real client route/interface/public-IP change is present.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runs", nargs="+", help="Run spec as workload:timing:rebinding_after:artifact_dir")
    parser.add_argument("--output", default="docs/results/chrome-h3-rebinding-timing-sensitivity-20260624.md")
    parser.add_argument("--csv-output", default="data/chrome-h3-rebinding-timing-sensitivity-20260624.csv")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    rows = [row_from_spec(item) for item in args.runs]
    if args.csv_output:
        write_csv(rows, Path(args.csv_output))
    text = json.dumps(rows, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(rows)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
