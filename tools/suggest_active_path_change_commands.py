#!/usr/bin/env python3
"""Suggest operator-reviewed active path-change command candidates.

The tool is read-only by default. It inspects local network services,
interfaces, and route state, then emits public-safe command templates. Use
--include-commands only for local, ignored operator notes.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso
from network_ipv4 import has_usable_ipv4, usable_ipv4_addresses


@dataclass
class CommandResult:
    command: list[str]
    found: bool
    exit_code: int | None
    stdout: str
    stderr: str


@dataclass
class HardwarePort:
    hardware_port: str
    device: str


@dataclass
class NetworkService:
    order: int
    name: str
    hardware_port: str
    device: str
    disabled: bool


@dataclass
class InterfaceInfo:
    name: str
    active: bool
    ipv4: list[str]


def run_command(args: list[str], timeout: int = 8) -> CommandResult:
    found = shutil.which(args[0]) is not None or Path(args[0]).exists()
    if not found:
        return CommandResult(args, False, None, "", "command not found")
    try:
        proc = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return CommandResult(args, True, proc.returncode, proc.stdout.strip(), proc.stderr.strip())
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="ignore") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="ignore") if isinstance(exc.stderr, bytes) else (exc.stderr or "timeout")
        return CommandResult(args, True, 124, stdout.strip(), stderr.strip())


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def parse_hardware_ports(output: str) -> list[HardwarePort]:
    ports: list[HardwarePort] = []
    current_port = ""
    current_device = ""
    for raw in output.splitlines() + [""]:
        line = raw.strip()
        if not line:
            if current_port and current_device:
                ports.append(HardwarePort(current_port, current_device))
            current_port = ""
            current_device = ""
            continue
        if line.startswith("Hardware Port:"):
            current_port = line.split(":", 1)[1].strip()
        elif line.startswith("Device:"):
            current_device = line.split(":", 1)[1].strip()
    return ports


def parse_service_order(output: str) -> list[NetworkService]:
    services: list[NetworkService] = []
    current_order = 0
    current_name = ""
    current_disabled = False
    service_re = re.compile(r"^\((\d+)\)\s+(.+)$")
    mapping_re = re.compile(r"^\(Hardware Port:\s*(.*),\s*Device:\s*([^)]+)\)$")
    for raw in output.splitlines():
        line = raw.strip()
        service_match = service_re.match(line)
        if service_match:
            current_order = int(service_match.group(1))
            current_name = service_match.group(2).strip()
            current_disabled = current_name.startswith("*")
            current_name = current_name.lstrip("*").strip()
            continue
        mapping_match = mapping_re.match(line)
        if mapping_match and current_name:
            services.append(
                NetworkService(
                    order=current_order,
                    name=current_name,
                    hardware_port=mapping_match.group(1).strip(),
                    device=mapping_match.group(2).strip(),
                    disabled=current_disabled,
                )
            )
            current_order = 0
            current_name = ""
            current_disabled = False
    return services


def parse_ifconfig(output: str) -> list[InterfaceInfo]:
    interfaces: dict[str, InterfaceInfo] = {}
    current = ""
    for line in output.splitlines():
        match = re.match(r"^([a-zA-Z0-9_.-]+):\s", line)
        if match:
            current = match.group(1)
            interfaces.setdefault(current, InterfaceInfo(current, False, []))
            continue
        if not current:
            continue
        if "status: active" in line:
            interfaces[current].active = True
        inet_match = re.search(r"\binet\s+(\d+\.\d+\.\d+\.\d+)\b", line)
        if inet_match:
            interfaces[current].ipv4.append(inet_match.group(1))
    return list(interfaces.values())


def parse_route_get(output: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw in output.splitlines():
        line = raw.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip().replace(" ", "_")] = value.strip()
    return data


def parse_adb_devices(output: str) -> int:
    count = 0
    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            count += 1
    return count


def active_non_loopback_ipv4(interfaces: list[InterfaceInfo]) -> list[InterfaceInfo]:
    return [
        item
        for item in interfaces
        if item.active and has_usable_ipv4(item.ipv4)
    ]


def public_interface_summary(interface: InterfaceInfo) -> dict[str, Any]:
    non_loopback_count = len([ip for ip in interface.ipv4 if not ip.startswith("127.")])
    usable_count = len(usable_ipv4_addresses(interface.ipv4))
    return {
        "name": interface.name,
        "active": interface.active,
        "usable_ipv4_count": usable_count,
        "non_loopback_ipv4_count": non_loopback_count,
    }


def public_command_summary(result: CommandResult) -> dict[str, Any]:
    return {
        "command": result.command,
        "found": result.found,
        "exit_code": result.exit_code,
        "stdout": "",
        "stderr": "",
    }


def service_for_device(services: list[NetworkService], device: str) -> NetworkService | None:
    for service in services:
        if service.device == device and not service.disabled:
            return service
    return None


def candidate(
    candidate_id: str,
    label: str,
    ready: bool,
    reason: str,
    command_template: str,
    restore_template: str,
    include_commands: bool,
    command: str = "",
    restore_command: str = "",
    detected: dict[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "id": candidate_id,
        "label": label,
        "ready": ready,
        "reason": reason,
        "command_template": command_template,
        "restore_template": restore_template,
        "command": command if include_commands else "",
        "restore_command": restore_command if include_commands else "",
        "detected": detected or {},
        "requires_operator_approval": True,
    }


def order_command(services: list[NetworkService], first: NetworkService, second: NetworkService) -> str:
    ordered_names = [first.name, second.name]
    for service in sorted(services, key=lambda item: item.order):
        if service.disabled or service.name in ordered_names:
            continue
        ordered_names.append(service.name)
    return "networksetup -ordernetworkservices " + " ".join(shell_quote(name) for name in ordered_names)


def build_plan(
    *,
    hardware_ports_text: str,
    service_order_text: str,
    ifconfig_text: str,
    default_route_text: str,
    adb_devices_text: str,
    include_commands: bool = False,
) -> dict[str, Any]:
    hardware_ports = parse_hardware_ports(hardware_ports_text)
    services = parse_service_order(service_order_text)
    interfaces = parse_ifconfig(ifconfig_text)
    active_ipv4 = active_non_loopback_ipv4(interfaces)
    active_names = sorted(item.name for item in active_ipv4)
    default_route = parse_route_get(default_route_text)
    default_interface = default_route.get("interface", "")
    primary_service = service_for_device(services, default_interface) if default_interface else None
    secondary_services = [
        service
        for service in services
        if service.device in active_names and service.device != default_interface and not service.disabled
    ]
    secondary_service = secondary_services[0] if secondary_services else None
    wifi_port = next((port for port in hardware_ports if port.hardware_port.lower() == "wi-fi"), None)
    wifi_active = bool(wifi_port and wifi_port.device in active_names)
    adb_device_count = parse_adb_devices(adb_devices_text)
    secondary_ready = len(active_ipv4) >= 2

    candidates: list[dict[str, Any]] = []
    wifi_reason = "ready: Wi-Fi is active and at least one secondary active IPv4 path exists"
    if not wifi_port:
        wifi_reason = "blocked: Wi-Fi hardware port was not detected"
    elif not wifi_active:
        wifi_reason = "blocked: Wi-Fi is not an active IPv4 path"
    elif not secondary_ready:
        wifi_reason = "blocked: no active secondary non-loopback IPv4 path was detected"
    wifi_device = wifi_port.device if wifi_port else "<wifi-device>"
    candidates.append(
        candidate(
            "macos_wifi_power_cutover",
            "Turn Wi-Fi off after secondary path is active",
            bool(wifi_port and wifi_active and secondary_ready),
            wifi_reason,
            "networksetup -setairportpower <wifi-device> off",
            "networksetup -setairportpower <wifi-device> on",
            include_commands,
            command=f"networksetup -setairportpower {shell_quote(wifi_device)} off" if wifi_port else "",
            restore_command=f"networksetup -setairportpower {shell_quote(wifi_device)} on" if wifi_port else "",
            detected={"wifi_device": wifi_device},
        )
    )

    service_reason = "ready: default and secondary services are both active"
    if not primary_service:
        service_reason = "blocked: default route interface could not be mapped to a network service"
    elif not secondary_service:
        service_reason = "blocked: no active secondary service was detected"
    service_ready = bool(primary_service and secondary_service)
    candidates.append(
        candidate(
            "macos_service_order_cutover",
            "Put active secondary service before the current default service",
            service_ready,
            service_reason,
            "networksetup -ordernetworkservices <secondary-service> <primary-service> <remaining-services...>",
            "networksetup -ordernetworkservices <primary-service> <secondary-service> <remaining-services...>",
            include_commands,
            command=order_command(services, secondary_service, primary_service) if service_ready else "",
            restore_command=order_command(services, primary_service, secondary_service) if service_ready else "",
            detected={
                "primary_service": primary_service.name if primary_service else "",
                "secondary_service": secondary_service.name if secondary_service else "",
                "primary_device": primary_service.device if primary_service else "",
                "secondary_device": secondary_service.device if secondary_service else "",
            },
        )
    )

    android_ready = adb_device_count > 0
    candidates.append(
        candidate(
            "android_wifi_to_cellular_cutover",
            "Disable Android Wi-Fi and rely on cellular",
            android_ready,
            "ready: ADB device is connected" if android_ready else "blocked: no ADB device is connected",
            "adb shell svc wifi disable",
            "adb shell svc wifi enable",
            include_commands,
            command="adb shell svc wifi disable",
            restore_command="adb shell svc wifi enable",
            detected={"adb_device_count": str(adb_device_count)},
        )
    )

    ready_candidates = [item["id"] for item in candidates if item["ready"]]
    return {
        "generated": utc_date_iso(),
        "commands_included": include_commands,
        "read_only": True,
        "summary": {
            "active_ipv4_interface_count": len(active_ipv4),
            "active_ipv4_interfaces": active_names,
            "default_interface": default_interface,
            "secondary_path_ready": secondary_ready,
            "ready_candidate_count": len(ready_candidates),
            "ready_candidates": ready_candidates,
        },
        "detected": {
            "hardware_ports": [asdict(item) for item in hardware_ports],
            "network_services": [asdict(item) for item in services],
            "active_ipv4_interfaces": [public_interface_summary(item) for item in active_ipv4],
            "default_route": {"interface": default_interface},
        },
        "candidates": candidates,
        "claim_boundary": "A candidate command is not migration evidence; count a trial only after before/after client path snapshots and server/qlog/NetLog artifacts validate it.",
    }


def collect_plan(include_commands: bool = False) -> dict[str, Any]:
    hardware_ports = run_command(["networksetup", "-listallhardwareports"])
    service_order = run_command(["networksetup", "-listnetworkserviceorder"])
    ifconfig = run_command(["ifconfig"])
    default_route = run_command(["route", "-n", "get", "default"])
    adb = run_command(["adb", "devices"])
    plan = build_plan(
        hardware_ports_text=hardware_ports.stdout if hardware_ports.exit_code == 0 else "",
        service_order_text=service_order.stdout if service_order.exit_code == 0 else "",
        ifconfig_text=ifconfig.stdout if ifconfig.exit_code == 0 else "",
        default_route_text=default_route.stdout if default_route.exit_code == 0 else "",
        adb_devices_text=adb.stdout if adb.exit_code == 0 else "",
        include_commands=include_commands,
    )
    plan["commands"] = {
        "hardware_ports": public_command_summary(hardware_ports),
        "service_order": public_command_summary(service_order),
        "ifconfig": public_command_summary(ifconfig),
        "default_route": public_command_summary(default_route),
        "adb_devices": public_command_summary(adb),
    }
    return plan


def emit_markdown(plan: dict[str, Any]) -> str:
    summary = plan["summary"]
    lines = [
        "# Active Path-Change Command Candidates",
        "",
        f"Generated: `{plan['generated']}`",
        "",
        "This report is read-only. It does not execute network-change commands.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| active IPv4 interfaces | `{', '.join(summary['active_ipv4_interfaces']) or '-'}` |",
        f"| default interface | `{summary['default_interface'] or '-'}` |",
        f"| secondary path ready | `{'yes' if summary['secondary_path_ready'] else 'no'}` |",
        f"| ready candidates | `{', '.join(summary['ready_candidates']) or '-'}` |",
        f"| commands included | `{'yes' if plan['commands_included'] else 'no'}` |",
        "",
        "## Candidates",
        "",
        "| candidate | ready | reason | command form | restore form |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in plan["candidates"]:
        command_form = item["command"] if plan["commands_included"] and item["command"] else item["command_template"]
        restore_form = item["restore_command"] if plan["commands_included"] and item["restore_command"] else item["restore_template"]
        lines.append(
            f"| `{item['id']}` | `{'yes' if item['ready'] else 'no'}` | {item['reason']} | `{command_form}` | `{restore_form}` |"
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            plan["claim_boundary"],
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument(
        "--include-commands",
        action="store_true",
        help="include fully substituted local command candidates; use only for ignored operator notes",
    )
    args = parser.parse_args()

    plan = collect_plan(include_commands=args.include_commands)
    text = json.dumps(plan, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(plan)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
