#!/usr/bin/env python3
"""Append a validated final handover result row to experiment-results.csv."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass, asdict
from research_clock import utc_date_iso
from pathlib import Path
from typing import Any

from audit_final_browser_handover_trials import load_rows
from check_final_handover_trial_artifact_bundle import build_trial_bundle_report, trial_shape_from_id
from draft_final_handover_result_row import CSV_FIELDS, emit_csv
from validate_final_handover_trial_artifact import build_validation


DEFAULT_EXPERIMENTS = "data/experiment-results.csv"
DEFAULT_REQUIREMENTS = "data/final-browser-handover-required-trials.csv"


@dataclass
class AppendResult:
    trial_id: str
    experiments_path: str
    apply: bool
    appended: bool
    duplicate_trial_id: bool
    appendable_to_experiment_results: bool
    counts_toward_final_protocol: bool
    claim_strength: str
    matched_final_requirements: list[str]
    require_artifact_bundle: bool
    artifact_bundle_complete: bool
    artifact_bundle_blockers: list[str]
    warnings: list[str]
    row: dict[str, str]


def ensure_schema(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"experiments CSV not found: {path}")
    with path.open(newline="", encoding="utf-8") as fp:
        reader = csv.reader(fp)
        header = next(reader, None)
    if header != CSV_FIELDS:
        raise ValueError(f"unexpected CSV header in {path}: {header}")


def duplicate_trial_id(path: Path, trial_id: str) -> bool:
    rows = load_rows(path)
    return any(row.get("trial_id") == trial_id for row in rows)


def append_row(path: Path, row: dict[str, str]) -> None:
    with path.open("a", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS)
        writer.writerow(row)


def build_append_result(
    trial_id: str,
    artifact_dir: Path,
    experiments_path: Path,
    requirements_path: Path,
    run_date: str,
    summary_path: Path | None,
    require_final_countable: bool,
    require_artifact_bundle: bool,
    apply: bool,
) -> AppendResult:
    ensure_schema(experiments_path)
    validation = build_validation(trial_id, artifact_dir, requirements_path, run_date, summary_path)
    row = validation["draft_row"]
    duplicate = duplicate_trial_id(experiments_path, trial_id)
    warnings = list(validation["warnings"])
    artifact_bundle_complete = True
    artifact_bundle_blockers: list[str] = []
    if require_artifact_bundle:
        bundle = build_trial_bundle_report(
            trial_shape_from_id(trial_id),
            artifact_dir,
            requirements_path,
            require_final_countable,
        )
        artifact_bundle_complete = bool(bundle["artifact_bundle_complete"])
        artifact_bundle_blockers = list(bundle["blockers"])
        if not artifact_bundle_complete:
            warnings.append("required artifact bundle is incomplete")
    if duplicate:
        warnings.append("trial_id already exists in experiment-results CSV")
    if require_final_countable and not validation["counts_toward_final_protocol"]:
        warnings.append("require_final_countable was set but row does not match final protocol requirements")

    can_append = (
        validation["appendable_to_experiment_results"]
        and not duplicate
        and (validation["counts_toward_final_protocol"] or not require_final_countable)
        and (artifact_bundle_complete or not require_artifact_bundle)
    )
    appended = False
    if apply and can_append:
        append_row(experiments_path, row)
        appended = True

    return AppendResult(
        trial_id=trial_id,
        experiments_path=experiments_path.as_posix(),
        apply=apply,
        appended=appended,
        duplicate_trial_id=duplicate,
        appendable_to_experiment_results=validation["appendable_to_experiment_results"],
        counts_toward_final_protocol=validation["counts_toward_final_protocol"],
        claim_strength=validation["claim_strength"],
        matched_final_requirements=validation["matched_final_requirements"],
        require_artifact_bundle=require_artifact_bundle,
        artifact_bundle_complete=artifact_bundle_complete,
        artifact_bundle_blockers=artifact_bundle_blockers,
        warnings=warnings,
        row=row,
    )


def emit_markdown(result: AppendResult) -> str:
    warnings = result.warnings or ["-"]
    matched = result.matched_final_requirements or ["-"]
    lines = [
        "# Final Handover Result Row Append",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| trial_id | `{result.trial_id}` |",
        f"| experiments CSV | `{result.experiments_path}` |",
        f"| apply mode | `{'yes' if result.apply else 'no'}` |",
        f"| appended | `{'yes' if result.appended else 'no'}` |",
        f"| duplicate trial_id | `{'yes' if result.duplicate_trial_id else 'no'}` |",
        f"| appendable | `{'yes' if result.appendable_to_experiment_results else 'no'}` |",
        f"| counts toward final protocol | `{'yes' if result.counts_toward_final_protocol else 'no'}` |",
        f"| claim strength | `{result.claim_strength}` |",
        f"| require artifact bundle | `{'yes' if result.require_artifact_bundle else 'no'}` |",
        f"| artifact bundle complete | `{'yes' if result.artifact_bundle_complete else 'no'}` |",
        "",
        "## Matched Requirements",
        "",
    ]
    lines.extend(f"- {item}" for item in matched)
    if result.artifact_bundle_blockers:
        lines.extend(["", "## Artifact Bundle Blockers", ""])
        lines.extend(f"- {item}" for item in result.artifact_bundle_blockers)
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in warnings)
    lines.extend(["", "## CSV Row", "", "```csv", emit_csv(result.row).rstrip(), "```"])
    return "\n".join(lines).rstrip() + "\n"


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
    parser.add_argument("--trial-id", required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--summary")
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--requirements", default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--date", default=utc_date_iso())
    parser.add_argument("--require-final-countable", action="store_true")
    parser.add_argument("--require-artifact-bundle", action="store_true")
    parser.add_argument("--apply", action="store_true", help="actually append the row; default is dry-run")
    parser.add_argument("--format", choices=["json", "markdown", "csv"], default="markdown")
    parser.add_argument("--output")
    args = parser.parse_args()

    try:
        result = build_append_result(
            trial_id=args.trial_id,
            artifact_dir=Path(args.artifact_dir),
            experiments_path=Path(args.experiments),
            requirements_path=Path(args.requirements),
            run_date=args.date,
            summary_path=Path(args.summary) if args.summary else None,
            require_final_countable=args.require_final_countable,
            require_artifact_bundle=args.require_artifact_bundle,
            apply=args.apply,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc))
        return 2

    if args.format == "json":
        text = json.dumps(asdict(result), indent=2, ensure_ascii=False) + "\n"
    elif args.format == "csv":
        text = emit_csv(result.row)
    else:
        text = emit_markdown(result)

    write_output(text, args.output)

    if args.apply and not result.appended:
        return 1
    if args.require_artifact_bundle and not result.artifact_bundle_complete:
        return 1
    if args.require_final_countable and not result.counts_toward_final_protocol:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
