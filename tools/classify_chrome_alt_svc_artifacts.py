#!/usr/bin/env python3
"""Classify Chrome natural HTTP/3 Alt-Svc bootstrap artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

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


def summarize_netlog(path: Path, addr: str) -> dict[str, object]:
    text = read_text(path)
    parsed = read_json(path)
    if parsed:
        summary = chrome_h3.parse_netlog(parsed, addr)
        target_host, target_port = addr.rsplit(":", 1)
        reverse_types = chrome_h3.reverse_netlog_event_types(parsed)
        broken_alt_service = False
        advertised_alt_service = False
        for event in parsed.get("events", []):
            name = reverse_types.get(event.get("type"), str(event.get("type")))
            if name != "HTTP_SERVER_PROPERTIES_UPDATE_PREFS":
                continue
            params = event.get("params") or {}
            for item in params.get("broken_alternative_services") or []:
                if (
                    item.get("host") == target_host
                    and str(item.get("port")) == target_port
                    and item.get("protocol_str") == "quic"
                ):
                    broken_alt_service = True
            for server in params.get("servers") or []:
                if server.get("server") != f"https://{addr}":
                    continue
                for alt in server.get("alternative_service") or []:
                    if alt.get("protocol_str") == "quic":
                        advertised_alt_service = True
        summary["target_broken_alternative_service"] = broken_alt_service
        summary["target_advertised_alternative_service"] = advertised_alt_service
    elif text:
        summary = chrome_h3.parse_netlog_text_fallback(text, addr)
        summary["target_broken_alternative_service"] = "broken_alternative_services" in text and addr in text
        summary["target_advertised_alternative_service"] = "alternative_service" in text and addr in text
    else:
        summary = {
            "parser_mode": "missing",
            "target_quic_session_count": 0,
            "target_using_quic_job_count": 0,
            "target_http_stream_job_count": 0,
            "target_non_quic_job_count": 0,
            "target_url_request_count": 0,
            "migration_event_counts": {},
            "network_event_counts": {},
            "target_broken_alternative_service": False,
            "target_advertised_alternative_service": False,
        }
    summary["path"] = str(path)
    return summary


def summarize_qlog(qlog_dir: Path) -> dict[str, object]:
    text_parts: list[str] = []
    connection_close_reasons: list[str] = []
    if qlog_dir.exists():
        for path in qlog_dir.rglob("*"):
            if path.is_file() and path.suffix in {".sqlog", ".qlog", ".json", ".jsonl", ".txt"}:
                file_text = read_text(path)
                text_parts.append(file_text)
                for record in file_text.split("\x1e"):
                    record = record.strip()
                    if not record:
                        continue
                    try:
                        event = json.loads(record)
                    except json.JSONDecodeError:
                        continue
                    data = event.get("data") or {}
                    if event.get("name") == "transport:connection_closed" and data.get("reason"):
                        connection_close_reasons.append(str(data["reason"]))
                    for frame in data.get("frames") or []:
                        if frame.get("frame_type") == "connection_close" and frame.get("reason"):
                            connection_close_reasons.append(str(frame["reason"]))
    text = "\n".join(text_parts)
    lower = text.lower()
    has_certificate_error = "certificate_unknown" in lower or "certificate unknown" in lower
    has_certificate_verify_failed = "certificate_verify_failed" in lower
    has_crypto_error = "crypto_error" in lower or "crypto error" in lower
    return {
        "has_certificate_error": has_certificate_error,
        "has_certificate_verify_failed": has_certificate_verify_failed,
        "has_crypto_error": has_crypto_error,
        "connection_close_reasons": connection_close_reasons[:10],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_dir")
    parser.add_argument("--addr", required=True)
    parser.add_argument("--expected-requests", type=int, default=2)
    parser.add_argument("--bootstrap-exit", type=int, default=0)
    parser.add_argument("--h3-exit", type=int, default=0)
    parser.add_argument("--server-exit", type=int, default=0)
    parser.add_argument("--output")
    args = parser.parse_args()

    base = Path(args.artifact_dir)
    server = read_json(base / "results" / "server.json")
    requests = server.get("requests") or []
    protos = [request.get("proto") for request in requests]
    alpns = [request.get("tls_alpn") for request in requests]
    remote_addrs = sorted({request.get("remote_addr") for request in requests if request.get("remote_addr")})
    paths = [request.get("path") for request in requests]
    labels = [request.get("label") for request in requests]
    qcounts = chrome_h3.qlog_counts(base / "qlog")
    bootstrap_netlog = summarize_netlog(base / "chrome" / "bootstrap-netlog.json", args.addr)
    h3_netlog = summarize_netlog(base / "chrome" / "h3-netlog.json", args.addr)
    qlog_summary = summarize_qlog(base / "qlog")

    has_tcp_bootstrap = any(str(proto).startswith("HTTP/1.") or str(proto).startswith("HTTP/2") for proto in protos)
    has_h3_request = any(str(proto).startswith("HTTP/3") for proto in protos)
    h3_netlog_has_quic_candidate = int(h3_netlog.get("target_using_quic_job_count") or 0) > 0
    h3_netlog_has_quic_session_hint = int(h3_netlog.get("target_quic_session_count") or 0) > 0
    h3_netlog_has_confirmed_quic_session = (
        h3_netlog.get("parser_mode") == "json" and h3_netlog_has_quic_session_hint
    )
    h3_confirmed_by_netlog = h3_netlog_has_quic_candidate and h3_netlog_has_confirmed_quic_session
    qlog_has_h3 = qcounts["http3_frame"] > 0
    request_reached_server = server.get("ok") is True and len(requests) >= args.expected_requests

    qlog_has_certificate_error = bool(qlog_summary["has_certificate_error"])
    h3_netlog_has_broken_alt_service = bool(h3_netlog.get("target_broken_alternative_service"))

    if request_reached_server and has_tcp_bootstrap and has_h3_request and h3_confirmed_by_netlog and qlog_has_h3:
        classification = "alt_svc_h3_upgrade_observed"
        status = "PASS"
    elif request_reached_server and has_tcp_bootstrap and not has_h3_request and qlog_has_certificate_error:
        classification = "alt_svc_quic_candidate_cert_rejected"
        status = "PASS_NEGATIVE_CONTROL"
    elif request_reached_server and has_tcp_bootstrap and not has_h3_request and h3_netlog_has_broken_alt_service:
        classification = "alt_svc_marked_broken_without_h3_request"
        status = "PASS_NEGATIVE_CONTROL"
    elif request_reached_server and has_tcp_bootstrap and not has_h3_request and qlog_has_h3:
        classification = "alt_svc_quic_candidate_without_h3_request"
        status = "PASS_NEGATIVE_CONTROL"
    elif request_reached_server and has_tcp_bootstrap and not has_h3_request:
        classification = "alt_svc_advertised_but_h3_not_observed"
        status = "PASS_NEGATIVE_CONTROL"
    elif request_reached_server:
        classification = "browser_requests_observed_but_protocol_mix_inconclusive"
        status = "PASS_NEGATIVE_CONTROL"
    else:
        classification = "browser_alt_svc_request_failed"
        status = "FAIL"

    summary: dict[str, object] = {
        "status": status,
        "classification": classification,
        "artifact_dir": str(base),
        "expected_requests": args.expected_requests,
        "bootstrap_exit": args.bootstrap_exit,
        "h3_exit": args.h3_exit,
        "server_exit": args.server_exit,
        "server_ok": server.get("ok"),
        "server_error": server.get("error"),
        "server_request_count": len(requests),
        "server_request_paths": paths,
        "server_request_labels": labels,
        "server_request_protos": protos,
        "server_request_tls_alpns": alpns,
        "server_remote_addrs": remote_addrs,
        "has_tcp_bootstrap": has_tcp_bootstrap,
        "has_h3_request": has_h3_request,
        "h3_netlog_has_quic_candidate": h3_netlog_has_quic_candidate,
        "h3_netlog_has_quic_session_hint": h3_netlog_has_quic_session_hint,
        "h3_netlog_has_confirmed_quic_session": h3_netlog_has_confirmed_quic_session,
        "h3_confirmed_by_netlog": h3_confirmed_by_netlog,
        "bootstrap_netlog": bootstrap_netlog,
        "h3_netlog": h3_netlog,
        "qlog_counts": {key: qcounts[key] for key in chrome_h3.QLOG_PATTERNS},
        "qlog_has_h3": qlog_has_h3,
        "qlog_summary": qlog_summary,
    }

    text = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if status.startswith("PASS") else 1


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
