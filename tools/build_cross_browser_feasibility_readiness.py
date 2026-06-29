#!/usr/bin/env python3
"""Build a cross-browser feasibility readiness report for final CM trials."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from audit_final_browser_handover_trials import build_audit
from check_browser_cm_observability import build_readiness as build_observability_readiness
from check_handover_readiness import build_readiness as build_handover_readiness
from research_clock import utc_date_iso
from suggest_active_path_change_commands import collect_plan


DEFAULT_EXPERIMENTS = "data/experiment-results.csv"
DEFAULT_REQUIREMENTS = "data/final-browser-handover-required-trials.csv"
DEFAULT_RECOVERY_PLAN = "data/public-origin-recovery-plan-20260629.json"
DEFAULT_JSON_OUTPUT = "data/cross-browser-feasibility-readiness-20260629.json"
DEFAULT_CSV_OUTPUT = "data/cross-browser-feasibility-readiness-20260629.csv"
DEFAULT_MD_OUTPUT = "docs/results/cross-browser-feasibility-readiness-20260629.md"
DEFAULT_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
DEFAULT_SAFARI = "/Applications/Safari.app/Contents/MacOS/Safari"
DEFAULT_SAFARI_TP = "/Applications/Safari Technology Preview.app/Contents/MacOS/Safari Technology Preview"


CSV_FIELDS = [
    "candidate",
    "paper_role",
    "local_tooling",
    "path_change_gate",
    "public_origin_gate",
    "protocol_gap",
    "claim_boundary",
    "next_action",
]


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    def cell(value: object) -> str:
        return str(value if value is not None else "").replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def requirement_lookup(audit: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["requirement_id"]: row for row in audit.get("results", [])}


def requirement_progress(audit: dict[str, Any], requirement_id: str) -> str:
    row = requirement_lookup(audit).get(requirement_id)
    if not row:
        return "missing"
    return f"{row.get('matched_count', 0)}/{row.get('min_count', 0)}"


def candidate_by_id(path_plan: dict[str, Any], candidate_id: str) -> dict[str, Any]:
    for row in path_plan.get("candidates", []):
        if row.get("id") == candidate_id:
            return row
    return {"ready": False, "reason": "candidate missing"}


def public_origin_gate(recovery: dict[str, Any]) -> str:
    origin = recovery.get("public_origin") or {}
    classification = origin.get("classification", "missing")
    h3 = yes_no(bool(origin.get("has_h3_alt_svc")))
    return f"{classification}; h3_alt_svc={h3}"


def baseline_gate(recovery: dict[str, Any]) -> str:
    baseline = recovery.get("baseline") or {}
    if not baseline:
        return "missing"
    return f"{baseline.get('status', '-')}; {baseline.get('classification', '-')}"


def active_path_summary(path_plan: dict[str, Any]) -> str:
    summary = path_plan.get("summary") or {}
    ready = summary.get("ready_candidates") or []
    if ready:
        return "ready candidates: " + ", ".join(ready)
    reasons = [
        f"{row.get('id')}: {row.get('reason')}"
        for row in path_plan.get("candidates", [])
        if not row.get("ready")
    ]
    return "; ".join(reasons) or "not evaluated"


def build_rows(
    observability: Any,
    handover: Any,
    path_plan: dict[str, Any],
    recovery: dict[str, Any],
    audit: dict[str, Any],
) -> list[dict[str, str]]:
    mac_wifi = candidate_by_id(path_plan, "macos_wifi_power_cutover")
    mac_iphone = candidate_by_id(path_plan, "macos_wifi_to_iphone_usb_latent_failover")
    android_path = candidate_by_id(path_plan, "android_wifi_to_cellular_cutover")
    chrome_noheartbeat = requirement_progress(audit, "chrome-downlink-noheartbeat-active-cm")
    chrome_heartbeat = requirement_progress(audit, "chrome-downlink-heartbeat-active-cm")
    p1 = requirement_progress(audit, "p1-safari-or-android-feasibility")
    public_gate = public_origin_gate(recovery)

    return [
        {
            "candidate": "Chrome active public handover",
            "paper_role": "Main browser CM claim gate",
            "local_tooling": f"Chrome NetLog={yes_no(observability.chrome_netlog_ready)}; Chrome binary={yes_no(handover.chrome_found)}",
            "path_change_gate": f"desktop_path_ready={yes_no(handover.secondary_path_ready or mac_iphone.get('ready', False))}; {mac_wifi.get('reason', '-')}; latent={mac_iphone.get('reason', '-')}",
            "public_origin_gate": public_gate,
            "protocol_gap": f"noheartbeat={chrome_noheartbeat}; heartbeat={chrome_heartbeat}",
            "claim_boundary": "Only counts as browser CM if application H3, client path change, server tuple change, qlog path validation, one Chrome target QUIC session, and task completion align in the same row.",
            "next_action": "Recover public origin, restore a ready desktop path-change trigger, rerun fresh baseline, then run 3 no-heartbeat and 3 heartbeat rows.",
        },
        {
            "candidate": "Safari P1 feasibility",
            "paper_role": "Cross-browser feasibility with weaker browser-internal observability",
            "local_tooling": f"Safari WebDriver={yes_no(observability.safari_webdriver_ready)}; packet capture={yes_no(observability.packet_capture_tooling_ready)}; iOS rvictl={yes_no(observability.ios_remote_capture_candidate)}",
            "path_change_gate": f"desktop_path_ready={yes_no(handover.secondary_path_ready or mac_iphone.get('ready', False))}; latent={mac_iphone.get('reason', '-')}",
            "public_origin_gate": public_gate,
            "protocol_gap": f"p1={p1}",
            "claim_boundary": "Safari lacks Chrome NetLog-equivalent evidence in this harness, so a PASS_FEASIBILITY row must be described as server/qlog/client-path evidence, not full browser-internal session proof.",
            "next_action": "After public origin and Mac path-change are ready, run the Safari network-change wrapper and classify with missing-browser-netlog boundary.",
        },
        {
            "candidate": "Android Chrome P1 feasibility",
            "paper_role": "True mobile-platform feasibility beyond Mac+iPhone tethered failover",
            "local_tooling": f"ADB found={yes_no(handover.adb_found)}; Android device connected={yes_no(handover.android_ready)}",
            "path_change_gate": f"android_path_ready={yes_no(android_path.get('ready', False))}; {android_path.get('reason', '-')}",
            "public_origin_gate": public_gate,
            "protocol_gap": f"p1={p1}",
            "claim_boundary": "Android Chrome rows need Android before/after route snapshots plus server/qlog evidence; without browser-internal NetLog they remain feasibility evidence unless stronger telemetry is added.",
            "next_action": "Connect an Android device over ADB, verify cellular fallback, then run Android network-change wrapper after public origin recovery.",
        },
    ]


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    observability = build_observability_readiness(args.chrome_bin, args.safari_bin, args.safari_tp_bin)
    handover = build_handover_readiness(args.chrome_bin)
    path_plan = collect_plan(include_commands=False)
    recovery = load_json(Path(args.recovery_plan))
    audit = build_audit(Path(args.requirements), Path(args.experiments))
    rows = build_rows(observability, handover, path_plan, recovery, audit)

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "source_files": {
            "experiments": args.experiments,
            "requirements": args.requirements,
            "recovery_plan": args.recovery_plan,
        },
        "final_protocol": {
            "complete": audit["complete"],
            "complete_count": audit["complete_count"],
            "requirement_count": audit["requirement_count"],
            "blockers": audit["blockers"],
        },
        "current_gates": {
            "baseline": baseline_gate(recovery),
            "public_origin": public_origin_gate(recovery),
            "aws_identity": ((recovery.get("origin_access") or {}).get("aws") or {}).get("classification", "missing"),
            "active_path": active_path_summary(path_plan),
            "safari_webdriver_ready": observability.safari_webdriver_ready,
            "android_ready": handover.android_ready,
            "disk_available_gib": handover.disk_available_gib,
        },
        "observability": asdict(observability),
        "handover": {
            "check_date": handover.check_date,
            "chrome_found": handover.chrome_found,
            "adb_found": handover.adb_found,
            "adb_device_count": len(handover.adb_devices),
            "android_ready": handover.android_ready,
            "active_ipv4_interfaces": [
                {
                    "name": item.name,
                    "active": item.active,
                    "ipv4_count": len(item.ipv4),
                }
                for item in handover.active_ipv4_interfaces
            ],
            "secondary_path_ready": handover.secondary_path_ready,
            "aws_found": handover.aws_found,
            "aws_identity_ok": handover.aws_identity_ok,
            "disk_available_gib": handover.disk_available_gib,
            "blockers": handover.blockers,
        },
        "path_plan_summary": path_plan.get("summary", {}),
        "rows": rows,
        "safe_conclusion": (
            "Safari is currently closer than Android on local tooling, but neither can fill the P1 feasibility gate "
            "until the public origin and an active client path-change trigger are ready. Android additionally needs a connected ADB device."
        ),
    }


def write_outputs(report: dict[str, Any], json_output: Path, csv_output: Path, md_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    csv_output.parent.mkdir(parents=True, exist_ok=True)
    md_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with csv_output.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(report["rows"])
    md_output.write_text(emit_markdown(report), encoding="utf-8")


def emit_markdown(report: dict[str, Any]) -> str:
    gates = report["current_gates"]
    final = report["final_protocol"]
    rows = report["rows"]
    return "\n".join(
        [
            "# Cross-Browser Feasibility Readiness",
            "",
            f"Generated: `{report['generated']}`",
            "",
            "## Purpose",
            "",
            "This report fixes the current Chrome/Safari/Android readiness boundary for the final browser handover protocol. It is a readiness and claim-boundary artifact, not migration evidence.",
            "",
            "## Current Gates",
            "",
            markdown_table(
                ["gate", "value"],
                [
                    ["final protocol", f"{final['complete_count']}/{final['requirement_count']}"],
                    ["baseline", gates["baseline"]],
                    ["public origin", gates["public_origin"]],
                    ["AWS identity", gates["aws_identity"]],
                    ["active path", gates["active_path"]],
                    ["Safari WebDriver", yes_no(bool(gates["safari_webdriver_ready"]))],
                    ["Android ready", yes_no(bool(gates["android_ready"]))],
                    ["disk available GiB", gates["disk_available_gib"]],
                ],
            ),
            "",
            "## Candidate Matrix",
            "",
            markdown_table(
                [
                    "candidate",
                    "paper role",
                    "local tooling",
                    "path-change gate",
                    "public-origin gate",
                    "protocol gap",
                    "next action",
                ],
                [
                    [
                        row["candidate"],
                        row["paper_role"],
                        row["local_tooling"],
                        row["path_change_gate"],
                        row["public_origin_gate"],
                        row["protocol_gap"],
                        row["next_action"],
                    ]
                    for row in rows
                ],
            ),
            "",
            "## Claim Boundaries",
            "",
            markdown_table(
                ["candidate", "claim boundary"],
                [[row["candidate"], row["claim_boundary"]] for row in rows],
            ),
            "",
            "## Safe Conclusion",
            "",
            report["safe_conclusion"],
            "",
            "## Regeneration",
            "",
            f"`python3 tools/{Path(__file__).name}`",
            "",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--requirements", default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--recovery-plan", default=DEFAULT_RECOVERY_PLAN)
    parser.add_argument("--chrome-bin", default=DEFAULT_CHROME)
    parser.add_argument("--safari-bin", default=DEFAULT_SAFARI)
    parser.add_argument("--safari-tp-bin", default=DEFAULT_SAFARI_TP)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    parser.add_argument("--md-output", default=DEFAULT_MD_OUTPUT)
    args = parser.parse_args()

    report = build_report(args)
    write_outputs(report, Path(args.json_output), Path(args.csv_output), Path(args.md_output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
