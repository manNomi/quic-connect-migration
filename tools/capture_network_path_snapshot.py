#!/usr/bin/env python3
"""Capture local route/interface state for browser network-change experiments."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import socket
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from network_ipv4 import has_usable_ipv4


@dataclass
class CommandResult:
    command: list[str]
    found: bool
    exit_code: int | None
    stdout: str
    stderr: str


@dataclass
class InterfaceInfo:
    name: str
    active: bool
    ipv4: list[str]


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_command(args: list[str], timeout: int = 5) -> CommandResult:
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


def endpoint(raw_url: str) -> tuple[str, int]:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"expected URL with hostname: {raw_url}")
    return parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80)


def resolve_first_address(host: str, port: int) -> str:
    try:
        for family, _, _, _, sockaddr in socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP):
            if family in (socket.AF_INET, socket.AF_INET6):
                return str(sockaddr[0])
    except OSError:
        return ""
    return ""


def parse_key_value_route(output: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw in output.splitlines():
        line = raw.strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip().replace(" ", "_")] = value.strip()
    return data


def parse_linux_route(output: str) -> dict[str, str]:
    data: dict[str, str] = {}
    tokens = output.split()
    if "dev" in tokens:
        data["interface"] = tokens[tokens.index("dev") + 1]
    if "via" in tokens:
        data["gateway"] = tokens[tokens.index("via") + 1]
    if "src" in tokens:
        data["source"] = tokens[tokens.index("src") + 1]
    if tokens:
        data["raw_first_line"] = " ".join(tokens)
    return data


def route_snapshot(label: str, target: str) -> dict[str, object]:
    route_result: CommandResult | None = None
    if shutil.which("route"):
        args = ["route", "-n", "get", target]
        route_result = run_command(args)
        if route_result.exit_code == 0 or not shutil.which("ip"):
            parsed = parse_key_value_route(route_result.stdout) if route_result.exit_code == 0 else {}
            return {"label": label, "tool": "route", "parsed": parsed, "command": asdict(route_result)}
    if shutil.which("ip"):
        args = ["ip", "route", "get", target]
        result = run_command(args)
        parsed = parse_linux_route(result.stdout) if result.exit_code == 0 else {}
        payload: dict[str, object] = {"label": label, "tool": "ip", "parsed": parsed, "command": asdict(result)}
        if route_result is not None:
            payload["route_command_fallback"] = asdict(route_result)
        return payload
    result = CommandResult(["route/ip"], False, None, "", "route and ip commands not found")
    return {"label": label, "tool": "", "parsed": {}, "command": asdict(result)}


def public_ip_probe(url: str, timeout: int) -> dict[str, object] | None:
    if not url:
        return None
    result = run_command(["curl", "-sS", "--max-time", str(timeout), url], timeout=timeout + 1)
    return {"url": url, "command": asdict(result), "ip": result.stdout.strip() if result.exit_code == 0 else ""}


def build_snapshot(url: str, include_public_ip_url: str, timeout: int) -> dict[str, object]:
    host, port = endpoint(url)
    first_address = resolve_first_address(host, port)
    ifconfig = run_command(["ifconfig"], timeout=timeout)
    interfaces = parse_ifconfig(ifconfig.stdout) if ifconfig.exit_code == 0 else []
    active_ipv4 = [
        asdict(info)
        for info in interfaces
        if info.active and has_usable_ipv4(info.ipv4)
    ]
    target_for_route = first_address or host
    return {
        "captured_at": now_utc(),
        "url": url,
        "host": host,
        "port": port,
        "resolved_first_address": first_address,
        "active_ipv4_interfaces": active_ipv4,
        "default_route": route_snapshot("default", "default"),
        "target_route": route_snapshot("target", target_for_route),
        "ifconfig_command": asdict(ifconfig),
        "public_ip_probe": public_ip_probe(include_public_ip_url, timeout),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--public-ip-url", default="")
    parser.add_argument("--timeout", type=int, default=5)
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        snapshot = build_snapshot(args.url, args.public_ip_url, args.timeout)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    text = json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
