#!/usr/bin/env python3
"""Check whether a final handover trial has the expected raw artifact bundle."""

from __future__ import annotations

import argparse
import glob
import json
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path
from typing import Any

from build_final_handover_trial_packet import expected_artifacts
from plan_final_browser_handover_runs import DEFAULT_CONFIG, DEFAULT_REQUIRED_TRIALS, PUBLIC_TEMPLATE_VALUES, make_plan, parse_env_file
from select_next_final_handover_trial import DEFAULT_EXPERIMENTS, build_selection
from validate_final_handover_trial_artifact import build_validation


DEFAULT_OUTPUT = "docs/results/final-handover-trial-artifact-bundle-check-20260624.md"


@dataclass
class ArtifactPresence:
    role: str
    path: str
    kind: str
    exists: bool
    size_bytes: int
    match_count: int
    detail: str


def plan_values(config: str, use_local_config: bool) -> dict[str, str]:
    values = dict(PUBLIC_TEMPLATE_VALUES)
    if use_local_config:
        values.update({key: value for key, value in parse_env_file(Path(config)).items() if value})
    return values


def select_trial(args: argparse.Namespace) -> dict[str, Any] | None:
    values = plan_values(args.config, args.use_local_config)
    plans = make_plan(values, args.repetitions, args.prefer_p1)
    if args.trial_id:
        for plan in plans:
            if plan.trial_id == args.trial_id:
                return asdict(plan)
        raise SystemExit(f"unknown final handover trial_id in generated plan: {args.trial_id}")

    selection_args = argparse.Namespace(
        experiments=args.experiments,
        requirements=args.requirements,
        config=args.config,
        use_local_config=args.use_local_config,
        repetitions=args.repetitions,
        prefer_p1=args.prefer_p1,
    )
    return build_selection(selection_args)["next_trial"]


def check_path(path_pattern: str, role: str) -> ArtifactPresence:
    has_glob = any(char in path_pattern for char in "*?[")
    if has_glob:
        matches = sorted(Path(path) for path in glob.glob(path_pattern))
        total_size = sum(path.stat().st_size for path in matches if path.is_file())
        return ArtifactPresence(
            role=role,
            path=path_pattern,
            kind="glob",
            exists=bool(matches),
            size_bytes=total_size,
            match_count=len(matches),
            detail="glob_matched" if matches else "glob_missing",
        )

    path = Path(path_pattern)
    if path.is_dir():
        children = [item for item in path.rglob("*") if item.is_file()]
        total_size = sum(item.stat().st_size for item in children)
        return ArtifactPresence(
            role=role,
            path=path_pattern,
            kind="directory",
            exists=bool(children),
            size_bytes=total_size,
            match_count=len(children),
            detail="directory_has_files" if children else "directory_missing_or_empty",
        )
    if path.is_file():
        return ArtifactPresence(
            role=role,
            path=path_pattern,
            kind="file",
            exists=True,
            size_bytes=path.stat().st_size,
            match_count=1,
            detail="file_exists",
        )
    return ArtifactPresence(
        role=role,
        path=path_pattern,
        kind="path",
        exists=False,
        size_bytes=0,
        match_count=0,
        detail="missing",
    )


def validation_payload(trial_id: str, artifact_dir: Path, requirements: Path, require_final_countable: bool) -> dict[str, Any]:
    try:
        validation = build_validation(trial_id, artifact_dir, requirements, date.today().isoformat())
    except FileNotFoundError as exc:
        return {
            "available": False,
            "error": str(exc),
            "counts_toward_final_protocol": False,
            "claim_strength": "summary_missing",
            "matched_final_requirements": [],
            "warnings": ["classifier summary is missing"],
        }
    payload = {
        "available": True,
        "error": "",
        "counts_toward_final_protocol": validation["counts_toward_final_protocol"],
        "claim_strength": validation["claim_strength"],
        "matched_final_requirements": validation["matched_final_requirements"],
        "warnings": validation["warnings"],
    }
    if require_final_countable and not validation["counts_toward_final_protocol"]:
        payload["warnings"] = list(payload["warnings"]) + ["require_final_countable was set but validation did not match final protocol"]
    return payload


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    trial = select_trial(args)
    if trial is None:
        return {
            "check_date": date.today().isoformat(),
            "trial_selected": False,
            "trial": None,
            "artifact_bundle_complete": False,
            "registration_ready": False,
            "artifact_checks": [],
            "validation": {"available": False, "error": "no next trial selected"},
            "blockers": ["no next trial selected"],
        }

    checks = [check_path(item["path"], item["role"]) for item in expected_artifacts(trial)]
    artifact_complete = all(check.exists for check in checks)
    artifact_dir = Path(f"repro/quic-go-min-repro/{trial['artifact_dir']}")
    validation = validation_payload(
        trial["trial_id"],
        artifact_dir,
        Path(args.requirements),
        args.require_final_countable,
    )
    registration_ready = artifact_complete and bool(validation.get("counts_toward_final_protocol"))
    blockers = []
    blockers.extend(f"missing artifact: {check.role} ({check.path})" for check in checks if not check.exists)
    if not validation.get("available"):
        blockers.append(f"validation unavailable: {validation.get('error')}")
    elif args.require_final_countable and not validation.get("counts_toward_final_protocol"):
        blockers.append("artifact validation does not count toward final protocol")

    return {
        "check_date": date.today().isoformat(),
        "trial_selected": True,
        "trial": trial,
        "artifact_dir": artifact_dir.as_posix(),
        "artifact_bundle_complete": artifact_complete,
        "registration_ready": registration_ready,
        "require_final_countable": args.require_final_countable,
        "artifact_checks": [asdict(check) for check in checks],
        "validation": validation,
        "blockers": blockers,
    }


def emit_markdown(report: dict[str, Any]) -> str:
    trial = report["trial"] or {}
    blockers = report["blockers"] or ["-"]
    lines = [
        "# Final Handover Trial Artifact Bundle Check",
        "",
        f"Generated: `{report['check_date']}`",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| trial selected | `{'yes' if report['trial_selected'] else 'no'}` |",
        f"| trial_id | `{trial.get('trial_id', '-')}` |",
        f"| browser | `{trial.get('browser', '-')}` |",
        f"| phase | `{trial.get('phase', '-')}` |",
        f"| artifact dir | `{report.get('artifact_dir', '-')}` |",
        f"| artifact bundle complete | `{'yes' if report['artifact_bundle_complete'] else 'no'}` |",
        f"| registration ready | `{'yes' if report['registration_ready'] else 'no'}` |",
        f"| validation claim strength | `{report['validation'].get('claim_strength', '-')}` |",
        "",
        "## Artifact Checks",
        "",
        "| role | path | kind | present | matches | bytes | detail |",
        "| --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    if not report["artifact_checks"]:
        lines.append("| - | - | - | - | - | - | - |")
    for check in report["artifact_checks"]:
        lines.append(
            f"| {check['role']} | `{check['path']}` | `{check['kind']}` | `{'yes' if check['exists'] else 'no'}` | {check['match_count']} | {check['size_bytes']} | `{check['detail']}` |"
        )
    lines.extend(["", "## Validation", ""])
    validation = report["validation"]
    lines.extend(
        [
            f"- available: `{'yes' if validation.get('available') else 'no'}`",
            f"- counts toward final protocol: `{'yes' if validation.get('counts_toward_final_protocol') else 'no'}`",
            f"- matched requirements: `{', '.join(validation.get('matched_final_requirements') or ['-'])}`",
            f"- error: `{validation.get('error') or '-'}`",
            "",
            "## Blockers",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in blockers)
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trial-id")
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--requirements", default=DEFAULT_REQUIRED_TRIALS)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--use-local-config", action="store_true")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--prefer-p1", choices=["safari", "android", "both"], default="safari")
    parser.add_argument("--require-final-countable", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report = build_report(args)
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if args.require_complete and not report["registration_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
