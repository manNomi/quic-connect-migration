#!/usr/bin/env python3
"""Apply or dry-run the reviewed artifact cleanup plan."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from plan_artifact_cleanup import build_plan
from report_artifact_storage import DEFAULT_ROOTS, human_size
from research_clock import utc_date_iso


CONFIRM_TOKEN = "DELETE-REVIEW-UNREFERENCED"


@dataclass(frozen=True)
class CleanupAction:
    path: str
    recommendation: str
    bytes_planned: int
    size_human: str
    action: str
    ok: bool
    reason: str


def is_within_roots(path: Path, roots: list[Path]) -> bool:
    try:
        resolved = path.resolve()
    except FileNotFoundError:
        resolved = path.absolute()
    for root in roots:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


def validate_candidate(candidate: dict[str, Any], roots: list[Path], execute: bool) -> CleanupAction:
    path = Path(candidate["path"])
    size = int(candidate["total_bytes"])
    recommendation = candidate.get("recommendation", "")
    if recommendation != "review-unreferenced":
        return CleanupAction(
            path.as_posix(),
            recommendation,
            size,
            human_size(size),
            "skip",
            False,
            "candidate recommendation is not review-unreferenced",
        )
    if not is_within_roots(path, roots):
        return CleanupAction(path.as_posix(), recommendation, size, human_size(size), "skip", False, "path is outside artifact roots")
    if not path.exists():
        return CleanupAction(path.as_posix(), recommendation, size, human_size(size), "skip", False, "path does not exist")
    if not path.is_dir():
        return CleanupAction(path.as_posix(), recommendation, size, human_size(size), "skip", False, "path is not a directory")
    if path.is_symlink():
        return CleanupAction(path.as_posix(), recommendation, size, human_size(size), "skip", False, "path is a symlink")
    return CleanupAction(
        path.as_posix(),
        recommendation,
        size,
        human_size(size),
        "delete" if execute else "would-delete",
        True,
        "validated review-unreferenced directory",
    )


def apply_cleanup(args: argparse.Namespace) -> dict[str, Any]:
    roots = args.roots or DEFAULT_ROOTS
    plan = build_plan(
        roots,
        args.target_free_gib,
        args.candidate_policy,
        Path(args.experiments),
        args.repetitions,
        args.prefer_p1,
    )
    root_paths = [Path(root) for root in roots]
    execute = bool(args.execute)
    confirm_ok = args.confirm == CONFIRM_TOKEN
    refusal_reasons: list[str] = []
    if execute and args.candidate_policy != "review-unreferenced":
        refusal_reasons.append("execute requires --candidate-policy review-unreferenced")
    if execute and not confirm_ok:
        refusal_reasons.append(f"execute requires --confirm {CONFIRM_TOKEN}")

    actions = [validate_candidate(candidate, root_paths, execute and not refusal_reasons) for candidate in plan["selected_candidates"]]
    invalid_actions = [action for action in actions if not action.ok]
    if execute and invalid_actions:
        refusal_reasons.append("one or more selected candidates failed safety validation")

    before = shutil.disk_usage(".")
    deleted: list[str] = []
    if execute and not refusal_reasons:
        for action in actions:
            shutil.rmtree(action.path)
            deleted.append(action.path)
    after = shutil.disk_usage(".")

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "mode": "execute" if execute else "dry-run",
        "executed": execute and not refusal_reasons,
        "confirm_required": CONFIRM_TOKEN,
        "confirm_ok": confirm_ok,
        "refusal_reasons": refusal_reasons,
        "target_free_gib": args.target_free_gib,
        "candidate_policy": args.candidate_policy,
        "selected_count": len(actions),
        "selected_reclaimable_human": plan["selected_reclaimable_human"],
        "remaining_gap_human": plan["remaining_gap_human"],
        "disk_free_before_human": human_size(before.free),
        "disk_free_after_human": human_size(after.free),
        "deleted_count": len(deleted),
        "deleted_paths": deleted,
        "actions": [asdict(action) for action in actions],
        "note": "Default mode is dry-run. Execution is allowed only for validated review-unreferenced artifact directories with the exact confirmation token.",
    }


def emit_markdown(report: dict[str, Any]) -> str:
    refusal = report["refusal_reasons"] or ["none"]
    lines = [
        "# Artifact Cleanup Apply Report",
        "",
        f"Generated: `{report['generated']}`",
        "",
        "This report is public-safe. It never prints qlog, NetLog, pcap, keylog, credential, domain, or device contents.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| mode | `{report['mode']}` |",
        f"| executed | `{'yes' if report['executed'] else 'no'}` |",
        f"| target free GiB | `{report['target_free_gib']}` |",
        f"| candidate policy | `{report['candidate_policy']}` |",
        f"| selected candidates | `{report['selected_count']}` |",
        f"| selected reclaimable | `{report['selected_reclaimable_human']}` |",
        f"| remaining gap before cleanup | `{report['remaining_gap_human']}` |",
        f"| disk free before | `{report['disk_free_before_human']}` |",
        f"| disk free after | `{report['disk_free_after_human']}` |",
        f"| deleted count | `{report['deleted_count']}` |",
        f"| confirm required | `{report['confirm_required']}` |",
        f"| confirm ok | `{'yes' if report['confirm_ok'] else 'no'}` |",
        "",
        "## Refusal Reasons",
        "",
    ]
    lines.extend(f"- {item}" for item in refusal)
    lines.extend(
        [
            "",
            "## Candidate Actions",
            "",
            "| action | ok | path | size | reason |",
            "| --- | --- | --- | ---: | --- |",
        ]
    )
    if not report["actions"]:
        lines.append("| - | - | - | - | - |")
    for action in report["actions"]:
        lines.append(
            f"| `{action['action']}` | `{'yes' if action['ok'] else 'no'}` | `{action['path']}` | `{action['size_human']}` | {action['reason']} |"
        )
    lines.extend(["", "## Note", "", report["note"]])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", dest="roots")
    parser.add_argument("--target-free-gib", type=float, default=7.0)
    parser.add_argument("--candidate-policy", choices=["all", "review-unreferenced"], default="review-unreferenced")
    parser.add_argument("--experiments", default="data/experiment-results.csv")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--prefer-p1", choices=["safari", "android", "both"], default="safari")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--confirm", default="")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    args = parser.parse_args()

    if args.target_free_gib <= 0:
        raise SystemExit("--target-free-gib must be positive")
    report = apply_cleanup(args)
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0 if not report["refusal_reasons"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
