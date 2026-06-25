#!/usr/bin/env python3
"""Plan local artifact cleanup needed before heavy browser handover captures."""

from __future__ import annotations

import argparse
import json
from research_clock import utc_date_iso
from pathlib import Path
from typing import Any

from audit_artifact_cleanup_safety import build_audit as build_cleanup_safety_audit
from report_artifact_storage import DEFAULT_ROOTS, build_report, human_size, immediate_children


def cleanup_candidates(
    roots: list[str],
    candidate_policy: str,
    experiments_path: Path,
    repetitions: int,
    prefer_p1: str,
) -> list[dict[str, Any]]:
    if candidate_policy == "all":
        return [
            {
                "path": item.path,
                "total_bytes": item.total_bytes,
                "file_count": item.file_count,
                "directory_count": item.directory_count,
                "recommendation": "review-required",
            }
            for root in roots
            for item in immediate_children(Path(root))
        ]
    audit = build_cleanup_safety_audit(
        roots=roots,
        experiments_path=experiments_path,
        target_free_gib=0.01,
        repetitions=repetitions,
        prefer_p1=prefer_p1,
    )
    return [
        {
            "path": item["path"],
            "total_bytes": item["size_bytes"],
            "file_count": item["file_count"],
            "directory_count": item["directory_count"],
            "recommendation": item["recommendation"],
        }
        for item in audit["items"]
        if item["recommendation"] == "review-unreferenced"
    ]


def build_plan(
    roots: list[str],
    target_free_gib: float,
    candidate_policy: str = "all",
    experiments_path: Path = Path("data/experiment-results.csv"),
    repetitions: int = 3,
    prefer_p1: str = "safari",
) -> dict[str, Any]:
    storage = build_report(roots, max_entries=1000)
    disk = storage["disk"]
    current_free = int(disk["free_bytes"])
    target_free = int(target_free_gib * (1024**3))
    needed = max(0, target_free - current_free)
    candidates = cleanup_candidates(roots, candidate_policy, experiments_path, repetitions, prefer_p1)
    candidates.sort(key=lambda item: item["total_bytes"], reverse=True)

    selected = []
    recovered = 0
    for candidate in candidates:
        if recovered >= needed:
            break
        selected.append(candidate)
        recovered += int(candidate["total_bytes"])

    projected_free = current_free + recovered
    return {
        "check_date": utc_date_iso(),
        "target_free_gib": target_free_gib,
        "candidate_policy": candidate_policy,
        "target_free_bytes": target_free,
        "current_free_bytes": current_free,
        "current_free_human": human_size(current_free),
        "needed_bytes": needed,
        "needed_human": human_size(needed),
        "artifact_roots": roots,
        "candidate_count": len(candidates),
        "selected_count": len(selected),
        "selected_reclaimable_bytes": recovered,
        "selected_reclaimable_human": human_size(recovered),
        "projected_free_bytes": projected_free,
        "projected_free_human": human_size(projected_free),
        "target_met_by_selected": projected_free >= target_free,
        "remaining_gap_bytes": max(0, target_free - projected_free),
        "remaining_gap_human": human_size(max(0, target_free - projected_free)),
        "selected_candidates": selected,
        "note": "Dry-run only. Review docs/results and data/experiment-results.csv before deleting any raw artifact directory.",
    }


def emit_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# Artifact Cleanup Dry-run Plan",
        "",
        f"Generated: `{plan['check_date']}`",
        "",
        "## Summary",
        "",
        "| metric | value |",
        "| --- | --- |",
        f"| target free GiB | `{plan['target_free_gib']}` |",
        f"| candidate policy | `{plan['candidate_policy']}` |",
        f"| current free | `{plan['current_free_human']}` |",
        f"| free space needed | `{plan['needed_human']}` |",
        f"| selected candidates | `{plan['selected_count']}/{plan['candidate_count']}` |",
        f"| reclaimable from selected | `{plan['selected_reclaimable_human']}` |",
        f"| projected free after selected cleanup | `{plan['projected_free_human']}` |",
        f"| target met by selected cleanup | `{'yes' if plan['target_met_by_selected'] else 'no'}` |",
        f"| remaining external cleanup gap | `{plan['remaining_gap_human']}` |",
        "",
        "## Selected Candidates",
        "",
        "| path | size | files | directories | recommendation |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    if not plan["selected_candidates"]:
        lines.append("| - | - | - | - | - |")
    for item in plan["selected_candidates"]:
        lines.append(
            f"| `{item['path']}` | `{human_size(int(item['total_bytes']))}` | {item['file_count']} | {item['directory_count']} | `{item.get('recommendation', '-')}` |"
        )
    lines.extend(
        [
            "",
            "## Note",
            "",
            plan["note"],
            "",
            "`candidate_policy=review-unreferenced` excludes artifact directories referenced by tracked CSVs or planned final trial ids.",
            "",
            "This tool does not delete files. It only identifies how much local ignored artifact cleanup can contribute before running large NetLog/qlog/pcap experiments.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", dest="roots")
    parser.add_argument("--target-free-gib", type=float, default=5.0)
    parser.add_argument("--candidate-policy", choices=["all", "review-unreferenced"], default="all")
    parser.add_argument("--experiments", default="data/experiment-results.csv")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--prefer-p1", choices=["safari", "android", "both"], default="safari")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    args = parser.parse_args()

    if args.target_free_gib <= 0:
        raise SystemExit("--target-free-gib must be positive")

    plan = build_plan(
        args.roots or DEFAULT_ROOTS,
        args.target_free_gib,
        args.candidate_policy,
        Path(args.experiments),
        args.repetitions,
        args.prefer_p1,
    )
    text = json.dumps(plan, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(plan)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
