#!/usr/bin/env python3
"""Build a minimal staged run plan from the replication sufficiency audit."""

from __future__ import annotations

import argparse
import csv
import re
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from research_clock import utc_date_iso


DEFAULT_INPUT = "data/replication-sufficiency-audit-20260624.csv"
DEFAULT_OUTPUT = "docs/results/replication-run-plan-20260624.md"
DEFAULT_CSV_OUTPUT = "data/replication-run-plan-20260624.csv"
DEFAULT_MIN_OPTIONAL_LOCAL_FREE_GIB = 10.0


TRANSITION_REPS = 6
ANCHOR_CONDITIONS = {
    "downlink-6000ms",
    "upload-4600ms",
    "upload-4900ms",
    "upload-retry1-12000ms",
    "upload-retry1-15000ms",
    "upload-retry2-18000ms",
    "upload-retry2-21000ms",
    "downlink-wait_only_no_retry-6000ms",
    "downlink-retry_enabled_1x500ms-6000ms",
    "poll-3000ms",
    "poll-6000ms",
}


CSV_FIELDS = [
    "stage",
    "priority",
    "condition_id",
    "source",
    "current_role",
    "current_pass_runs",
    "suggested_repetitions",
    "purpose",
    "run_when",
    "command_source",
    "notes",
]


@dataclass(frozen=True)
class PlanRow:
    stage: str
    priority: int
    condition_id: str
    source: str
    current_role: str
    current_pass_runs: str
    suggested_repetitions: str
    purpose: str
    run_when: str
    command_source: str
    notes: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def int_value(raw: str | None, default: int = 0) -> int:
    if raw in {None, ""}:
        return default
    return int(raw)


def window_ms(condition_id: str) -> int:
    match = re.search(r"(\d+)ms$", condition_id)
    return int(match.group(1)) if match else 0


def command_source_for(source: str) -> str:
    if source in {"workload_transition", "polling_transition"}:
        return "docs/reproducibility-guide-ko.md sections 34-36; run-chrome-h3-rebinding-transient-boundary-repetition.sh"
    if source == "upload_recovery":
        return "docs/reproducibility-guide-ko.md sections 32-33; run-chrome-h3-rebinding-transient-boundary-repetition.sh with upload retry env"
    if source == "downlink_recovery":
        return "docs/reproducibility-guide-ko.md section 35; run-chrome-h3-rebinding-transient-boundary-repetition.sh with downlink retry/wait env"
    return "docs/reproducibility-guide-ko.md"


def build_public_first_row() -> PlanRow:
    return PlanRow(
        stage="P0-public-browser-handover",
        priority=0,
        condition_id="controlled-public-final-protocol",
        source="final_browser_handover",
        current_role="blocked",
        current_pass_runs="0/6 final requirements",
        suggested_repetitions="6 required trial rows",
        purpose="Produce the missing publishable browser/mobile active path-change evidence before broad CM claims.",
        run_when="after controlled public origin config, active secondary path, and network-change command are ready",
        command_source="docs/results/final-handover-trial-packet-20260624.md",
        notes="This remains higher priority than optional local replication because it closes the main paper blocker.",
    )


def transition_plan(row: dict[str, str]) -> PlanRow:
    condition = row["condition_id"]
    runs = int_value(row.get("runs"))
    if runs >= TRANSITION_REPS:
        return PlanRow(
            stage="L1-transition-zone-reviewed",
            priority=3,
            condition_id=condition,
            source=row["source"],
            current_role=row["evidence_role"],
            current_pass_runs=f"{row['pass_count']}/{row['runs']}",
            suggested_repetitions="0",
            purpose="Record that the planned local transition-zone repetition target has been reached.",
            run_when="no immediate local repetition; revisit only if the paper needs narrower windows or a different workload.",
            command_source=command_source_for(row["source"]),
            notes="Target repetitions reached; keep the condition as transition-zone evidence instead of treating it as a binary threshold.",
        )
    return PlanRow(
        stage="L1-transition-zone-replication",
        priority=1,
        condition_id=condition,
        source=row["source"],
        current_role=row["evidence_role"],
        current_pass_runs=f"{row['pass_count']}/{row['runs']}",
        suggested_repetitions=str(TRANSITION_REPS),
        purpose="Stabilize mixed transition-zone wording and detect whether the mixed row is timer/packet-alignment sensitive.",
        run_when="after disk free space is comfortable for local NetLog/qlog artifacts or after old artifacts are reviewed",
        command_source=command_source_for(row["source"]),
        notes="Keep this as transition-zone evidence even after extra repetitions unless the mixed behavior disappears consistently.",
    )


def anchor_plan(row: dict[str, str]) -> PlanRow:
    condition = row["condition_id"]
    extra = row.get("additional_same_outcome_runs_for_rule_of_thumb") or "0"
    return PlanRow(
        stage="L2-boundary-anchor-replication",
        priority=2,
        condition_id=condition,
        source=row["source"],
        current_role=row["evidence_role"],
        current_pass_runs=f"{row['pass_count']}/{row['runs']}",
        suggested_repetitions=extra,
        purpose="Turn an important all-pass/all-fail local boundary anchor from directional evidence into stronger local support.",
        run_when="only if the paper needs stronger local reliability wording after public handover trials are attempted",
        command_source=command_source_for(row["source"]),
        notes="The suggested count assumes future rows preserve the same all-pass or all-fail outcome.",
    )


def build_plan(input_path: Path) -> dict[str, object]:
    audit_rows = read_csv(input_path)
    rows: list[PlanRow] = [build_public_first_row()]
    selected: set[str] = set()

    for row in sorted(audit_rows, key=lambda item: (item["source"], window_ms(item["condition_id"]))):
        if row.get("evidence_role") == "transition_zone":
            rows.append(transition_plan(row))
            selected.add(row["condition_id"])

    for row in sorted(audit_rows, key=lambda item: (item["source"], window_ms(item["condition_id"]))):
        condition = row["condition_id"]
        if condition in ANCHOR_CONDITIONS and condition not in selected:
            rows.append(anchor_plan(row))
            selected.add(condition)

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "input": str(input_path),
        "transition_repetitions_per_condition": TRANSITION_REPS,
        "anchor_condition_count": len(ANCHOR_CONDITIONS),
        "rows": [asdict(row) for row in rows],
    }


def add_disk_guard(plan: dict[str, object], root: Path, min_optional_local_free_gib: float) -> dict[str, object]:
    free_gib = round(shutil.disk_usage(root).free / (1024**3), 2)
    ready = free_gib >= min_optional_local_free_gib
    enriched = dict(plan)
    enriched["local_optional_replication_disk"] = {
        "free_gib": free_gib,
        "min_optional_local_free_gib": min_optional_local_free_gib,
        "ready": ready,
        "recommendation": "hold-local-optional-replication" if not ready else "optional-local-replication-disk-ready",
    }
    return enriched


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def emit_markdown(plan: dict[str, object]) -> str:
    rows = list(plan["rows"])  # type: ignore[arg-type]
    transition_rows = [row for row in rows if row["stage"] == "L1-transition-zone-replication"]
    transition_reviewed_rows = [row for row in rows if row["stage"] == "L1-transition-zone-reviewed"]
    anchor_rows = [row for row in rows if row["stage"] == "L2-boundary-anchor-replication"]
    detail_rows = [
        [
            row["stage"],
            str(row["priority"]),
            f"`{row['condition_id']}`",
            row["current_pass_runs"],
            row["suggested_repetitions"],
            row["purpose"],
            row["run_when"],
        ]
        for row in rows
    ]
    sections = [
        "# Replication Run Plan",
        "",
        f"Generated: `{plan['generated']}`",
        "",
        "This plan is public-safe. It turns the replication sufficiency audit into a staged execution plan and keeps the final public/browser handover protocol as the first priority.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| plan rows | `{len(rows)}` |",
        f"| P0 public/browser rows | `1` |",
        f"| L1 transition-zone rows | `{len(transition_rows)}` |",
        f"| L1 transition-zone reviewed rows | `{len(transition_reviewed_rows)}` |",
        f"| L2 anchor rows | `{len(anchor_rows)}` |",
        f"| transition repetitions per condition | `{plan['transition_repetitions_per_condition']}` |",
        f"| optional local replication disk | `{(plan.get('local_optional_replication_disk') or {}).get('recommendation', '-')}` |",
        f"| optional local free GiB | `{(plan.get('local_optional_replication_disk') or {}).get('free_gib', '-')}` |",
        "",
        "## Staged Plan",
        "",
        markdown_table(
            [
                "stage",
                "priority",
                "condition",
                "current PASS/runs",
                "suggested reps",
                "purpose",
                "run when",
            ],
            detail_rows,
        ),
        "",
        "## Command Sources",
        "",
        markdown_table(
            ["condition", "command source", "notes"],
            [[f"`{row['condition_id']}`", row["command_source"], row["notes"]] for row in rows],
        ),
        "",
        "## Interpretation",
        "",
        "- Do not spend the remaining disk budget on broad local replication before the controlled-public final protocol is unblocked.",
        "- If `optional local replication disk` is `hold-local-optional-replication`, keep the next disk budget for controlled-public/browser artifacts.",
        "- If public/browser handover remains externally blocked, L1 transition-zone rows are the highest-value local repetitions.",
        "- Transition-zone rows that have reached the planned repetition count should be used to refine wording, not rerun blindly.",
        "- L2 anchor repetitions are optional unless the paper needs stronger local reliability wording.",
    ]
    return "\n".join(sections).rstrip() + "\n"


def write_csv(plan: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(plan["rows"])  # type: ignore[arg-type]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=DEFAULT_INPUT)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    parser.add_argument("--min-optional-local-free-gib", type=float, default=DEFAULT_MIN_OPTIONAL_LOCAL_FREE_GIB)
    args = parser.parse_args()

    plan = add_disk_guard(build_plan(Path(args.input)), Path("."), args.min_optional_local_free_gib)
    write_csv(plan, Path(args.csv_output))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(plan), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
