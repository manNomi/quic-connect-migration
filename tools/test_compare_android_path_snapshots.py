#!/usr/bin/env python3
"""Regression tests for Android route/address snapshot comparison."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from compare_android_path_snapshots import build_comparison


ROUTE_WIFI = "default via 192.168.0.1 dev wlan0 proto dhcp metric 600\n192.168.0.0/24 dev wlan0\n"
ROUTE_CELL = "default via 10.12.0.1 dev rmnet_data0 proto static metric 100\n10.12.0.0/24 dev rmnet_data0\n"
ADDR_WIFI = "2: wlan0: <UP>\n    inet 192.168.0.22/24 brd 192.168.0.255 scope global wlan0\n"
ADDR_CELL = "7: rmnet_data0: <UP>\n    inet 10.12.0.8/24 brd 10.12.0.255 scope global rmnet_data0\n"


def write(path: Path, text: str) -> str:
    path.write_text(text, encoding="utf-8")
    return path.as_posix()


def args_for(root: Path, *, route_after: str = ROUTE_WIFI, addr_after: str = ADDR_WIFI) -> argparse.Namespace:
    return argparse.Namespace(
        before_route=write(root / "route-before.txt", ROUTE_WIFI),
        after_route=write(root / "route-after.txt", route_after),
        before_addr=write(root / "addr-before.txt", ADDR_WIFI),
        after_addr=write(root / "addr-after.txt", addr_after),
        before_connectivity=write(root / "connectivity-before.txt", "NetworkAgentInfo WIFI CONNECTED VALIDATED\n"),
        after_connectivity=write(root / "connectivity-after.txt", "NetworkAgentInfo WIFI CONNECTED VALIDATED\n"),
    )


def test_no_change_is_not_active_path_change() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = build_comparison(args_for(Path(tmp)))
    assert result["classification"] == "no_client_path_change_observed"
    assert result["active_path_changed"] is False


def test_route_and_addr_change_is_active_path_change() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = build_comparison(args_for(Path(tmp), route_after=ROUTE_CELL, addr_after=ADDR_CELL))
    assert result["classification"] == "client_active_path_changed"
    assert result["active_path_changed"] is True
    assert result["default_route_changed"] is True
    assert result["global_ipv4_changed"] is True


def test_missing_snapshot_is_reported() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        args = args_for(root)
        Path(args.after_route).unlink()
        result = build_comparison(args)
    assert result["classification"] == "path_snapshot_missing"
    assert result["active_path_changed"] is False


def main() -> int:
    test_no_change_is_not_active_path_change()
    test_route_and_addr_change_is_active_path_change()
    test_missing_snapshot_is_reported()
    print("compare_android_path_snapshots=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
