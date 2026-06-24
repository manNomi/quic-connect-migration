#!/usr/bin/env python3
"""Build a public-safe P0 unblock status from final protocol readiness data."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

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
        "python3 tools/check_public_origin_readiness.py --url \"$PUBLIC_ORIGIN_URL\" --require-h3-alt-svc --format markdown",
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


def build_status(matrix_path: Path, scorecard_path: Path) -> dict[str, object]:
    matrix_rows = read_csv(matrix_path)
    scorecard = read_csv(scorecard_path)
    next_trial = first_blocked_trial(matrix_rows)
    next_missing = set(split_cell(next_trial.get("missing_gates", ""))) if next_trial else set()
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
        "total_planned_trials": len(matrix_rows),
        "blocked_planned_trials": sum(1 for row in matrix_rows if row.get("ready") != "True"),
        "complete_requirements": sum(1 for row in scorecard if row.get("complete") == "True"),
        "requirement_count": len(scorecard),
        "needed_now_count": sum(1 for row in rows if row.status == "needed-now"),
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
            "- The next concrete P0 step is to clear all `needed-now` gates for `controlled-public-chrome-h3-baseline-001`.",
            "- Active network-change gates remain after-baseline work until the controlled public application H3 baseline is registered.",
            "- This tracker does not create result evidence; it prevents premature execution and premature browser CM claims.",
        ]
    )
    return "\n".join(sections).rstrip() + "\n"


def write_csv(status: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(status["rows"])  # type: ignore[arg-type]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", default=DEFAULT_MATRIX)
    parser.add_argument("--scorecard", default=DEFAULT_SCORECARD)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    args = parser.parse_args()

    status = build_status(Path(args.matrix), Path(args.scorecard))
    write_csv(status, Path(args.csv_output))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(status), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
