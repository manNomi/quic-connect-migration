#!/usr/bin/env python3
"""Regression tests for local IPv4 path evidence helpers."""

from __future__ import annotations

from network_ipv4 import has_usable_ipv4, is_usable_ipv4, usable_ipv4_addresses


def test_excludes_loopback_link_local_unspecified_multicast_and_invalid() -> None:
    for address in ["127.0.0.1", "169.254.12.34", "0.0.0.0", "224.0.0.1", "not-an-ip"]:
        assert is_usable_ipv4(address) is False


def test_accepts_private_and_shared_client_addresses() -> None:
    for address in ["192.168.1.10", "172.20.10.8", "10.0.0.5", "100.64.0.7", "8.8.8.8"]:
        assert is_usable_ipv4(address) is True


def test_filters_address_lists() -> None:
    assert usable_ipv4_addresses(["127.0.0.1", "169.254.1.2", "172.20.10.8"]) == ["172.20.10.8"]
    assert has_usable_ipv4(["169.254.1.2"]) is False
    assert has_usable_ipv4(["169.254.1.2", "192.168.1.10"]) is True


def main() -> int:
    test_excludes_loopback_link_local_unspecified_multicast_and_invalid()
    test_accepts_private_and_shared_client_addresses()
    test_filters_address_lists()
    print("network_ipv4=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
