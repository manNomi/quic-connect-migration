#!/usr/bin/env python3
"""Regression tests for final research unblock dashboard row synthesis."""

from __future__ import annotations

from build_final_research_unblock_dashboard import action_rows


def base_recovery() -> dict:
    return {
        "origin_access": {
            "aws": {"identity_ok": False, "classification": "invalid_client_token"},
            "tcp": {"classification": "connection_refused"},
            "recovery_paths": {
                "remote_ssh_ready": False,
                "local_tls_material_ready": False,
            },
        },
        "public_origin": {"ok": False, "classification": "not_ready", "has_h3_alt_svc": False},
        "baseline": {"ready": True, "status": "PASS"},
        "final_protocol": {"complete_count": 3, "requirement_count": 6},
        "next_step": {
            "step_id": "aws-credentials",
            "next_command": "import creds",
        },
    }


def base_readiness() -> dict:
    return {
        "next_trial": {"trial_id": "controlled-public-chrome-downlink-noheartbeat-network-change-001"},
        "ready": False,
        "missing_required_gates": ["desktop_path_change_ready", "public_origin_live_ready"],
        "gates": {
            "desktop_path_change_ready": False,
            "safari_webdriver_ready": True,
            "android_adb_ready": False,
        },
        "handover": {
            "desktop_path_change_mode": "not-ready",
            "secondary_path_ready": False,
        },
        "iphone_usb": {
            "classification": "iphone_usb_service_configured_hardware_absent",
            "next_actions": ["Reconnect the USB-C cable and unlock the iPhone."],
        },
    }


def by_gate(rows: list[dict[str, str]], gate_id: str) -> dict[str, str]:
    for row in rows:
        if row["gate_id"] == gate_id:
            return row
    raise AssertionError(f"missing row {gate_id}")


def test_current_blockers_are_p0_and_actionable() -> None:
    rows = action_rows(base_recovery(), base_readiness())
    assert by_gate(rows, "aws_identity_or_manual_origin_access")["status"] == "blocked"
    assert by_gate(rows, "public_origin_live_h3")["status"] == "blocked"
    path = by_gate(rows, "desktop_path_change_ready")
    assert path["status"] == "blocked"
    assert "Reconnect the USB-C cable" in path["next_action"]
    assert by_gate(rows, "next_chrome_active_row")["status"] == "waiting"


def test_ready_origin_and_path_unlock_next_chrome_row() -> None:
    recovery = base_recovery()
    recovery["origin_access"]["aws"]["identity_ok"] = True
    recovery["origin_access"]["aws"]["classification"] = "ok"
    recovery["origin_access"]["tcp"]["classification"] = "ok"
    recovery["public_origin"] = {"ok": True, "classification": "ok", "has_h3_alt_svc": True}

    readiness = base_readiness()
    readiness["ready"] = True
    readiness["missing_required_gates"] = []
    readiness["gates"]["desktop_path_change_ready"] = True
    readiness["handover"]["desktop_path_change_mode"] = "latent-iphone-usb-failover"
    readiness["iphone_usb"]["classification"] = "latent_iphone_usb_failover_observed"

    rows = action_rows(recovery, readiness)
    assert by_gate(rows, "aws_identity_or_manual_origin_access")["status"] == "ready"
    assert by_gate(rows, "public_origin_live_h3")["status"] == "ready"
    assert by_gate(rows, "desktop_path_change_ready")["status"] == "ready"
    assert by_gate(rows, "fresh_public_h3_baseline")["status"] == "ready"
    assert by_gate(rows, "next_chrome_active_row")["status"] == "ready"


def main() -> int:
    test_current_blockers_are_p0_and_actionable()
    test_ready_origin_and_path_unlock_next_chrome_row()
    print("build_final_research_unblock_dashboard=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
