#!/usr/bin/env python3
"""Build a public-safe non-iPhone desktop path-change readiness packet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso
from suggest_active_path_change_commands import collect_plan


DEFAULT_OUTPUT = "docs/results/noniphone-desktop-path-change-readiness-20260701.md"
DEFAULT_JSON_OUTPUT = "data/noniphone-desktop-path-change-readiness-20260701.json"
DESKTOP_CANDIDATE_IDS = {"macos_wifi_power_cutover", "macos_service_order_cutover"}


def lower_values(values: list[Any]) -> str:
    return " ".join(str(value).lower() for value in values if value is not None)


def device_labels(plan: dict[str, Any], device: str) -> str:
    labels: list[Any] = [device]
    detected = plan.get("detected", {})
    for item in detected.get("hardware_ports", []) if isinstance(detected, dict) else []:
        if isinstance(item, dict) and item.get("device") == device:
            labels.append(item.get("hardware_port", ""))
    for item in detected.get("network_services", []) if isinstance(detected, dict) else []:
        if isinstance(item, dict) and item.get("device") == device:
            labels.extend([item.get("name", ""), item.get("hardware_port", "")])
    return lower_values(labels)


def is_iphone_device(plan: dict[str, Any], device: str) -> bool:
    return "iphone" in device_labels(plan, device)


def active_interface_names(plan: dict[str, Any]) -> list[str]:
    detected = plan.get("detected", {})
    interfaces = detected.get("active_ipv4_interfaces", []) if isinstance(detected, dict) else []
    names: list[str] = []
    for item in interfaces:
        if isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"]))
    return sorted(set(names))


def noniphone_secondary_interfaces(plan: dict[str, Any]) -> list[str]:
    summary = plan.get("summary", {})
    default_interface = str(summary.get("default_interface") or "")
    return [
        name
        for name in active_interface_names(plan)
        if name != default_interface and not is_iphone_device(plan, name)
    ]


def candidate_is_iphone(candidate: dict[str, Any]) -> bool:
    values = [candidate.get("id", ""), candidate.get("label", "")]
    detected = candidate.get("detected", {})
    if isinstance(detected, dict):
        values.extend(detected.values())
    return "iphone" in lower_values(values)


def candidate_is_desktop_noniphone(candidate: dict[str, Any]) -> bool:
    candidate_id = str(candidate.get("id") or "")
    if candidate_id not in DESKTOP_CANDIDATE_IDS:
        return False
    if candidate_is_iphone(candidate):
        return False
    return True


def desktop_candidates(plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        candidate
        for candidate in plan.get("candidates", [])
        if isinstance(candidate, dict) and candidate_is_desktop_noniphone(candidate)
    ]


def build_packet(plan: dict[str, Any]) -> dict[str, Any]:
    summary = plan.get("summary", {})
    candidates = desktop_candidates(plan)
    secondary = noniphone_secondary_interfaces(plan)
    ready_candidate_ids: list[str] = []
    rows: list[dict[str, Any]] = []

    for item in candidates:
        candidate_id = str(item.get("id") or "")
        raw_ready = bool(item.get("ready"))
        ready = raw_ready and bool(secondary)
        reason = str(item.get("reason") or "")
        if raw_ready and not secondary:
            reason = "blocked: no active non-iPhone secondary desktop path was detected"
        rows.append(
            {
                "id": candidate_id,
                "label": str(item.get("label") or ""),
                "ready": ready,
                "source_ready": raw_ready,
                "reason": reason,
                "command_template": str(item.get("command_template") or ""),
                "restore_template": str(item.get("restore_template") or ""),
                "requires_operator_approval": bool(item.get("requires_operator_approval", True)),
            }
        )
        if ready:
            ready_candidate_ids.append(candidate_id)

    excluded = [
        str(item.get("id") or "")
        for item in plan.get("candidates", [])
        if isinstance(item, dict) and not candidate_is_desktop_noniphone(item)
    ]
    active_names = active_interface_names(plan)
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "read_only": True,
        "commands_included": False,
        "source_tool": "tools/suggest_active_path_change_commands.py",
        "active_ipv4_interface_count": len(active_names),
        "active_ipv4_interfaces": active_names,
        "default_interface": str(summary.get("default_interface") or ""),
        "noniphone_secondary_interfaces": secondary,
        "noniphone_desktop_path_ready": bool(ready_candidate_ids),
        "ready_candidate_count": len(ready_candidate_ids),
        "ready_candidates": ready_candidate_ids,
        "candidate_rows": rows,
        "excluded_candidate_ids": excluded,
        "blockers": blockers(bool(ready_candidate_ids), active_names, secondary),
        "claim_boundary": (
            "This is readiness evidence only. It excludes iPhone latent failover and does not prove "
            "browser Connection Migration until a controlled public trial records client path change, "
            "server tuple change, qlog path validation, Chrome session continuity, and application completion."
        ),
    }


def blockers(ready: bool, active_names: list[str], secondary: list[str]) -> list[str]:
    items: list[str] = []
    if ready:
        return items
    if len(active_names) < 2:
        items.append("only one active non-loopback IPv4 interface is currently detected")
    if not secondary:
        items.append("no active non-iPhone secondary desktop interface is currently detected")
    items.append("NETWORK_CHANGE_CMD must remain operator-provided and uncommitted")
    return items


def emit_markdown(packet: dict[str, Any]) -> str:
    lines = [
        "# non-iPhone Desktop Path-Change Readiness",
        "",
        f"Generated: `{packet['generated']}`",
        "",
        "This packet is public-safe and read-only. It does not execute network-change commands, and it excludes iPhone-based latent failover candidates.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| active IPv4 interfaces | `{', '.join(packet['active_ipv4_interfaces']) or '-'}` |",
        f"| default interface | `{packet['default_interface'] or '-'}` |",
        f"| non-iPhone secondary interfaces | `{', '.join(packet['noniphone_secondary_interfaces']) or '-'}` |",
        f"| non-iPhone desktop path ready | `{'yes' if packet['noniphone_desktop_path_ready'] else 'no'}` |",
        f"| ready candidates | `{', '.join(packet['ready_candidates']) or '-'}` |",
        f"| commands included | `{'yes' if packet['commands_included'] else 'no'}` |",
        "",
        "## Candidate Rows",
        "",
        "| candidate | ready | reason | command template | restore template |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in packet["candidate_rows"]:
        lines.append(
            f"| `{item['id']}` | `{'yes' if item['ready'] else 'no'}` | {item['reason']} | "
            f"`{item['command_template']}` | `{item['restore_template']}` |"
        )

    lines.extend(
        [
            "",
            "## Excluded Candidates",
            "",
            "| candidate | reason |",
            "| --- | --- |",
        ]
    )
    for candidate_id in packet["excluded_candidate_ids"]:
        reason = "iPhone-based or non-desktop path-change candidate"
        lines.append(f"| `{candidate_id}` | {reason} |")

    lines.extend(
        [
            "",
            "## Preconditions To Open This Gate",
            "",
            "1. Connect or enable a non-iPhone secondary path such as Ethernet, USB LAN, Thunderbolt Ethernet, or another non-iPhone routed interface.",
            "2. Confirm at least two active non-loopback IPv4 interfaces before setting `NETWORK_CHANGE_CMD`.",
            "3. Capture before/after route snapshots with `tools/capture_network_path_snapshot.py` against the controlled public H3 origin.",
            "4. Accept an active row only if `tools/compare_network_path_snapshots.py` reports `client_active_path_changed`.",
            "5. Keep concrete interface names, commands, hostnames, qlogs, NetLogs, pcaps, keylogs, and private config out of committed files.",
            "",
            "## Blockers",
            "",
        ]
    )
    if packet["blockers"]:
        lines.extend(f"- {item}" for item in packet["blockers"])
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            packet["claim_boundary"],
            "",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def read_plan(path: str) -> dict[str, Any]:
    if not path:
        return collect_plan(include_commands=False)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_outputs(output: Path, json_output: Path, packet: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(packet), encoding="utf-8")
    json_output.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="", help="optional JSON from suggest_active_path_change_commands.py")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    packet = build_packet(read_plan(args.input))
    write_outputs(Path(args.output), Path(args.json_output), packet)
    print(f"wrote {args.output}")
    print(f"wrote {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
