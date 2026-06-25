#!/usr/bin/env python3
"""Check readiness of a controlled public HTTPS origin for Chrome H3 tests."""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from research_clock import utc_date_iso
from urllib.parse import urlparse


@dataclass
class PublicOriginReadiness:
    check_date: str
    url: str
    host: str
    port: int
    dns_addresses: list[str]
    tcp_tls_ok: bool
    python_tls_ok: bool
    curl_https_ok: bool
    tls_version: str
    tls_cipher: str
    tls_subject: str
    tls_issuer: str
    curl_exit: int
    final_status: str
    has_h3_alt_svc: bool
    alt_svc_headers: str
    errors: list[str]

    @property
    def ok(self) -> bool:
        return bool(self.dns_addresses) and self.tcp_tls_ok and self.curl_exit == 0


def endpoint(raw_url: str) -> tuple[str, int]:
    parsed = urlparse(raw_url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError(f"expected https URL with hostname: {raw_url}")
    return parsed.hostname, parsed.port or 443


def dns_addresses(host: str, port: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    addresses: set[str] = set()
    try:
        for family, _, _, _, sockaddr in socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP):
            if family in (socket.AF_INET, socket.AF_INET6):
                addresses.add(sockaddr[0])
    except OSError as exc:
        errors.append(f"dns: {exc}")
    return sorted(addresses), errors


def first_rdn_name(value: tuple[tuple[tuple[str, str], ...], ...]) -> str:
    pairs: list[str] = []
    for rdn in value:
        for key, item in rdn:
            pairs.append(f"{key}={item}")
    return ", ".join(pairs)


def tls_probe(host: str, port: int, timeout: int) -> tuple[bool, str, str, str, str, list[str]]:
    errors: list[str] = []
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as tls_sock:
                cert = tls_sock.getpeercert()
                cipher = tls_sock.cipher()
                return (
                    True,
                    tls_sock.version() or "",
                    cipher[0] if cipher else "",
                    first_rdn_name(cert.get("subject", ())),
                    first_rdn_name(cert.get("issuer", ())),
                    errors,
                )
    except (OSError, ssl.SSLError) as exc:
        errors.append(f"tls: {exc}")
        return False, "", "", "", "", errors


def curl_headers(url: str, timeout: int) -> tuple[int, str, str, str, list[str]]:
    errors: list[str] = []
    proc = subprocess.run(
        ["curl", "-sSIL", "--max-time", str(timeout), url],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.stderr.strip():
        errors.append(f"curl: {proc.stderr.strip()}")
    statuses: list[str] = []
    alt_svc: list[str] = []
    for raw in proc.stdout.splitlines():
        line = raw.strip()
        lower = line.lower()
        if lower.startswith("http/"):
            statuses.append(line)
        elif lower.startswith("alt-svc:"):
            alt_svc.append(line.split(":", 1)[1].strip())
    alt_joined = " | ".join(alt_svc)
    return proc.returncode, statuses[-1] if statuses else "", alt_joined, proc.stdout, errors


def build_result(url: str, timeout: int) -> PublicOriginReadiness:
    host, port = endpoint(url)
    errors: list[str] = []
    addrs, dns_errors = dns_addresses(host, port)
    errors.extend(dns_errors)
    tls_ok, tls_version, tls_cipher, tls_subject, tls_issuer, tls_errors = tls_probe(host, port, timeout)
    errors.extend(tls_errors)
    curl_exit, final_status, alt_svc_headers, _, curl_errors = curl_headers(url, timeout)
    errors.extend(curl_errors)
    curl_https_ok = curl_exit == 0 and final_status.startswith("HTTP/")
    tcp_tls_ok = tls_ok or curl_https_ok
    return PublicOriginReadiness(
        check_date=utc_date_iso(),
        url=url,
        host=host,
        port=port,
        dns_addresses=addrs,
        tcp_tls_ok=tcp_tls_ok,
        python_tls_ok=tls_ok,
        curl_https_ok=curl_https_ok,
        tls_version=tls_version if tls_ok else ("curl-verified" if curl_https_ok else ""),
        tls_cipher=tls_cipher,
        tls_subject=tls_subject,
        tls_issuer=tls_issuer,
        curl_exit=curl_exit,
        final_status=final_status,
        has_h3_alt_svc="h3" in alt_svc_headers.lower(),
        alt_svc_headers=alt_svc_headers,
        errors=errors,
    )


def redact_value(value: str, result: PublicOriginReadiness) -> str:
    redacted = value
    for token, replacement in [
        (result.url, "<redacted-url>"),
        (result.host, "<redacted-host>"),
        (result.tls_subject, "<redacted-tls-subject>"),
        (result.tls_issuer, "<redacted-tls-issuer>"),
    ]:
        if token:
            redacted = redacted.replace(token, replacement)
    for address in result.dns_addresses:
        if address:
            redacted = redacted.replace(address, "<redacted-address>")
    return redacted


def redacted_dns_summary(result: PublicOriginReadiness) -> str:
    if not result.dns_addresses:
        return "-"
    count = len(result.dns_addresses)
    return f"<redacted:{count} address{'es' if count != 1 else ''}>"


def payload(result: PublicOriginReadiness, redact_sensitive: bool) -> dict[str, object]:
    data: dict[str, object] = asdict(result)
    data["ok"] = result.ok
    data["redacted"] = redact_sensitive
    if not redact_sensitive:
        return data
    data["url"] = "<redacted-url>"
    data["host"] = "<redacted-host>"
    data["dns_addresses"] = ["<redacted-address>"] if result.dns_addresses else []
    data["tls_subject"] = "<redacted-tls-subject>" if result.tls_subject else ""
    data["tls_issuer"] = "<redacted-tls-issuer>" if result.tls_issuer else ""
    data["alt_svc_headers"] = redact_value(result.alt_svc_headers, result)
    data["errors"] = [redact_value(error, result) for error in result.errors]
    return data


def emit_markdown(result: PublicOriginReadiness, redact_sensitive: bool = False) -> str:
    url = "<redacted-url>" if redact_sensitive else result.url
    dns = redacted_dns_summary(result) if redact_sensitive else ", ".join(result.dns_addresses) or "-"
    alt_svc = redact_value(result.alt_svc_headers, result) if redact_sensitive else result.alt_svc_headers
    errors = [redact_value(error, result) for error in result.errors] if redact_sensitive else result.errors
    return "\n".join(
        [
            "| check | value |",
            "| --- | --- |",
            f"| url | `{url}` |",
            f"| DNS addresses | `{dns}` |",
            f"| TCP/TLS OK | `{str(result.tcp_tls_ok).lower()}` |",
            f"| Python TLS OK | `{str(result.python_tls_ok).lower()}` |",
            f"| curl HTTPS OK | `{str(result.curl_https_ok).lower()}` |",
            f"| TLS version | `{result.tls_version or '-'}` |",
            f"| final status | `{result.final_status or '-'}` |",
            f"| h3 Alt-Svc | `{str(result.has_h3_alt_svc).lower()}` |",
            f"| Alt-Svc | `{alt_svc or '-'}` |",
            f"| errors | `{'; '.join(errors) or '-'}` |",
        ]
    ) + "\n"


def write_output(text: str, output_arg: str | None) -> None:
    if output_arg == "-":
        sys.stdout.write(text)
        return
    if not output_arg:
        sys.stdout.write(text)
        return
    output = Path(output_arg)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--require-h3-alt-svc", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--redact-sensitive", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        result = build_result(args.url, args.timeout)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.format == "markdown":
        text = emit_markdown(result, redact_sensitive=args.redact_sensitive)
    else:
        text = json.dumps(payload(result, args.redact_sensitive), indent=2, ensure_ascii=False) + "\n"
    write_output(text, args.output)

    if args.require_h3_alt_svc and not result.has_h3_alt_svc:
        return 1
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
