#!/usr/bin/env python3
"""Plan local artifact cleanup needed before heavy browser handover captures."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any

from report_artifact_storage import DEFAULT_ROOTS, build_report, human_size, immediate_children


def build_plan(roots: list[str], target_free_gib: float) -> dict[str, Any]:
    storage = build_report(roots, max_entries=1000)
    disk = storage["disk"]
    current_free = int(disk["free_bytes"])
    target_free = int(target_free_gib * (1024**3))
    needed = max(0, target_free - current_free)
    candidates = []
    for root in roots:
        candidates.extend(immediate_children(Path(root)))
    candidates.sort(key=lambda item: item.total_bytes, reverse=True)

    selected = []
    recovered = 0
    for candidate in candidates:
        if recovered >= needed:
            break
        selected.append(candidate)
        recovered += candidate.total_bytes

    projected_free = current_free + recovered
    return {
        "check_date": date.today().isoformat(),
        "target_free_gib": target_free_gib,
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
        "selected_candidates": [asdict(item) for item in selected],
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
        "| path | size | files | directories |",
        "| --- | ---: | ---: | ---: |",
    ]
    if not plan["selected_candidates"]:
        lines.append("| - | - | - | - |")
    for item in plan["selected_candidates"]:
        lines.append(
            f"| `{item['path']}` | `{human_size(int(item['total_bytes']))}` | {item['file_count']} | {item['directory_count']} |"
        )
    lines.extend(
        [
            "",
            "## Note",
            "",
            plan["note"],
            "",
            "This tool does not delete files. It only identifies how much local ignored artifact cleanup can contribute before running large NetLog/qlog/pcap experiments.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", dest="roots")
    parser.add_argument("--target-free-gib", type=float, default=5.0)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    args = parser.parse_args()

    if args.target_free_gib <= 0:
        raise SystemExit("--target-free-gib must be positive")

    plan = build_plan(args.roots or DEFAULT_ROOTS, args.target_free_gib)
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
