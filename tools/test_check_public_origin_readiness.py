#!/usr/bin/env python3
"""Regression tests for public origin readiness checks without network access."""

from __future__ import annotations

import types

import check_public_origin_readiness as readiness


def test_endpoint_requires_https_and_parses_default_port() -> None:
    assert readiness.endpoint("https://h3.test.local/browser-slow") == ("h3.test.local", 443)
    assert readiness.endpoint("https://h3.test.local:8443/browser-slow") == ("h3.test.local", 8443)
    try:
        readiness.endpoint("http://h3.test.local/browser-slow")
    except ValueError as exc:
        assert "expected https URL" in str(exc)
    else:
        raise AssertionError("http URL should be rejected")


def test_curl_headers_keeps_final_status_and_alt_svc() -> None:
    original_run = readiness.subprocess.run

    def fake_run(*_args: object, **_kwargs: object) -> types.SimpleNamespace:
        return types.SimpleNamespace(
            returncode=0,
            stdout=(
                "HTTP/1.1 301 Moved Permanently\r\n"
                "Alt-Svc: h3=\":443\"; ma=60\r\n"
                "\r\n"
                "HTTP/2 200\r\n"
                "Content-Type: text/html\r\n"
            ),
            stderr="",
        )

    readiness.subprocess.run = fake_run  # type: ignore[assignment]
    try:
        exit_code, final_status, alt_svc, _raw, errors = readiness.curl_headers("https://h3.test.local/", 3)
    finally:
        readiness.subprocess.run = original_run  # type: ignore[assignment]

    assert exit_code == 0
    assert final_status == "HTTP/2 200"
    assert alt_svc == 'h3=":443"; ma=60'
    assert errors == []


def test_build_result_combines_dns_tls_curl_without_live_network() -> None:
    original_dns = readiness.dns_addresses
    original_tls = readiness.tls_probe
    original_curl = readiness.curl_headers

    def fake_dns(host: str, port: int) -> tuple[list[str], list[str]]:
        assert (host, port) == ("h3.test.local", 443)
        return ["203.0.113.10"], []

    def fake_tls(host: str, port: int, timeout: int) -> tuple[bool, str, str, str, str, list[str]]:
        assert (host, port, timeout) == ("h3.test.local", 443, 5)
        return True, "TLSv1.3", "TLS_AES_128_GCM_SHA256", "commonName=h3.test.local", "commonName=Test CA", []

    def fake_curl(url: str, timeout: int) -> tuple[int, str, str, str, list[str]]:
        assert (url, timeout) == ("https://h3.test.local/browser-slow", 5)
        return 0, "HTTP/2 200", 'h3=":443"; ma=60', "", []

    readiness.dns_addresses = fake_dns  # type: ignore[assignment]
    readiness.tls_probe = fake_tls  # type: ignore[assignment]
    readiness.curl_headers = fake_curl  # type: ignore[assignment]
    try:
        result = readiness.build_result("https://h3.test.local/browser-slow", 5)
    finally:
        readiness.dns_addresses = original_dns  # type: ignore[assignment]
        readiness.tls_probe = original_tls  # type: ignore[assignment]
        readiness.curl_headers = original_curl  # type: ignore[assignment]

    assert result.ok is True
    assert result.dns_addresses == ["203.0.113.10"]
    assert result.tcp_tls_ok is True
    assert result.python_tls_ok is True
    assert result.curl_https_ok is True
    assert result.has_h3_alt_svc is True
    assert result.errors == []
    markdown = readiness.emit_markdown(result)
    assert "| h3 Alt-Svc | `true` |" in markdown


def test_build_result_records_failed_origin_without_throwing() -> None:
    original_dns = readiness.dns_addresses
    original_tls = readiness.tls_probe
    original_curl = readiness.curl_headers

    readiness.dns_addresses = lambda _host, _port: ([], ["dns: not found"])  # type: ignore[assignment]
    readiness.tls_probe = lambda _host, _port, _timeout: (False, "", "", "", "", ["tls: failed"])  # type: ignore[assignment]
    readiness.curl_headers = lambda _url, _timeout: (7, "", "", "", ["curl: failed"])  # type: ignore[assignment]
    try:
        result = readiness.build_result("https://missing.test.local/browser-slow", 2)
    finally:
        readiness.dns_addresses = original_dns  # type: ignore[assignment]
        readiness.tls_probe = original_tls  # type: ignore[assignment]
        readiness.curl_headers = original_curl  # type: ignore[assignment]

    assert result.ok is False
    assert result.has_h3_alt_svc is False
    assert result.errors == ["dns: not found", "tls: failed", "curl: failed"]


def main() -> int:
    test_endpoint_requires_https_and_parses_default_port()
    test_curl_headers_keeps_final_status_and_alt_svc()
    test_build_result_combines_dns_tls_curl_without_live_network()
    test_build_result_records_failed_origin_without_throwing()
    print("check_public_origin_readiness=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
