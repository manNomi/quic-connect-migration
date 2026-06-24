#!/usr/bin/env python3
"""Open a URL in Android Chrome through ADB and record a sanitized result."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class CommandResult:
    name: str
    command: list[str]
    found: bool
    exit_code: int | None
    stdout: str
    stderr: str


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sanitize_command(command: list[str], serial: str) -> list[str]:
    if not serial:
        return command
    return ["<android-serial>" if item == serial else item for item in command]


def sanitize_text(text: str | bytes | None, serial: str, include_output: bool) -> str:
    if not include_output:
        return ""
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")
    value = text or ""
    return value.replace(serial, "<android-serial>") if serial else value


def run_command(name: str, command: list[str], serial: str, include_output: bool, timeout: int) -> CommandResult:
    found = shutil.which(command[0]) is not None
    if not found:
        return CommandResult(name, sanitize_command(command, serial), False, None, "", "command not found")
    try:
        proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return CommandResult(
            name,
            sanitize_command(command, serial),
            True,
            proc.returncode,
            sanitize_text(proc.stdout, serial, include_output),
            sanitize_text(proc.stderr, serial, include_output),
        )
    except subprocess.TimeoutExpired as exc:
        return CommandResult(
            name,
            sanitize_command(command, serial),
            True,
            124,
            sanitize_text(exc.stdout, serial, include_output),
            sanitize_text(exc.stderr or "timeout", serial, include_output),
        )


def parse_devices(output: str) -> list[str]:
    devices: list[str] = []
    for line in output.splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices


def adb_prefix(adb_bin: str, serial: str) -> list[str]:
    return [adb_bin, "-s", serial] if serial else [adb_bin]


def run_navigation(args: argparse.Namespace) -> dict[str, Any]:
    started_at = now_utc()
    device_query = run_command("adb_devices", [args.adb_bin, "devices"], "", True, args.command_timeout)
    devices = parse_devices(device_query.stdout)
    serial = args.serial or (devices[0] if len(devices) == 1 else "")
    steps: list[CommandResult] = [
        CommandResult(
            "adb_devices",
            [args.adb_bin, "devices"],
            device_query.found,
            device_query.exit_code,
            sanitize_text(device_query.stdout, serial, args.include_command_output),
            sanitize_text(device_query.stderr, serial, args.include_command_output),
        )
    ]

    if not serial:
        completed_at = now_utc()
        return {
            "started_at": started_at,
            "completed_at": completed_at,
            "url": args.url,
            "package": args.package,
            "device_count": len(devices),
            "device_selected": False,
            "navigation_ok": False,
            "wait_seconds": args.wait_seconds,
            "error": "no_unique_android_device",
            "steps": [asdict(item) for item in steps],
        }

    prefix = adb_prefix(args.adb_bin, serial)
    if args.force_stop:
        steps.append(
            run_command(
                "force_stop",
                [*prefix, "shell", "am", "force-stop", args.package],
                serial,
                args.include_command_output,
                args.command_timeout,
            )
        )

    steps.append(
        run_command(
            "start_url",
            [
                *prefix,
                "shell",
                "am",
                "start",
                "-W",
                "-a",
                "android.intent.action.VIEW",
                "-d",
                args.url,
                "-p",
                args.package,
            ],
            serial,
            args.include_command_output,
            args.command_timeout,
        )
    )
    time.sleep(args.wait_seconds)
    completed_at = now_utc()
    start_step = next((item for item in steps if item.name == "start_url"), None)
    navigation_ok = bool(start_step and start_step.exit_code == 0)
    return {
        "started_at": started_at,
        "completed_at": completed_at,
        "url": args.url,
        "package": args.package,
        "device_count": len(devices),
        "device_selected": True,
        "device_label": "device-1",
        "navigation_ok": navigation_ok,
        "wait_seconds": args.wait_seconds,
        "error": "" if navigation_ok else "android_chrome_navigation_failed",
        "steps": [asdict(item) for item in steps],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--adb-bin", default="adb")
    parser.add_argument("--serial", default="")
    parser.add_argument("--package", default="com.android.chrome")
    parser.add_argument("--wait-seconds", type=float, default=18)
    parser.add_argument("--command-timeout", type=int, default=30)
    parser.add_argument("--force-stop", action="store_true")
    parser.add_argument("--include-command-output", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()

    result = run_navigation(args)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if result["navigation_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
