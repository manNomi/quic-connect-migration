#!/usr/bin/env python3
"""Check local readiness for browser/Cronet network handover experiments."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


ACCOUNT_ID_RE = re.compile(r"\b\d{12}\b")


@dataclass
class CommandResult:
    command: str
    found: bool
    exit_code: int | None
    stdout: str
    stderr: str


@dataclass
class InterfaceInfo:
    name: str
    active: bool
    ipv4: list[str]


@dataclass
class HandoverReadiness:
    check_date: str
    chrome_found: bool
    chrome_path: str
    adb_found: bool
    adb_devices: list[str]
    android_ready: bool
    network_services: list[str]
    active_ipv4_interfaces: list[InterfaceInfo]
    secondary_path_ready: bool
    aws_found: bool
    aws_identity_ok: bool
    aws_identity_redacted: str
    disk_available_gib: float
    blockers: list[str]
    commands: dict[str, CommandResult]

    @property
    def desktop_handover_ready(self) -> bool:
        return self.chrome_found and self.secondary_path_ready


def run_command(args: list[str], timeout: int = 8) -> CommandResult:
    found = shutil.which(args[0]) is not None or Path(args[0]).exists()
    if not found:
        return CommandResult(" ".join(args), False, None, "", "command not found")
    try:
        proc = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return CommandResult(
            " ".join(args),
            True,
            proc.returncode,
            redact(proc.stdout.strip()),
            redact(proc.stderr.strip()),
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(" ".join(args), True, 124, redact(exc.stdout or ""), redact(exc.stderr or "timeout"))


def redact(text: str | bytes) -> str:
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")
    return ACCOUNT_ID_RE.sub("<account-id>", text)


def parse_adb_devices(output: str) -> list[str]:
    devices: list[str] = []
    for line in output.splitlines()[1:]:
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(f"device-{len(devices) + 1}")
    return devices


def parse_network_services(output: str) -> list[str]:
    services: list[str] = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("An asterisk"):
            continue
        services.append(stripped.lstrip("*"))
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


def disk_available_gib(path: str) -> float:
    usage = shutil.disk_usage(path)
    return round(usage.free / (1024**3), 2)


def summarize_command(result: CommandResult, include_output: bool) -> CommandResult:
    if include_output:
        return result
    return CommandResult(result.command, result.found, result.exit_code, "", "")


def build_readiness(chrome_bin: str, include_command_output: bool = False) -> HandoverReadiness:
    adb = run_command(["adb", "devices"])
    networksetup = run_command(["networksetup", "-listallnetworkservices"])
    ifconfig = run_command(["ifconfig"])
    aws = run_command(["aws", "sts", "get-caller-identity", "--output", "json"])

    adb_devices = parse_adb_devices(adb.stdout) if adb.exit_code == 0 else []
    services = parse_network_services(networksetup.stdout) if networksetup.exit_code == 0 else []
    interfaces = parse_ifconfig(ifconfig.stdout) if ifconfig.exit_code == 0 else []
    active_ipv4 = [
        info
        for info in interfaces
        if info.active and any(not ip.startswith("127.") for ip in info.ipv4)
    ]

    chrome_found = os.path.exists(chrome_bin) and os.access(chrome_bin, os.X_OK)
    aws_identity_ok = aws.exit_code == 0 and bool(aws.stdout)
    blockers: list[str] = []
    if not chrome_found:
        blockers.append("Chrome binary not found")
    if len(active_ipv4) < 2:
        blockers.append("Need at least two active non-loopback IPv4 interfaces for desktop path-change experiments")
    if not adb_devices:
        blockers.append("No Android device connected over ADB")
    if not aws_identity_ok:
        blockers.append("AWS caller identity is not available for automated public-origin provisioning")

    return HandoverReadiness(
        check_date=date.today().isoformat(),
        chrome_found=chrome_found,
        chrome_path=chrome_bin,
        adb_found=adb.found,
        adb_devices=adb_devices,
        android_ready=bool(adb_devices),
        network_services=services,
        active_ipv4_interfaces=active_ipv4,
        secondary_path_ready=len(active_ipv4) >= 2,
        aws_found=aws.found,
        aws_identity_ok=aws_identity_ok,
        aws_identity_redacted=aws.stdout if aws_identity_ok else "",
        disk_available_gib=disk_available_gib("."),
        blockers=blockers,
        commands={
            "adb_devices": summarize_command(adb, include_command_output),
            "network_services": summarize_command(networksetup, include_command_output),
            "ifconfig": summarize_command(ifconfig, include_command_output),
            "aws_identity": summarize_command(aws, include_command_output),
        },
    )


def emit_markdown(readiness: HandoverReadiness) -> str:
    active = ", ".join(f"{info.name}({','.join(info.ipv4)})" for info in readiness.active_ipv4_interfaces) or "-"
    blockers = "; ".join(readiness.blockers) or "-"
    lines = [
        "| check | value |",
        "| --- | --- |",
        f"| Chrome found | `{str(readiness.chrome_found).lower()}` |",
        f"| ADB found | `{str(readiness.adb_found).lower()}` |",
        f"| Android devices | `{', '.join(readiness.adb_devices) or '-'}` |",
        f"| active IPv4 interfaces | `{active}` |",
        f"| secondary path ready | `{str(readiness.secondary_path_ready).lower()}` |",
        f"| AWS identity OK | `{str(readiness.aws_identity_ok).lower()}` |",
        f"| disk available GiB | `{readiness.disk_available_gib}` |",
        f"| desktop handover ready | `{str(readiness.desktop_handover_ready).lower()}` |",
        f"| Android handover ready | `{str(readiness.android_ready).lower()}` |",
        f"| blockers | `{blockers}` |",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrome-bin", default="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument(
        "--include-command-output",
        action="store_true",
        help="include raw command stdout/stderr; omit for public artifacts",
    )
    args = parser.parse_args()

    readiness = build_readiness(args.chrome_bin, include_command_output=args.include_command_output)
    if args.format == "json":
        text = json.dumps(asdict(readiness), indent=2, ensure_ascii=False) + "\n"
    else:
        text = emit_markdown(readiness)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
