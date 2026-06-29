#!/usr/bin/env python3
"""Check readiness for the final browser/mobile HTTP/3 handover protocol."""

from __future__ import annotations

import argparse
import json
import shlex
from dataclasses import asdict, dataclass
from research_clock import utc_date_iso
from pathlib import Path
from typing import Any

from audit_final_browser_handover_trials import build_audit as build_final_trial_audit
from check_browser_cm_observability import build_readiness as build_observability_readiness
from check_controlled_public_experiment_readiness import load_summary
from check_handover_readiness import build_readiness as build_handover_readiness
from check_public_origin_readiness import build_result as build_public_origin_readiness
from report_artifact_storage import build_report as build_storage_report
from report_artifact_storage import human_size
from suggest_active_path_change_commands import collect_plan


DEFAULT_CONFIG = "harness/config/controlled-public-origin.env"
DEFAULT_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEFAULT_SAFARI = "/Applications/Safari.app/Contents/MacOS/Safari"
DEFAULT_SAFARI_TP = "/Applications/Safari Technology Preview.app/Contents/MacOS/Safari Technology Preview"


@dataclass
class ConfigReadiness:
    path: str
    exists: bool
    public_origin_url_present: bool
    public_origin_network_change_url_present: bool
    baseline_summary_present: bool
    network_change_command_present: bool
    android_network_change_command_present: bool
    public_origin_url_preview: str
    network_change_command_preview: str
    android_network_change_command_preview: str


def command_preview(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return ""
    return "<configured>"


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        try:
            parts = shlex.split(line, comments=True, posix=True)
        except ValueError:
            parts = [line]
        for part in parts:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            if key:
                values[key] = value
    return values


def config_readiness(config_path: Path, overrides: dict[str, str]) -> tuple[ConfigReadiness, dict[str, str]]:
    from check_controlled_public_config import check_key

    values = parse_env_file(config_path)
    values.update({key: value for key, value in overrides.items() if value})
    network_change_cmd = values.get("NETWORK_CHANGE_CMD", "")
    android_network_change_cmd = values.get("ANDROID_NETWORK_CHANGE_CMD", "")
    public_origin_url = values.get("PUBLIC_ORIGIN_NETWORK_CHANGE_URL") or values.get("PUBLIC_ORIGIN_URL", "")
    readiness = ConfigReadiness(
        path=config_path.as_posix(),
        exists=config_path.exists(),
        public_origin_url_present=check_key("PUBLIC_ORIGIN_URL", values).valid,
        public_origin_network_change_url_present=check_key("PUBLIC_ORIGIN_NETWORK_CHANGE_URL", values).valid,
        baseline_summary_present=check_key("CONTROLLED_PUBLIC_BASELINE_SUMMARY", values).valid,
        network_change_command_present=check_key("NETWORK_CHANGE_CMD", values).valid,
        android_network_change_command_present=check_key("ANDROID_NETWORK_CHANGE_CMD", values).valid,
        public_origin_url_preview=command_preview(public_origin_url),
        network_change_command_preview=command_preview(network_change_cmd),
        android_network_change_command_preview=command_preview(android_network_change_cmd),
    )
    return readiness, values


def baseline_ready(path: str) -> dict[str, Any]:
    summary = load_summary(path)
    return {
        "path": summary.path,
        "exists": summary.exists,
        "status": summary.status,
        "classification": summary.classification,
        "ready": summary.exists and summary.status.startswith("PASS"),
        "error": summary.error,
    }


def desktop_path_change_status(
    *,
    secondary_path_ready: bool,
    allow_latent_secondary_path: bool,
    latent_iphone_usb_candidate_ready: bool,
) -> dict[str, Any]:
    if secondary_path_ready:
        return {
            "ready": True,
            "mode": "active-secondary-path",
            "claim_boundary": "alternate client path was active before the trigger",
        }
    if allow_latent_secondary_path and latent_iphone_usb_candidate_ready:
        return {
            "ready": True,
            "mode": "latent-iphone-usb-failover",
            "claim_boundary": "iPhone USB activates after Wi-Fi loss; report as delayed OS failover, not simultaneous active-path migration",
        }
    return {
        "ready": False,
        "mode": "not-ready",
        "claim_boundary": "no desktop client path-change trigger is currently ready",
    }


def active_interface_summary(items: list[dict[str, Any]], redact_sensitive: bool = False) -> str:
    summaries: list[str] = []
    for item in items:
        name = str(item.get("name") or "-")
        ipv4 = item.get("ipv4")
        addresses = [str(address) for address in ipv4] if isinstance(ipv4, list) else []
        if redact_sensitive:
            count = len(addresses)
            suffix = "es" if count != 1 else ""
            address_text = f"<redacted:{count} address{suffix}>" if count else "-"
        else:
            address_text = ",".join(addresses)
        summaries.append(f"{name}({address_text})")
    return ", ".join(summaries) or "-"


def redact_public_origin(public_origin: dict[str, Any] | None) -> dict[str, Any] | None:
    if public_origin is None:
        return None
    redacted = dict(public_origin)
    for key in ["url", "host", "tls_subject", "tls_issuer", "alt_svc_headers"]:
        if redacted.get(key):
            redacted[key] = f"<redacted-{key.replace('_', '-')}>"
    if isinstance(redacted.get("dns_addresses"), list):
        redacted["dns_addresses"] = ["<redacted-address>"] if redacted["dns_addresses"] else []
    if isinstance(redacted.get("errors"), list):
        redacted["errors"] = ["<redacted-error>" for _ in redacted["errors"]]
    redacted["redacted"] = True
    return redacted


def redact_payload(readiness: dict[str, Any]) -> dict[str, Any]:
    payload = json.loads(json.dumps(readiness))
    interfaces = payload.get("handover", {}).get("active_ipv4_interfaces")
    if isinstance(interfaces, list):
        for item in interfaces:
            if isinstance(item, dict) and isinstance(item.get("ipv4"), list):
                item["ipv4"] = ["<redacted-address>" for _ in item["ipv4"]]
    payload["public_origin"] = redact_public_origin(payload.get("public_origin"))
    payload["redacted"] = True
    return payload


def build_readiness(args: argparse.Namespace) -> dict[str, Any]:
    overrides = {
        "PUBLIC_ORIGIN_URL": args.public_origin_url,
        "PUBLIC_ORIGIN_NETWORK_CHANGE_URL": args.public_origin_network_change_url,
        "CONTROLLED_PUBLIC_BASELINE_SUMMARY": args.baseline_summary,
        "NETWORK_CHANGE_CMD": args.network_change_cmd,
        "ANDROID_NETWORK_CHANGE_CMD": args.android_network_change_cmd,
    }
    config, values = config_readiness(Path(args.config), overrides)
    final_trials = build_final_trial_audit(Path(args.required_trials), Path(args.experiments))
    handover = build_handover_readiness(args.chrome_bin)
    command_plan = collect_plan(include_commands=False)
    latent_iphone_usb_candidate_ready = bool(
        command_plan.get("summary", {}).get("latent_iphone_usb_candidate_ready")
    )
    desktop_path_change = desktop_path_change_status(
        secondary_path_ready=handover.secondary_path_ready,
        allow_latent_secondary_path=args.allow_latent_secondary_path,
        latent_iphone_usb_candidate_ready=latent_iphone_usb_candidate_ready,
    )
    observability = build_observability_readiness(args.chrome_bin, args.safari_bin, args.safari_tp_bin)
    storage = build_storage_report(["repro/quic-go-min-repro/artifacts", "harness/results"], max_entries=5)
    baseline = baseline_ready(values.get("CONTROLLED_PUBLIC_BASELINE_SUMMARY", ""))
    public_origin: dict[str, Any] | None = None
    if args.check_public_origin:
        target_url = values.get("PUBLIC_ORIGIN_NETWORK_CHANGE_URL") or values.get("PUBLIC_ORIGIN_URL", "")
        if target_url:
            try:
                public_origin_result = build_public_origin_readiness(target_url, args.timeout)
                public_origin = asdict(public_origin_result)
                public_origin["ok"] = public_origin_result.ok
            except Exception as exc:  # noqa: BLE001 - readiness must preserve exact local failure.
                public_origin = {"ok": False, "error": str(exc), "url": target_url}
        else:
            public_origin = {"ok": False, "error": "public origin URL is not configured"}

    disk_ready = float(storage["disk"]["free_gib"]) >= args.min_disk_gib
    chrome_protocol_ready = (
        handover.chrome_found
        and desktop_path_change["ready"]
        and config.network_change_command_present
        and baseline["ready"]
        and disk_ready
    )
    safari_protocol_ready = (
        observability.safari_webdriver_ready
        and config.network_change_command_present
        and baseline["ready"]
        and disk_ready
    )
    android_protocol_ready = (
        handover.android_ready
        and (config.android_network_change_command_present or config.network_change_command_present)
        and baseline["ready"]
        and disk_ready
    )
    public_origin_gate_ready = True
    if args.check_public_origin:
        public_origin_gate_ready = bool(public_origin and public_origin.get("ok"))

    blockers: list[str] = []
    if not config.exists:
        blockers.append("controlled public config file is missing")
    if not config.public_origin_url_present:
        blockers.append("PUBLIC_ORIGIN_URL is not configured")
    if not config.public_origin_network_change_url_present:
        blockers.append("PUBLIC_ORIGIN_NETWORK_CHANGE_URL is not configured")
    if not baseline["ready"]:
        blockers.append("controlled public baseline summary is missing or not PASS/PASS_FEASIBILITY")
    if not config.network_change_command_present:
        blockers.append("NETWORK_CHANGE_CMD is not configured")
    if not desktop_path_change["ready"]:
        blockers.append("desktop path-change trigger is not ready")
    if not handover.android_ready:
        blockers.append("Android device is not connected over ADB")
    if not disk_ready:
        blockers.append(f"disk free space is below {args.min_disk_gib} GiB")
    if not final_trials["complete"]:
        blockers.append("final browser handover trial protocol is not complete")
    if args.check_public_origin and not public_origin_gate_ready:
        blockers.append("controlled public origin readiness check failed")

    return {
        "check_date": utc_date_iso(),
        "config": asdict(config),
        "baseline": baseline,
        "disk": {
            "free_gib": storage["disk"]["free_gib"],
            "min_required_gib": args.min_disk_gib,
            "ready": disk_ready,
            "artifact_total_bytes": storage["total_artifact_bytes"],
            "artifact_total_human": human_size(int(storage["total_artifact_bytes"])),
        },
        "handover": {
            "desktop_handover_ready": handover.desktop_handover_ready,
            "android_ready": handover.android_ready,
            "secondary_path_ready": handover.secondary_path_ready,
            "allow_latent_secondary_path": args.allow_latent_secondary_path,
            "latent_iphone_usb_candidate_ready": latent_iphone_usb_candidate_ready,
            "desktop_path_change_ready": desktop_path_change["ready"],
            "desktop_path_change_mode": desktop_path_change["mode"],
            "desktop_path_change_claim_boundary": desktop_path_change["claim_boundary"],
            "active_ipv4_interfaces": [asdict(item) for item in handover.active_ipv4_interfaces],
        },
        "observability": {
            "chrome_netlog_ready": observability.chrome_netlog_ready,
            "safari_webdriver_ready": observability.safari_webdriver_ready,
            "packet_capture_tooling_ready": observability.packet_capture_tooling_ready,
        },
        "public_origin": public_origin,
        "final_trials": {
            "complete": final_trials["complete"],
            "complete_count": final_trials["complete_count"],
            "requirement_count": final_trials["requirement_count"],
            "blockers": final_trials["blockers"],
        },
        "protocol_ready": {
            "chrome": chrome_protocol_ready and public_origin_gate_ready,
            "safari": safari_protocol_ready and public_origin_gate_ready,
            "android_chrome": android_protocol_ready and public_origin_gate_ready,
        },
        "can_finish_goal_now": False,
        "blockers": blockers,
    }


def emit_markdown(readiness: dict[str, Any], redact_sensitive: bool = False) -> str:
    active = active_interface_summary(readiness["handover"]["active_ipv4_interfaces"], redact_sensitive)
    protocol = readiness["protocol_ready"]
    config = readiness["config"]
    baseline = readiness["baseline"]
    final_trials = readiness["final_trials"]
    blockers = readiness["blockers"] or ["-"]
    lines = [
        "# Final Browser Handover Readiness",
        "",
        f"Generated: `{readiness['check_date']}`",
        "",
        "## Summary",
        "",
        "| check | value |",
        "| --- | --- |",
        f"| Chrome protocol ready | `{'yes' if protocol['chrome'] else 'no'}` |",
        f"| Safari protocol ready | `{'yes' if protocol['safari'] else 'no'}` |",
        f"| Android Chrome protocol ready | `{'yes' if protocol['android_chrome'] else 'no'}` |",
        f"| final trial completion | `{final_trials['complete_count']}/{final_trials['requirement_count']}` |",
        f"| can finish goal now | `{'yes' if readiness['can_finish_goal_now'] else 'no'}` |",
        "",
        "## Gates",
        "",
        "| gate | value |",
        "| --- | --- |",
        f"| config present | `{'yes' if config['exists'] else 'no'}` |",
        f"| public origin URL | `{config['public_origin_url_preview'] or '-'}` |",
        f"| baseline summary ready | `{'yes' if baseline['ready'] else 'no'}` |",
        f"| baseline status | `{baseline['status'] or baseline['error'] or '-'}` |",
        f"| network-change command present | `{'yes' if config['network_change_command_present'] else 'no'}` |",
        f"| Android network-change command present | `{'yes' if config['android_network_change_command_present'] else 'no'}` |",
        f"| active IPv4 interfaces | `{active}` |",
        f"| secondary path ready | `{'yes' if readiness['handover']['secondary_path_ready'] else 'no'}` |",
        f"| latent iPhone USB candidate ready | `{'yes' if readiness['handover']['latent_iphone_usb_candidate_ready'] else 'no'}` |",
        f"| allow latent secondary path | `{'yes' if readiness['handover']['allow_latent_secondary_path'] else 'no'}` |",
        f"| desktop path-change ready | `{'yes' if readiness['handover']['desktop_path_change_ready'] else 'no'}` |",
        f"| desktop path-change mode | `{readiness['handover']['desktop_path_change_mode']}` |",
        f"| Android ready | `{'yes' if readiness['handover']['android_ready'] else 'no'}` |",
        f"| Safari WebDriver ready | `{'yes' if readiness['observability']['safari_webdriver_ready'] else 'no'}` |",
        f"| disk ready | `{'yes' if readiness['disk']['ready'] else 'no'}` |",
        f"| disk free GiB | `{readiness['disk']['free_gib']}` |",
        "",
        "## Blockers",
        "",
    ]
    lines.extend(f"- {blocker}" for blocker in blockers)
    if final_trials["blockers"]:
        lines.extend(["", "## Final Trial Blockers", ""])
        lines.extend(f"- {blocker}" for blocker in final_trials["blockers"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--public-origin-url", default="")
    parser.add_argument("--public-origin-network-change-url", default="")
    parser.add_argument("--baseline-summary", default="")
    parser.add_argument("--network-change-cmd", default="")
    parser.add_argument("--android-network-change-cmd", default="")
    parser.add_argument("--required-trials", default="data/final-browser-handover-required-trials.csv")
    parser.add_argument("--experiments", default="data/experiment-results.csv")
    parser.add_argument("--chrome-bin", default=DEFAULT_CHROME)
    parser.add_argument("--safari-bin", default=DEFAULT_SAFARI)
    parser.add_argument("--safari-tp-bin", default=DEFAULT_SAFARI_TP)
    parser.add_argument("--min-disk-gib", type=float, default=7.0)
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--check-public-origin", action="store_true")
    parser.add_argument(
        "--allow-latent-secondary-path",
        action="store_true",
        help="allow delayed Wi-Fi-to-iPhone-USB failover as the desktop path-change trigger",
    )
    parser.add_argument("--redact-sensitive", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    args = parser.parse_args()

    readiness = build_readiness(args)
    output_readiness = redact_payload(readiness) if args.redact_sensitive else readiness
    text = (
        json.dumps(output_readiness, indent=2, ensure_ascii=False) + "\n"
        if args.format == "json"
        else emit_markdown(output_readiness, redact_sensitive=args.redact_sensitive)
    )
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if any(readiness["protocol_ready"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
