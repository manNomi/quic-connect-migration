#!/usr/bin/env python3
"""Summarize Chrome HTTP/3 local UDP rebinding upload artifacts."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


CSV_FIELDS = [
    "run_id",
    "status",
    "classification",
    "server_remote_addr_count",
    "netlog_target_quic_session_count",
    "netlog_target_using_quic_job_count",
    "upload_sink_request_count",
    "upload_sink_request_bytes",
    "qlog_path_challenge",
    "qlog_path_response",
    "proxy_switched",
    "proxy_upstream_a_addr",
    "proxy_upstream_b_addr",
    "artifact_dir",
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def upload_sink_records(artifact_dir: Path, summary: dict[str, Any]) -> list[dict[str, Any]]:
    server = read_json(artifact_dir / "results" / "server.json")
    requests = server.get("requests") or summary.get("server_requests") or []
    return [item for item in requests if isinstance(item, dict) and item.get("path") == "/upload-sink"]


def row_from_artifact(artifact_dir: Path) -> dict[str, str]:
    summary = read_json(artifact_dir / "results" / "chrome-summary.json")
    proxy = summary.get("rebinding_proxy") if isinstance(summary.get("rebinding_proxy"), dict) else {}
    qlog_counts = summary.get("qlog_counts") if isinstance(summary.get("qlog_counts"), dict) else {}
    uploads = upload_sink_records(artifact_dir, summary)
    return {
        "run_id": artifact_dir.name,
        "status": str(summary.get("status") or "missing"),
        "classification": str(summary.get("classification") or "missing"),
        "server_remote_addr_count": str(summary.get("server_remote_addr_count") or 0),
        "netlog_target_quic_session_count": str(summary.get("netlog_target_quic_session_count") or 0),
        "netlog_target_using_quic_job_count": str(summary.get("netlog_target_using_quic_job_count") or 0),
        "upload_sink_request_count": str(len(uploads)),
        "upload_sink_request_bytes": str(sum(int(item.get("request_bytes") or 0) for item in uploads)),
        "qlog_path_challenge": str(qlog_counts.get("path_challenge") or 0),
        "qlog_path_response": str(qlog_counts.get("path_response") or 0),
        "proxy_switched": str(proxy.get("switched") is True).lower(),
        "proxy_upstream_a_addr": str(proxy.get("upstream_a_addr") or ""),
        "proxy_upstream_b_addr": str(proxy.get("upstream_b_addr") or ""),
        "artifact_dir": artifact_dir.as_posix(),
    }


def read_rows(artifact_dirs: list[Path]) -> list[dict[str, str]]:
    return [row_from_artifact(path) for path in artifact_dirs]


def count_by(rows: list[dict[str, str]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(row[key] for row in rows).items()))


def emit_markdown(rows: list[dict[str, str]]) -> str:
    lines = [
        "# Chrome H3 Local UDP Rebinding Upload Summary",
        "",
        f"Generated: `{date.today().isoformat()}`",
        "",
        "This summary aggregates local Chrome forced-H3 streaming upload repetitions through a UDP rebinding proxy. It is a local NAT-rebinding control, not a public Wi-Fi/LTE handover result.",
        "",
        "## Aggregate",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| runs | `{len(rows)}` |",
        f"| status counts | `{count_by(rows, 'status')}` |",
        f"| classification counts | `{count_by(rows, 'classification')}` |",
        f"| upload request counts | `{count_by(rows, 'upload_sink_request_count')}` |",
        "",
        "## Runs",
        "",
        "| run | status | classification | remote tuples | Chrome QUIC sessions | upload sink requests | upload bytes | qlog PATH_CHALLENGE/PATH_RESPONSE | proxy switched |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {run_id} | {status} | `{classification}` | {server_remote_addr_count} | "
            "{netlog_target_quic_session_count} | {upload_sink_request_count} | {upload_sink_request_bytes} | "
            "{qlog_path_challenge}/{qlog_path_response} | {proxy_switched} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Interpretation Boundary",
            "",
            "Use these rows as a client-sending local control. If uploads complete while request-level server tuples stay stable, the result strengthens the evidence boundary: request logs alone may miss packet-level rebinding, so qlog and browser NetLog remain required. These rows do not complete the final controlled-public browser handover protocol.",
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
    parser.add_argument("artifact_dirs", nargs="+")
    parser.add_argument("--output", default="docs/results/chrome-h3-rebinding-upload-summary-20260624.md")
    parser.add_argument("--csv-output", default="data/chrome-h3-rebinding-upload-summary-20260624.csv")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    rows = read_rows([Path(item) for item in args.artifact_dirs])
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
