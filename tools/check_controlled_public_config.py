#!/usr/bin/env python3
"""Validate the local controlled-public origin config without exposing secrets."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from check_final_browser_handover_readiness import parse_env_file


DEFAULT_CONFIG = "harness/config/controlled-public-origin.env"
DEFAULT_OUTPUT = "docs/results/controlled-public-config-check-20260624.md"

BASELINE_REQUIRED = [
    "PUBLIC_ORIGIN_HOST",
    "PUBLIC_ORIGIN_PORT",
    "PUBLIC_ORIGIN_URL",
    "TLS_CERT_FILE",
    "TLS_KEY_FILE",
    "LISTEN_ADDR",
    "TCP_ADDR",
    "ALT_SVC",
    "CHROME_BIN",
]

ACTIVE_REQUIRED = [
    "PUBLIC_ORIGIN_NETWORK_CHANGE_URL",
    "CONTROLLED_PUBLIC_BASELINE_SUMMARY",
    "NETWORK_CHANGE_AFTER_SECONDS",
    "NETWORK_CHANGE_CMD",
]

ANDROID_REQUIRED = [
    "ANDROID_NETWORK_CHANGE_CMD",
]


@dataclass
class KeyCheck:
    key: str
    present: bool
    placeholder: bool
    valid: bool
    detail: str


def is_placeholder(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    lowered = stripped.lower()
    return lowered in {"...", "todo", "changeme", "change-me", "example"} or "example.com" in lowered


def valid_port(value: str) -> bool:
    try:
        port = int(value)
    except ValueError:
        return False
    return 1 <= port <= 65535


def valid_int(value: str) -> bool:
    try:
        int(value)
        return True
    except ValueError:
        return False


def valid_url(value: str, host: str | None = None) -> bool:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.netloc:
        return False
    if host and parsed.hostname and parsed.hostname != host:
        return False
    return True


def valid_alt_svc(value: str) -> bool:
    return "h3" in value and re.search(r":\d+", value) is not None


def check_key(key: str, values: dict[str, str]) -> KeyCheck:
    value = values.get(key, "")
    present = key in values and value.strip() != ""
    placeholder = is_placeholder(value)
    valid = present and not placeholder
    detail = "present"
    if not present:
        detail = "missing"
    elif placeholder:
        detail = "placeholder_or_empty"

    host = values.get("PUBLIC_ORIGIN_HOST")
    if valid and key == "PUBLIC_ORIGIN_PORT":
        valid = valid_port(value)
        detail = "valid_port" if valid else "invalid_port"
    elif valid and key in {"PUBLIC_ORIGIN_URL", "PUBLIC_ORIGIN_NETWORK_CHANGE_URL"}:
        valid = valid_url(value, host)
        detail = "valid_https_url" if valid else "invalid_https_url_or_host_mismatch"
    elif valid and key == "NETWORK_CHANGE_AFTER_SECONDS":
        valid = valid_int(value)
        detail = "valid_integer" if valid else "invalid_integer"
    elif valid and key == "ALT_SVC":
        valid = valid_alt_svc(value)
        detail = "valid_h3_alt_svc" if valid else "invalid_h3_alt_svc"
    elif valid and key == "CHROME_BIN":
        valid = Path(value).exists()
        detail = "path_exists" if valid else "path_missing"
    return KeyCheck(key=key, present=present, placeholder=placeholder, valid=valid, detail=detail)


def build_report(config_path: Path, check_files: bool = False) -> dict[str, Any]:
    values = parse_env_file(config_path)
    keys = list(dict.fromkeys(BASELINE_REQUIRED + ACTIVE_REQUIRED + ANDROID_REQUIRED))
    checks = [check_key(key, values) for key in keys]
    by_key = {check.key: check for check in checks}

    if check_files:
        for key in ["TLS_CERT_FILE", "TLS_KEY_FILE", "CONTROLLED_PUBLIC_BASELINE_SUMMARY"]:
            if key not in by_key:
                continue
            value = values.get(key, "")
            if by_key[key].valid and not Path(value).exists():
                by_key[key].valid = False
                by_key[key].detail = "path_missing"
            elif by_key[key].valid:
                by_key[key].detail = "path_exists"

    baseline_ready = config_path.exists() and all(by_key[key].valid for key in BASELINE_REQUIRED)
    active_ready = baseline_ready and all(by_key[key].valid for key in ACTIVE_REQUIRED)
    android_ready = active_ready and all(by_key[key].valid for key in ANDROID_REQUIRED)
    blockers: list[str] = []
    if not config_path.exists():
        blockers.append("controlled public config file is missing")
    for key in BASELINE_REQUIRED:
        if not by_key[key].valid:
            blockers.append(f"baseline config key not ready: {key} ({by_key[key].detail})")
    for key in ACTIVE_REQUIRED:
        if not by_key[key].valid:
            blockers.append(f"active network-change config key not ready: {key} ({by_key[key].detail})")

    return {
        "check_date": date.today().isoformat(),
        "config_path": config_path.as_posix(),
        "config_exists": config_path.exists(),
        "check_files": check_files,
        "baseline_config_ready": baseline_ready,
        "active_network_change_config_ready": active_ready,
        "android_network_change_config_ready": android_ready,
        "key_checks": [asdict(by_key[key]) for key in keys],
        "blockers": blockers,
        "public_safe": True,
    }


def emit_markdown(report: dict[str, Any]) -> str:
    blockers = report["blockers"] or ["-"]
    lines = [
        "# Controlled Public Config Check",
        "",
        f"Generated: `{report['check_date']}`",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| config path | `{report['config_path']}` |",
        f"| config exists | `{'yes' if report['config_exists'] else 'no'}` |",
        f"| check local files | `{'yes' if report['check_files'] else 'no'}` |",
        f"| baseline config ready | `{'yes' if report['baseline_config_ready'] else 'no'}` |",
        f"| active network-change config ready | `{'yes' if report['active_network_change_config_ready'] else 'no'}` |",
        f"| Android network-change config ready | `{'yes' if report['android_network_change_config_ready'] else 'no'}` |",
        f"| public safe | `{'yes' if report['public_safe'] else 'no'}` |",
        "",
        "## Key Checks",
        "",
        "| key | present | placeholder | valid | detail |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in report["key_checks"]:
        lines.append(
            f"| `{item['key']}` | `{'yes' if item['present'] else 'no'}` | `{'yes' if item['placeholder'] else 'no'}` | `{'yes' if item['valid'] else 'no'}` | `{item['detail']}` |"
        )
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in blockers)
    lines.extend(
        [
            "",
            "This report intentionally does not print actual domain names, certificate paths, private key paths, or network-change commands.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--check-files", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--require-baseline-ready", action="store_true")
    parser.add_argument("--require-active-ready", action="store_true")
    args = parser.parse_args()

    report = build_report(Path(args.config), args.check_files)
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if args.require_active_ready and not report["active_network_change_config_ready"]:
        return 1
    if args.require_baseline_ready and not report["baseline_config_ready"]:
        return 1
    if not report["baseline_config_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
