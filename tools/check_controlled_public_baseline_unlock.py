#!/usr/bin/env python3
"""Check whether a controlled-public Chrome H3 baseline unlocks active trials."""

from __future__ import annotations

import argparse
import json
from research_clock import utc_date_iso
from pathlib import Path
from typing import Any

from check_final_handover_trial_artifact_bundle import build_trial_bundle_report, trial_shape_from_id
from validate_final_handover_trial_artifact import DEFAULT_REQUIREMENTS, build_validation


DEFAULT_TRIAL_ID = "controlled-public-chrome-h3-baseline-001"
DEFAULT_ARTIFACT_DIR = "repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001"
DEFAULT_OUTPUT = "docs/results/controlled-public-baseline-unlock-check-20260624.md"

UNLOCK_CLASSIFICATIONS = {
    "controlled_public_application_h3_confirmed",
    "controlled_public_server_qlog_h3_confirmed_browser_netlog_inconclusive",
}


def build_unlock_report(trial_id: str, artifact_dir: Path, requirements_path: Path) -> dict[str, Any]:
    trial = trial_shape_from_id(trial_id)
    bundle = build_trial_bundle_report(
        trial,
        artifact_dir,
        requirements_path,
        require_final_countable=True,
    )
    try:
        validation = build_validation(trial_id, artifact_dir, requirements_path, utc_date_iso())
    except FileNotFoundError as exc:
        validation = {
            "summary_path": "",
            "summary_status": "",
            "summary_classification": "",
            "counts_toward_final_protocol": False,
            "matched_final_requirements": [],
            "claim_strength": "summary_missing",
            "warnings": [str(exc)],
        }

    classification = str(validation.get("summary_classification") or "")
    status = str(validation.get("summary_status") or "")
    baseline_summary_pass = status == "PASS" and classification in UNLOCK_CLASSIFICATIONS
    final_countable = bool(validation.get("counts_toward_final_protocol"))
    bundle_complete = bool(bundle.get("artifact_bundle_complete"))
    unlocks_active_trials = baseline_summary_pass and final_countable and bundle_complete

    blockers: list[str] = []
    if not baseline_summary_pass:
        blockers.append(
            f"baseline summary is not an unlocking PASS classification: status={status or '-'} classification={classification or '-'}"
        )
    if not final_countable:
        blockers.append("baseline validation does not count toward final browser handover protocol")
    if not bundle_complete:
        blockers.extend(bundle.get("blockers") or ["baseline artifact bundle is incomplete"])

    return {
        "check_date": utc_date_iso(),
        "trial_id": trial_id,
        "artifact_dir": artifact_dir.as_posix(),
        "summary_path": validation.get("summary_path"),
        "summary_status": status,
        "summary_classification": classification,
        "allowed_unlock_classifications": sorted(UNLOCK_CLASSIFICATIONS),
        "baseline_summary_pass": baseline_summary_pass,
        "counts_toward_final_protocol": final_countable,
        "artifact_bundle_complete": bundle_complete,
        "unlocks_active_trials": unlocks_active_trials,
        "matched_final_requirements": validation.get("matched_final_requirements") or [],
        "claim_strength": validation.get("claim_strength"),
        "validation_warnings": validation.get("warnings") or [],
        "artifact_blockers": bundle.get("blockers") or [],
        "blockers": blockers,
        "public_safe": True,
    }


def emit_markdown(report: dict[str, Any]) -> str:
    blockers = report["blockers"] or ["-"]
    warnings = report["validation_warnings"] or ["-"]
    matched = report["matched_final_requirements"] or ["-"]
    lines = [
        "# Controlled Public Baseline Unlock Check",
        "",
        f"Generated: `{report['check_date']}`",
        "",
        "This public-safe check decides whether a controlled-public Chrome HTTP/3 baseline can unlock active browser network-change trials.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| trial_id | `{report['trial_id']}` |",
        f"| artifact_dir | `{report['artifact_dir']}` |",
        f"| summary_path | `{report['summary_path'] or '-'}` |",
        f"| summary status | `{report['summary_status'] or '-'}` |",
        f"| summary classification | `{report['summary_classification'] or '-'}` |",
        f"| baseline summary PASS | `{'yes' if report['baseline_summary_pass'] else 'no'}` |",
        f"| counts toward final protocol | `{'yes' if report['counts_toward_final_protocol'] else 'no'}` |",
        f"| artifact bundle complete | `{'yes' if report['artifact_bundle_complete'] else 'no'}` |",
        f"| unlocks active trials | `{'yes' if report['unlocks_active_trials'] else 'no'}` |",
        f"| claim strength | `{report['claim_strength'] or '-'}` |",
        f"| public safe | `{'yes' if report['public_safe'] else 'no'}` |",
        "",
        "## Allowed Unlock Classifications",
        "",
    ]
    lines.extend(f"- `{item}`" for item in report["allowed_unlock_classifications"])
    lines.extend(["", "## Matched Final Requirements", ""])
    lines.extend(f"- {item}" for item in matched)
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {item}" for item in warnings)
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in blockers)
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial-id", default=DEFAULT_TRIAL_ID)
    parser.add_argument("--artifact-dir", default=DEFAULT_ARTIFACT_DIR)
    parser.add_argument("--requirements", default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--require-unlocked", action="store_true")
    args = parser.parse_args()

    report = build_unlock_report(args.trial_id, Path(args.artifact_dir), Path(args.requirements))

    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if args.require_unlocked and not report["unlocks_active_trials"]:
        return 1
    return 0 if report["baseline_summary_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
