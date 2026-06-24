#!/usr/bin/env python3
"""Build a public-safe worksheet for filling controlled-public origin config."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from check_controlled_public_config import (
    ACTIVE_REQUIRED,
    ANDROID_REQUIRED,
    BASELINE_REQUIRED,
    DEFAULT_CONFIG,
    build_report,
)


DEFAULT_OUTPUT = "docs/results/controlled-public-config-worksheet-20260624.md"


@dataclass(frozen=True)
class FieldInfo:
    key: str
    stage: str
    owner: str
    privacy: str
    expected_shape: str
    used_by: str


FIELD_INFO = {
    "PUBLIC_ORIGIN_HOST": FieldInfo(
        "PUBLIC_ORIGIN_HOST",
        "baseline",
        "origin/client",
        "private lab domain",
        "DNS hostname controlled by the researcher",
        "server TLS hostname, browser URL host, public readiness checks",
    ),
    "PUBLIC_ORIGIN_PORT": FieldInfo(
        "PUBLIC_ORIGIN_PORT",
        "baseline",
        "origin/client",
        "safe if generic",
        "integer TCP/UDP port, usually 443",
        "server listener and browser origin URL planning",
    ),
    "PUBLIC_ORIGIN_URL": FieldInfo(
        "PUBLIC_ORIGIN_URL",
        "baseline",
        "client",
        "private lab URL",
        "https URL whose host equals PUBLIC_ORIGIN_HOST",
        "Chrome no-change application H3 baseline",
    ),
    "TLS_CERT_FILE": FieldInfo(
        "TLS_CERT_FILE",
        "baseline",
        "origin host",
        "private filesystem path",
        "absolute path to WebPKI fullchain certificate",
        "quic-go controlled public server wrapper",
    ),
    "TLS_KEY_FILE": FieldInfo(
        "TLS_KEY_FILE",
        "baseline",
        "origin host",
        "secret filesystem path",
        "absolute path to private key readable only on origin host",
        "quic-go controlled public server wrapper",
    ),
    "LISTEN_ADDR": FieldInfo(
        "LISTEN_ADDR",
        "baseline",
        "origin host",
        "safe if generic",
        "IP:port listener address, usually 0.0.0.0:443",
        "UDP QUIC/H3 listener",
    ),
    "TCP_ADDR": FieldInfo(
        "TCP_ADDR",
        "baseline",
        "origin host",
        "safe if generic",
        "IP:port listener address, usually 0.0.0.0:443",
        "TCP HTTPS Alt-Svc bootstrap listener",
    ),
    "ALT_SVC": FieldInfo(
        "ALT_SVC",
        "baseline",
        "origin host",
        "safe if generic",
        'Alt-Svc value containing h3 and a port, e.g. h3=":443"; ma=60',
        "browser HTTP/3 advertisement",
    ),
    "CHROME_BIN": FieldInfo(
        "CHROME_BIN",
        "baseline",
        "client",
        "local filesystem path",
        "absolute path to Chrome executable",
        "Chrome CDP/NetLog wrappers",
    ),
    "PUBLIC_ORIGIN_NETWORK_CHANGE_URL": FieldInfo(
        "PUBLIC_ORIGIN_NETWORK_CHANGE_URL",
        "active",
        "client",
        "private lab URL",
        "long-running https workload URL whose host equals PUBLIC_ORIGIN_HOST",
        "active network-change workload",
    ),
    "CONTROLLED_PUBLIC_BASELINE_SUMMARY": FieldInfo(
        "CONTROLLED_PUBLIC_BASELINE_SUMMARY",
        "active",
        "client",
        "local artifact path",
        "path to baseline summary JSON with status=PASS",
        "precondition gate before active network-change",
    ),
    "NETWORK_CHANGE_AFTER_SECONDS": FieldInfo(
        "NETWORK_CHANGE_AFTER_SECONDS",
        "active",
        "client",
        "safe if generic",
        "integer delay before running the explicit path-change command",
        "network-change wrapper timing",
    ),
    "NETWORK_CHANGE_CMD": FieldInfo(
        "NETWORK_CHANGE_CMD",
        "active",
        "client",
        "dangerous local command",
        "explicit command approved by the operator for this machine/network",
        "desktop active path-change trigger",
    ),
    "ANDROID_NETWORK_CHANGE_CMD": FieldInfo(
        "ANDROID_NETWORK_CHANGE_CMD",
        "android",
        "client/android",
        "dangerous local command",
        "explicit ADB or host command approved by the operator",
        "Android Chrome P1 feasibility path-change trigger",
    ),
}


def ordered_keys() -> list[str]:
    return list(dict.fromkeys(BASELINE_REQUIRED + ACTIVE_REQUIRED + ANDROID_REQUIRED))


def field_stage(key: str) -> str:
    if key in BASELINE_REQUIRED:
        return "baseline"
    if key in ACTIVE_REQUIRED:
        return "active"
    if key in ANDROID_REQUIRED:
        return "android"
    return "optional"


def build_worksheet(config_path: Path, check_files: bool) -> dict[str, Any]:
    report = build_report(config_path, check_files)
    key_checks = {item["key"]: item for item in report["key_checks"]}
    rows = []
    for key in ordered_keys():
        info = FIELD_INFO.get(
            key,
            FieldInfo(key, field_stage(key), "unknown", "unknown", "non-empty value", "controlled-public harness"),
        )
        check = key_checks[key]
        rows.append(
            {
                **asdict(info),
                "present": check["present"],
                "placeholder": check["placeholder"],
                "valid": check["valid"],
                "detail": check["detail"],
                "next_action": next_action(check, info),
            }
        )

    baseline_missing = [row["key"] for row in rows if row["stage"] == "baseline" and not row["valid"]]
    active_missing = [row["key"] for row in rows if row["stage"] == "active" and not row["valid"]]
    android_missing = [row["key"] for row in rows if row["stage"] == "android" and not row["valid"]]
    if baseline_missing:
        next_step = "fill_baseline_config"
    elif active_missing:
        next_step = "run_baseline_then_fill_active_config"
    elif android_missing:
        next_step = "optional_android_config_missing"
    else:
        next_step = "config_ready_for_all_declared_stages"

    return {
        "check_date": date.today().isoformat(),
        "config_path": config_path.as_posix(),
        "check_files": check_files,
        "config_exists": report["config_exists"],
        "baseline_config_ready": report["baseline_config_ready"],
        "active_network_change_config_ready": report["active_network_change_config_ready"],
        "android_network_change_config_ready": report["android_network_change_config_ready"],
        "next_step": next_step,
        "baseline_missing": baseline_missing,
        "active_missing": active_missing,
        "android_missing": android_missing,
        "fields": rows,
        "public_safe": True,
    }


def next_action(check: dict[str, Any], info: FieldInfo) -> str:
    if check["valid"]:
        return "ready"
    if not check["present"]:
        return f"add {info.key} to the local env file"
    if check["placeholder"]:
        return f"replace placeholder with a real {info.expected_shape}"
    if check["detail"] == "path_missing":
        return "fix the path or run this check on the host where the path exists"
    return f"fix value shape: {check['detail']}"


def emit_markdown(worksheet: dict[str, Any]) -> str:
    lines = [
        "# Controlled Public Config Worksheet",
        "",
        f"Generated: `{worksheet['check_date']}`",
        "",
        "This worksheet is public-safe. It reports presence, validity, ownership, and next actions without printing actual domains, TLS paths, private keys, or network-change commands.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| config path | `{worksheet['config_path']}` |",
        f"| config exists | `{'yes' if worksheet['config_exists'] else 'no'}` |",
        f"| check local files | `{'yes' if worksheet['check_files'] else 'no'}` |",
        f"| baseline config ready | `{'yes' if worksheet['baseline_config_ready'] else 'no'}` |",
        f"| active network-change config ready | `{'yes' if worksheet['active_network_change_config_ready'] else 'no'}` |",
        f"| Android network-change config ready | `{'yes' if worksheet['android_network_change_config_ready'] else 'no'}` |",
        f"| next step | `{worksheet['next_step']}` |",
        "",
        "## Missing By Stage",
        "",
        "| stage | keys |",
        "| --- | --- |",
        f"| baseline | `{', '.join(worksheet['baseline_missing']) or '-'}` |",
        f"| active | `{', '.join(worksheet['active_missing']) or '-'}` |",
        f"| android | `{', '.join(worksheet['android_missing']) or '-'}` |",
        "",
        "## Fields",
        "",
        "| stage | key | owner | privacy | expected shape | valid | next action |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in worksheet["fields"]:
        lines.append(
            f"| `{row['stage']}` | `{row['key']}` | {row['owner']} | {row['privacy']} | {row['expected_shape']} | `{'yes' if row['valid'] else 'no'}` | {row['next_action']} |"
        )
    lines.extend(
        [
            "",
            "## Run Order",
            "",
            "1. Copy `harness/config/controlled-public-origin.env.example` to the ignored local config path.",
            "2. Fill baseline fields on the public origin host and client machine.",
            "3. Run `python3 tools/check_controlled_public_config.py --require-baseline-ready`.",
            "4. Run the controlled-public H3 baseline and keep the `status=PASS` summary.",
            "5. Fill active network-change fields only after choosing a real secondary path and an explicit command.",
            "6. Run final handover trials only after readiness and artifact bundle gates pass.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--check-files", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    worksheet = build_worksheet(Path(args.config), args.check_files)
    text = json.dumps(worksheet, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(worksheet)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
