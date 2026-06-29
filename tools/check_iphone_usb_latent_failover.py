#!/usr/bin/env python3
"""Check and optionally measure macOS iPhone USB latent failover.

This tool targets the macOS pattern where iPhone USB tethering exists as a
hardware port but stays inactive while Wi-Fi is up, then becomes the default
route after Wi-Fi is disabled. That is useful handover evidence, but it is not
the same as two simultaneously active client paths.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from network_ipv4 import has_usable_ipv4, usable_ipv4_addresses
from research_clock import utc_date_iso


@dataclass
class CommandResult:
    command: list[str]
    found: bool
    exit_code: int | None
    stdout: str
    stderr: str


@dataclass
class InterfaceState:
    name: str
    present: bool
    active: bool
    ipv4: list[str]
    service_configured: bool = False
    service_device: str = ""
    hardware_port_present: bool = False
    hardware_device: str = ""
    device_listed: bool = False


@dataclass
class StateSnapshot:
    captured_ms: int
    wifi_power: str
    default_interface: str
    iphone_usb: InterfaceState


def run_command(args: list[str], timeout: int = 8) -> CommandResult:
    found = shutil.which(args[0]) is not None or Path(args[0]).exists()
    if not found:
        return CommandResult(args, False, None, "", "command not found")
    try:
        proc = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="ignore") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="ignore") if isinstance(exc.stderr, bytes) else (exc.stderr or "timeout")
        return CommandResult(args, True, 124, stdout.strip(), stderr.strip())
    return CommandResult(args, True, proc.returncode, proc.stdout.strip(), proc.stderr.strip())


def parse_interface_state(device: str, ifconfig_text: str) -> InterfaceState:
    pattern = re.compile(rf"^{re.escape(device)}:\s.*?(?=^[a-zA-Z0-9_.-]+:\s|\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(ifconfig_text)
    if not match:
        return InterfaceState(device, False, False, [])
    block = match.group(0)
    ipv4 = re.findall(r"\binet\s+(\d+\.\d+\.\d+\.\d+)\b", block)
    return InterfaceState(device, True, "status: active" in block, ipv4)


def parse_service_order_device(service_name: str, output: str) -> str:
    lines = output.splitlines()
    service_pattern = re.compile(rf"^\(\d+\)\s+{re.escape(service_name)}\s*$")
    device_pattern = re.compile(r"^\(Hardware Port:\s*.*?,\s*Device:\s*([^)]+)\)\s*$")
    for index, line in enumerate(lines):
        if not service_pattern.match(line.strip()):
            continue
        if index + 1 >= len(lines):
            return ""
        match = device_pattern.match(lines[index + 1].strip())
        return match.group(1) if match else ""
    return ""


def parse_hardware_port_device(port_name: str, output: str) -> str:
    blocks = re.split(r"\n\s*\n", output.strip())
    for block in blocks:
        port = re.search(rf"^Hardware Port:\s*{re.escape(port_name)}\s*$", block, re.MULTILINE)
        device = re.search(r"^Device:\s*(\S+)\s*$", block, re.MULTILINE)
        if port and device:
            return device.group(1)
    return ""


def parse_ifconfig_device_list(output: str) -> list[str]:
    return [item.strip() for item in output.split() if item.strip()]


def enrich_interface_state(
    state: InterfaceState,
    *,
    service_device: str,
    hardware_device: str,
    listed_devices: list[str],
) -> InterfaceState:
    return InterfaceState(
        name=state.name,
        present=state.present,
        active=state.active,
        ipv4=state.ipv4,
        service_configured=bool(service_device),
        service_device=service_device,
        hardware_port_present=bool(hardware_device),
        hardware_device=hardware_device,
        device_listed=state.name in listed_devices,
    )


def parse_default_interface(route_text: str) -> str:
    match = re.search(r"^\s*interface:\s*(\S+)\s*$", route_text, re.MULTILINE)
    return match.group(1) if match else ""


def redact_ipv4(value: object) -> object:
    if isinstance(value, str):
        return re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", "<redacted-address>", value)
    if isinstance(value, list):
        return [redact_ipv4(item) for item in value]
    if isinstance(value, dict):
        return {key: redact_ipv4(item) for key, item in value.items()}
    return value


def snapshot(wifi_device: str, iphone_device: str, iphone_service: str, start: float) -> StateSnapshot:
    wifi = run_command(["networksetup", "-getairportpower", wifi_device])
    service_order = run_command(["networksetup", "-listnetworkserviceorder"])
    hardware_ports = run_command(["networksetup", "-listallhardwareports"])
    route = run_command(["route", "-n", "get", "default"])
    ifconfig_list = run_command(["ifconfig", "-l"])
    ifconfig = run_command(["ifconfig", iphone_device])
    if ifconfig.exit_code != 0:
        ifconfig = run_command(["ifconfig"])
    base_iphone = parse_interface_state(iphone_device, ifconfig.stdout if ifconfig.exit_code == 0 else "")
    service_device = parse_service_order_device(iphone_service, service_order.stdout) if service_order.exit_code == 0 else ""
    hardware_device = parse_hardware_port_device(iphone_service, hardware_ports.stdout) if hardware_ports.exit_code == 0 else ""
    listed_devices = parse_ifconfig_device_list(ifconfig_list.stdout) if ifconfig_list.exit_code == 0 else []
    return StateSnapshot(
        captured_ms=round((time.monotonic() - start) * 1000),
        wifi_power=wifi.stdout if wifi.exit_code == 0 else "",
        default_interface=parse_default_interface(route.stdout) if route.exit_code == 0 else "",
        iphone_usb=enrich_interface_state(
            base_iphone,
            service_device=service_device,
            hardware_device=hardware_device,
            listed_devices=listed_devices,
        ),
    )


def is_failover_ready(state: StateSnapshot, iphone_device: str) -> bool:
    return (
        state.iphone_usb.present
        and state.iphone_usb.active
        and has_usable_ipv4(state.iphone_usb.ipv4)
        and state.default_interface == iphone_device
    )


def compact_state(state: StateSnapshot) -> dict[str, object]:
    iphone = asdict(state.iphone_usb)
    iphone["usable_ipv4"] = usable_ipv4_addresses(state.iphone_usb.ipv4)
    return {
        "captured_ms": state.captured_ms,
        "wifi_power": state.wifi_power,
        "default_interface": state.default_interface,
        "iphone_usb": iphone,
    }


def classify(before: StateSnapshot, after: StateSnapshot, ready_at_ms: int | None, measured: bool) -> str:
    if not before.iphone_usb.present and not after.iphone_usb.present:
        candidate = after.iphone_usb if after.iphone_usb.service_configured else before.iphone_usb
        if candidate.service_configured and not candidate.hardware_port_present:
            return "iphone_usb_service_configured_hardware_absent"
        if candidate.service_configured and not candidate.device_listed:
            return "iphone_usb_service_configured_interface_absent"
        if candidate.service_configured:
            return "iphone_usb_service_configured_not_detected"
        return "iphone_usb_not_detected"
    if ready_at_ms is not None:
        if before.default_interface and before.default_interface != after.default_interface:
            return "latent_iphone_usb_failover_observed"
        return "iphone_usb_default_observed"
    if not measured:
        if is_failover_ready(after, after.iphone_usb.name):
            return "iphone_usb_already_default"
        if before.iphone_usb.present and not before.iphone_usb.active:
            return "iphone_usb_latent_candidate_unmeasured"
        return "iphone_usb_not_ready"
    if after.iphone_usb.present and after.iphone_usb.active and not has_usable_ipv4(after.iphone_usb.ipv4):
        return "iphone_usb_active_without_usable_ipv4"
    return "iphone_usb_failover_not_observed"


def next_actions_for(classification: str) -> list[str]:
    if classification == "iphone_usb_service_configured_hardware_absent":
        return [
            "Reconnect the USB-C cable and unlock the iPhone.",
            "Enable Personal Hotspot on the iPhone and keep the screen awake for the next check.",
            "Check macOS System Settings > Network and confirm the iPhone USB service is physically present, not only remembered as a saved service.",
            "Rerun this checker before running a browser handover trial.",
        ]
    if classification == "iphone_usb_service_configured_interface_absent":
        return [
            "Toggle iPhone Personal Hotspot off and on, then reconnect the cable.",
            "Confirm the configured iPhone USB device name matches the live interface shown by ifconfig -l.",
            "Rerun this checker; do not run active public rows until the interface is present.",
        ]
    if classification == "iphone_usb_latent_candidate_unmeasured":
        return [
            "Run with --measure --restore-wifi to confirm delayed Wi-Fi-loss-to-iPhone-USB failover timing.",
            "Use the measured ready_at_ms as the path-change trigger preflight evidence.",
        ]
    if classification == "latent_iphone_usb_failover_observed":
        return [
            "Use ALLOW_LATENT_SECONDARY_PATH=1 and NETWORK_CHANGE_CMD=\"networksetup -setairportpower 'en0' off\" for page-ready trials.",
            "Report the setup as delayed OS failover, not simultaneous active multipath.",
        ]
    if classification == "iphone_usb_active_without_usable_ipv4":
        return [
            "Renew DHCP or reconnect the iPhone USB service before running browser trials.",
            "Confirm the iPhone USB interface has a usable IPv4 address and becomes the default route after Wi-Fi is disabled.",
        ]
    return [
        "Resolve the iPhone USB network interface state before running active browser handover rows.",
    ]


def build_report(
    *,
    wifi_device: str,
    iphone_device: str,
    iphone_service: str,
    measure: bool,
    timeout_seconds: float,
    poll_interval_ms: int,
    restore_wifi: bool,
) -> dict[str, object]:
    start = time.monotonic()
    before = snapshot(wifi_device, iphone_device, iphone_service, start)
    events = [compact_state(before)]
    ready_at_ms: int | None = None
    network_change_exit: int | None = None

    if measure:
        network_change = run_command(["networksetup", "-setairportpower", wifi_device, "off"], timeout=timeout_seconds)
        network_change_exit = network_change.exit_code
        deadline = time.monotonic() + timeout_seconds
        last_event = events[-1]
        while time.monotonic() <= deadline:
            current = snapshot(wifi_device, iphone_device, iphone_service, start)
            current_event = compact_state(current)
            if current_event != last_event:
                events.append(current_event)
                last_event = current_event
            if is_failover_ready(current, iphone_device):
                ready_at_ms = current.captured_ms
                break
            time.sleep(poll_interval_ms / 1000)

    after = snapshot(wifi_device, iphone_device, iphone_service, start)
    if compact_state(after) != events[-1]:
        events.append(compact_state(after))

    restore_exit: int | None = None
    if restore_wifi:
        restore = run_command(["networksetup", "-setairportpower", wifi_device, "on"], timeout=timeout_seconds)
        restore_exit = restore.exit_code

    classification = classify(before, after, ready_at_ms, measure)
    return {
        "check_date": utc_date_iso(),
        "tool": "check_iphone_usb_latent_failover",
        "mode": "measure" if measure else "snapshot",
        "wifi_device": wifi_device,
        "iphone_device": iphone_device,
        "iphone_service": iphone_service,
        "measured": measure,
        "ready": ready_at_ms is not None or is_failover_ready(after, iphone_device),
        "ready_at_ms": ready_at_ms,
        "classification": classification,
        "next_actions": next_actions_for(classification),
        "network_change_exit": network_change_exit,
        "restore_wifi": restore_wifi,
        "restore_exit": restore_exit,
        "before": compact_state(before),
        "after": compact_state(after),
        "events": events,
        "claim_boundary": (
            "This measures OS-level delayed Wi-Fi-to-iPhone-USB failover. "
            "It can validate a real client path change trigger, but by itself it does not prove single-connection QUIC migration."
        ),
    }


def emit_markdown(report: dict[str, object]) -> str:
    before = report["before"] if isinstance(report["before"], dict) else {}
    after = report["after"] if isinstance(report["after"], dict) else {}
    before_iphone = before.get("iphone_usb", {}) if isinstance(before.get("iphone_usb"), dict) else {}
    after_iphone = after.get("iphone_usb", {}) if isinstance(after.get("iphone_usb"), dict) else {}
    next_actions = report.get("next_actions") if isinstance(report.get("next_actions"), list) else []
    lines = [
        "# iPhone USB Latent Failover Check",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| date | `{report['check_date']}` |",
        f"| mode | `{report['mode']}` |",
        f"| Wi-Fi device | `{report['wifi_device']}` |",
        f"| iPhone USB service | `{report['iphone_service']}` |",
        f"| iPhone USB device | `{report['iphone_device']}` |",
        f"| ready | `{'yes' if report['ready'] else 'no'}` |",
        f"| ready at | `{report['ready_at_ms'] if report['ready_at_ms'] is not None else '-'}` ms |",
        f"| classification | `{report['classification']}` |",
        f"| before default interface | `{before.get('default_interface') or '-'}` |",
        f"| after default interface | `{after.get('default_interface') or '-'}` |",
        f"| network-change exit | `{report['network_change_exit'] if report['network_change_exit'] is not None else '-'}` |",
        "",
        "## iPhone USB Inventory",
        "",
        "| field | before | after |",
        "| --- | --- | --- |",
        f"| service configured | `{'yes' if before_iphone.get('service_configured') else 'no'}` | `{'yes' if after_iphone.get('service_configured') else 'no'}` |",
        f"| service device | `{before_iphone.get('service_device') or '-'}` | `{after_iphone.get('service_device') or '-'}` |",
        f"| hardware port present | `{'yes' if before_iphone.get('hardware_port_present') else 'no'}` | `{'yes' if after_iphone.get('hardware_port_present') else 'no'}` |",
        f"| hardware device | `{before_iphone.get('hardware_device') or '-'}` | `{after_iphone.get('hardware_device') or '-'}` |",
        f"| ifconfig listed | `{'yes' if before_iphone.get('device_listed') else 'no'}` | `{'yes' if after_iphone.get('device_listed') else 'no'}` |",
        f"| interface present | `{'yes' if before_iphone.get('present') else 'no'}` | `{'yes' if after_iphone.get('present') else 'no'}` |",
        f"| interface active | `{'yes' if before_iphone.get('active') else 'no'}` | `{'yes' if after_iphone.get('active') else 'no'}` |",
        "",
        "## Next Actions",
        "",
    ]
    lines.extend(f"- {item}" for item in next_actions)
    lines.extend([
        "",
        "## Claim Boundary",
        "",
        str(report["claim_boundary"]),
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wifi-device", default="en0")
    parser.add_argument("--iphone-device", default="en8")
    parser.add_argument("--iphone-service", default="iPhone USB")
    parser.add_argument("--measure", action="store_true", help="turn Wi-Fi off and poll until iPhone USB becomes default")
    parser.add_argument("--timeout-seconds", type=float, default=15)
    parser.add_argument("--poll-interval-ms", type=int, default=250)
    parser.add_argument("--restore-wifi", action="store_true", help="turn Wi-Fi back on after measurement")
    parser.add_argument("--redact-sensitive", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    args = parser.parse_args()

    report = build_report(
        wifi_device=args.wifi_device,
        iphone_device=args.iphone_device,
        iphone_service=args.iphone_service,
        measure=args.measure,
        timeout_seconds=args.timeout_seconds,
        poll_interval_ms=args.poll_interval_ms,
        restore_wifi=args.restore_wifi,
    )
    if args.redact_sensitive:
        report = redact_ipv4(report)  # type: ignore[assignment]
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
        if not text.endswith("\n"):
            sys.stdout.write("\n")
    return 0 if report.get("ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
