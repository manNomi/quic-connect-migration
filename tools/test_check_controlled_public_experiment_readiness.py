#!/usr/bin/env python3
"""Regression tests for controlled public experiment readiness output."""

from __future__ import annotations

import json

from check_controlled_public_experiment_readiness import (
    ArtifactCheck,
    ControlledPublicExperimentReadiness,
    emit_markdown,
    payload,
)


def sample_readiness() -> ControlledPublicExperimentReadiness:
    return ControlledPublicExperimentReadiness(
        check_date="2026-06-25",
        public_origin_url="https://private-origin.example.test/browser-downlink?token=secret",
        controlled_public_origin_ready=True,
        application_h3_baseline_ready=True,
        network_change_harness_ready=True,
        desktop_handover_ready=True,
        allow_latent_secondary_path=False,
        latent_iphone_usb_candidate_ready=False,
        desktop_path_change_mode="active-secondary-path",
        can_run_application_h3_baseline=True,
        can_run_network_change=True,
        chrome_found=True,
        secondary_path_ready=True,
        active_ipv4_interfaces=[{"name": "en0", "ipv4": ["192.0.2.44"]}],
        network_change_command_present=True,
        network_change_command_preview="sudo networksetup -setairportpower Wi-Fi off",
        baseline_summary=ArtifactCheck(
            "/Users/researcher/private/artifacts/baseline-summary.json",
            True,
            "PASS",
            "controlled_public_application_h3_confirmed",
            "",
        ),
        server_artifact=ArtifactCheck(
            "/Users/researcher/private/artifacts/results/server.json",
            True,
            "PASS",
            "server_ok",
            "",
        ),
        public_origin={
            "check_date": "2026-06-25",
            "url": "https://private-origin.example.test/browser-downlink?token=secret",
            "host": "private-origin.example.test",
            "port": 443,
            "dns_addresses": ["203.0.113.99"],
            "tcp_tls_ok": True,
            "python_tls_ok": True,
            "curl_https_ok": True,
            "tls_version": "TLSv1.3",
            "tls_cipher": "TLS_AES_128_GCM_SHA256",
            "tls_subject": "commonName=private-origin.example.test",
            "tls_issuer": "commonName=Private Test CA",
            "curl_exit": 0,
            "final_status": "HTTP/2 200",
            "has_h3_alt_svc": True,
            "alt_svc_headers": 'h3=":443"; ma=60',
            "errors": ["curl: private-origin.example.test resolved to 203.0.113.99"],
            "ok": True,
            "redacted": False,
        },
        blockers=[
            "manual check touched https://private-origin.example.test/browser-downlink?token=secret",
            "do not print sudo networksetup -setairportpower Wi-Fi off",
        ],
    )


def assert_no_private_values(text: str) -> None:
    for private_value in [
        "private-origin.example.test",
        "token=secret",
        "203.0.113.99",
        "192.0.2.44",
        "sudo networksetup",
        "/Users/researcher/private",
    ]:
        assert private_value not in text


def test_redacted_json_does_not_leak_private_origin_or_commands() -> None:
    data = payload(sample_readiness(), redact_sensitive=True)
    encoded = json.dumps(data, ensure_ascii=False)
    assert_no_private_values(encoded)
    assert data["public_origin_url"] == "<configured>"
    assert data["network_change_command_preview"] == "<configured>"
    assert data["public_origin"]["url"] == "<redacted-url>"  # type: ignore[index]
    assert data["active_ipv4_interfaces"][0]["ipv4"] == ["<redacted-address>"]  # type: ignore[index]


def test_redacted_markdown_does_not_leak_private_origin_or_commands() -> None:
    markdown = emit_markdown(sample_readiness(), redact_sensitive=True)
    assert_no_private_values(markdown)
    assert "| public origin URL | `<configured>` |" in markdown
    assert "| NETWORK_CHANGE_CMD preview | `<configured>` |" in markdown
    assert "| desktop path-change mode | `active-secondary-path` |" in markdown
    assert "en0(<redacted:1 address>)" in markdown
    assert "| baseline summary | `PASS` |" in markdown


def main() -> int:
    test_redacted_json_does_not_leak_private_origin_or_commands()
    test_redacted_markdown_does_not_leak_private_origin_or_commands()
    print("check_controlled_public_experiment_readiness=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
