#!/usr/bin/env python3
"""Regression tests for active path-change command candidate suggestions."""

from __future__ import annotations

from suggest_active_path_change_commands import build_plan


HARDWARE_PORTS = """
Hardware Port: Wi-Fi
Device: en0
Ethernet Address: aa:bb:cc:dd:ee:ff

Hardware Port: iPhone USB
Device: en8
Ethernet Address: 11:22:33:44:55:66
"""

SERVICE_ORDER = """
An asterisk (*) denotes that a network service is disabled.
(1) Wi-Fi
(Hardware Port: Wi-Fi, Device: en0)

(2) iPhone USB
(Hardware Port: iPhone USB, Device: en8)
"""

IFCONFIG_TWO_ACTIVE = """
en0: flags=8863<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> mtu 1500
    inet 192.168.1.10 netmask 0xffffff00 broadcast 192.168.1.255
    status: active
en8: flags=8863<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> mtu 1500
    inet 172.20.10.2 netmask 0xfffffff0 broadcast 172.20.10.15
    status: active
"""

IFCONFIG_ONE_ACTIVE = """
en0: flags=8863<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> mtu 1500
    inet 192.168.1.10 netmask 0xffffff00 broadcast 192.168.1.255
    status: active
en8: flags=8822<BROADCAST,SMART,SIMPLEX,MULTICAST> mtu 1500
    status: inactive
"""

IFCONFIG_LINK_LOCAL_SECONDARY = """
en0: flags=8863<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> mtu 1500
    inet 192.168.1.10 netmask 0xffffff00 broadcast 192.168.1.255
    status: active
en9: flags=8863<UP,BROADCAST,RUNNING,SIMPLEX,MULTICAST> mtu 1500
    inet 169.254.12.34 netmask 0xffff0000 broadcast 169.254.255.255
    status: active
"""

DEFAULT_ROUTE = """
   route to: default
destination: default
    gateway: 192.168.1.1
  interface: en0
"""

ADB_DEVICE = """
List of devices attached
device-serial	device
"""


def candidate_by_id(plan: dict, candidate_id: str) -> dict:
    for candidate in plan["candidates"]:
        if candidate["id"] == candidate_id:
            return candidate
    raise AssertionError(f"missing candidate {candidate_id}")


def test_secondary_path_enables_macos_candidates_without_printing_commands() -> None:
    plan = build_plan(
        hardware_ports_text=HARDWARE_PORTS,
        service_order_text=SERVICE_ORDER,
        ifconfig_text=IFCONFIG_TWO_ACTIVE,
        default_route_text=DEFAULT_ROUTE,
        adb_devices_text="List of devices attached\n",
        include_commands=False,
    )
    assert plan["summary"]["secondary_path_ready"] is True
    assert plan["summary"]["latent_iphone_usb_candidate_ready"] is False
    wifi = candidate_by_id(plan, "macos_wifi_power_cutover")
    order = candidate_by_id(plan, "macos_service_order_cutover")
    latent = candidate_by_id(plan, "macos_wifi_to_iphone_usb_latent_failover")
    assert wifi["ready"] is True
    assert order["ready"] is True
    assert latent["ready"] is False
    assert wifi["command"] == ""
    assert order["command"] == ""
    assert wifi["detected"]["wifi_device"] == "en0"
    assert order["detected"]["secondary_service"] == "iPhone USB"


def test_include_commands_requires_explicit_flag() -> None:
    plan = build_plan(
        hardware_ports_text=HARDWARE_PORTS,
        service_order_text=SERVICE_ORDER,
        ifconfig_text=IFCONFIG_TWO_ACTIVE,
        default_route_text=DEFAULT_ROUTE,
        adb_devices_text=ADB_DEVICE,
        include_commands=True,
    )
    wifi = candidate_by_id(plan, "macos_wifi_power_cutover")
    android = candidate_by_id(plan, "android_wifi_to_cellular_cutover")
    assert "en0" in wifi["command"]
    assert android["ready"] is True
    assert android["command"] == "adb shell svc wifi disable"


def test_single_active_interface_blocks_desktop_candidates() -> None:
    plan = build_plan(
        hardware_ports_text=HARDWARE_PORTS,
        service_order_text=SERVICE_ORDER,
        ifconfig_text=IFCONFIG_ONE_ACTIVE,
        default_route_text=DEFAULT_ROUTE,
        adb_devices_text="List of devices attached\n",
        include_commands=True,
    )
    assert plan["summary"]["secondary_path_ready"] is False
    assert plan["summary"]["latent_iphone_usb_candidate_ready"] is True
    assert candidate_by_id(plan, "macos_wifi_power_cutover")["ready"] is False
    assert candidate_by_id(plan, "macos_wifi_to_iphone_usb_latent_failover")["ready"] is True
    assert candidate_by_id(plan, "macos_service_order_cutover")["ready"] is False


def test_link_local_ipv4_does_not_count_as_secondary_path() -> None:
    plan = build_plan(
        hardware_ports_text=HARDWARE_PORTS,
        service_order_text=SERVICE_ORDER,
        ifconfig_text=IFCONFIG_LINK_LOCAL_SECONDARY,
        default_route_text=DEFAULT_ROUTE,
        adb_devices_text="List of devices attached\n",
        include_commands=True,
    )
    assert plan["summary"]["secondary_path_ready"] is False
    assert plan["summary"]["active_ipv4_interfaces"] == ["en0"]
    assert candidate_by_id(plan, "macos_wifi_power_cutover")["ready"] is False


def test_latent_iphone_usb_candidate_includes_command_only_when_requested() -> None:
    plan = build_plan(
        hardware_ports_text=HARDWARE_PORTS,
        service_order_text=SERVICE_ORDER,
        ifconfig_text=IFCONFIG_ONE_ACTIVE,
        default_route_text=DEFAULT_ROUTE,
        adb_devices_text="List of devices attached\n",
        include_commands=True,
    )
    latent = candidate_by_id(plan, "macos_wifi_to_iphone_usb_latent_failover")
    assert latent["ready"] is True
    assert latent["detected"]["iphone_service"] == "iPhone USB"
    assert latent["detected"]["iphone_device"] == "en8"
    assert latent["command"] == "networksetup -setairportpower 'en0' off"
    assert latent["restore_command"] == "networksetup -setairportpower 'en0' on"


def main() -> int:
    test_secondary_path_enables_macos_candidates_without_printing_commands()
    test_include_commands_requires_explicit_flag()
    test_single_active_interface_blocks_desktop_candidates()
    test_link_local_ipv4_does_not_count_as_secondary_path()
    test_latent_iphone_usb_candidate_includes_command_only_when_requested()
    print("suggest_active_path_change_commands=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
