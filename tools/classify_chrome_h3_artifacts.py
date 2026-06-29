#!/usr/bin/env python3
"""Classify Chrome HTTP/3 artifacts for browser migration experiments."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


QLOG_PATTERNS = {
    "path_challenge": "path_challenge",
    "path_response": "path_response",
    "connection_started": "connection_started",
    "connection_closed": "connection_closed",
    "packet_sent": "packet_sent",
    "packet_received": "packet_received",
    "http3_frame": "http3:frame",
    "chosen_alpn": "chosen_alpn",
    "migration": "migration",
    "path": "path",
}


def classify_netlog_migration_event(name: str) -> str:
    upper = name.upper()
    if "MIGRAT" not in upper:
        return ""
    if "MODE" in upper:
        return "mode"
    if "SUCCESS" in upper:
        return "success"
    if "FAIL" in upper:
        return "failure"
    if "_ON_" in upper or "TRIGGER" in upper or "PATH_DEGRADING" in upper or "WRITE_ERROR" in upper:
        return "trigger"
    return "other"


def read_json(path: Path) -> tuple[dict, str | None]:
    if not path.exists():
        return {}, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore")), None
    except json.JSONDecodeError as exc:
        return {}, f"json_decode_error:{exc}"
    except OSError as exc:
        return {}, f"os_error:{exc}"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def qlog_counts(qlog_dir: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    if not qlog_dir.exists():
        return counts
    for path in qlog_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in {".sqlog", ".qlog", ".json", ".jsonl", ".txt"}:
            continue
        text = read_text(path).lower()
        for key, needle in QLOG_PATTERNS.items():
            counts[key] += text.count(needle.lower())
    return counts


def reverse_netlog_event_types(netlog: dict) -> dict[int, str]:
    event_types = netlog.get("constants", {}).get("logEventTypes", {})
    reverse: dict[int, str] = {}
    for name, value in event_types.items():
        try:
            reverse[int(value)] = str(name)
        except (TypeError, ValueError):
            continue
    return reverse


def parse_netlog(netlog: dict, addr: str) -> dict[str, object]:
    target_host, target_port = addr.rsplit(":", 1)
    reverse_types = reverse_netlog_event_types(netlog)
    target_quic_source_ids: set[str] = set()
    target_quic_sessions = 0
    target_using_quic_jobs = 0
    target_url_requests = 0
    target_http_stream_jobs = 0
    target_non_quic_jobs = 0
    migration_event_counts: Counter[str] = Counter()
    migration_event_class_counts: Counter[str] = Counter()
    network_event_counts: Counter[str] = Counter()

    for event in netlog.get("events", []):
        name = reverse_types.get(event.get("type"), str(event.get("type")))
        params = event.get("params") or {}
        source = event.get("source") or {}

        if name == "QUIC_SESSION" and params.get("host") == target_host and str(params.get("port")) == target_port:
            target_quic_sessions += 1
            if "id" in source:
                target_quic_source_ids.add(str(source["id"]))

        if name == "HTTP_STREAM_JOB" and params.get("destination") == f"https://{addr}":
            target_http_stream_jobs += 1
            if params.get("using_quic") is True:
                target_using_quic_jobs += 1
            else:
                target_non_quic_jobs += 1

        if name == "URL_REQUEST_START_JOB" and str(params.get("url", "")).startswith(f"https://{addr}/"):
            target_url_requests += 1

        upper_name = name.upper()
        if "MIGRAT" in upper_name:
            migration_event_counts[name] += 1
            migration_class = classify_netlog_migration_event(name)
            if migration_class:
                migration_event_class_counts[migration_class] += 1
        if "NETWORK" in upper_name and ("CHANGE" in upper_name or "CHANGED" in upper_name):
            network_event_counts[name] += 1

    return {
        "parser_mode": "json",
        "target_quic_session_count": target_quic_sessions,
        "target_quic_source_ids": sorted(target_quic_source_ids),
        "target_using_quic_job_count": target_using_quic_jobs,
        "target_http_stream_job_count": target_http_stream_jobs,
        "target_non_quic_job_count": target_non_quic_jobs,
        "target_url_request_count": target_url_requests,
        "migration_event_counts": dict(sorted(migration_event_counts.items())),
        "migration_event_class_counts": dict(sorted(migration_event_class_counts.items())),
        "network_event_counts": dict(sorted(network_event_counts.items())),
    }


def parse_netlog_text_fallback(netlog_text: str, addr: str) -> dict[str, object]:
    # Chrome headless can be terminated after the request evidence is written but
    # before the NetLog JSON is closed. In that case, use conservative string
    # evidence from event params rather than event constants alone.
    target_host, target_port = addr.rsplit(":", 1)
    compact = netlog_text.replace(" ", "")
    host_port_seen = (
        f'"host":"{target_host}"' in compact
        and (f'"port":{target_port}' in compact or f'"port":"{target_port}"' in compact)
    )
    destination = f'"destination":"https://{addr}"'
    using_quic = '"using_quic":true'
    target_using_quic_jobs = compact.count(destination)
    if target_using_quic_jobs:
        target_using_quic_jobs = min(target_using_quic_jobs, compact.count(using_quic))
    target_url_requests = compact.count(f'"url":"https://{addr}/')
    return {
        "parser_mode": "text_fallback",
        "target_quic_session_count": 1 if host_port_seen else 0,
        "target_quic_source_ids": [],
        "target_using_quic_job_count": target_using_quic_jobs,
        "target_http_stream_job_count": compact.count(destination),
        "target_non_quic_job_count": 0,
        "target_url_request_count": target_url_requests,
        "migration_event_counts": {},
        "migration_event_class_counts": {},
        "network_event_counts": {},
    }


def summarize_rebinding_proxy(proxy: dict, error: str | None) -> dict[str, object] | None:
    if error == "missing" and not proxy:
        return None
    return {
        "error": error,
        "switched": proxy.get("switched"),
        "upstream_a_addr": proxy.get("upstream_a_addr"),
        "upstream_b_addr": proxy.get("upstream_b_addr"),
        "client_packets": proxy.get("client_packets"),
        "server_packets_a": proxy.get("server_packets_a"),
        "server_packets_b": proxy.get("server_packets_b"),
    }


def rebinding_proxy_switched(summary: dict[str, object]) -> bool:
    proxy = summary.get("rebinding_proxy")
    return isinstance(proxy, dict) and proxy.get("switched") is True


def dump_application_complete(dump: str, workload: str) -> bool:
    if "upload" in workload:
        return 'data-upload-complete="true"' in dump and 'data-upload-status="200"' in dump
    if "downlink" in workload:
        return 'data-downlink-complete="true"' in dump
    if "poll" in workload:
        return 'data-poll-complete="true"' in dump
    if "media" in workload:
        return 'data-media-complete="true"' in dump
    if "range" in workload:
        return 'data-range-complete="true"' in dump
    if "slow" in workload:
        return 'data-slow-complete="true"' in dump or "slowComplete = 'true'" in dump
    return True


def dump_data_attr(dump: str, name: str) -> str | None:
    match = re.search(rf'\bdata-{re.escape(name)}="([^"]*)"', dump)
    if not match:
        return None
    return match.group(1)


def dump_data_attr_int(dump: str, name: str) -> int | None:
    value = dump_data_attr(dump, name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def dump_task_timing(dump: str, workload: str) -> dict[str, int | None]:
    if "upload" in workload:
        prefix = "upload"
    elif "downlink" in workload:
        prefix = "downlink"
    elif "poll" in workload:
        prefix = "poll"
    elif "media" in workload:
        prefix = "media"
    elif "range" in workload:
        prefix = "range"
    elif "slow" in workload:
        prefix = "slow"
    else:
        return {"elapsed_ms": None, "error_elapsed_ms": None}
    return {
        "elapsed_ms": dump_data_attr_int(dump, f"{prefix}-elapsed-ms"),
        "error_elapsed_ms": dump_data_attr_int(dump, f"{prefix}-error-elapsed-ms"),
    }


def classify(summary: dict[str, object]) -> str:
    request_reached_server = bool(summary["request_reached_server"])
    qlog_has_path_validation = bool(summary["qlog_has_path_validation"])
    qlog_has_path_probe = bool(summary.get("qlog_has_path_probe"))
    remote_addr_count = int(summary["server_remote_addr_count"])
    target_quic_sessions = int(summary["netlog_target_quic_session_count"])
    target_using_quic_jobs = int(summary["netlog_target_using_quic_job_count"])
    network_change_requested = summary.get("network_change_exit") is not None
    proxy_switched = rebinding_proxy_switched(summary)
    client_path_change = summary.get("client_path_change")
    client_path_classification = ""
    if isinstance(client_path_change, dict):
        client_path_classification = str(client_path_change.get("classification") or "")
    client_active_path_changed = client_path_classification == "client_active_path_changed"

    if not request_reached_server or target_using_quic_jobs <= 0:
        return "browser_h3_request_failed"
    if summary.get("dump_application_complete") is False or summary.get("dump_has_chrome_error") is True:
        return "browser_application_task_failed"
    if proxy_switched and remote_addr_count > 1 and qlog_has_path_validation and target_quic_sessions == 1:
        return "nat_rebinding_possible_session_continuity"
    if proxy_switched and remote_addr_count > 1 and target_quic_sessions > 1:
        return "nat_rebinding_multiple_quic_sessions"
    if proxy_switched and remote_addr_count > 1 and not qlog_has_path_validation:
        return "nat_rebinding_tuple_changed_without_path_validation"
    if proxy_switched and remote_addr_count == 1 and qlog_has_path_validation:
        return "nat_rebinding_path_validation_without_observed_tuple_change"
    if proxy_switched and remote_addr_count == 1 and qlog_has_path_probe and not qlog_has_path_validation:
        return "nat_rebinding_path_probe_without_validation"
    if remote_addr_count > 1 and qlog_has_path_validation and target_quic_sessions == 1:
        return "possible_connection_migration"
    if remote_addr_count > 1 and target_quic_sessions > 1:
        if not network_change_requested:
            return "multiple_quic_sessions_without_network_change"
        if client_path_classification and not client_active_path_changed:
            return "multiple_quic_sessions_without_client_path_change"
        return "reconnect_or_multiple_sessions"
    if remote_addr_count > 1 and not qlog_has_path_validation:
        return "tuple_changed_without_path_validation"
    if remote_addr_count == 1 and qlog_has_path_validation:
        return "path_validation_without_observed_tuple_change"
    if remote_addr_count == 1 and target_quic_sessions == 1:
        return "no_path_change_baseline"
    return "inconclusive"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_dir")
    parser.add_argument("--addr", required=True)
    parser.add_argument("--expected-requests", type=int, required=True)
    parser.add_argument("--workload", required=True)
    parser.add_argument("--chrome-exit", type=int, default=0)
    parser.add_argument("--server-exit", type=int, default=0)
    parser.add_argument("--output")
    args = parser.parse_args()

    base = Path(args.artifact_dir)
    server, server_error = read_json(base / "results" / "server.json")
    network_change, network_change_error = read_json(base / "results" / "network-change.json")
    client_path_change, client_path_change_error = read_json(base / "results" / "client-path-change-summary.json")
    rebinding_proxy, rebinding_proxy_error = read_json(base / "results" / "rebinding-proxy.json")
    netlog_path = base / "chrome" / "netlog.json"
    netlog_text = read_text(netlog_path)
    netlog, netlog_error = read_json(netlog_path)
    dump = read_text(base / "chrome" / "dump-dom.txt")
    requests = server.get("requests") or []
    remote_addrs = sorted({request.get("remote_addr") for request in requests if request.get("remote_addr")})
    labels = [request.get("label") for request in requests]
    paths = [request.get("path") for request in requests]
    qcounts = qlog_counts(base / "qlog")
    if netlog:
        netlog_summary = parse_netlog(netlog, args.addr)
    elif netlog_text:
        netlog_summary = parse_netlog_text_fallback(netlog_text, args.addr)
    else:
        netlog_summary = {
            "parser_mode": "missing",
            "target_quic_session_count": 0,
            "target_quic_source_ids": [],
            "target_using_quic_job_count": 0,
            "target_http_stream_job_count": 0,
            "target_non_quic_job_count": 0,
            "target_url_request_count": 0,
            "migration_event_counts": {},
            "migration_event_class_counts": {},
            "network_event_counts": {},
        }
    request_reached_server = server.get("ok") is True and len(requests) >= args.expected_requests
    dump_timing = dump_task_timing(dump, args.workload)

    summary: dict[str, object] = {
        "status": "PASS",
        "artifact_dir": str(base),
        "workload": args.workload,
        "expected_requests": args.expected_requests,
        "chrome_exit": args.chrome_exit,
        "chrome_completed_cleanly": args.chrome_exit == 0,
        "chrome_timed_out_after_request": args.chrome_exit == 124 and request_reached_server,
        "server_exit": args.server_exit,
        "server_ok": server.get("ok"),
        "server_error": server.get("error") or server_error,
        "server_request_count": len(requests),
        "server_remote_addr": requests[0].get("remote_addr") if requests else None,
        "server_remote_addrs": remote_addrs,
        "server_remote_addr_count": len(remote_addrs),
        "server_request_labels": labels,
        "server_request_paths": paths,
        "request_reached_server": request_reached_server,
        "network_change_exit": network_change.get("exit"),
        "network_change_error": network_change_error,
        "client_path_change": client_path_change or None,
        "client_path_change_error": client_path_change_error,
        "rebinding_proxy": summarize_rebinding_proxy(rebinding_proxy, rebinding_proxy_error),
        "netlog_parse_error": netlog_error,
        "netlog_parser_mode": netlog_summary["parser_mode"],
        "netlog_has_forced_origin": "origin-to-force-quic" in netlog_text or args.addr in netlog_text,
        "netlog_has_quic_session": int(netlog_summary["target_quic_session_count"]) > 0,
        "netlog_target_quic_session_count": netlog_summary["target_quic_session_count"],
        "netlog_target_quic_source_ids": netlog_summary["target_quic_source_ids"],
        "netlog_target_using_quic_job_count": netlog_summary["target_using_quic_job_count"],
        "netlog_target_http_stream_job_count": netlog_summary["target_http_stream_job_count"],
        "netlog_target_non_quic_job_count": netlog_summary["target_non_quic_job_count"],
        "netlog_target_url_request_count": netlog_summary["target_url_request_count"],
        "netlog_migration_event_counts": netlog_summary["migration_event_counts"],
        "netlog_migration_event_class_counts": netlog_summary["migration_event_class_counts"],
        "netlog_network_event_counts": netlog_summary["network_event_counts"],
        "qlog_counts": {key: qcounts[key] for key in QLOG_PATTERNS},
        "qlog_has_h3": qcounts["http3_frame"] > 0,
        "qlog_has_path_probe": qcounts["path_challenge"] > 0 or qcounts["path_response"] > 0,
        "qlog_has_path_validation": qcounts["path_challenge"] > 0 and qcounts["path_response"] > 0,
        "dump_dom_bytes": len(dump),
        "dump_has_chrome_error": "ERR_" in dump,
        "dump_application_complete": dump_application_complete(dump, args.workload),
        "dump_task_elapsed_ms": dump_timing["elapsed_ms"],
        "dump_task_error_elapsed_ms": dump_timing["error_elapsed_ms"],
    }
    summary["classification"] = classify(summary)

    if (
        not request_reached_server
        or not summary["netlog_has_quic_session"]
        or not summary["qlog_has_h3"]
        or summary["classification"] == "browser_application_task_failed"
    ):
        summary["status"] = "FAIL"

    text = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
