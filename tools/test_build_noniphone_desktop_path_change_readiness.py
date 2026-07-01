#!/usr/bin/env python3
"""Regression tests for non-iPhone desktop path-change readiness packets."""

from __future__ import annotations

from build_noniphone_desktop_path_change_readiness import build_packet, emit_markdown


def base_plan() -> dict:
    return {
        "generated": "2026-07-01",
        "commands_included": False,
        "read_only": True,
        "summary": {
            "active_ipv4_interfaces": ["en0"],
            "default_interface": "en0",
            "secondary_path_ready": False,
            "ready_candidates": ["macos_wifi_to_iphone_usb_latent_failover"],
        },
        "detected": {
            "hardware_ports": [
                {"hardware_port": "Wi-Fi", "device": "en0"},
                {"hardware_port": "iPhone USB", "device": "en8"},
            ],
            "network_services": [
                {"name": "Wi-Fi", "hardware_port": "Wi-Fi", "device": "en0", "disabled": False},
                {"name": "iPhone USB", "hardware_port": "iPhone USB", "device": "en8", "disabled": False},
            ],
            "active_ipv4_interfaces": [
                {"name": "en0", "active": True, "usable_ipv4_count": 1, "non_loopback_ipv4_count": 1}
            ],
        },
        "candidates": [
            {
                "id": "macos_wifi_power_cutover",
                "label": "Turn Wi-Fi off after secondary path is active",
                "ready": False,
                "reason": "blocked: no active secondary non-loopback IPv4 path was detected",
                "command_template": "networksetup -setairportpower <wifi-device> off",
                "restore_template": "networksetup -setairportpower <wifi-device> on",
                "detected": {"wifi_device": "en0"},
                "requires_operator_approval": True,
            },
            {
                "id": "macos_wifi_to_iphone_usb_latent_failover",
                "label": "Turn Wi-Fi off and measure delayed iPhone USB activation",
                "ready": True,
                "reason": "ready: Wi-Fi is active and iPhone USB is present but latent/inactive",
                "command_template": "networksetup -setairportpower <wifi-device> off",
                "restore_template": "networksetup -setairportpower <wifi-device> on",
                "detected": {"wifi_device": "en0", "iphone_service": "iPhone USB", "iphone_device": "en8"},
                "requires_operator_approval": True,
            },
            {
                "id": "android_wifi_to_cellular_cutover",
                "label": "Disable Android Wi-Fi and rely on cellular",
                "ready": True,
                "reason": "ready: ADB device is connected",
                "command_template": "adb shell svc wifi disable",
                "restore_template": "adb shell svc wifi enable",
                "detected": {"adb_device_count": "1"},
                "requires_operator_approval": True,
            },
        ],
    }


def test_iphone_and_android_candidates_do_not_open_desktop_gate() -> None:
    packet = build_packet(base_plan())
    assert packet["noniphone_desktop_path_ready"] is False
    assert packet["ready_candidates"] == []
    assert "macos_wifi_to_iphone_usb_latent_failover" in packet["excluded_candidate_ids"]
    assert "android_wifi_to_cellular_cutover" in packet["excluded_candidate_ids"]
    assert "no active non-iPhone secondary desktop interface" in " ".join(packet["blockers"])
    markdown = emit_markdown(packet)
    assert "excludes iPhone-based latent failover candidates" in markdown
    assert "iPhone-based or non-desktop" in markdown


def test_active_noniphone_secondary_opens_desktop_gate() -> None:
    plan = base_plan()
    plan["summary"]["active_ipv4_interfaces"] = ["en0", "en7"]
    plan["summary"]["secondary_path_ready"] = True
    plan["detected"]["hardware_ports"].append({"hardware_port": "USB 10/100 LAN", "device": "en7"})
    plan["detected"]["network_services"].append(
        {"name": "USB 10/100 LAN", "hardware_port": "USB 10/100 LAN", "device": "en7", "disabled": False}
    )
    plan["detected"]["active_ipv4_interfaces"].append(
        {"name": "en7", "active": True, "usable_ipv4_count": 1, "non_loopback_ipv4_count": 1}
    )
    plan["candidates"][0]["ready"] = True
    plan["candidates"][0]["reason"] = "ready: Wi-Fi is active and at least one secondary active IPv4 path exists"
    packet = build_packet(plan)
    assert packet["noniphone_desktop_path_ready"] is True
    assert packet["noniphone_secondary_interfaces"] == ["en7"]
    assert packet["ready_candidates"] == ["macos_wifi_power_cutover"]
    assert packet["blockers"] == []


def main() -> int:
    test_iphone_and_android_candidates_do_not_open_desktop_gate()
    test_active_noniphone_secondary_opens_desktop_gate()
    print("build_noniphone_desktop_path_change_readiness=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
