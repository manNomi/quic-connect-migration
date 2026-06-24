#!/usr/bin/env python3
"""Build a readiness matrix for every planned final browser handover trial."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from research_clock import utc_date_iso
from pathlib import Path
from typing import Any

from audit_final_browser_handover_trials import build_audit, load_rows
from check_browser_cm_observability import build_readiness as build_observability_readiness
from check_final_browser_handover_readiness import baseline_ready, command_preview, parse_env_file
from check_handover_readiness import build_readiness as build_handover_readiness
from check_next_final_handover_trial_readiness import DEFAULT_CHROME, DEFAULT_SAFARI, DEFAULT_SAFARI_TP
from plan_final_browser_handover_runs import DEFAULT_CONFIG, DEFAULT_REQUIRED_TRIALS, PUBLIC_TEMPLATE_VALUES, make_plan
from report_artifact_storage import build_report as build_storage_report
from select_next_final_handover_trial import DEFAULT_EXPERIMENTS


DEFAULT_OUTPUT = "docs/results/final-protocol-readiness-matrix-20260624.md"
DEFAULT_CSV_OUTPUT = "data/final-protocol-readiness-matrix-20260624.csv"


def existing_trial_ids(experiments_path: Path) -> set[str]:
    return {row["trial_id"] for row in load_rows(experiments_path)}


def incomplete_requirement_ids(audit: dict[str, Any]) -> set[str]:
    return {row["requirement_id"] for row in audit["results"] if not row["complete"]}


def required_gates_for_trial(plan: dict[str, Any], check_local_files: bool = False) -> list[str]:
    phase = plan["phase"]
    browser = plan["browser"]
    gates = [
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
        gates.extend(["safari_webdriver_ready", "desktop_secondary_path_ready"])
    if browser == "Android Chrome":
        gates.append("android_adb_ready")
    if phase in {"active-network-change", "p1-feasibility"}:
        gates.extend(["baseline_summary_ready", "network_change_command_present"])
        if browser == "Chrome":
            gates.append("desktop_secondary_path_ready")
        if browser == "Android Chrome":
            gates.append("android_network_change_command_present")
    return gates


def build_global_gates(args: argparse.Namespace) -> dict[str, bool]:
    values = parse_env_file(Path(args.config))
    handover = build_handover_readiness(args.chrome_bin)
    observability = build_observability_readiness(args.chrome_bin, args.safari_bin, args.safari_tp_bin)
    storage = build_storage_report(["repro/quic-go-min-repro/artifacts", "harness/results"], max_entries=5)
    tls_cert = values.get("TLS_CERT_FILE", "")
    tls_key = values.get("TLS_KEY_FILE", "")
    network_change_cmd = values.get("NETWORK_CHANGE_CMD", "")
    android_network_change_cmd = values.get("ANDROID_NETWORK_CHANGE_CMD", "")
    return {
        "controlled_public_config_present": Path(args.config).exists(),
        "public_origin_host_configured": bool(values.get("PUBLIC_ORIGIN_HOST")),
        "public_origin_url_configured": bool(values.get("PUBLIC_ORIGIN_URL")),
        "tls_config_present": bool(tls_cert) and bool(tls_key),
        "tls_cert_file_exists": bool(tls_cert) and Path(tls_cert).exists(),
        "tls_key_file_exists": bool(tls_key) and Path(tls_key).exists(),
        "disk_ready": float(storage["disk"]["free_gib"]) >= args.min_disk_gib,
        "chrome_ready": handover.chrome_found,
        "safari_webdriver_ready": observability.safari_webdriver_ready,
        "android_adb_ready": handover.android_ready,
        "desktop_secondary_path_ready": handover.secondary_path_ready,
        "baseline_summary_ready": baseline_ready(values.get("CONTROLLED_PUBLIC_BASELINE_SUMMARY", ""))["ready"],
        "network_change_command_present": bool(network_change_cmd.strip()) and network_change_cmd.strip() != "...",
        "android_network_change_command_present": bool(android_network_change_cmd.strip())
        and android_network_change_cmd.strip() != "...",
    }


def plan_values(config: str, use_local_config: bool) -> dict[str, str]:
    values = dict(PUBLIC_TEMPLATE_VALUES)
    if use_local_config:
        values.update({key: value for key, value in parse_env_file(Path(config)).items() if value})
    return values


def row_state(plan: dict[str, Any], existing: set[str], incomplete_requirements: set[str], missing_gates: list[str]) -> str:
    if plan["trial_id"] in existing:
        return "recorded"
    if plan["requirement_id"] not in incomplete_requirements:
        return "requirement-complete"
    if not missing_gates:
        return "ready"
    return "blocked"


def build_matrix(args: argparse.Namespace) -> dict[str, Any]:
    audit = build_audit(Path(args.requirements), Path(args.experiments))
    incomplete = incomplete_requirement_ids(audit)
    existing = existing_trial_ids(Path(args.experiments))
    plans = [asdict(plan) for plan in make_plan(plan_values(args.config, args.use_local_config), args.repetitions, args.prefer_p1)]
    gates = build_global_gates(args)
    values = parse_env_file(Path(args.config))
    rows: list[dict[str, Any]] = []
    for index, plan in enumerate(plans, start=1):
        required = required_gates_for_trial(plan, args.check_local_files)
        missing = [gate for gate in required if not gates.get(gate, False)]
        rows.append(
            {
                "order": index,
                "trial_id": plan["trial_id"],
                "requirement_id": plan["requirement_id"],
                "phase": plan["phase"],
                "browser": plan["browser"],
                "heartbeat": plan["heartbeat"],
                "required_gates": required,
                "missing_gates": missing,
                "ready": not missing,
                "state": row_state(plan, existing, incomplete, missing),
            }
        )

    state_counts: dict[str, int] = {}
    for row in rows:
        state_counts[row["state"]] = state_counts.get(row["state"], 0) + 1

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "config_path": args.config,
        "config_exists": Path(args.config).exists(),
        "public_origin_url_preview": command_preview(values.get("PUBLIC_ORIGIN_URL", "")),
        "check_local_files": args.check_local_files,
        "final_protocol_complete": audit["complete"],
        "complete_count": audit["complete_count"],
        "requirement_count": audit["requirement_count"],
        "planned_trial_count": len(rows),
        "state_counts": state_counts,
        "global_gates": gates,
        "rows": rows,
    }


def emit_markdown(matrix: dict[str, Any]) -> str:
    lines = [
        "# Final Protocol Readiness Matrix",
        "",
        f"Generated: `{matrix['generated']}`",
        "",
        "This matrix is public-safe. It evaluates every planned final browser handover execution against the current local readiness gates without printing private domains, TLS paths, or network-change commands.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| final protocol complete | `{'yes' if matrix['final_protocol_complete'] else 'no'}` |",
        f"| complete requirements | `{matrix['complete_count']}/{matrix['requirement_count']}` |",
        f"| planned executions | `{matrix['planned_trial_count']}` |",
        f"| config exists | `{'yes' if matrix['config_exists'] else 'no'}` |",
        f"| public origin URL | `{matrix['public_origin_url_preview'] or '-'}` |",
        f"| state counts | `{matrix['state_counts']}` |",
        "",
        "## Global Gates",
        "",
        "| gate | value |",
        "| --- | --- |",
    ]
    for gate, value in matrix["global_gates"].items():
        lines.append(f"| `{gate}` | `{'yes' if value else 'no'}` |")

    lines.extend(
        [
            "",
            "## Planned Trial Readiness",
            "",
            "| order | trial | phase | browser | state | missing gates |",
            "| ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for row in matrix["rows"]:
        missing = ", ".join(row["missing_gates"]) or "-"
        lines.append(
            f"| {row['order']} | `{row['trial_id']}` | {row['phase']} | {row['browser']} | `{row['state']}` | `{missing}` |"
        )
    return "\n".join(lines).rstrip() + "\n"


def write_csv(matrix: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "order",
        "trial_id",
        "requirement_id",
        "phase",
        "browser",
        "heartbeat",
        "ready",
        "state",
        "required_gates",
        "missing_gates",
    ]
    with output.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for row in matrix["rows"]:
            writer.writerow({**row, "required_gates": ";".join(row["required_gates"]), "missing_gates": ";".join(row["missing_gates"])})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--requirements", default=DEFAULT_REQUIRED_TRIALS)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--use-local-config", action="store_true")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--prefer-p1", choices=["safari", "android", "both"], default="safari")
    parser.add_argument("--chrome-bin", default=DEFAULT_CHROME)
    parser.add_argument("--safari-bin", default=DEFAULT_SAFARI)
    parser.add_argument("--safari-tp-bin", default=DEFAULT_SAFARI_TP)
    parser.add_argument("--min-disk-gib", type=float, default=5.0)
    parser.add_argument("--check-local-files", action="store_true")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    matrix = build_matrix(args)
    if args.csv_output:
        write_csv(matrix, Path(args.csv_output))
    text = json.dumps(matrix, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(matrix)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
