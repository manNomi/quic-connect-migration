#!/usr/bin/env python3
"""Summarize tracked controlled-public Chrome validation records."""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_OUTPUT = "docs/results/controlled-public-chrome-bridge-synthesis-20260701.md"
DEFAULT_JSON_OUTPUT = "data/controlled-public-chrome-bridge-synthesis-20260701.json"
DEFAULT_CSV_OUTPUT = "data/controlled-public-chrome-bridge-synthesis-20260701.csv"
DEFAULT_GLOB = "docs/results/controlled-public-chrome-*-validation.md"


@dataclass(frozen=True)
class TrialRecord:
    source_path: str
    trial_id: str
    date: str
    status: str
    classification: str
    claim_strength: str
    trigger_class: str
    workload: str
    retry_policy: str
    page_ready: bool
    application_success: bool
    path_validation_observed: bool
    tuple_change_observed: bool
    failure_layer: str
    server_remote_addr_count: str
    target_h3_remote_addr_count: str
    counts_toward_final_protocol: str
    notes: str


def run_git_ls_files(pattern: str) -> list[Path]:
    proc = subprocess.run(
        ["git", "ls-files", pattern],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        return []
    return [Path(line.strip()) for line in proc.stdout.splitlines() if line.strip()]


def parse_summary_table(text: str) -> dict[str, str]:
    summary: dict[str, str] = {}
    in_summary = False
    for raw in text.splitlines():
        line = raw.strip()
        if line == "## Summary":
            in_summary = True
            continue
        if in_summary and line.startswith("## "):
            break
        if not in_summary or not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if len(cells) == 2 and cells[0] != "field":
            summary[cells[0]] = cells[1]
    return summary


def parse_draft_csv_row(text: str) -> dict[str, str]:
    match = re.search(r"## Draft CSV Row\s+```csv\n(.*?)\n```", text, re.DOTALL)
    if not match:
        raise ValueError("Draft CSV Row block not found")
    rows = list(csv.DictReader(io.StringIO(match.group(1))))
    if len(rows) != 1:
        raise ValueError(f"expected one draft CSV row, got {len(rows)}")
    return {key: value for key, value in rows[0].items() if key is not None}


def bool_from_csv(value: str) -> bool:
    return value.strip().lower() == "true"


def value_from_notes(notes: str, label: str) -> str:
    match = re.search(rf"{re.escape(label)}\s+(\d+)", notes)
    return match.group(1) if match else "-"


def derive_workload(trial_id: str, application_task: str) -> str:
    lower_id = trial_id.lower()
    lower_task = application_task.lower()
    if "range" in lower_id or "range" in lower_task:
        return "byte_range_download"
    if "upload" in lower_id or "upload" in lower_task:
        return "upload"
    if "origin-smoke" in lower_id:
        return "origin_smoke"
    if "downlink" in lower_id or "downlink" in lower_task or "slow-js" in lower_task:
        return "downlink"
    return "unknown"


def derive_retry_policy(trial_id: str) -> str:
    lower = trial_id.lower()
    if "noretry" in lower or "no-retry" in lower:
        return "none"
    if "retry" in lower:
        return "application_retry"
    return "not_labeled"


def derive_trigger_class(migration_trigger: str, deployment_tier: str) -> str:
    trigger = f"{migration_trigger} {deployment_tier}".lower()
    if "active path change" in trigger or "network-change" in trigger or "network_change_cmd" in trigger:
        return "active_network_change"
    if "no network change" in trigger or "no active path-change" in trigger or "baseline" in trigger:
        return "nochange_baseline"
    return "unknown"


def parse_trial(path: Path) -> TrialRecord:
    text = path.read_text(encoding="utf-8")
    summary = parse_summary_table(text)
    row = parse_draft_csv_row(text)
    notes = row.get("notes", "")
    return TrialRecord(
        source_path=path.as_posix(),
        trial_id=row.get("trial_id", summary.get("trial_id", "")),
        date=row.get("date", ""),
        status=row.get("status", summary.get("summary status", "")),
        classification=summary.get("summary classification", row.get("failure_layer", "")),
        claim_strength=summary.get("claim strength", ""),
        trigger_class=derive_trigger_class(row.get("migration_trigger", ""), row.get("deployment_tier", "")),
        workload=derive_workload(row.get("trial_id", ""), row.get("application_task", "")),
        retry_policy=derive_retry_policy(row.get("trial_id", "")),
        page_ready="page-ready" in row.get("trial_id", ""),
        application_success=bool_from_csv(row.get("application_success", "")),
        path_validation_observed=bool_from_csv(row.get("path_validation_observed", "")),
        tuple_change_observed=bool_from_csv(row.get("tuple_change_observed", "")),
        failure_layer=row.get("failure_layer", ""),
        server_remote_addr_count=value_from_notes(notes, "server remote addr count"),
        target_h3_remote_addr_count=value_from_notes(notes, "target h3 remote addr count"),
        counts_toward_final_protocol=summary.get("counts toward final protocol", ""),
        notes=notes,
    )


def count_by(records: list[TrialRecord], field: str) -> dict[str, int]:
    counts = Counter(str(getattr(record, field)) for record in records)
    return dict(sorted(counts.items()))


def build_synthesis(paths: list[Path] | None = None) -> dict[str, Any]:
    selected_paths = paths if paths is not None else run_git_ls_files(DEFAULT_GLOB)
    records = [parse_trial(path) for path in selected_paths]
    active = [record for record in records if record.trigger_class == "active_network_change"]
    baseline = [record for record in records if record.trigger_class == "nochange_baseline"]
    strong_cm_success = [
        record
        for record in active
        if record.status == "PASS"
        and record.application_success
        and record.path_validation_observed
        and record.tuple_change_observed
    ]
    task_success_without_path_validation = [
        record
        for record in active
        if record.application_success and not record.path_validation_observed
    ]
    task_failed_without_path_validation = [
        record
        for record in active
        if not record.application_success and not record.path_validation_observed
    ]
    baseline_h3_confirmed = [
        record
        for record in baseline
        if record.status == "PASS" and record.application_success
    ]

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "source_scope": "tracked git files matching docs/results/controlled-public-chrome-*-validation.md",
        "trial_count": len(records),
        "active_network_change_count": len(active),
        "nochange_baseline_count": len(baseline),
        "baseline_h3_confirmed_count": len(baseline_h3_confirmed),
        "strong_cm_success_count": len(strong_cm_success),
        "task_success_without_path_validation_count": len(task_success_without_path_validation),
        "task_failed_without_path_validation_count": len(task_failed_without_path_validation),
        "status_counts": count_by(records, "status"),
        "classification_counts": count_by(records, "classification"),
        "claim_strength_counts": count_by(records, "claim_strength"),
        "trigger_counts": count_by(records, "trigger_class"),
        "workload_counts": count_by(records, "workload"),
        "records": [asdict(record) for record in records],
        "interpretation": {
            "supported": "Tracked controlled-public Chrome records confirm that the public origin could serve HTTP/3 browser workloads in no-change baselines, and that active path-change trials were executed and classified conservatively.",
            "not_supported": "This corpus does not contain a controlled-public Chrome single-session Connection Migration success: no active-network-change row combines application success, tuple change, and QUIC path validation evidence.",
            "paper_use": "Use these rows as deployment/browser bridge gap evidence and negative controls, not as final browser CM success evidence.",
        },
    }


def emit_csv(synthesis: dict[str, Any]) -> str:
    fields = [
        "source_path",
        "trial_id",
        "date",
        "status",
        "classification",
        "claim_strength",
        "trigger_class",
        "workload",
        "retry_policy",
        "page_ready",
        "application_success",
        "path_validation_observed",
        "tuple_change_observed",
        "failure_layer",
        "server_remote_addr_count",
        "target_h3_remote_addr_count",
        "counts_toward_final_protocol",
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for record in synthesis["records"]:
        writer.writerow({field: record.get(field, "") for field in fields})
    return buffer.getvalue()


def emit_markdown(synthesis: dict[str, Any]) -> str:
    lines = [
        "# Controlled Public Chrome Bridge Synthesis",
        "",
        f"Generated: `{synthesis['generated']}`",
        "",
        "This public-safe synthesis reads tracked Chrome controlled-public validation documents and classifies what they can and cannot prove. It intentionally excludes raw qlogs, NetLogs, pcaps, hostnames, IP addresses, credentials, and untracked local validation notes.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| source scope | `{synthesis['source_scope']}` |",
        f"| trial count | `{synthesis['trial_count']}` |",
        f"| active network-change rows | `{synthesis['active_network_change_count']}` |",
        f"| no-change baseline rows | `{synthesis['nochange_baseline_count']}` |",
        f"| baseline H3 confirmed rows | `{synthesis['baseline_h3_confirmed_count']}` |",
        f"| strong controlled-public CM success rows | `{synthesis['strong_cm_success_count']}` |",
        f"| active task success without path validation rows | `{synthesis['task_success_without_path_validation_count']}` |",
        f"| active task failure without path validation rows | `{synthesis['task_failed_without_path_validation_count']}` |",
        "",
        "## Counts",
        "",
        "| category | counts |",
        "| --- | --- |",
        f"| status | `{synthesis['status_counts']}` |",
        f"| classification | `{synthesis['classification_counts']}` |",
        f"| claim strength | `{synthesis['claim_strength_counts']}` |",
        f"| trigger | `{synthesis['trigger_counts']}` |",
        f"| workload | `{synthesis['workload_counts']}` |",
        "",
        "## Interpretation",
        "",
        f"- Supported: {synthesis['interpretation']['supported']}",
        f"- Not supported: {synthesis['interpretation']['not_supported']}",
        f"- Paper use: {synthesis['interpretation']['paper_use']}",
        "",
        "## Trial Rows",
        "",
        "| trial | status | class | workload | trigger | app success | path validation | tuple change | claim strength |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for record in synthesis["records"]:
        lines.append(
            "| `{trial_id}` | `{status}` | `{classification}` | `{workload}` | `{trigger_class}` | `{application_success}` | `{path_validation_observed}` | `{tuple_change_observed}` | `{claim_strength}` |".format(
                **record
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "These records are useful because they show that the controlled public browser harness can produce both H3 baselines and conservative negative controls. They do not yet close the paper's strongest browser/deployment claim, because the active path-change rows do not show QUIC path validation and application continuity together.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(markdown_path: Path, json_path: Path, csv_path: Path, synthesis: dict[str, Any]) -> None:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(emit_markdown(synthesis), encoding="utf-8")
    json_path.write_text(json.dumps(synthesis, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    csv_path.write_text(emit_csv(synthesis), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    args = parser.parse_args()

    synthesis = build_synthesis()
    write_outputs(Path(args.output), Path(args.json_output), Path(args.csv_output), synthesis)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
