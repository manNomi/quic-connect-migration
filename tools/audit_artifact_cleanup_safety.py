#!/usr/bin/env python3
"""Audit local artifact cleanup candidates against experiment CSV references."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from plan_final_browser_handover_runs import PUBLIC_TEMPLATE_VALUES, make_plan
from report_artifact_storage import DEFAULT_ROOTS, directory_size, human_size, immediate_children


DEFAULT_EXPERIMENTS = "data/experiment-results.csv"
DEFAULT_ARTIFACT_REFERENCE_CSVS = ["data/chrome-h3-rebinding-repetition-summary-20260624.csv"]
DEFAULT_OUTPUT = "docs/results/artifact-cleanup-safety-audit-20260624.md"


@dataclass
class ArtifactReference:
    trial_id: str
    artifact_dir: str


@dataclass
class CleanupSafetyItem:
    path: str
    size_bytes: int
    size_human: str
    file_count: int
    directory_count: int
    referenced_by_csv: bool
    referenced_trial_ids: list[str]
    planned_final_trial_artifact: bool
    controlled_public_like: bool
    recommendation: str
    reason: str


def norm_path(value: str | Path) -> str:
    return Path(value).as_posix().rstrip("/")


def path_overlaps(candidate: str, reference: str) -> bool:
    candidate = norm_path(candidate)
    reference = norm_path(reference)
    return candidate == reference or candidate.startswith(reference + "/") or reference.startswith(candidate + "/")


def load_references_from_csv(path: Path) -> list[ArtifactReference]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fp:
        rows = csv.DictReader(fp)
        return [
            ArtifactReference(row.get("trial_id") or row.get("run_id") or row.get("artifact_dir", ""), row.get("artifact_dir", ""))
            for row in rows
            if row.get("artifact_dir")
        ]


def load_references(experiments_path: Path, extra_reference_csvs: list[Path] | None = None) -> list[ArtifactReference]:
    references = load_references_from_csv(experiments_path)
    for path in extra_reference_csvs or []:
        references.extend(load_references_from_csv(path))
    return references


def planned_final_trial_ids(repetitions: int, prefer_p1: str) -> set[str]:
    return {trial.trial_id for trial in make_plan(dict(PUBLIC_TEMPLATE_VALUES), repetitions, prefer_p1)}


def classify_candidate(
    candidate_path: str,
    references: list[ArtifactReference],
    planned_ids: set[str],
) -> tuple[bool, list[str], bool, bool, str, str]:
    matched_refs = [ref.trial_id for ref in references if path_overlaps(candidate_path, ref.artifact_dir)]
    name = Path(candidate_path).name
    planned_final = name in planned_ids
    controlled_public_like = name.startswith("controlled-public-")

    if matched_refs:
        return (
            True,
            matched_refs,
            planned_final,
            controlled_public_like,
            "keep-referenced",
            "artifact path is referenced by a tracked artifact reference CSV",
        )
    if planned_final:
        return (
            False,
            [],
            True,
            controlled_public_like,
            "keep-planned-final-trial",
            "artifact path matches a planned final browser handover trial id",
        )
    if controlled_public_like:
        return (
            False,
            [],
            False,
            True,
            "review-controlled-public",
            "controlled-public artifact may be related to public-origin preflight or final-trial preparation",
        )
    return (
        False,
        [],
        False,
        False,
        "review-unreferenced",
        "artifact path is not referenced by tracked artifact CSVs or planned final-trial ids",
    )


def build_audit(
    roots: list[str],
    experiments_path: Path,
    target_free_gib: float,
    repetitions: int,
    prefer_p1: str,
    extra_reference_csvs: list[Path] | None = None,
) -> dict[str, Any]:
    if extra_reference_csvs is None:
        extra_reference_csvs = [Path(path) for path in DEFAULT_ARTIFACT_REFERENCE_CSVS]
    references = load_references(experiments_path, extra_reference_csvs)
    planned_ids = planned_final_trial_ids(repetitions, prefer_p1)
    candidates = []
    for root in roots:
        candidates.extend(immediate_children(Path(root)))
    candidates.sort(key=lambda item: item.total_bytes, reverse=True)

    items: list[CleanupSafetyItem] = []
    for candidate in candidates:
        referenced, trial_ids, planned_final, controlled_public_like, recommendation, reason = classify_candidate(
            candidate.path,
            references,
            planned_ids,
        )
        items.append(
            CleanupSafetyItem(
                path=candidate.path,
                size_bytes=candidate.total_bytes,
                size_human=human_size(candidate.total_bytes),
                file_count=candidate.file_count,
                directory_count=candidate.directory_count,
                referenced_by_csv=referenced,
                referenced_trial_ids=trial_ids,
                planned_final_trial_artifact=planned_final,
                controlled_public_like=controlled_public_like,
                recommendation=recommendation,
                reason=reason,
            )
        )

    disk = shutil.disk_usage(".")
    target_free_bytes = int(target_free_gib * (1024**3))
    review_unreferenced_bytes = sum(item.size_bytes for item in items if item.recommendation == "review-unreferenced")
    protected_bytes = sum(item.size_bytes for item in items if item.recommendation.startswith("keep-"))
    projected_free = disk.free + review_unreferenced_bytes
    root_reports = [directory_size(Path(root)) for root in roots]
    return {
        "check_date": date.today().isoformat(),
        "experiments": experiments_path.as_posix(),
        "artifact_reference_csvs": [path.as_posix() for path in extra_reference_csvs],
        "roots": roots,
        "target_free_gib": target_free_gib,
        "disk_free_bytes": disk.free,
        "disk_free_human": human_size(disk.free),
        "target_free_bytes": target_free_bytes,
        "candidate_count": len(items),
        "referenced_candidate_count": sum(1 for item in items if item.referenced_by_csv),
        "planned_final_candidate_count": sum(1 for item in items if item.planned_final_trial_artifact),
        "review_unreferenced_count": sum(1 for item in items if item.recommendation == "review-unreferenced"),
        "review_unreferenced_bytes": review_unreferenced_bytes,
        "review_unreferenced_human": human_size(review_unreferenced_bytes),
        "protected_bytes": protected_bytes,
        "protected_human": human_size(protected_bytes),
        "projected_free_if_review_unreferenced_removed_bytes": projected_free,
        "projected_free_if_review_unreferenced_removed_human": human_size(projected_free),
        "target_met_if_review_unreferenced_removed": projected_free >= target_free_bytes,
        "remaining_gap_if_review_unreferenced_removed_human": human_size(max(0, target_free_bytes - projected_free)),
        "artifact_roots_total_human": human_size(sum(item.total_bytes for item in root_reports)),
        "items": [asdict(item) for item in items],
        "note": "Non-destructive audit only. Treat every item as review-required unless the referenced CSV rows and paper tables are backed up elsewhere.",
    }


def emit_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Artifact Cleanup Safety Audit",
        "",
        f"Generated: `{audit['check_date']}`",
        "",
        "## Summary",
        "",
        "| metric | value |",
        "| --- | --- |",
        f"| experiments CSV | `{audit['experiments']}` |",
        f"| disk free | `{audit['disk_free_human']}` |",
        f"| target free GiB | `{audit['target_free_gib']}` |",
        f"| artifact roots total | `{audit['artifact_roots_total_human']}` |",
        f"| extra artifact reference CSVs | `{audit['artifact_reference_csvs']}` |",
        f"| cleanup candidates | `{audit['candidate_count']}` |",
        f"| CSV-referenced candidates | `{audit['referenced_candidate_count']}` |",
        f"| planned final-trial candidates | `{audit['planned_final_candidate_count']}` |",
        f"| review-unreferenced candidates | `{audit['review_unreferenced_count']}` |",
        f"| review-unreferenced size | `{audit['review_unreferenced_human']}` |",
        f"| protected referenced/planned size | `{audit['protected_human']}` |",
        f"| projected free if review-unreferenced removed | `{audit['projected_free_if_review_unreferenced_removed_human']}` |",
        f"| target met if review-unreferenced removed | `{'yes' if audit['target_met_if_review_unreferenced_removed'] else 'no'}` |",
        f"| remaining gap then | `{audit['remaining_gap_if_review_unreferenced_removed_human']}` |",
        "",
        "## Recommendations",
        "",
        "| recommendation | meaning |",
        "| --- | --- |",
        "| `keep-referenced` | referenced by a tracked artifact CSV; keep unless archived and paper evidence is preserved |",
        "| `keep-planned-final-trial` | matches a planned final browser handover trial id |",
        "| `review-controlled-public` | controlled-public preparation output; inspect manually before cleanup |",
        "| `review-unreferenced` | not referenced by current artifact CSVs or planned final ids; still review before deletion |",
        "",
        "## Candidates",
        "",
        "| recommendation | path | size | referenced trials | reason |",
        "| --- | --- | ---: | --- | --- |",
    ]
    if not audit["items"]:
        lines.append("| - | - | - | - | - |")
    for item in audit["items"]:
        refs = ", ".join(item["referenced_trial_ids"]) if item["referenced_trial_ids"] else "-"
        lines.append(
            f"| `{item['recommendation']}` | `{item['path']}` | `{item['size_human']}` | {refs} | {item['reason']} |"
        )
    lines.extend(["", "## Note", "", audit["note"]])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", dest="roots")
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--reference-csv", action="append", dest="reference_csvs")
    parser.add_argument("--target-free-gib", type=float, default=5.0)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--prefer-p1", choices=["safari", "android", "both"], default="safari")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    if args.target_free_gib <= 0:
        raise SystemExit("--target-free-gib must be positive")
    if args.repetitions < 1:
        raise SystemExit("--repetitions must be positive")

    audit = build_audit(
        args.roots or DEFAULT_ROOTS,
        Path(args.experiments),
        args.target_free_gib,
        args.repetitions,
        args.prefer_p1,
        [Path(path) for path in args.reference_csvs] if args.reference_csvs is not None else None,
    )
    text = json.dumps(audit, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(audit)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
