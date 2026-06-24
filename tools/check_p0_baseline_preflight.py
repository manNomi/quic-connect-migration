#!/usr/bin/env python3
"""Check whether the P0 controlled-public baseline may start artifact capture."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from build_final_handover_trial_packet import build_packet
from build_p0_unblock_status import build_status as build_p0_status
from check_controlled_public_config import build_report as build_config_report
from check_next_final_handover_trial_readiness import DEFAULT_CHROME, DEFAULT_CONFIG, DEFAULT_SAFARI, DEFAULT_SAFARI_TP
from plan_final_browser_handover_runs import DEFAULT_REQUIRED_TRIALS
from research_clock import utc_date_iso
from select_next_final_handover_trial import DEFAULT_EXPERIMENTS


DEFAULT_MATRIX = "data/final-protocol-readiness-matrix-20260624.csv"
DEFAULT_SCORECARD = "data/final-trial-acceptance-scorecard-20260624.csv"
DEFAULT_OUTPUT = "docs/results/p0-baseline-preflight-check-20260624.md"
DEFAULT_CSV_OUTPUT = "data/p0-baseline-preflight-check-20260624.csv"


CSV_FIELDS = ["check", "required", "ok", "evidence", "next_action"]


@dataclass(frozen=True)
class PreflightCheck:
    check: str
    required: bool
    ok: bool
    evidence: str
    next_action: str


def packet_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        experiments=args.experiments,
        requirements=args.requirements,
        config=args.config,
        use_local_config=False,
        repetitions=args.repetitions,
        prefer_p1=args.prefer_p1,
        chrome_bin=args.chrome_bin,
        safari_bin=args.safari_bin,
        safari_tp_bin=args.safari_tp_bin,
        min_disk_gib=args.min_disk_gib,
        check_local_files=args.check_local_files,
        check_public_origin=args.check_public_origin,
        timeout=args.timeout,
    )


def bool_text(value: bool) -> str:
    return "yes" if value else "no"


def check_row(name: str, required: bool, ok: bool, evidence: str, next_action: str) -> PreflightCheck:
    return PreflightCheck(name, required, ok, evidence, next_action)


def allowed_next_action(go: bool, needed_now: list[str], missing_required: list[str], config_ready: bool) -> str:
    if go:
        return "start-origin-server-and-client-baseline-capture"
    if needed_now:
        return "fill-private-controlled-public-config"
    if not config_ready:
        return "fix-baseline-config-values"
    if missing_required:
        return "fix-missing-required-gates: " + ";".join(missing_required)
    return "review-preflight-state"


def build_preflight(args: argparse.Namespace) -> dict[str, Any]:
    packet = build_packet(packet_args(args))
    p0_status = build_p0_status(Path(args.matrix), Path(args.scorecard))
    config = build_config_report(Path(args.config), check_files=args.check_local_files)

    next_trial = packet["next_trial"] or {}
    needed_now = list(packet.get("missing_required_gates") or [])
    p0_needed_now = [row["unblock_item"] for row in p0_status["rows"] if row["status"] == "needed-now"]
    missing_required = list(packet.get("missing_required_gates") or [])
    gates = packet.get("gate_values") or {}
    next_trial_is_baseline = next_trial.get("trial_id") == "controlled-public-chrome-h3-baseline-001"
    next_trial_ready = bool(packet.get("next_trial_ready"))
    config_ready = bool(config.get("baseline_config_ready"))
    go = bool(next_trial_ready and next_trial_is_baseline and config_ready and not (p0_needed_now or needed_now))
    next_action = allowed_next_action(go, p0_needed_now or needed_now, missing_required, config_ready)

    checks = [
        check_row(
            "next_trial_selected",
            True,
            bool(next_trial),
            f"trial_id={next_trial.get('trial_id', '-')}",
            "run select_next_final_handover_trial.py" if not next_trial else "-",
        ),
        check_row(
            "next_trial_is_p0_baseline",
            True,
            next_trial_is_baseline,
            f"trial_id={next_trial.get('trial_id', '-')}",
            "do not use this guard for non-P0 trials",
        ),
        check_row(
            "baseline_config_ready",
            True,
            config_ready,
            f"config_exists={config.get('config_exists')}; baseline_config_ready={config_ready}",
            "fill harness/config/controlled-public-origin.env and rerun check_controlled_public_config.py",
        ),
        check_row(
            "needed_now_gates_cleared",
            True,
            not p0_needed_now,
            "needed_now=" + (";".join(p0_needed_now) if p0_needed_now else "-"),
            "clear all needed-now gates in p0-unblock-status",
        ),
        check_row(
            "next_trial_ready",
            True,
            next_trial_ready,
            "missing_required=" + (";".join(missing_required) if missing_required else "-"),
            "run check_next_final_handover_trial_readiness.py and fix missing gates",
        ),
        check_row(
            "disk_ready",
            True,
            bool(gates.get("disk_ready")),
            f"disk_ready={bool_text(bool(gates.get('disk_ready')))}",
            "free disk before heavy NetLog/qlog capture",
        ),
        check_row(
            "chrome_ready",
            True,
            bool(gates.get("chrome_ready")),
            f"chrome_ready={bool_text(bool(gates.get('chrome_ready')))}",
            "install or configure Chrome binary",
        ),
    ]

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "go_for_p0_baseline_capture": go,
        "allowed_next_action": next_action,
        "next_trial": next_trial,
        "packet_state": packet.get("state"),
        "needed_now_gates": p0_needed_now,
        "missing_required_gates": missing_required,
        "checks": [asdict(item) for item in checks],
    }


def emit_markdown(preflight: dict[str, Any]) -> str:
    next_trial = preflight["next_trial"]
    needed_now = preflight["needed_now_gates"] or ["-"]
    missing = preflight["missing_required_gates"] or ["-"]
    lines = [
        "# P0 Baseline Preflight Check",
        "",
        f"Generated: `{preflight['generated']}`",
        "",
        "This check is public-safe. It decides whether the P0 controlled-public Chrome baseline may start server/client artifact capture.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| go for capture | `{'yes' if preflight['go_for_p0_baseline_capture'] else 'no'}` |",
        f"| allowed next action | `{preflight['allowed_next_action']}` |",
        f"| next trial | `{next_trial.get('trial_id', '-')}` |",
        f"| packet state | `{preflight['packet_state']}` |",
        f"| needed-now gates | `{'; '.join(needed_now)}` |",
        f"| missing required gates | `{'; '.join(missing)}` |",
        "",
        "## Checks",
        "",
        "| check | required | ok | evidence | next action |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in preflight["checks"]:
        lines.append(
            f"| `{item['check']}` | `{'yes' if item['required'] else 'no'}` | `{'yes' if item['ok'] else 'no'}` | `{item['evidence']}` | {item['next_action']} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- If `go for capture` is `no`, do not start the origin server or Chrome client capture stages.",
            "- This guard should be run immediately before stage 2 of the P0 baseline execution packet.",
            "- A `yes` here still only permits the baseline trial; it does not claim browser connection migration.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def write_csv(preflight: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(preflight["checks"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", default=DEFAULT_MATRIX)
    parser.add_argument("--scorecard", default=DEFAULT_SCORECARD)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--requirements", default=DEFAULT_REQUIRED_TRIALS)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--prefer-p1", choices=["safari", "android", "both"], default="safari")
    parser.add_argument("--chrome-bin", default=DEFAULT_CHROME)
    parser.add_argument("--safari-bin", default=DEFAULT_SAFARI)
    parser.add_argument("--safari-tp-bin", default=DEFAULT_SAFARI_TP)
    parser.add_argument("--min-disk-gib", type=float, default=5.0)
    parser.add_argument("--check-local-files", action="store_true")
    parser.add_argument("--check-public-origin", action="store_true")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--require-go", action="store_true")
    args = parser.parse_args()

    preflight = build_preflight(args)
    write_csv(preflight, Path(args.csv_output))
    text = json.dumps(preflight, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(preflight)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")
    if args.require_go and not preflight["go_for_p0_baseline_capture"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
