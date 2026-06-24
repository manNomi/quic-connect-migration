#!/usr/bin/env python3
"""Check browser and packet-observability readiness for HTTP/3 CM experiments."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from research_clock import utc_date_iso
from pathlib import Path


@dataclass
class CommandResult:
    command: list[str]
    found: bool
    exit_code: int | None
    stdout: str
    stderr: str


@dataclass
class BrowserPath:
    name: str
    path: str
    found: bool
    executable: bool
    version: str


@dataclass
class BrowserCMObservability:
    check_date: str
    chrome: BrowserPath
    safari: BrowserPath
    safari_technology_preview: BrowserPath
    safaridriver: CommandResult
    tcpdump: CommandResult
    rvictl: CommandResult
    networksetup: CommandResult
    route: CommandResult
    ifconfig: CommandResult
    chrome_netlog_ready: bool
    safari_webdriver_ready: bool
    packet_capture_tooling_ready: bool
    ios_remote_capture_candidate: bool
    blockers: list[str]


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


def app_version(app_path: str) -> str:
    if not Path(app_path).exists():
        return ""
    mdls = run_command(["mdls", "-raw", "-name", "kMDItemVersion", app_path])
    if mdls.exit_code == 0 and mdls.stdout and mdls.stdout != "(null)":
        return mdls.stdout
    plist = Path(app_path) / "Contents" / "Info.plist"
    if plist.exists():
        defaults = run_command(["defaults", "read", plist.as_posix(), "CFBundleShortVersionString"])
        if defaults.exit_code == 0:
            return defaults.stdout
    return ""


def browser_path(name: str, path: str) -> BrowserPath:
    found = Path(path).exists()
    executable = found and os.access(path, os.X_OK)
    app_path = path.split("/Contents/MacOS/", 1)[0] if "/Contents/MacOS/" in path else path
    return BrowserPath(name, path, found, executable, app_version(app_path))


def summarize_command(result: CommandResult, include_output: bool) -> CommandResult:
    if include_output:
        return result
    return CommandResult(result.command, result.found, result.exit_code, "", "")


def build_readiness(
    chrome_bin: str,
    safari_bin: str,
    safari_tp_bin: str,
    include_command_output: bool = False,
) -> BrowserCMObservability:
    chrome = browser_path("Chrome", chrome_bin)
    safari = browser_path("Safari", safari_bin)
    safari_tp = browser_path("Safari Technology Preview", safari_tp_bin)
    safaridriver = run_command(["safaridriver", "--version"])
    tcpdump = run_command(["tcpdump", "--version"])
    rvictl = run_command(["rvictl", "-h"])
    networksetup = run_command(["networksetup", "-listallnetworkservices"])
    route = run_command(["route", "-n", "get", "default"])
    ifconfig = run_command(["ifconfig"])

    chrome_netlog_ready = chrome.executable
    safari_webdriver_ready = safari.executable and safaridriver.found and safaridriver.exit_code in (0, 1)
    packet_capture_tooling_ready = tcpdump.found and route.exit_code == 0 and ifconfig.exit_code == 0
    ios_remote_capture_candidate = rvictl.found
    blockers: list[str] = []
    if not chrome_netlog_ready:
        blockers.append("Chrome executable not found for NetLog-based browser H3 experiments")
    if safari.found and not safari_webdriver_ready:
        blockers.append("Safari exists but safaridriver is not ready")
    if not safari.found and not safari_tp.found:
        blockers.append("Safari or Safari Technology Preview not found")
    if safari.found and not packet_capture_tooling_ready:
        blockers.append("Safari experiments need packet/route observability, but packet tooling is incomplete")
    if safari.found:
        blockers.append("Safari does not provide a Chrome NetLog-equivalent artifact in this harness; use packet capture and server-side qlog")
    if not ios_remote_capture_candidate:
        blockers.append("rvictl not found; iOS remote virtual interface capture is not ready")

    return BrowserCMObservability(
        check_date=utc_date_iso(),
        chrome=chrome,
        safari=safari,
        safari_technology_preview=safari_tp,
        safaridriver=summarize_command(safaridriver, include_command_output),
        tcpdump=summarize_command(tcpdump, include_command_output),
        rvictl=summarize_command(rvictl, include_command_output),
        networksetup=summarize_command(networksetup, include_command_output),
        route=summarize_command(route, include_command_output),
        ifconfig=summarize_command(ifconfig, include_command_output),
        chrome_netlog_ready=chrome_netlog_ready,
        safari_webdriver_ready=safari_webdriver_ready,
        packet_capture_tooling_ready=packet_capture_tooling_ready,
        ios_remote_capture_candidate=ios_remote_capture_candidate,
        blockers=blockers,
    )


def command_summary(result: CommandResult) -> str:
    if not result.found:
        return "missing"
    if result.exit_code is None:
        return "unknown"
    text = result.stdout or result.stderr
    first_line = text.splitlines()[0] if text else ""
    return f"exit={result.exit_code}" + (f", {first_line}" if first_line else "")


def emit_markdown(readiness: BrowserCMObservability) -> str:
    blockers = "; ".join(readiness.blockers) or "-"
    rows = [
        "| check | value |",
        "| --- | --- |",
        f"| Chrome found | `{str(readiness.chrome.found).lower()}` |",
        f"| Chrome version | `{readiness.chrome.version or '-'}` |",
        f"| Chrome NetLog ready | `{str(readiness.chrome_netlog_ready).lower()}` |",
        f"| Safari found | `{str(readiness.safari.found).lower()}` |",
        f"| Safari version | `{readiness.safari.version or '-'}` |",
        f"| Safari TP found | `{str(readiness.safari_technology_preview.found).lower()}` |",
        f"| Safari TP version | `{readiness.safari_technology_preview.version or '-'}` |",
        f"| safaridriver | `{command_summary(readiness.safaridriver)}` |",
        f"| Safari WebDriver ready | `{str(readiness.safari_webdriver_ready).lower()}` |",
        f"| tcpdump | `{command_summary(readiness.tcpdump)}` |",
        f"| rvictl | `{command_summary(readiness.rvictl)}` |",
        f"| packet capture tooling ready | `{str(readiness.packet_capture_tooling_ready).lower()}` |",
        f"| iOS remote capture candidate | `{str(readiness.ios_remote_capture_candidate).lower()}` |",
        f"| blockers | `{blockers}` |",
    ]
    return "\n".join(rows) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chrome-bin", default="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    parser.add_argument("--safari-bin", default="/Applications/Safari.app/Contents/MacOS/Safari")
    parser.add_argument(
        "--safari-technology-preview-bin",
        default="/Applications/Safari Technology Preview.app/Contents/MacOS/Safari Technology Preview",
    )
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument(
        "--include-command-output",
        action="store_true",
        help="include raw command stdout/stderr; omit for public artifacts",
    )
    args = parser.parse_args()

    readiness = build_readiness(
        args.chrome_bin,
        args.safari_bin,
        args.safari_technology_preview_bin,
        include_command_output=args.include_command_output,
    )
    if args.format == "json":
        text = json.dumps(asdict(readiness), indent=2, ensure_ascii=False) + "\n"
    else:
        text = emit_markdown(readiness)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
