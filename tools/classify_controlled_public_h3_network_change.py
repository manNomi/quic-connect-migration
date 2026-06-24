#!/usr/bin/env python3
"""Classify controlled public-origin Chrome HTTP/3 network-change artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from classify_chrome_h3_artifacts import QLOG_PATTERNS, qlog_counts
from classify_chrome_public_h3_artifacts import summarize_netlog
from classify_controlled_public_h3_baseline import read_json, request_summary


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def network_change_summary(path: Path) -> dict[str, Any]:
    data, error = read_json(path)
    return {
        "error": error,
        "exit": data.get("exit"),
        "command_present": bool(data.get("command_present")),
        "started_at": data.get("started_at"),
        "completed_at": data.get("completed_at"),
    }


def client_path_change_summary(path: Path) -> dict[str, Any]:
    data, error = read_json(path)
    return {
        "error": error,
        "classification": data.get("classification"),
        "active_path_changed": bool(data.get("active_path_changed")),
        "active_interface_set_changed": bool(data.get("active_interface_set_changed")),
        "default_interface_changed": bool(data.get("default_interface_changed")),
        "target_interface_changed": bool(data.get("target_interface_changed")),
        "default_gateway_changed": bool(data.get("default_gateway_changed")),
        "target_gateway_changed": bool(data.get("target_gateway_changed")),
        "public_ip_changed": bool(data.get("public_ip_changed")),
        "before": data.get("before") if isinstance(data.get("before"), dict) else {},
        "after": data.get("after") if isinstance(data.get("after"), dict) else {},
    }


def classify(summary: dict[str, Any]) -> tuple[str, str]:
    server_requests = summary["server_requests"]
    network_change = summary["network_change"]
    netlog = summary["netlog"]
    qlog_has_path_validation = summary["server_qlog_has_path_validation"]
    browser_kind = summary["browser_kind"]
    remote_addr_count = int(server_requests["remote_addr_count"])
    quic_sessions = int(netlog.get("target_quic_session_count") or 0)

    if summary["server_error"] == "missing":
        return "FAIL", "controlled_public_network_change_server_artifact_missing"
    if not summary["server_ok"] or not server_requests["reached_expected_count"]:
        return "FAIL", "controlled_public_network_change_workload_failed"
    if not summary["server_qlog_has_application_h3"]:
        return "FAIL", "controlled_public_network_change_application_h3_precondition_failed"
    if network_change["error"] == "missing" or not network_change["command_present"]:
        return "PASS_NEGATIVE_CONTROL", "controlled_public_network_change_not_executed"
    if network_change["exit"] not in (0, None):
        return "FAIL", "controlled_public_network_change_command_failed"

    if browser_kind != "chrome" and remote_addr_count > 1 and qlog_has_path_validation:
        return "PASS_FEASIBILITY", "possible_connection_migration_server_qlog_only"
    if remote_addr_count > 1 and qlog_has_path_validation and quic_sessions <= 1:
        return "PASS", "possible_connection_migration"
    if remote_addr_count > 1 and qlog_has_path_validation and quic_sessions > 1:
        return "PASS_NEGATIVE_CONTROL", "reconnect_or_multiple_sessions"
    if remote_addr_count > 1 and not qlog_has_path_validation:
        return "PASS_NEGATIVE_CONTROL", "tuple_changed_without_path_validation"
    if remote_addr_count == 1 and qlog_has_path_validation:
        return "PASS_NEGATIVE_CONTROL", "path_validation_without_observed_tuple_change"
    if remote_addr_count == 1:
        return "PASS_NEGATIVE_CONTROL", "no_path_change_after_trigger"
    return "PASS_NEGATIVE_CONTROL", "controlled_public_network_change_inconclusive"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_dir", help="browser/network-change artifact directory")
    parser.add_argument("--server-artifact-dir", help="server artifact directory; defaults to artifact_dir")
    parser.add_argument("--url", required=True)
    parser.add_argument("--expected-requests", type=int)
    parser.add_argument("--browser-kind", choices=["chrome", "safari"], default="chrome")
    parser.add_argument("--browser-exit", type=int)
    parser.add_argument("--chrome-exit", type=int)
    parser.add_argument("--allow-missing-browser-netlog", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    artifact_dir = Path(args.artifact_dir)
    server_dir = Path(args.server_artifact_dir) if args.server_artifact_dir else artifact_dir
    browser_exit = args.browser_exit if args.browser_exit is not None else (args.chrome_exit if args.chrome_exit is not None else 0)
    server, server_error = read_json(server_dir / "results" / "server.json")
    readiness, readiness_error = read_json(artifact_dir / "results" / "public-origin-readiness.json")
    qcounts = qlog_counts(server_dir / "qlog")
    netlog = summarize_netlog(artifact_dir / "chrome" / "network-change-netlog.json", args.url)
    dump = read_text(artifact_dir / "chrome" / "network-change-dump-dom.txt")
    server_requests = request_summary(server, args.expected_requests)
    network_change = network_change_summary(artifact_dir / "results" / "network-change.json")
    client_path_change = client_path_change_summary(artifact_dir / "results" / "client-path-change-summary.json")

    summary: dict[str, Any] = {
        "status": "FAIL",
        "classification": "unclassified",
        "artifact_dir": str(artifact_dir),
        "server_artifact_dir": str(server_dir),
        "url": args.url,
        "browser_kind": args.browser_kind,
        "browser_exit": browser_exit,
        "browser_completed_cleanly": browser_exit == 0,
        "browser_timed_out_after_request": browser_exit == 124 and server_requests["reached_expected_count"],
        "chrome_exit": browser_exit if args.browser_kind == "chrome" else None,
        "chrome_completed_cleanly": browser_exit == 0 if args.browser_kind == "chrome" else None,
        "chrome_timed_out_after_request": browser_exit == 124 and server_requests["reached_expected_count"] if args.browser_kind == "chrome" else None,
        "allow_missing_browser_netlog": args.allow_missing_browser_netlog,
        "server_error": server_error,
        "readiness_error": readiness_error,
        "server_ok": server.get("ok") is True,
        "server_result_error": server.get("error"),
        "server_requests": server_requests,
        "network_change": network_change,
        "client_path_change": client_path_change,
        "public_origin_readiness": {
            "https_ok": readiness.get("https_ok"),
            "has_h3_alt_svc": readiness.get("has_h3_alt_svc"),
            "browser_h3_candidate": readiness.get("browser_h3_candidate"),
            "workload_candidate": readiness.get("workload_candidate"),
            "final_status": readiness.get("final_status"),
        },
        "netlog": netlog,
        "netlog_has_application_h3": int(netlog.get("target_application_using_quic_job_count") or 0) > 0,
        "netlog_has_h3_discovery": (
            int(netlog.get("target_dns_alpn_h3_job_count") or 0)
            + int(netlog.get("target_quic_session_count") or 0)
        )
        > 0,
        "qlog_counts": {key: qcounts[key] for key in QLOG_PATTERNS},
        "server_qlog_has_application_h3": qcounts["chosen_alpn"] > 0 and qcounts["http3_frame"] > 0,
        "server_qlog_has_path_validation": qcounts["path_challenge"] > 0 or qcounts["path_response"] > 0,
        "dump_dom_bytes": len(dump),
        "dump_has_chrome_error": "ERR_" in dump,
    }
    status, classification = classify(summary)
    summary["status"] = status
    summary["classification"] = classification

    text = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if status.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
