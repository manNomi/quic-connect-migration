#!/usr/bin/env python3
"""Check readiness for the currently selected final handover trial."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from research_clock import utc_date_iso
from pathlib import Path
from typing import Any

from check_browser_cm_observability import build_readiness as build_observability_readiness
from check_controlled_public_config import check_key
from check_final_browser_handover_readiness import baseline_ready, command_preview, parse_env_file
from check_handover_readiness import build_readiness as build_handover_readiness
from check_public_origin_readiness import build_result as build_public_origin_readiness
from check_public_origin_readiness import payload as public_origin_payload
from report_artifact_storage import build_report as build_storage_report
from select_next_final_handover_trial import DEFAULT_EXPERIMENTS, build_selection
from suggest_active_path_change_commands import collect_plan


DEFAULT_CONFIG = "harness/config/controlled-public-origin.env"
DEFAULT_REQUIREMENTS = "data/final-browser-handover-required-trials.csv"
DEFAULT_OUTPUT = "docs/results/final-handover-next-trial-readiness-20260624.md"
DEFAULT_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEFAULT_SAFARI = "/Applications/Safari.app/Contents/MacOS/Safari"
DEFAULT_SAFARI_TP = "/Applications/Safari Technology Preview.app/Contents/MacOS/Safari Technology Preview"


def write_output(text: str, output_arg: str | None) -> None:
    if output_arg == "-":
        print(text, end="")
        return
    if output_arg:
        output = Path(output_arg)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def required_gate_names(next_trial: dict[str, Any] | None, check_local_files: bool = False) -> list[str]:
    if not next_trial:
        return []
    phase = next_trial["phase"]
    browser = next_trial["browser"]
    gates = [
        "next_trial_selected",
        "controlled_public_config_present",
        "public_origin_host_configured",
        "public_origin_url_configured",
        "tls_config_present",
        "disk_ready",
    ]
    if check_local_files:
        gates.extend(["tls_cert_file_exists", "tls_key_file_exists"])
    if browser == "Chrome":
        gates.append("chrome_ready")
    if browser == "Safari":
        gates.extend(["safari_webdriver_ready", "desktop_path_change_ready"])
    if browser == "Android Chrome":
        gates.append("android_adb_ready")
    if phase in {"active-network-change", "p1-feasibility"}:
        gates.extend(["baseline_summary_ready", "network_change_command_present"])
        if browser == "Chrome":
            gates.append("desktop_path_change_ready")
        if browser == "Android Chrome":
            gates.append("android_network_change_command_present")
    return gates


def evaluate_required_gates(required: list[str], gates: dict[str, bool]) -> tuple[bool, list[str]]:
    blockers = [name for name in required if not gates.get(name, False)]
    return not blockers, blockers


def valid_config_key(values: dict[str, str], key: str) -> bool:
    return check_key(key, values).valid


def build_readiness(args: argparse.Namespace) -> dict[str, Any]:
    redact_sensitive = bool(getattr(args, "redact_sensitive", False))
    selection_args = argparse.Namespace(
        experiments=args.experiments,
        requirements=args.requirements,
        config=args.config,
        use_local_config=args.use_local_config_for_plan,
        repetitions=args.repetitions,
        prefer_p1=args.prefer_p1,
        redact_sensitive=redact_sensitive,
    )
    selection = build_selection(selection_args)
    next_trial = selection["next_trial"]

    values = parse_env_file(Path(args.config))
    overrides = {
        "NETWORK_CHANGE_CMD": getattr(args, "network_change_cmd", ""),
        "ANDROID_NETWORK_CHANGE_CMD": getattr(args, "android_network_change_cmd", ""),
    }
    values.update({key: value for key, value in overrides.items() if value})
    handover = build_handover_readiness(args.chrome_bin)
    command_plan = collect_plan(include_commands=False)
    latent_iphone_usb_candidate_ready = bool(
        command_plan.get("summary", {}).get("latent_iphone_usb_candidate_ready")
    )
    allow_latent_secondary_path = bool(getattr(args, "allow_latent_secondary_path", False))
    desktop_path_change_ready = handover.secondary_path_ready or (
        allow_latent_secondary_path and latent_iphone_usb_candidate_ready
    )
    if handover.secondary_path_ready:
        desktop_path_change_mode = "active-secondary-path"
    elif allow_latent_secondary_path and latent_iphone_usb_candidate_ready:
        desktop_path_change_mode = "latent-iphone-usb-failover"
    else:
        desktop_path_change_mode = "not-ready"
    observability = build_observability_readiness(args.chrome_bin, args.safari_bin, args.safari_tp_bin)
    storage = build_storage_report(["repro/quic-go-min-repro/artifacts", "harness/results"], max_entries=5)
    baseline = baseline_ready(values.get("CONTROLLED_PUBLIC_BASELINE_SUMMARY", ""))
    disk_ready = float(storage["disk"]["free_gib"]) >= args.min_disk_gib

    network_change_cmd = values.get("NETWORK_CHANGE_CMD", "")
    android_network_change_cmd = values.get("ANDROID_NETWORK_CHANGE_CMD", "")
    tls_cert = values.get("TLS_CERT_FILE", "")
    tls_key = values.get("TLS_KEY_FILE", "")
    public_origin: dict[str, Any] | None = None
    if args.check_public_origin:
        public_url = values.get("PUBLIC_ORIGIN_URL", "")
        if public_url:
            try:
                result = build_public_origin_readiness(public_url, args.timeout)
                public_origin = public_origin_payload(result, redact_sensitive)
            except Exception as exc:  # noqa: BLE001 - readiness reports exact local failure.
                url = "<redacted-url>" if redact_sensitive else public_url
                public_origin = {"ok": False, "error": command_preview(str(exc)) if redact_sensitive else str(exc), "url": url}
        else:
            public_origin = {"ok": False, "error": "PUBLIC_ORIGIN_URL is not configured"}

    gates = {
        "next_trial_selected": next_trial is not None,
        "controlled_public_config_present": Path(args.config).exists(),
        "public_origin_host_configured": valid_config_key(values, "PUBLIC_ORIGIN_HOST"),
        "public_origin_url_configured": valid_config_key(values, "PUBLIC_ORIGIN_URL"),
        "tls_config_present": valid_config_key(values, "TLS_CERT_FILE") and valid_config_key(values, "TLS_KEY_FILE"),
        "tls_cert_file_exists": bool(tls_cert) and Path(tls_cert).exists(),
        "tls_key_file_exists": bool(tls_key) and Path(tls_key).exists(),
        "disk_ready": disk_ready,
        "chrome_ready": handover.chrome_found,
        "safari_webdriver_ready": observability.safari_webdriver_ready,
        "android_adb_ready": handover.android_ready,
        "desktop_secondary_path_ready": handover.secondary_path_ready,
        "latent_iphone_usb_candidate_ready": latent_iphone_usb_candidate_ready,
        "allow_latent_secondary_path": allow_latent_secondary_path,
        "desktop_path_change_ready": desktop_path_change_ready,
        "baseline_summary_ready": baseline["ready"],
        "network_change_command_present": valid_config_key(values, "NETWORK_CHANGE_CMD"),
        "android_network_change_command_present": valid_config_key(values, "ANDROID_NETWORK_CHANGE_CMD"),
    }
    if args.check_public_origin:
        gates["public_origin_live_ready"] = bool(public_origin and public_origin.get("ok"))

    required = required_gate_names(next_trial, args.check_local_files)
    if args.check_public_origin:
        required.append("public_origin_live_ready")
    ready, missing = evaluate_required_gates(required, gates)

    return {
        "generated": utc_date_iso(),
        "redact_sensitive": redact_sensitive,
        "config_path": args.config,
        "config_exists": Path(args.config).exists(),
        "check_local_files": args.check_local_files,
        "public_origin_url_preview": command_preview(values.get("PUBLIC_ORIGIN_URL", "")),
        "network_change_command_preview": command_preview(network_change_cmd),
        "android_network_change_command_preview": command_preview(android_network_change_cmd),
        "next_trial": next_trial,
        "required_gates": required,
        "gates": gates,
        "ready": ready,
        "missing_required_gates": missing,
        "selection": {
            "complete_count": selection["complete_count"],
            "requirement_count": selection["requirement_count"],
            "protocol_complete": selection["protocol_complete"],
            "blockers": selection["blockers"],
        },
        "disk": {
            "free_gib": storage["disk"]["free_gib"],
            "min_required_gib": args.min_disk_gib,
            "artifact_total_bytes": storage["total_artifact_bytes"],
        },
        "handover": {
            "chrome_found": handover.chrome_found,
            "secondary_path_ready": handover.secondary_path_ready,
            "latent_iphone_usb_candidate_ready": latent_iphone_usb_candidate_ready,
            "allow_latent_secondary_path": allow_latent_secondary_path,
            "desktop_path_change_ready": desktop_path_change_ready,
            "desktop_path_change_mode": desktop_path_change_mode,
            "android_ready": handover.android_ready,
            "active_ipv4_interfaces": [asdict(item) for item in handover.active_ipv4_interfaces],
        },
        "observability": {
            "safari_webdriver_ready": observability.safari_webdriver_ready,
            "chrome_netlog_ready": observability.chrome_netlog_ready,
            "packet_capture_tooling_ready": observability.packet_capture_tooling_ready,
        },
        "baseline": baseline,
        "public_origin": public_origin,
    }


def emit_markdown(readiness: dict[str, Any]) -> str:
    next_trial = readiness["next_trial"]
    missing = readiness["missing_required_gates"] or ["-"]
    if readiness.get("redact_sensitive"):
        active = ", ".join(
            f"{item['name']}(<redacted:{len(item['ipv4'])} address{'es' if len(item['ipv4']) != 1 else ''}>)"
            for item in readiness["handover"]["active_ipv4_interfaces"]
        ) or "-"
    else:
        active = ", ".join(
            f"{item['name']}({','.join(item['ipv4'])})"
            for item in readiness["handover"]["active_ipv4_interfaces"]
        ) or "-"
    lines = [
        "# Final Handover Next Trial Readiness",
        "",
        f"Generated: `{readiness['generated']}`",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| ready | `{'yes' if readiness['ready'] else 'no'}` |",
        f"| config path | `{readiness['config_path']}` |",
        f"| config exists | `{'yes' if readiness['config_exists'] else 'no'}` |",
        f"| check local files | `{'yes' if readiness['check_local_files'] else 'no'}` |",
        f"| next trial | `{next_trial['trial_id'] if next_trial else '-'}` |",
        f"| next phase | `{next_trial['phase'] if next_trial else '-'}` |",
        f"| next browser | `{next_trial['browser'] if next_trial else '-'}` |",
        f"| final completion | `{readiness['selection']['complete_count']}/{readiness['selection']['requirement_count']}` |",
        f"| disk free GiB | `{readiness['disk']['free_gib']}` |",
        f"| active IPv4 interfaces | `{active}` |",
        f"| desktop path-change mode | `{readiness['handover']['desktop_path_change_mode']}` |",
        f"| public origin URL | `{readiness['public_origin_url_preview'] or '-'}` |",
        "",
        "## Required Gates",
        "",
        "| gate | value | required |",
        "| --- | --- | --- |",
    ]
    required = set(readiness["required_gates"])
    for name, value in readiness["gates"].items():
        lines.append(f"| `{name}` | `{'yes' if value else 'no'}` | `{'yes' if name in required else 'no'}` |")
    lines.extend(["", "## Missing Required Gates", ""])
    lines.extend(f"- {item}" for item in missing)
    if next_trial:
        lines.extend(
            [
                "",
                "## Next Trial Commands",
                "",
                "Server/origin terminal:",
                "",
                "```bash",
                next_trial["server_command"],
                "```",
                "",
                "Browser/client terminal:",
                "",
                "```bash",
                next_trial["client_command"],
                "```",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--requirements", default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--use-local-config-for-plan", action="store_true")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--prefer-p1", choices=["safari", "android", "both"], default="safari")
    parser.add_argument("--chrome-bin", default=DEFAULT_CHROME)
    parser.add_argument("--safari-bin", default=DEFAULT_SAFARI)
    parser.add_argument("--safari-tp-bin", default=DEFAULT_SAFARI_TP)
    parser.add_argument("--min-disk-gib", type=float, default=7.0)
    parser.add_argument(
        "--check-local-files",
        action="store_true",
        help="require TLS files to exist on the machine running this checker; use on the public origin host",
    )
    parser.add_argument("--check-public-origin", action="store_true")
    parser.add_argument("--allow-latent-secondary-path", action="store_true")
    parser.add_argument("--network-change-cmd", default="")
    parser.add_argument("--android-network-change-cmd", default="")
    parser.add_argument("--redact-sensitive", action="store_true")
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    readiness = build_readiness(args)
    text = json.dumps(readiness, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(readiness)
    write_output(text, args.output)
    return 0 if readiness["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
