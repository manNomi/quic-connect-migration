#!/usr/bin/env python3
"""Classify Chrome public-origin natural HTTP/3 artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

import classify_chrome_h3_artifacts as chrome_h3


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except (json.JSONDecodeError, OSError):
        return {}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def endpoint_from_url(raw_url: str) -> tuple[str, int, str, set[str]]:
    parsed = urlparse(raw_url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError(f"expected https URL with hostname: {raw_url}")
    port = parsed.port or 443
    host = parsed.hostname
    origin_with_port = f"https://{host}:{port}"
    origins = {origin_with_port}
    if port == 443:
        origins.add(f"https://{host}")
    return host, port, origin_with_port, origins


def summarize_netlog(path: Path, raw_url: str) -> dict[str, object]:
    host, port, origin_with_port, origins = endpoint_from_url(raw_url)
    netlog = read_json(path)
    text = read_text(path)
    if not netlog:
        compact = text.replace(" ", "")
        return {
            "parser_mode": "text_fallback" if text else "missing",
            "target_quic_session_count": compact.count(f'"host":"{host}"'),
            "target_using_quic_job_count": compact.count('"using_quic":true'),
            "target_http_stream_job_count": sum(compact.count(f'"destination":"{origin}"') for origin in origins),
            "target_url_request_count": compact.count(f'"url":"https://{host}/'),
            "target_advertised_alternative_service": "alternative_service" in text and host in text,
            "target_broken_alternative_service": "broken_alternative_services" in text and host in text,
            "migration_event_counts": {},
            "path": str(path),
        }

    reverse_types = chrome_h3.reverse_netlog_event_types(netlog)
    quic_sessions = 0
    using_quic_jobs = 0
    http_stream_jobs = 0
    non_quic_jobs = 0
    url_requests = 0
    advertised_alt_service = False
    broken_alt_service = False
    migration_event_counts: dict[str, int] = {}

    for event in netlog.get("events", []):
        name = reverse_types.get(event.get("type"), str(event.get("type")))
        params = event.get("params") or {}
        upper_name = name.upper()
        if "MIGRAT" in upper_name:
            migration_event_counts[name] = migration_event_counts.get(name, 0) + 1

        if name == "QUIC_SESSION" and params.get("host") == host and str(params.get("port")) == str(port):
            quic_sessions += 1

        if name == "HTTP_STREAM_JOB":
            destination = params.get("destination")
            logical_destination = params.get("logical_destination")
            if destination in origins or logical_destination in origins:
                http_stream_jobs += 1
                if params.get("using_quic") is True:
                    using_quic_jobs += 1
                else:
                    non_quic_jobs += 1

        if name == "URL_REQUEST_START_JOB" and str(params.get("url", "")).startswith(f"https://{host}/"):
            url_requests += 1

        if name == "HTTP_SERVER_PROPERTIES_UPDATE_PREFS":
            for item in params.get("broken_alternative_services") or []:
                if item.get("host") == host and str(item.get("port")) == str(port) and item.get("protocol_str") == "quic":
                    broken_alt_service = True
            for server in params.get("servers") or []:
                if server.get("server") not in origins and server.get("server") != origin_with_port:
                    continue
                for alt in server.get("alternative_service") or []:
                    if alt.get("protocol_str") == "quic":
                        advertised_alt_service = True

    return {
        "parser_mode": "json",
        "target_host": host,
        "target_port": port,
        "target_origins": sorted(origins),
        "target_quic_session_count": quic_sessions,
        "target_using_quic_job_count": using_quic_jobs,
        "target_http_stream_job_count": http_stream_jobs,
        "target_non_quic_job_count": non_quic_jobs,
        "target_url_request_count": url_requests,
        "target_advertised_alternative_service": advertised_alt_service,
        "target_broken_alternative_service": broken_alt_service,
        "migration_event_counts": dict(sorted(migration_event_counts.items())),
        "path": str(path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_dir")
    parser.add_argument("--url", required=True)
    parser.add_argument("--bootstrap-exit", type=int, default=0)
    parser.add_argument("--second-exit", type=int, default=0)
    parser.add_argument("--output")
    args = parser.parse_args()

    base = Path(args.artifact_dir)
    bootstrap = summarize_netlog(base / "chrome" / "bootstrap-netlog.json", args.url)
    second = summarize_netlog(base / "chrome" / "second-netlog.json", args.url)

    bootstrap_h3_observed = (
        int(bootstrap.get("target_quic_session_count") or 0) > 0
        and int(bootstrap.get("target_using_quic_job_count") or 0) > 0
    )
    second_h3_observed = (
        int(second.get("target_quic_session_count") or 0) > 0
        and int(second.get("target_using_quic_job_count") or 0) > 0
    )
    any_h3_observed = bootstrap_h3_observed or second_h3_observed
    any_alt_advertised = bool(bootstrap.get("target_advertised_alternative_service") or second.get("target_advertised_alternative_service"))
    any_broken = bool(bootstrap.get("target_broken_alternative_service") or second.get("target_broken_alternative_service"))
    any_target_request = int(bootstrap.get("target_url_request_count") or 0) + int(second.get("target_url_request_count") or 0) > 0

    if any_h3_observed:
        classification = "public_natural_h3_observed"
        status = "PASS"
    elif any_broken:
        classification = "public_alt_svc_marked_broken"
        status = "PASS_NEGATIVE_CONTROL"
    elif any_alt_advertised or any_target_request:
        classification = "public_alt_svc_or_request_observed_but_h3_not_confirmed"
        status = "PASS_NEGATIVE_CONTROL"
    else:
        classification = "public_h3_target_request_not_observed"
        status = "FAIL"

    summary = {
        "status": status,
        "classification": classification,
        "artifact_dir": str(base),
        "url": args.url,
        "bootstrap_exit": args.bootstrap_exit,
        "second_exit": args.second_exit,
        "bootstrap_netlog": bootstrap,
        "second_netlog": second,
        "bootstrap_h3_observed": bootstrap_h3_observed,
        "second_h3_observed": second_h3_observed,
        "any_h3_observed": any_h3_observed,
        "any_target_request": any_target_request,
    }

    text = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if status.startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
