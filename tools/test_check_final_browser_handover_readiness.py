#!/usr/bin/env python3
"""Regression tests for final browser handover readiness helpers."""

from __future__ import annotations

import json

from check_final_browser_handover_readiness import emit_markdown, redact_payload, desktop_path_change_status


def test_active_secondary_path_wins_over_latent_mode() -> None:
    status = desktop_path_change_status(
        secondary_path_ready=True,
        allow_latent_secondary_path=True,
        latent_iphone_usb_candidate_ready=True,
    )
    assert status["ready"] is True
    assert status["mode"] == "active-secondary-path"


def test_latent_mode_requires_explicit_allow_flag() -> None:
    status = desktop_path_change_status(
        secondary_path_ready=False,
        allow_latent_secondary_path=False,
        latent_iphone_usb_candidate_ready=True,
    )
    assert status["ready"] is False
    assert status["mode"] == "not-ready"


def test_latent_mode_can_satisfy_desktop_path_change_gate() -> None:
    status = desktop_path_change_status(
        secondary_path_ready=False,
        allow_latent_secondary_path=True,
        latent_iphone_usb_candidate_ready=True,
    )
    assert status["ready"] is True
    assert status["mode"] == "latent-iphone-usb-failover"
    assert "delayed OS failover" in status["claim_boundary"]


def test_redacted_payload_and_markdown_hide_private_origin_and_local_ip() -> None:
    readiness = {
        "check_date": "2026-06-29",
        "protocol_ready": {"chrome": False, "safari": False, "android_chrome": False},
        "final_trials": {"complete_count": 0, "requirement_count": 1, "blockers": []},
        "can_finish_goal_now": False,
        "config": {
            "exists": True,
            "public_origin_url_preview": "<configured>",
            "network_change_command_present": True,
            "android_network_change_command_present": False,
        },
        "baseline": {"ready": True, "status": "PASS", "error": ""},
        "handover": {
            "active_ipv4_interfaces": [{"name": "en0", "active": True, "ipv4": ["192.168.32.190"]}],
            "secondary_path_ready": False,
            "latent_iphone_usb_candidate_ready": True,
            "allow_latent_secondary_path": True,
            "desktop_path_change_ready": True,
            "desktop_path_change_mode": "latent-iphone-usb-failover",
            "android_ready": False,
        },
        "observability": {"safari_webdriver_ready": True},
        "disk": {"ready": True, "free_gib": 35},
        "public_origin": {
            "url": "https://private-origin.example.test/browser",
            "host": "private-origin.example.test",
            "dns_addresses": ["203.0.113.1"],
            "tls_subject": "CN=private-origin.example.test",
            "tls_issuer": "CN=issuer",
            "alt_svc_headers": 'h3=":443"; ma=60',
            "errors": ["private-origin.example.test failed"],
        },
        "blockers": [],
    }
    redacted = redact_payload(readiness)
    encoded = json.dumps(redacted, ensure_ascii=False)
    markdown = emit_markdown(redacted, redact_sensitive=True)
    for private in ["192.168.32.190", "private-origin.example.test", "203.0.113.1"]:
        assert private not in encoded
        assert private not in markdown
    assert "en0(<redacted:1 address>)" in markdown


def main() -> int:
    test_active_secondary_path_wins_over_latent_mode()
    test_latent_mode_requires_explicit_allow_flag()
    test_latent_mode_can_satisfy_desktop_path_change_gate()
    test_redacted_payload_and_markdown_hide_private_origin_and_local_ip()
    print("check_final_browser_handover_readiness=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
