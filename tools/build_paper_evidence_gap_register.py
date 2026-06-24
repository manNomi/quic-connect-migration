#!/usr/bin/env python3
"""Build a paper-oriented evidence gap register from the research bundle."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any

from audit_final_browser_handover_trials import build_audit


DEFAULT_RUBRIC = "data/evidence-chain-rubric.csv"
DEFAULT_REQUIREMENTS = "data/final-browser-handover-required-trials.csv"
DEFAULT_EXPERIMENTS = "data/experiment-results.csv"
DEFAULT_OUTPUT = "docs/results/paper-evidence-gap-register-20260624.md"
DEFAULT_CSV_OUTPUT = "data/paper-evidence-gap-register-20260624.csv"


@dataclass(frozen=True)
class GapRow:
    claim_id: str
    claim: str
    evidence_item: str
    current_repo_status: str
    paper_use_now: str
    gap: str
    blocking_requirement_ids: str
    next_action: str


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:72] or "claim"


def incomplete_requirement_ids(audit: dict[str, Any]) -> list[str]:
    return [row["requirement_id"] for row in audit["results"] if not row["complete"]]


def classify_paper_use(status: str) -> str:
    normalized = status.lower()
    if normalized == "observed":
        return "scoped claim supported"
    if normalized.startswith("observed_in_"):
        return "control evidence only"
    if normalized.startswith("partially_observed"):
        return "limitation or caution only"
    if normalized == "pending":
        return "do not claim yet"
    return "needs manual review"


def blocking_requirements_for(claim: str, evidence_item: str, incomplete: list[str]) -> list[str]:
    text = f"{claim} {evidence_item}".lower()
    blockers: list[str] = []
    if "browser used http/3" in text or "application h3" in text:
        blockers.append("chrome-controlled-public-application-h3-baseline")
    if "network-change trigger" in text or "client path" in text:
        blockers.extend(
            [
                "chrome-downlink-noheartbeat-active-cm",
                "chrome-downlink-heartbeat-active-cm",
                "p1-safari-or-android-feasibility",
            ]
        )
    if "connection migration occurred" in text or "session continuity" in text or "path validation" in text:
        blockers.extend(
            [
                "chrome-downlink-noheartbeat-active-cm",
                "chrome-downlink-heartbeat-active-cm",
                "p1-safari-or-android-feasibility",
            ]
        )
    if "application continuity" in text or "task completion" in text:
        blockers.extend(
            [
                "chrome-downlink-noheartbeat-active-cm",
                "chrome-downlink-heartbeat-active-cm",
                "chrome-downlink-noheartbeat-nochange-baseline",
                "chrome-downlink-heartbeat-nochange-baseline",
            ]
        )
    if "publishable as browser cm evidence" in text or "combined evidence chain" in text:
        blockers.extend(incomplete)

    seen: set[str] = set()
    filtered = []
    for blocker in blockers:
        if blocker in incomplete and blocker not in seen:
            seen.add(blocker)
            filtered.append(blocker)
    return filtered


def gap_for(claim: str, evidence_item: str, status: str, blockers: list[str]) -> str:
    text = f"{claim} {evidence_item}".lower()
    normalized = status.lower()
    if normalized == "observed" and not blockers:
        if "deployment path" in text:
            return "none for scoped AWS NLB/direct-origin claim; CDN/proxy scope still separate"
        return "none for the currently scoped claim"
    if normalized.startswith("observed_in_"):
        return "needs browser/runtime repetition before being generalized beyond controlled implementation evidence"
    if normalized.startswith("partially_observed"):
        if "client path" in text:
            return "needs active secondary path proof: before/after route, interface, or public IP change"
        if "session continuity" in text:
            return "needs browser active-path trial showing no replacement session plus path-validation evidence"
        return "needs stronger observation before positive claim"
    if normalized == "pending":
        return "needs complete final browser handover protocol rows"
    if blockers:
        return "needs linked final trial requirement completion"
    return "manual review needed"


def next_action_for(blockers: list[str], status: str) -> str:
    if blockers:
        return "run and register: " + "; ".join(blockers)
    if status.lower() == "observed":
        return "cite as scoped result and keep limitation wording"
    if status.lower().startswith("observed_in_"):
        return "use as positive control; do not generalize to browsers"
    if status.lower().startswith("partially_observed"):
        return "collect missing artifact class before upgrading claim"
    return "review manually before citing"


def build_register(rubric_path: Path, requirements_path: Path, experiments_path: Path) -> dict[str, Any]:
    rubric = load_csv(rubric_path)
    audit = build_audit(requirements_path, experiments_path)
    incomplete = incomplete_requirement_ids(audit)
    rows: list[GapRow] = []
    seen_ids: dict[str, int] = {}

    for source_row in rubric:
        claim = source_row["claim"]
        claim_id_base = slugify(claim)
        count = seen_ids.get(claim_id_base, 0) + 1
        seen_ids[claim_id_base] = count
        claim_id = claim_id_base if count == 1 else f"{claim_id_base}-{count}"
        status = source_row["current_repo_status"]
        blockers = blocking_requirements_for(claim, source_row["evidence_item"], incomplete)
        rows.append(
            GapRow(
                claim_id=claim_id,
                claim=claim,
                evidence_item=source_row["evidence_item"],
                current_repo_status=status,
                paper_use_now=classify_paper_use(status),
                gap=gap_for(claim, source_row["evidence_item"], status, blockers),
                blocking_requirement_ids=";".join(blockers) if blockers else "-",
                next_action=next_action_for(blockers, status),
            )
        )

    return {
        "generated": date.today().isoformat(),
        "public_safe": True,
        "rubric_path": str(rubric_path),
        "requirements_path": str(requirements_path),
        "experiments_path": str(experiments_path),
        "final_protocol_complete": audit["complete"],
        "complete_requirements": audit["complete_count"],
        "requirement_count": audit["requirement_count"],
        "incomplete_requirements": incomplete,
        "rows": [asdict(row) for row in rows],
    }


def emit_markdown(register: dict[str, Any]) -> str:
    incomplete = register["incomplete_requirements"] or ["-"]
    lines = [
        "# Paper Evidence Gap Register",
        "",
        f"Generated: `{register['generated']}`",
        "",
        "This register is public-safe. It converts the evidence-chain rubric into paper-claim guidance and links unresolved claims to final browser handover trial requirements.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| final protocol complete | `{'yes' if register['final_protocol_complete'] else 'no'}` |",
        f"| complete requirements | `{register['complete_requirements']}/{register['requirement_count']}` |",
        f"| incomplete requirements | `{'; '.join(incomplete)}` |",
        "",
        "## Claim Register",
        "",
        "| claim id | evidence item | current status | paper use now | gap | blocking requirements |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in register["rows"]:
        lines.append(
            f"| `{row['claim_id']}` | {row['evidence_item']} | `{row['current_repo_status']}` | {row['paper_use_now']} | {row['gap']} | `{row['blocking_requirement_ids']}` |"
        )

    lines.extend(["", "## Next Actions", ""])
    for row in register["rows"]:
        lines.append(f"- `{row['claim_id']}`: {row['next_action']}")
    return "\n".join(lines).rstrip() + "\n"


def write_csv(register: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "claim_id",
        "claim",
        "evidence_item",
        "current_repo_status",
        "paper_use_now",
        "gap",
        "blocking_requirement_ids",
        "next_action",
    ]
    with output.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(register["rows"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rubric", default=DEFAULT_RUBRIC)
    parser.add_argument("--requirements", default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    register = build_register(Path(args.rubric), Path(args.requirements), Path(args.experiments))
    if args.csv_output:
        write_csv(register, Path(args.csv_output))
    text = json.dumps(register, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(register)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
