#!/usr/bin/env python3
"""Validate whether a final browser handover artifact can be registered."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from audit_final_browser_handover_trials import load_rows, row_matches
from draft_final_handover_result_row import CSV_FIELDS, build_row, emit_csv, find_summary, read_json


DEFAULT_REQUIREMENTS = "data/final-browser-handover-required-trials.csv"


def claim_strength(row: dict[str, str], matched_requirements: list[str]) -> str:
    status = row["status"]
    if matched_requirements:
        if status == "PASS_FEASIBILITY":
            return "p1_feasibility_counts_toward_protocol"
        return "counts_toward_final_protocol"
    if status == "PASS_NEGATIVE_CONTROL":
        return "negative_control_record_only"
    if status == "FAIL":
        return "failed_trial_record_only"
    return "record_only_not_final_counting"


def warnings_for(row: dict[str, str], matched_requirements: list[str]) -> list[str]:
    warnings: list[str] = []
    if not matched_requirements:
        warnings.append("draft row does not match any final browser handover requirement")
    if row["status"] == "PASS_NEGATIVE_CONTROL":
        warnings.append("negative-control row is appendable but must not be claimed as CM success")
    if row["status"] == "PASS_FEASIBILITY":
        warnings.append("feasibility row is server/qlog-only unless browser-internal evidence is added")
    if row["application_success"] != "true":
        warnings.append("application_success is not true")
    if "reconnect_or_multiple_sessions" in row["notes"]:
        warnings.append("reconnect_or_multiple_sessions excludes Chrome active CM success")
    if "tuple_changed_without_path_validation" in row["notes"]:
        warnings.append("tuple change without qlog path validation excludes CM success")
    if "no_path_change_after_trigger" in row["notes"]:
        warnings.append("network-change trigger did not produce active path-change evidence")
    if "path_snapshot_missing" in row["notes"]:
        warnings.append("missing client path snapshot excludes active handover success")
    if "no_client_active_path_change_observed" in row["notes"]:
        warnings.append("client path snapshot did not show active path change")
    return warnings


def build_validation(
    trial_id: str,
    artifact_dir: Path,
    requirements_path: Path,
    run_date: str,
    summary_path: Path | None = None,
) -> dict[str, Any]:
    summary_file = find_summary(artifact_dir, summary_path.as_posix() if summary_path else None)
    summary = read_json(summary_file)
    row = build_row(trial_id, artifact_dir, summary, run_date)
    requirements = load_rows(requirements_path)
    matched = [item["requirement_id"] for item in requirements if row_matches(item, row)]
    warnings = warnings_for(row, matched)
    registration_ready = all(field in row and row[field] != "" for field in CSV_FIELDS)
    return {
        "validated_at": date.today().isoformat(),
        "trial_id": trial_id,
        "artifact_dir": artifact_dir.as_posix(),
        "summary_path": summary_file.as_posix(),
        "summary_status": summary.get("status"),
        "summary_classification": summary.get("classification"),
        "csv_fields_complete": registration_ready,
        "appendable_to_experiment_results": registration_ready,
        "matched_final_requirements": matched,
        "counts_toward_final_protocol": bool(matched),
        "claim_strength": claim_strength(row, matched),
        "warnings": warnings,
        "draft_row": row,
    }


def emit_markdown(result: dict[str, Any]) -> str:
    warnings = result["warnings"] or ["-"]
    matched = result["matched_final_requirements"] or ["-"]
    row = result["draft_row"]
    lines = [
        "# Final Handover Trial Artifact Validation",
        "",
        f"Validated: `{result['validated_at']}`",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| trial_id | `{result['trial_id']}` |",
        f"| artifact_dir | `{result['artifact_dir']}` |",
        f"| summary_path | `{result['summary_path']}` |",
        f"| summary status | `{result['summary_status']}` |",
        f"| summary classification | `{result['summary_classification']}` |",
        f"| csv fields complete | `{'yes' if result['csv_fields_complete'] else 'no'}` |",
        f"| appendable to experiment-results | `{'yes' if result['appendable_to_experiment_results'] else 'no'}` |",
        f"| counts toward final protocol | `{'yes' if result['counts_toward_final_protocol'] else 'no'}` |",
        f"| claim strength | `{result['claim_strength']}` |",
        "",
        "## Matched Requirements",
        "",
    ]
    lines.extend(f"- {item}" for item in matched)
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in warnings)
    lines.extend(["", "## Draft CSV Row", "", "```csv", emit_csv(row).rstrip(), "```"])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial-id", required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--summary")
    parser.add_argument("--requirements", default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--require-final-countable", action="store_true")
    args = parser.parse_args()

    try:
        result = build_validation(
            trial_id=args.trial_id,
            artifact_dir=Path(args.artifact_dir),
            requirements_path=Path(args.requirements),
            run_date=args.date,
            summary_path=Path(args.summary) if args.summary else None,
        )
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(result)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if args.require_final_countable and not result["counts_toward_final_protocol"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
