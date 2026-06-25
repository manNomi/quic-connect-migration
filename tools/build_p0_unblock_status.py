#!/usr/bin/env python3
"""Build a public-safe P0 unblock status from final protocol readiness data."""

from __future__ import annotations

import argparse
import csv
import io
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from check_next_final_handover_trial_readiness import (
    DEFAULT_CHROME,
    DEFAULT_CONFIG,
    DEFAULT_EXPERIMENTS,
    DEFAULT_REQUIREMENTS,
    DEFAULT_SAFARI,
    DEFAULT_SAFARI_TP,
    build_readiness as build_next_trial_readiness,
)
from research_clock import utc_date_iso


DEFAULT_MATRIX = "data/final-protocol-readiness-matrix-20260624.csv"
DEFAULT_SCORECARD = "data/final-trial-acceptance-scorecard-20260624.csv"
DEFAULT_OUTPUT = "docs/results/p0-unblock-status-20260624.md"
DEFAULT_CSV_OUTPUT = "data/p0-unblock-status-20260624.csv"


CSV_FIELDS = [
    "order",
    "unblock_item",
    "status",
    "blocked_trials",
    "blocks_next_trial",
    "validation_command",
    "operator_action",
    "safe_handling",
]


GATE_GUIDANCE = {
    "controlled_public_config_present": (
        "needed-now",
        "python3 tools/check_controlled_public_config.py --require-baseline-ready",
        "Create the ignored controlled-public origin env file and fill non-secret baseline fields locally.",
        "Do not commit the private env file or real domain/certificate paths.",
    ),
    "public_origin_host_configured": (
        "needed-now",
        "python3 tools/check_controlled_public_config.py --require-baseline-ready",
        "Set the public origin host in the private controlled-public config.",
        "Do not print the real host in tracked reports.",
    ),
    "public_origin_url_configured": (
        "needed-now",
        "python3 tools/check_public_origin_readiness.py --url \"$PUBLIC_ORIGIN_URL\" --require-h3-alt-svc --redact-sensitive --format markdown",
        "Set the public WebPKI URL and verify Alt-Svc/H3 readiness.",
        "Use redacted/public-safe summaries only.",
    ),
    "tls_config_present": (
        "needed-now",
        "python3 tools/check_controlled_public_config.py --require-baseline-ready",
        "Set TLS certificate and key paths on the private origin host/config.",
        "Never commit private keys or local certificate paths.",
    ),
    "baseline_summary_ready": (
        "needed-after-baseline",
        "python3 tools/check_controlled_public_baseline_unlock.py --require-unlocked",
        "Run and register the controlled-public Chrome application H3 baseline.",
        "Register only validated summaries with raw artifact bundle references kept local/ignored.",
    ),
    "network_change_command_present": (
        "needed-after-baseline",
        "python3 tools/check_controlled_public_config.py --require-active-ready",
        "Provide an operator-approved active network-change command.",
        "Do not commit machine-specific interface commands.",
    ),
    "desktop_secondary_path_ready": (
        "needed-after-baseline",
        "python3 tools/check_handover_readiness.py --format markdown",
        "Prepare a real active secondary non-loopback path for desktop browser trials.",
        "Do not infer path change from server tuple evidence alone.",
    ),
    "disk_ready": (
        "ready",
        "python3 tools/report_artifact_storage.py --output docs/results/artifact-storage-report-20260624.md",
        "Keep enough local disk free before heavy browser capture runs.",
        "Review cleanup safety audit before deleting ignored artifacts.",
    ),
    "chrome_ready": (
        "ready",
        "python3 tools/check_handover_readiness.py --format markdown",
        "Chrome is available for the next selected baseline trial.",
        "Use public-safe NetLog summaries in tracked docs.",
    ),
    "safari_webdriver_ready": (
        "ready-or-later",
        "python3 tools/check_browser_cm_observability.py --format markdown",
        "Safari WebDriver is only required for the P1 Safari feasibility branch.",
        "Safari lacks Chrome NetLog-equivalent evidence; keep claim strength separate.",
    ),
    "android_adb_ready": (
        "optional-later",
        "adb devices && python3 tools/check_handover_readiness.py --format markdown",
        "Connect Android over ADB only if Android is selected for P1 feasibility.",
        "Do not commit device identifiers.",
    ),
}


@dataclass(frozen=True)
class UnblockRow:
    order: int
    unblock_item: str
    status: str
    blocked_trials: int
    blocks_next_trial: str
    validation_command: str
    operator_action: str
    safe_handling: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def split_cell(value: str) -> list[str]:
    return [item for item in (value or "").split(";") if item]


def first_blocked_trial(matrix_rows: list[dict[str, str]]) -> dict[str, str] | None:
    for row in sorted(matrix_rows, key=lambda item: int(item.get("order") or 9999)):
        if row.get("ready") != "True":
            return row
    return None


def gate_counts(matrix_rows: list[dict[str, str]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in matrix_rows:
        for gate in split_cell(row.get("missing_gates", "")):
            counts[gate] += 1
    return counts


def local_readiness_summary(readiness: dict[str, object] | None, overlay_applied: bool) -> dict[str, object]:
    if not readiness:
        return {"enabled": False, "overlay_applied": False}
    next_trial = readiness.get("next_trial") or {}
    disk = readiness.get("disk") or {}
    return {
        "enabled": True,
        "overlay_applied": overlay_applied,
        "ready": bool(readiness.get("ready")),
        "config_path": readiness.get("config_path", ""),
        "config_exists": bool(readiness.get("config_exists")),
        "next_trial": next_trial.get("trial_id", "") if isinstance(next_trial, dict) else "",
        "missing_required_gates": list(readiness.get("missing_required_gates") or []),
        "required_gates": list(readiness.get("required_gates") or []),
        "disk_free_gib": disk.get("free_gib", "") if isinstance(disk, dict) else "",
    }


def build_status(
    matrix_path: Path,
    scorecard_path: Path,
    local_readiness: dict[str, object] | None = None,
) -> dict[str, object]:
    matrix_rows = read_csv(matrix_path)
    scorecard = read_csv(scorecard_path)
    matrix_next_blocked_trial = first_blocked_trial(matrix_rows)
    next_trial = matrix_next_blocked_trial
    if local_readiness:
        local_next = local_readiness.get("next_trial") or {}
        if isinstance(local_next, dict) and local_next.get("trial_id"):
            next_trial = local_next  # type: ignore[assignment]
    next_missing = set(split_cell(next_trial.get("missing_gates", ""))) if next_trial else set()
    local_overlay_applied = False
    if local_readiness:
        local_next = local_readiness.get("next_trial") or {}
        local_next_trial_id = local_next.get("trial_id") if isinstance(local_next, dict) else None
        if local_next_trial_id and next_trial and local_next_trial_id == next_trial.get("trial_id"):
            next_missing = set(local_readiness.get("missing_required_gates") or [])
            local_overlay_applied = True
    counts = gate_counts(matrix_rows)

    rows: list[UnblockRow] = []
    for index, (gate, blocked_count) in enumerate(sorted(counts.items(), key=lambda item: (-item[1], item[0])), start=1):
        status, command, action, safe = GATE_GUIDANCE.get(
            gate,
            (
                "needs-review",
                "python3 tools/build_final_protocol_readiness_matrix.py",
                "Review this gate manually before running final trials.",
                "Keep tracked outputs public-safe.",
            ),
        )
        if gate in next_missing and status.startswith("needed"):
            status = "needed-now"
        elif local_overlay_applied and status == "needed-now":
            status = "ready-for-next-trial"
        rows.append(
            UnblockRow(
                order=index,
                unblock_item=gate,
                status=status,
                blocked_trials=blocked_count,
                blocks_next_trial="yes" if gate in next_missing else "no",
                validation_command=command,
                operator_action=action,
                safe_handling=safe,
            )
        )

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "matrix_path": str(matrix_path),
        "scorecard_path": str(scorecard_path),
        "next_trial": next_trial or {},
        "matrix_next_blocked_trial": matrix_next_blocked_trial or {},
        "total_planned_trials": len(matrix_rows),
        "blocked_planned_trials": sum(1 for row in matrix_rows if row.get("ready") != "True"),
        "complete_requirements": sum(1 for row in scorecard if row.get("complete") == "True"),
        "requirement_count": len(scorecard),
        "needed_now_count": sum(1 for row in rows if row.status == "needed-now"),
        "local_readiness": local_readiness_summary(local_readiness, local_overlay_applied),
        "rows": [asdict(row) for row in rows],
    }


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def emit_markdown(status: dict[str, object]) -> str:
    rows = list(status["rows"])  # type: ignore[arg-type]
    next_trial = status["next_trial"]  # type: ignore[assignment]
    local = status.get("local_readiness", {"enabled": False})  # type: ignore[assignment]
    local_missing = ", ".join(f"`{item}`" for item in local.get("missing_required_gates", [])) or "-"
    local_overlay_state = "applied" if local.get("overlay_applied") else ("enabled-not-matched" if local.get("enabled") else "not-used")
    detail_rows = [
        [
            str(row["order"]),
            f"`{row['unblock_item']}`",
            f"`{row['status']}`",
            str(row["blocked_trials"]),
            f"`{row['blocks_next_trial']}`",
            row["operator_action"],
            f"`{row['validation_command']}`",
        ]
        for row in rows
    ]
    sections = [
        "# P0 Unblock Status",
        "",
        f"Generated: `{status['generated']}`",
        "",
        "This tracker is public-safe. It compresses final protocol readiness into the gates that currently block the P0 controlled-public/browser handover path.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| next trial | `{next_trial.get('trial_id', '-')}` |",
        f"| next phase | `{next_trial.get('phase', '-')}` |",
        f"| total planned trials | `{status['total_planned_trials']}` |",
        f"| blocked planned trials | `{status['blocked_planned_trials']}` |",
        f"| final requirements complete | `{status['complete_requirements']}/{status['requirement_count']}` |",
        f"| needed-now gates | `{status['needed_now_count']}` |",
        f"| local next-trial overlay | `{local_overlay_state}` |",
        f"| local next-trial ready | `{'yes' if local.get('ready') else ('no' if local.get('enabled') else '-')}` |",
        f"| local missing required gates | {local_missing} |",
        "",
        "## Blocking Gates",
        "",
        markdown_table(
            [
                "order",
                "gate",
                "status",
                "blocked trials",
                "blocks next",
                "operator action",
                "validation command",
            ],
            detail_rows,
        ),
        "",
        "## Safe Handling",
        "",
    ]
    for row in rows:
        sections.append(f"- `{row['unblock_item']}`: {row['safe_handling']}")
    sections.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The next concrete final-handover step is to clear all `needed-now` gates for the displayed next trial.",
            "- When the local overlay is `applied`, `blocks next` reflects the ignored local config/readiness state rather than only the tracked public matrix.",
            "- Active network-change gates remain after-baseline work until the controlled public application H3 baseline is registered.",
            "- This tracker does not create result evidence; it prevents premature execution and premature browser CM claims.",
        ]
    )
    return "\n".join(sections).rstrip() + "\n"


def csv_text(status: dict[str, object]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(status["rows"])  # type: ignore[arg-type]
    return buffer.getvalue()


def write_csv(status: dict[str, object], path_arg: Path | str) -> None:
    if str(path_arg) == "-":
        sys.stdout.write(csv_text(status))
        return
    path = Path(path_arg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(csv_text(status), encoding="utf-8")


def write_output(text: str, output_arg: str | None) -> None:
    if output_arg == "-":
        sys.stdout.write(text)
        return
    if not output_arg:
        sys.stdout.write(text)
        return
    output = Path(output_arg)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", default=DEFAULT_MATRIX)
    parser.add_argument("--scorecard", default=DEFAULT_SCORECARD)
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
    parser.add_argument("--redact-sensitive", action="store_true")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    args = parser.parse_args()

    local_readiness = None
    if args.use_local_config_for_plan:
        local_args = argparse.Namespace(
            experiments=args.experiments,
            requirements=args.requirements,
            config=args.config,
            use_local_config_for_plan=True,
            repetitions=args.repetitions,
            prefer_p1=args.prefer_p1,
            chrome_bin=args.chrome_bin,
            safari_bin=args.safari_bin,
            safari_tp_bin=args.safari_tp_bin,
            min_disk_gib=args.min_disk_gib,
            check_local_files=False,
            check_public_origin=False,
            redact_sensitive=bool(args.redact_sensitive or args.use_local_config_for_plan),
            timeout=8,
        )
        local_readiness = build_next_trial_readiness(local_args)

    status = build_status(Path(args.matrix), Path(args.scorecard), local_readiness=local_readiness)
    write_csv(status, args.csv_output)
    write_output(emit_markdown(status), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
