#!/usr/bin/env python3
"""Draft a data/experiment-results.csv row from final handover artifacts."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any


CSV_FIELDS = [
    "trial_id",
    "date",
    "status",
    "implementation",
    "deployment_tier",
    "protocol",
    "migration_trigger",
    "path_validation_observed",
    "tuple_change_observed",
    "application_task",
    "application_success",
    "manual_intervention_required",
    "failure_layer",
    "artifact_dir",
    "notes",
]


SUMMARY_CANDIDATES = [
    "results/controlled-public-h3-network-change-summary.json",
    "results/safari-controlled-public-h3-network-change-summary.json",
    "results/android-chrome-controlled-public-h3-network-change-summary.json",
    "results/controlled-public-h3-baseline-summary.json",
]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def find_summary(artifact_dir: Path, explicit: str | None = None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(f"summary not found: {path}")
        return path
    for rel in SUMMARY_CANDIDATES:
        path = artifact_dir / rel
        if path.exists():
            return path
    raise FileNotFoundError(f"no known final handover summary found under {artifact_dir}")


def bool_cell(value: bool) -> str:
    return "true" if value else "false"


def infer_browser(trial_id: str, summary: dict[str, Any]) -> str:
    browser_kind = str(summary.get("browser_kind") or "").lower()
    lowered = trial_id.lower()
    if "android" in lowered or browser_kind == "android-chrome":
        return "Android Chrome"
    if "safari" in lowered or browser_kind == "safari":
        return "Safari"
    return "Chrome"


def infer_phase(trial_id: str) -> str:
    lowered = trial_id.lower()
    if "nochange" in lowered:
        return "no-change-baseline"
    if "network-change" in lowered:
        return "active-network-change"
    return "baseline"


def has_heartbeat(trial_id: str, summary: dict[str, Any]) -> bool:
    lowered = trial_id.lower()
    if "noheartbeat" in lowered:
        return False
    if "heartbeat" in lowered:
        return True
    labels = " ".join(str(item) for item in (summary.get("server_requests") or {}).get("request_labels", []))
    workloads = " ".join(str(item) for item in (summary.get("server_requests") or {}).get("request_workloads", []))
    return "heartbeat" in f"{labels} {workloads}".lower()


def implementation_for(browser: str) -> str:
    return f"{browser} + controlled public quic-go H3"


def task_for(phase: str, heartbeat: bool) -> str:
    if phase == "baseline":
        return "GET /browser-slow plus streaming GET /slow-js"
    if heartbeat:
        return "GET /browser-downlink then streaming GET /downlink-stream plus GET /heartbeat"
    return "GET /browser-downlink then streaming GET /downlink-stream"


def status_for(phase: str, browser: str, summary: dict[str, Any]) -> str:
    raw_status = str(summary.get("status") or "FAIL")
    classification = str(summary.get("classification") or "")
    if phase == "active-network-change" and browser in {"Safari", "Android Chrome"}:
        if classification == "possible_connection_migration_server_qlog_only":
            return "PASS_FEASIBILITY"
        return raw_status if raw_status.startswith("PASS") else "FAIL"
    if phase == "active-network-change" and browser == "Chrome":
        if classification == "possible_connection_migration":
            return "PASS"
        if raw_status.startswith("PASS"):
            return "PASS_NEGATIVE_CONTROL"
        return "FAIL"
    if phase == "no-change-baseline":
        return "PASS" if raw_status.startswith("PASS") else "FAIL"
    return raw_status if raw_status.startswith("PASS") else "FAIL"


def deployment_for(phase: str, browser: str) -> str:
    if phase == "baseline":
        return "controlled public browser baseline"
    if phase == "no-change-baseline":
        return "controlled public browser no-change baseline"
    if browser == "Android Chrome":
        return "controlled public mobile browser active network-change"
    return "controlled public browser active network-change"


def trigger_for(phase: str, browser: str, heartbeat: bool) -> str:
    if phase == "baseline":
        return "controlled public application H3 baseline; no active path-change"
    if phase == "no-change-baseline":
        suffix = "with heartbeat" if heartbeat else "without heartbeat"
        return f"no network change; controlled public downlink streaming {suffix}"
    target = browser if browser != "Chrome" else "Chrome"
    return f"active path change during {target} downlink workload; NETWORK_CHANGE_CMD executed"


def failure_layer_for(status: str, summary: dict[str, Any]) -> str:
    if status in {"PASS", "PASS_FEASIBILITY"}:
        if status == "PASS_FEASIBILITY":
            return "server-qlog-only"
        return "none"
    classification = str(summary.get("classification") or "")
    if classification == "no_path_change_after_trigger":
        return "trigger-no-active-path-change"
    if classification == "reconnect_or_multiple_sessions":
        return "browser-reconnect-or-multiple-sessions"
    if classification == "tuple_changed_without_path_validation":
        return "path-validation-not-observed"
    if classification:
        return classification
    return "classifier-failure"


def application_success(summary: dict[str, Any], status: str) -> bool:
    if not status.startswith("PASS"):
        return False
    server_requests = summary.get("server_requests") or {}
    if server_requests and server_requests.get("reached_expected_count") is False:
        return False
    if summary.get("browser_completed_cleanly") is False and not summary.get("browser_timed_out_after_request"):
        return False
    return True


def notes_for(phase: str, browser: str, heartbeat: bool, summary: dict[str, Any]) -> str:
    classification = str(summary.get("classification") or "unclassified")
    server_requests = summary.get("server_requests") or {}
    remote_count = server_requests.get("remote_addr_count", "-")
    qlog_path = bool(summary.get("server_qlog_has_path_validation"))
    client_path = (summary.get("client_path_change") or {}).get("classification") or "-"
    parts = [f"classification {classification}"]
    if phase == "no-change-baseline":
        parts.append("no_path_change_baseline")
    if phase == "baseline":
        parts.append("controlled_public_application_h3_confirmed")
        parts.append("controlled_public_server_qlog_h3_confirmed")
    if browser in {"Safari", "Android Chrome"}:
        parts.append(f"{browser} navigation_ok={bool(summary.get('browser_completed_cleanly', True))}")
        parts.append("browser-internal QUIC log unavailable")
    if heartbeat:
        parts.append("heartbeat variant")
    parts.extend(
        [
            f"client_path_change={client_path}",
            f"server remote addr count {remote_count}",
            f"qlog path validation={str(qlog_path).lower()}",
        ]
    )
    return "; ".join(parts)


def build_row(trial_id: str, artifact_dir: Path, summary: dict[str, Any], run_date: str) -> dict[str, str]:
    browser = infer_browser(trial_id, summary)
    phase = infer_phase(trial_id)
    heartbeat = has_heartbeat(trial_id, summary)
    status = status_for(phase, browser, summary)
    server_requests = summary.get("server_requests") or {}
    remote_count = int(server_requests.get("remote_addr_count") or 0)
    path_validation = bool(summary.get("server_qlog_has_path_validation"))
    row = {
        "trial_id": trial_id,
        "date": run_date,
        "status": status,
        "implementation": implementation_for(browser),
        "deployment_tier": deployment_for(phase, browser),
        "protocol": "HTTP/3 over QUIC",
        "migration_trigger": trigger_for(phase, browser, heartbeat),
        "path_validation_observed": bool_cell(path_validation),
        "tuple_change_observed": bool_cell(remote_count > 1),
        "application_task": task_for(phase, heartbeat),
        "application_success": bool_cell(application_success(summary, status)),
        "manual_intervention_required": "false",
        "failure_layer": failure_layer_for(status, summary),
        "artifact_dir": artifact_dir.as_posix(),
        "notes": notes_for(phase, browser, heartbeat, summary),
    }
    return row


def emit_csv(row: dict[str, str]) -> str:
    from io import StringIO

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS)
    writer.writeheader()
    writer.writerow(row)
    return buffer.getvalue()


def emit_markdown(row: dict[str, str]) -> str:
    lines = [
        "# Final Handover Result Row Draft",
        "",
        "| field | value |",
        "| --- | --- |",
    ]
    for field in CSV_FIELDS:
        lines.append(f"| `{field}` | `{row[field]}` |")
    lines.extend(["", "CSV:", "", "```csv", emit_csv(row).rstrip(), "```"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial-id", required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--summary")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--format", choices=["csv", "json", "markdown"], default="csv")
    parser.add_argument("--output")
    args = parser.parse_args()

    artifact_dir = Path(args.artifact_dir)
    summary_path = find_summary(artifact_dir, args.summary)
    row = build_row(args.trial_id, artifact_dir, read_json(summary_path), args.date)

    if args.format == "json":
        text = json.dumps(row, indent=2, ensure_ascii=False) + "\n"
    elif args.format == "markdown":
        text = emit_markdown(row)
    else:
        text = emit_csv(row)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
