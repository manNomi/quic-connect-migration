#!/usr/bin/env python3
"""Regression tests for iPhone USB latent failover classification."""

from __future__ import annotations

from check_iphone_usb_latent_failover import (
    InterfaceState,
    StateSnapshot,
    classify,
    compact_state,
    parse_default_interface,
    parse_interface_state,
)


IFCONFIG_INACTIVE = """
en8: flags=8822<BROADCAST,SMART,SIMPLEX,MULTICAST> mtu 1500 constrained
    ether 66:48:42:22:ee:40
    media: autoselect <full-duplex>
    status: inactive
"""

IFCONFIG_ACTIVE = """
en8: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST> mtu 1500 constrained
    ether 66:48:42:22:ee:40
    inet 172.20.10.8 netmask 0xfffffff0 broadcast 172.20.10.15
    media: autoselect <full-duplex>
    status: active
"""

DEFAULT_EN0 = """
   route to: default
destination: default
    gateway: 192.168.32.1
  interface: en0
"""

DEFAULT_EN8 = """
   route to: default
destination: default
    gateway: 172.20.10.1
  interface: en8
"""


def state(ms: int, default_interface: str, iphone: InterfaceState) -> StateSnapshot:
    return StateSnapshot(
        captured_ms=ms,
        wifi_power="Wi-Fi Power (en0): On",
        default_interface=default_interface,
        iphone_usb=iphone,
    )


def test_parse_inactive_iphone_usb_interface() -> None:
    parsed = parse_interface_state("en8", IFCONFIG_INACTIVE)
    assert parsed.present is True
    assert parsed.active is False
    assert parsed.ipv4 == []


def test_parse_active_iphone_usb_interface() -> None:
    parsed = parse_interface_state("en8", IFCONFIG_ACTIVE)
    assert parsed.present is True
    assert parsed.active is True
    assert parsed.ipv4 == ["172.20.10.8"]
    assert compact_state(state(740, "en8", parsed))["iphone_usb"]["usable_ipv4"] == ["172.20.10.8"]


def test_parse_default_route_interface() -> None:
    assert parse_default_interface(DEFAULT_EN0) == "en0"
    assert parse_default_interface(DEFAULT_EN8) == "en8"


def test_unmeasured_inactive_iphone_usb_is_latent_candidate() -> None:
    inactive = parse_interface_state("en8", IFCONFIG_INACTIVE)
    before = state(0, "en0", inactive)
    assert classify(before, before, None, measured=False) == "iphone_usb_latent_candidate_unmeasured"


def test_measured_wifi_to_iphone_usb_transition_is_observed_failover() -> None:
    inactive = parse_interface_state("en8", IFCONFIG_INACTIVE)
    active = parse_interface_state("en8", IFCONFIG_ACTIVE)
    before = state(0, "en0", inactive)
    after = state(740, "en8", active)
    assert classify(before, after, 740, measured=True) == "latent_iphone_usb_failover_observed"


def main() -> int:
    test_parse_inactive_iphone_usb_interface()
    test_parse_active_iphone_usb_interface()
    test_parse_default_route_interface()
    test_unmeasured_inactive_iphone_usb_is_latent_candidate()
    test_measured_wifi_to_iphone_usb_transition_is_observed_failover()
    print("check_iphone_usb_latent_failover=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
