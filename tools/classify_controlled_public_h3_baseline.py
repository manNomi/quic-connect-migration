#!/usr/bin/env python3
"""Classify controlled public-origin Chrome HTTP/3 baseline artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from classify_chrome_h3_artifacts import QLOG_PATTERNS, qlog_counts


def read_json(path: Path) -> tuple[dict[str, Any], str | None]:
    if not path.exists():
        return {}, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore")), None
    except json.JSONDecodeError as exc:
        return {}, f"json_decode_error:{exc}"
    except OSError as exc:
        return {}, f"os_error:{exc}"


def request_summary(server: dict[str, Any], expected_requests: int | None) -> dict[str, Any]:
    requests = server.get("requests") or []
    inferred_expected = expected_requests
    if inferred_expected is None:
        try:
            inferred_expected = int(server.get("expected_requests") or 0)
        except (TypeError, ValueError):
            inferred_expected = 0
    if inferred_expected <= 0:
        inferred_expected = len(requests)

    remote_addrs = sorted({request.get("remote_addr") for request in requests if request.get("remote_addr")})
    protos = [request.get("proto") for request in requests]
    alpn = [request.get("tls_alpn") for request in requests]
    h1_requests = sum(
        1
        for request in requests
        if request.get("proto") == "HTTP/1.1" or request.get("tls_alpn") == "http/1.1"
    )
    decoded = sum(1 for request in requests if request.get("decode_successful") is True)

    return {
        "expected_requests": inferred_expected,
        "request_count": len(requests),
        "request_paths": [request.get("path") for request in requests],
        "request_workloads": [request.get("workload") for request in requests],
        "request_labels": [request.get("label") for request in requests],
        "request_protos": protos,
        "request_tls_alpn": alpn,
        "http1_request_count": h1_requests,
        "unknown_proto_request_count": sum(1 for proto in protos if not proto),
        "decoded_successfully_count": decoded,
        "remote_addrs": remote_addrs,
        "remote_addr_count": len(remote_addrs),
        "reached_expected_count": len(requests) >= inferred_expected,
    }


def browser_summary(chrome_public: dict[str, Any]) -> dict[str, Any]:
    bootstrap = chrome_public.get("bootstrap_netlog") or {}
    second = chrome_public.get("second_netlog") or {}
    application_jobs = (
        int(bootstrap.get("target_application_using_quic_job_count") or 0)
        + int(second.get("target_application_using_quic_job_count") or 0)
    )
    discovery_jobs = (
        int(bootstrap.get("target_dns_alpn_h3_job_count") or 0)
        + int(second.get("target_dns_alpn_h3_job_count") or 0)
    )
    quic_sessions = (
        int(bootstrap.get("target_quic_session_count") or 0)
        + int(second.get("target_quic_session_count") or 0)
    )
    main_non_quic_jobs = (
        int(bootstrap.get("target_main_non_quic_job_count") or 0)
        + int(second.get("target_main_non_quic_job_count") or 0)
    )
    return {
        "status": chrome_public.get("status"),
        "classification": chrome_public.get("classification"),
        "application_using_quic_job_count": application_jobs,
        "dns_alpn_h3_job_count": discovery_jobs,
        "quic_session_count": quic_sessions,
        "main_non_quic_job_count": main_non_quic_jobs,
        "any_application_h3_observed": bool(chrome_public.get("any_h3_observed")) or application_jobs > 0,
        "any_h3_discovery": bool(chrome_public.get("any_h3_discovery")) or discovery_jobs > 0 or quic_sessions > 0,
    }


def application_summary(browser_dir: Path) -> dict[str, Any]:
    cdp, cdp_error = read_json(browser_dir / "chrome" / "cdp-summary.json")
    page_state = cdp.get("page_state") if isinstance(cdp.get("page_state"), dict) else {}
    dataset = page_state.get("body_dataset") if isinstance(page_state.get("body_dataset"), dict) else {}
    error_keys = sorted(
        key
        for key in dataset
        if key.lower().endswith("error") or key.lower().endswith("lasterror")
    )
    terminal_error_keys = [key for key in error_keys if not key.lower().endswith("lasterror")]
    success: bool | None = None
    complete: bool | None = None
    workload = "unknown"
    if any(key.startswith("downlink") for key in dataset):
        workload = "downlink"
        complete = dataset.get("downlinkComplete") == "true"
        success = complete and not terminal_error_keys
    elif any(key.startswith("upload") for key in dataset):
        workload = "upload"
        complete = dataset.get("uploadComplete") == "true"
        success = complete and not terminal_error_keys
    elif any(key.startswith("poll") for key in dataset):
        workload = "poll"
        complete = dataset.get("pollComplete") == "true"
        success = complete and not terminal_error_keys
    elif any(key.startswith("media") for key in dataset):
        workload = "media"
        complete = dataset.get("mediaComplete") == "true"
        success = complete and not terminal_error_keys
    elif dataset.get("slowComplete") == "true":
        workload = "slow"
        complete = True
        success = True
    return {
        "cdp_summary_error": cdp_error,
        "workload": workload,
        "complete": complete,
        "success": success,
        "error_keys": error_keys,
        "terminal_error_keys": terminal_error_keys,
        "body_dataset": dataset,
    }


def classify(summary: dict[str, Any]) -> tuple[str, str]:
    if summary["server_error"] == "missing":
        return "FAIL", "controlled_public_server_artifact_missing"
    if summary["browser_error"] == "missing" and not summary["allow_missing_browser_summary"]:
        return "FAIL", "controlled_public_browser_artifact_missing"
    if not summary["server_ok"] or not summary["server_requests"]["reached_expected_count"]:
        return "FAIL", "controlled_public_server_workload_failed"
    if not summary["server_qlog_has_application_h3"]:
        if summary["browser"]["any_h3_discovery"]:
            return "PASS_NEGATIVE_CONTROL", "controlled_public_h3_discovery_without_server_application_h3"
        return "PASS_NEGATIVE_CONTROL", "controlled_public_application_h3_not_confirmed"
    if summary["browser"]["any_application_h3_observed"]:
        return "PASS", "controlled_public_application_h3_confirmed"
    if summary["browser_error"] == "missing":
        return "PASS_FEASIBILITY", "controlled_public_server_qlog_h3_confirmed_browser_summary_missing"
    return "PASS", "controlled_public_server_qlog_h3_confirmed_browser_netlog_inconclusive"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_dir", help="combined browser/server artifact directory")
    parser.add_argument("--server-artifact-dir", help="server artifact directory; defaults to artifact_dir")
    parser.add_argument("--browser-artifact-dir", help="browser artifact directory; defaults to artifact_dir")
    parser.add_argument("--expected-requests", type=int)
    parser.add_argument("--url", help="controlled public URL, copied into the output for traceability")
    parser.add_argument("--allow-missing-browser-summary", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    artifact_dir = Path(args.artifact_dir)
    server_dir = Path(args.server_artifact_dir) if args.server_artifact_dir else artifact_dir
    browser_dir = Path(args.browser_artifact_dir) if args.browser_artifact_dir else artifact_dir

    server, server_error = read_json(server_dir / "results" / "server.json")
    metadata, metadata_error = read_json(server_dir / "results" / "server-public-origin-metadata.json")
    readiness, readiness_error = read_json(browser_dir / "results" / "public-origin-readiness.json")
    chrome_public, browser_error = read_json(browser_dir / "results" / "chrome-public-h3-summary.json")

    qcounts = qlog_counts(server_dir / "qlog")
    qlog_summary = {key: qcounts[key] for key in QLOG_PATTERNS}
    server_requests = request_summary(server, args.expected_requests)
    browser = browser_summary(chrome_public)
    application = application_summary(browser_dir)
    server_qlog_has_application_h3 = qcounts["chosen_alpn"] > 0 and qcounts["http3_frame"] > 0

    summary: dict[str, Any] = {
        "status": "FAIL",
        "classification": "unclassified",
        "artifact_dir": str(artifact_dir),
        "server_artifact_dir": str(server_dir),
        "browser_artifact_dir": str(browser_dir),
        "url": args.url or chrome_public.get("url") or readiness.get("url"),
        "allow_missing_browser_summary": args.allow_missing_browser_summary,
        "server_error": server_error,
        "browser_error": browser_error,
        "metadata_error": metadata_error,
        "readiness_error": readiness_error,
        "server_ok": server.get("ok") is True,
        "server_result_error": server.get("error"),
        "server_metadata": metadata,
        "public_origin_readiness": {
            "https_ok": readiness.get("https_ok"),
            "has_h3_alt_svc": readiness.get("has_h3_alt_svc"),
            "browser_h3_candidate": readiness.get("browser_h3_candidate"),
            "workload_candidate": readiness.get("workload_candidate"),
            "final_status": readiness.get("final_status"),
        },
        "server_requests": server_requests,
        "browser": browser,
        "application": application,
        "qlog_counts": qlog_summary,
        "server_qlog_has_application_h3": server_qlog_has_application_h3,
        "server_qlog_has_path_validation": qcounts["path_challenge"] > 0 or qcounts["path_response"] > 0,
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
