#!/usr/bin/env python3
"""IPv4 address helpers for local network handover evidence."""

from __future__ import annotations

from ipaddress import IPv4Address, ip_address


def is_usable_ipv4(raw: str) -> bool:
    """Return true for IPv4 addresses that can represent an actual client path."""
    try:
        address = ip_address(raw)
    except ValueError:
        return False
    if not isinstance(address, IPv4Address):
        return False
    return not any(
        [
            address.is_loopback,
            address.is_link_local,
            address.is_unspecified,
            address.is_multicast,
            address == IPv4Address("255.255.255.255"),
        ]
    )


def usable_ipv4_addresses(addresses: list[str]) -> list[str]:
    return [address for address in addresses if is_usable_ipv4(address)]


def has_usable_ipv4(addresses: list[str]) -> bool:
    return bool(usable_ipv4_addresses(addresses))
