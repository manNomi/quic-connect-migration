#!/usr/bin/env python3
"""Compare before/after route snapshots for client path-change evidence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> tuple[dict[str, Any], str]:
    if not path.exists():
        return {}, "missing"
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore")), ""
    except (OSError, json.JSONDecodeError) as exc:
        return {}, f"read failed: {exc}"


def route_parsed(snapshot: dict[str, Any], key: str) -> dict[str, Any]:
    value = snapshot.get(key)
    if not isinstance(value, dict):
        return {}
    parsed = value.get("parsed")
    return parsed if isinstance(parsed, dict) else {}


def active_interface_names(snapshot: dict[str, Any]) -> list[str]:
    interfaces = snapshot.get("active_ipv4_interfaces")
    if not isinstance(interfaces, list):
        return []
    names = []
    for item in interfaces:
        if isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"]))
    return sorted(set(names))


def public_ip(snapshot: dict[str, Any]) -> str:
    probe = snapshot.get("public_ip_probe")
    if not isinstance(probe, dict):
        return ""
    return str(probe.get("ip") or "")


def changed(before: Any, after: Any) -> bool:
    return before != after and before not in (None, "") and after not in (None, "")


def build_summary(before_path: Path, after_path: Path) -> dict[str, Any]:
    before, before_error = load_json(before_path)
    after, after_error = load_json(after_path)
    before_default = route_parsed(before, "default_route")
    after_default = route_parsed(after, "default_route")
    before_target = route_parsed(before, "target_route")
    after_target = route_parsed(after, "target_route")
    before_active = active_interface_names(before)
    after_active = active_interface_names(after)
    before_public_ip = public_ip(before)
    after_public_ip = public_ip(after)

    default_interface_changed = changed(before_default.get("interface"), after_default.get("interface"))
    target_interface_changed = changed(before_target.get("interface"), after_target.get("interface"))
    default_gateway_changed = changed(before_default.get("gateway"), after_default.get("gateway"))
    target_gateway_changed = changed(before_target.get("gateway"), after_target.get("gateway"))
    active_interface_set_changed = before_active != after_active and bool(before_active or after_active)
    public_ip_changed = changed(before_public_ip, after_public_ip)
    active_path_changed = any(
        [
            default_interface_changed,
            target_interface_changed,
            default_gateway_changed,
            target_gateway_changed,
            public_ip_changed,
        ]
    )

    if before_error or after_error:
        classification = "path_snapshot_missing"
    elif active_path_changed:
        classification = "client_active_path_changed"
    elif active_interface_set_changed:
        classification = "interface_set_changed_without_route_change"
    else:
        classification = "no_client_path_change_observed"

    return {
        "before_path": str(before_path),
        "after_path": str(after_path),
        "before_error": before_error,
        "after_error": after_error,
        "classification": classification,
        "active_path_changed": active_path_changed,
        "active_interface_set_changed": active_interface_set_changed,
        "default_interface_changed": default_interface_changed,
        "target_interface_changed": target_interface_changed,
        "default_gateway_changed": default_gateway_changed,
        "target_gateway_changed": target_gateway_changed,
        "public_ip_changed": public_ip_changed,
        "before": {
            "captured_at": before.get("captured_at"),
            "active_interfaces": before_active,
            "default_interface": before_default.get("interface"),
            "target_interface": before_target.get("interface"),
            "default_gateway": before_default.get("gateway"),
            "target_gateway": before_target.get("gateway"),
            "public_ip": before_public_ip,
        },
        "after": {
            "captured_at": after.get("captured_at"),
            "active_interfaces": after_active,
            "default_interface": after_default.get("interface"),
            "target_interface": after_target.get("interface"),
            "default_gateway": after_default.get("gateway"),
            "target_gateway": after_target.get("gateway"),
            "public_ip": after_public_ip,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--output")
    args = parser.parse_args()

    summary = build_summary(Path(args.before), Path(args.after))
    text = json.dumps(summary, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if not (summary["before_error"] or summary["after_error"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
