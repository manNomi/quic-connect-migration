#!/usr/bin/env python3
"""Audit repetition sufficiency for local workload/recovery controls."""

from __future__ import annotations

import argparse
import csv
import math
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from research_clock import utc_date_iso


DEFAULT_WORKLOAD = "data/workload-transition-zone-synthesis-20260624.csv"
DEFAULT_APPLICATION_RECOVERY = "data/application-recovery-tradeoff-20260624.csv"
DEFAULT_DOWNLINK_RECOVERY = "data/downlink-recovery-comparison-20260624.csv"
DEFAULT_POLLING = "data/polling-transition-zone-synthesis-20260624.csv"
DEFAULT_OUTPUT = "docs/results/replication-sufficiency-audit-20260624.md"
DEFAULT_CSV_OUTPUT = "data/replication-sufficiency-audit-20260624.csv"
CONFIDENCE_Z = 1.96
STABLE_LOWER_TARGET = 0.80
FAILURE_UPPER_TARGET = 0.20


CSV_FIELDS = [
    "source",
    "condition_id",
    "condition_label",
    "pass_count",
    "runs",
    "pass_rate",
    "wilson_low_95",
    "wilson_high_95",
    "evidence_role",
    "paper_use",
    "additional_same_outcome_runs_for_rule_of_thumb",
    "next_action",
]


@dataclass(frozen=True)
class AuditRow:
    source: str
    condition_id: str
    condition_label: str
    pass_count: int
    runs: int
    pass_rate: str
    wilson_low_95: str
    wilson_high_95: str
    evidence_role: str
    paper_use: str
    additional_same_outcome_runs_for_rule_of_thumb: str
    next_action: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def int_value(raw: str | None, default: int = 0) -> int:
    if raw in {None, ""}:
        return default
    return int(raw)


def wilson_interval(pass_count: int, runs: int, z: float = CONFIDENCE_Z) -> tuple[float, float]:
    if runs <= 0:
        return 0.0, 1.0
    phat = pass_count / runs
    denominator = 1 + z * z / runs
    center = (phat + z * z / (2 * runs)) / denominator
    half = z * math.sqrt((phat * (1 - phat) / runs) + (z * z / (4 * runs * runs))) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def fmt_float(value: float) -> str:
    return f"{value:.3f}"


def additional_runs_needed(pass_count: int, runs: int, role: str) -> str:
    if role == "stable_candidate":
        for extra in range(0, 51):
            low, _ = wilson_interval(pass_count + extra, runs + extra)
            if low >= STABLE_LOWER_TARGET:
                return str(extra)
        return ">50"
    if role == "failure_candidate":
        for extra in range(0, 51):
            _, high = wilson_interval(pass_count, runs + extra)
            if high <= FAILURE_UPPER_TARGET:
                return str(extra)
        return ">50"
    return "-"


def classify(pass_count: int, runs: int) -> str:
    if runs <= 0:
        return "missing"
    if pass_count == runs:
        return "stable_candidate"
    if pass_count == 0:
        return "failure_candidate"
    return "transition_zone"


def paper_use(role: str, low: float, high: float) -> str:
    if role == "stable_candidate" and low >= STABLE_LOWER_TARGET:
        return "strong local stable-condition support"
    if role == "failure_candidate" and high <= FAILURE_UPPER_TARGET:
        return "strong local failure-condition support"
    if role == "transition_zone":
        return "transition-zone evidence; avoid binary threshold wording"
    if role == "missing":
        return "missing repetition data"
    return "directional local evidence; avoid reliability probability wording"


def next_action(role: str, extra: str) -> str:
    if role == "transition_zone":
        return "add narrower outage windows or more repetitions; report as mixed transition zone for now"
    if role == "stable_candidate" and extra not in {"0", "-"}:
        return f"add {extra} same-outcome repetitions before claiming a strong local stable condition"
    if role == "failure_candidate" and extra not in {"0", "-"}:
        return f"add {extra} same-outcome repetitions before claiming a strong local failure condition"
    if role == "stable_candidate":
        return "current repetitions meet the local rule-of-thumb; still do not generalize to public handover"
    if role == "failure_candidate":
        return "current repetitions meet the local rule-of-thumb; still do not generalize to public handover"
    return "collect repetitions before use"


def make_row(source: str, condition_id: str, condition_label: str, pass_count: int, runs: int) -> AuditRow:
    low, high = wilson_interval(pass_count, runs)
    role = classify(pass_count, runs)
    extra = additional_runs_needed(pass_count, runs, role)
    return AuditRow(
        source=source,
        condition_id=condition_id,
        condition_label=condition_label,
        pass_count=pass_count,
        runs=runs,
        pass_rate=fmt_float(pass_count / runs) if runs else "0.000",
        wilson_low_95=fmt_float(low),
        wilson_high_95=fmt_float(high),
        evidence_role=role,
        paper_use=paper_use(role, low, high),
        additional_same_outcome_runs_for_rule_of_thumb=extra,
        next_action=next_action(role, extra),
    )


def workload_rows(rows: list[dict[str, str]]) -> list[AuditRow]:
    output = []
    for row in rows:
        workload = row.get("workload", "unknown")
        window = row.get("drop_window_ms", "0")
        output.append(
            make_row(
                "workload_transition",
                f"{workload}-{window}ms",
                f"{workload} {window}ms transient outage",
                int_value(row.get("pass_count")),
                int_value(row.get("runs")),
            )
        )
    return output


def application_recovery_rows(rows: list[dict[str, str]]) -> list[AuditRow]:
    output = []
    for row in rows:
        retry = row.get("retry_attempts", "0")
        window = row.get("drop_window_ms", "0")
        output.append(
            make_row(
                "upload_recovery",
                f"upload-retry{retry}-{window}ms",
                f"upload retry={retry} {window}ms outage",
                int_value(row.get("pass_count")),
                int_value(row.get("runs")),
            )
        )
    return output


def downlink_recovery_rows(rows: list[dict[str, str]]) -> list[AuditRow]:
    output = []
    for row in rows:
        policy = row.get("policy", "unknown")
        window = row.get("drop_window_ms", "0")
        output.append(
            make_row(
                "downlink_recovery",
                f"downlink-{policy}-{window}ms",
                f"downlink {policy} {window}ms outage",
                int_value(row.get("pass_count")),
                int_value(row.get("runs")),
            )
        )
    return output


def polling_rows(rows: list[dict[str, str]]) -> list[AuditRow]:
    output = []
    for row in rows:
        window = row.get("drop_window_ms", "0")
        output.append(
            make_row(
                "polling_transition",
                f"poll-{window}ms",
                f"polling/dashboard {window}ms transient outage",
                int_value(row.get("pass_count")),
                int_value(row.get("runs")),
            )
        )
    return output


def build_audit(
    workload_path: Path,
    application_recovery_path: Path,
    downlink_recovery_path: Path,
    polling_path: Path,
) -> dict[str, object]:
    rows = []
    rows.extend(workload_rows(read_csv(workload_path)))
    rows.extend(application_recovery_rows(read_csv(application_recovery_path)))
    rows.extend(downlink_recovery_rows(read_csv(downlink_recovery_path)))
    rows.extend(polling_rows(read_csv(polling_path)))
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "rule_of_thumb": {
            "stable_candidate_lower_95_target": STABLE_LOWER_TARGET,
            "failure_candidate_upper_95_target": FAILURE_UPPER_TARGET,
            "note": "The added-run estimate assumes future repetitions preserve the same all-pass or all-fail outcome.",
        },
        "rows": [asdict(row) for row in rows],
    }


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(value.replace("|", "\\|") for value in row) + " |")
    return "\n".join(lines)


def emit_markdown(audit: dict[str, object]) -> str:
    rows = list(audit["rows"])  # type: ignore[arg-type]
    role_counts = Counter(row["evidence_role"] for row in rows)
    source_counts = Counter(row["source"] for row in rows)
    detail_rows = [
        [
            row["source"],
            f"`{row['condition_id']}`",
            f"{row['pass_count']}/{row['runs']}",
            f"{row['wilson_low_95']}-{row['wilson_high_95']}",
            row["evidence_role"],
            row["paper_use"],
            row["additional_same_outcome_runs_for_rule_of_thumb"],
        ]
        for row in rows
    ]
    next_rows = [[f"`{row['condition_id']}`", row["next_action"]] for row in rows if row["next_action"]]
    rule = audit["rule_of_thumb"]  # type: ignore[assignment]
    sections = [
        "# Replication Sufficiency Audit",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This audit is public-safe. It does not create new experiment results; it checks how cautiously the current repeated local controls should be worded in the paper.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| audited conditions | `{len(rows)}` |",
        f"| source counts | `{dict(sorted(source_counts.items()))}` |",
        f"| evidence roles | `{dict(sorted(role_counts.items()))}` |",
        f"| local stable lower-bound target | `{rule['stable_candidate_lower_95_target']}` |",
        f"| local failure upper-bound target | `{rule['failure_candidate_upper_95_target']}` |",
        "",
        "## Condition Audit",
        "",
        markdown_table(
            [
                "source",
                "condition",
                "PASS/runs",
                "Wilson 95% CI",
                "role",
                "paper use",
                "additional runs",
            ],
            detail_rows,
        ),
        "",
        "## Next Actions",
        "",
        markdown_table(["condition", "next action"], next_rows),
        "",
        "## Interpretation",
        "",
        "- Mixed rows are useful transition-zone evidence, not a binary threshold.",
        "- All-pass and all-fail rows with only three repetitions remain directional unless additional repetitions narrow the interval.",
        "- This audit supports cautious wording such as observed boundary or local control result, not guarantee or probability claims.",
    ]
    return "\n".join(sections).rstrip() + "\n"


def write_csv(audit: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(audit["rows"])  # type: ignore[arg-type]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workload", default=DEFAULT_WORKLOAD)
    parser.add_argument("--application-recovery", default=DEFAULT_APPLICATION_RECOVERY)
    parser.add_argument("--downlink-recovery", default=DEFAULT_DOWNLINK_RECOVERY)
    parser.add_argument("--polling", default=DEFAULT_POLLING)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    args = parser.parse_args()

    audit = build_audit(
        Path(args.workload),
        Path(args.application_recovery),
        Path(args.downlink_recovery),
        Path(args.polling),
    )
    write_csv(audit, Path(args.csv_output))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(audit), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
