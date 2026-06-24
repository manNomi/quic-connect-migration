#!/usr/bin/env python3
"""Build a paper-facing matrix of why QUIC CM is hard to deploy."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


DEFAULT_RUBRIC = "data/cm-operational-friction-rubric.csv"
DEFAULT_EXPERIMENTS = "data/experiment-results.csv"
DEFAULT_LITERATURE = "data/literature-review-tracker.csv"
DEFAULT_OUTPUT = "docs/results/cm-operational-friction-matrix-20260624.md"
DEFAULT_CSV_OUTPUT = "data/cm-operational-friction-matrix-20260624.csv"


@dataclass(frozen=True)
class FrictionRow:
    friction_id: str
    layer: str
    friction: str
    why_it_discourages_or_blocks_cm: str
    experiment_match_count: int
    experiment_status_counts: str
    literature_match_count: int
    literature_grades: str
    repo_claim_scope: str
    next_proof_needed: str
    confidence: str
    paper_use: str


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def split_terms(value: str) -> list[str]:
    return [term.strip().lower() for term in value.split(";") if term.strip()]


def row_text(row: dict[str, str], keys: list[str]) -> str:
    return " ".join(row.get(key, "") for key in keys).lower()


def match_rows(rows: list[dict[str, str]], terms: list[str], keys: list[str]) -> list[dict[str, str]]:
    if not terms:
        return []
    matches = []
    for row in rows:
        text = row_text(row, keys)
        if any(term in text for term in terms):
            matches.append(row)
    return matches


def format_counts(counter: Counter[str]) -> str:
    if not counter:
        return "-"
    return ";".join(f"{key}={counter[key]}" for key in sorted(counter))


def paper_use(confidence: str, experiment_count: int, literature_count: int) -> str:
    if confidence == "A" and experiment_count and literature_count:
        return "source-backed explanation with repo evidence"
    if confidence == "A" and literature_count:
        return "source-backed background; local evidence pending"
    if experiment_count and literature_count:
        return "cautious explanatory support"
    if literature_count:
        return "related-work support only"
    if experiment_count:
        return "internal evidence; add source citation"
    return "manual review needed"


def build_matrix(args: argparse.Namespace) -> dict[str, object]:
    rubric = load_csv(Path(args.rubric))
    experiments = load_csv(Path(args.experiments))
    literature = load_csv(Path(args.literature))
    rows: list[FrictionRow] = []

    for item in rubric:
        exp_matches = match_rows(
            experiments,
            split_terms(item["experiment_terms_any"]),
            [
                "trial_id",
                "status",
                "implementation",
                "deployment_tier",
                "migration_trigger",
                "failure_layer",
                "notes",
            ],
        )
        lit_matches = match_rows(
            literature,
            split_terms(item["literature_terms_any"]),
            ["grade", "type", "title", "venue_or_status", "relevance", "next_action"],
        )
        exp_status = Counter(row.get("status", "") for row in exp_matches)
        lit_grades = Counter(row.get("grade", "") for row in lit_matches)
        rows.append(
            FrictionRow(
                friction_id=item["friction_id"],
                layer=item["layer"],
                friction=item["friction"],
                why_it_discourages_or_blocks_cm=item["why_it_discourages_or_blocks_cm"],
                experiment_match_count=len(exp_matches),
                experiment_status_counts=format_counts(exp_status),
                literature_match_count=len(lit_matches),
                literature_grades=format_counts(lit_grades),
                repo_claim_scope=item["repo_claim_scope"],
                next_proof_needed=item["next_proof_needed"],
                confidence=item["confidence"],
                paper_use=paper_use(item["confidence"], len(exp_matches), len(lit_matches)),
            )
        )

    return {
        "generated": date.today().isoformat(),
        "rubric": args.rubric,
        "experiments": args.experiments,
        "literature": args.literature,
        "row_count": len(rows),
        "layer_counts": dict(sorted(Counter(row.layer for row in rows).items())),
        "paper_use_counts": dict(sorted(Counter(row.paper_use for row in rows).items())),
        "rows": [asdict(row) for row in rows],
    }


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(value).replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def emit_markdown(matrix: dict[str, object]) -> str:
    rows = matrix["rows"]
    assert isinstance(rows, list)
    lines = [
        "# CM Operational Friction Matrix",
        "",
        f"Generated: `{matrix['generated']}`",
        "",
        "This matrix turns the question \"why is connection migration not widely used?\" into layer-specific, evidence-linked friction points. It is public-safe and does not print private origin settings, commands, qlogs, pcaps, NetLogs, or credentials.",
        "",
        "## Summary",
        "",
        markdown_table(
            ["field", "value"],
            [
                ["rubric", f"`{matrix['rubric']}`"],
                ["experiment corpus", f"`{matrix['experiments']}`"],
                ["literature tracker", f"`{matrix['literature']}`"],
                ["friction rows", f"`{matrix['row_count']}`"],
                ["layer counts", f"`{matrix['layer_counts']}`"],
                ["paper-use counts", f"`{matrix['paper_use_counts']}`"],
            ],
        ),
        "",
        "## Matrix",
        "",
        markdown_table(
            [
                "id",
                "layer",
                "friction",
                "repo evidence",
                "literature evidence",
                "paper use",
                "next proof",
            ],
            [
                [
                    f"`{row['friction_id']}`",
                    row["layer"],
                    row["friction"],
                    f"{row['experiment_match_count']} ({row['experiment_status_counts']})",
                    f"{row['literature_match_count']} ({row['literature_grades']})",
                    row["paper_use"],
                    row["next_proof_needed"],
                ]
                for row in rows
            ],
        ),
        "",
        "## Paper Claim Boundary",
        "",
        "The matrix supports a conservative claim: QUIC CM is not absent as a transport primitive, but production use is gated by runtime policy, endpoint discovery, path-change proof, session attribution, CID-aware routing, intermediary behavior, observability, and application-workload effects.",
        "",
        "It does not support a final claim that Chrome/Safari/Android browser handover CM succeeds until the final browser handover protocol has countable rows.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_csv(matrix: dict[str, object], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rows = matrix["rows"]
    assert isinstance(rows, list)
    fieldnames = list(rows[0].keys()) if rows else []
    with output.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rubric", default=DEFAULT_RUBRIC)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--literature", default=DEFAULT_LITERATURE)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    args = parser.parse_args()

    matrix = build_matrix(args)
    if args.csv_output:
        write_csv(matrix, Path(args.csv_output))
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(emit_markdown(matrix), encoding="utf-8")
    else:
        print(emit_markdown(matrix), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
