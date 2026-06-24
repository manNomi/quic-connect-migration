#!/usr/bin/env python3
"""Compare Android route/address snapshots around a network-change command."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
from datetime import date
from pathlib import Path
from typing import Any


def read_text(path: str | None) -> tuple[str, bool]:
    if not path:
        return "", False
    target = Path(path)
    if not target.exists():
        return "", False
    try:
        return target.read_text(encoding="utf-8", errors="ignore"), True
    except OSError:
        return "", False


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:16] if text else ""


def normalize_lines(text: str) -> list[str]:
    return sorted(" ".join(line.split()) for line in text.splitlines() if line.strip())


def default_routes(text: str) -> list[str]:
    routes = []
    for line in normalize_lines(text):
        if line.startswith("default ") or line == "default":
            routes.append(line)
    return routes


def global_ipv4_addrs(text: str) -> list[str]:
    addrs: set[str] = set()
    for match in re.finditer(r"\binet\s+(\d+\.\d+\.\d+\.\d+)/", text):
        try:
            addr = ipaddress.ip_address(match.group(1))
        except ValueError:
            continue
        if addr.is_loopback or addr.is_link_local or addr.is_multicast or addr.is_unspecified:
            continue
        addrs.add(str(addr))
    return sorted(addrs)


def connected_connectivity_lines(text: str) -> list[str]:
    lines = []
    for line in normalize_lines(text):
        upper = line.upper()
        if "CONNECTED" in upper or "VALIDATED" in upper or "DEFAULT" in upper:
            lines.append(line)
    return lines


def build_comparison(args: argparse.Namespace) -> dict[str, Any]:
    before_route_text, before_route_exists = read_text(args.before_route)
    after_route_text, after_route_exists = read_text(args.after_route)
    before_addr_text, before_addr_exists = read_text(args.before_addr)
    after_addr_text, after_addr_exists = read_text(args.after_addr)
    before_connectivity_text, before_connectivity_exists = read_text(args.before_connectivity)
    after_connectivity_text, after_connectivity_exists = read_text(args.after_connectivity)

    before = {
        "route_exists": before_route_exists,
        "addr_exists": before_addr_exists,
        "connectivity_exists": before_connectivity_exists,
        "default_routes": default_routes(before_route_text),
        "global_ipv4_addrs": global_ipv4_addrs(before_addr_text),
        "route_digest": digest(before_route_text),
        "addr_digest": digest(before_addr_text),
        "connectivity_digest": digest(before_connectivity_text),
        "connected_connectivity_lines": connected_connectivity_lines(before_connectivity_text),
    }
    after = {
        "route_exists": after_route_exists,
        "addr_exists": after_addr_exists,
        "connectivity_exists": after_connectivity_exists,
        "default_routes": default_routes(after_route_text),
        "global_ipv4_addrs": global_ipv4_addrs(after_addr_text),
        "route_digest": digest(after_route_text),
        "addr_digest": digest(after_addr_text),
        "connectivity_digest": digest(after_connectivity_text),
        "connected_connectivity_lines": connected_connectivity_lines(after_connectivity_text),
    }

    route_missing = not before_route_exists or not after_route_exists
    addr_missing = not before_addr_exists or not after_addr_exists
    default_route_changed = before["default_routes"] != after["default_routes"]
    global_ipv4_changed = before["global_ipv4_addrs"] != after["global_ipv4_addrs"]
    route_raw_changed = before["route_digest"] != after["route_digest"]
    addr_raw_changed = before["addr_digest"] != after["addr_digest"]
    connectivity_changed = before["connectivity_digest"] != after["connectivity_digest"]
    active_path_changed = (not route_missing and not addr_missing) and (default_route_changed or global_ipv4_changed)

    if route_missing or addr_missing:
        classification = "path_snapshot_missing"
    elif active_path_changed:
        classification = "client_active_path_changed"
    elif connectivity_changed:
        classification = "android_connectivity_changed_without_route_change"
    elif route_raw_changed or addr_raw_changed:
        classification = "android_snapshot_changed_without_parsed_route_change"
    else:
        classification = "no_client_path_change_observed"

    return {
        "check_date": date.today().isoformat(),
        "classification": classification,
        "active_path_changed": active_path_changed,
        "default_route_changed": default_route_changed,
        "global_ipv4_changed": global_ipv4_changed,
        "route_raw_changed": route_raw_changed,
        "addr_raw_changed": addr_raw_changed,
        "connectivity_changed": connectivity_changed,
        "before": before,
        "after": after,
    }


def emit_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Android Client Path Change Summary",
        "",
        f"Generated: `{result['check_date']}`",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| classification | `{result['classification']}` |",
        f"| active path changed | `{'yes' if result['active_path_changed'] else 'no'}` |",
        f"| default route changed | `{'yes' if result['default_route_changed'] else 'no'}` |",
        f"| global IPv4 changed | `{'yes' if result['global_ipv4_changed'] else 'no'}` |",
        f"| connectivity changed | `{'yes' if result['connectivity_changed'] else 'no'}` |",
    ]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before-route", required=True)
    parser.add_argument("--after-route", required=True)
    parser.add_argument("--before-addr", required=True)
    parser.add_argument("--after-addr", required=True)
    parser.add_argument("--before-connectivity")
    parser.add_argument("--after-connectivity")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument("--output")
    args = parser.parse_args()

    result = build_comparison(args)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(result)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
