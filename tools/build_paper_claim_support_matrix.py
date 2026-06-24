#!/usr/bin/env python3
"""Build a paper claim-support matrix from generated experiment summaries."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from audit_final_browser_handover_trials import build_audit as build_final_trial_audit
from research_clock import utc_date_iso


DEFAULT_EXPERIMENTS = "data/experiment-results.csv"
DEFAULT_IMPLEMENTATIONS = "data/implementation-survey.csv"
DEFAULT_WORKLOAD = "data/workload-transition-zone-synthesis-20260624.csv"
DEFAULT_APPLICATION_RECOVERY = "data/application-recovery-tradeoff-20260624.csv"
DEFAULT_DOWNLINK_RECOVERY = "data/downlink-recovery-comparison-20260624.csv"
DEFAULT_POLLING = "data/polling-transition-zone-synthesis-20260624.csv"
DEFAULT_REQUIREMENTS = "data/final-browser-handover-required-trials.csv"
DEFAULT_OUTPUT = "docs/results/paper-claim-support-matrix-20260624.md"
DEFAULT_CSV_OUTPUT = "data/paper-claim-support-matrix-20260624.csv"


CSV_FIELDS = [
    "claim_id",
    "support_level",
    "claim_scope",
    "source_artifacts",
    "computed_evidence",
    "safe_paper_wording",
    "do_not_claim",
    "next_proof_needed",
]


@dataclass(frozen=True)
class ClaimRow:
    claim_id: str
    support_level: str
    claim_scope: str
    source_artifacts: str
    computed_evidence: str
    safe_paper_wording: str
    do_not_claim: str
    next_proof_needed: str


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def int_value(raw: str | None, default: int = 0) -> int:
    if raw in {None, ""}:
        return default
    return int(raw)


def count_rows(rows: Iterable[dict[str, str]], **filters: str) -> int:
    total = 0
    for row in rows:
        if all(row.get(key) == expected for key, expected in filters.items()):
            total += 1
    return total


def contains_count(rows: Iterable[dict[str, str]], key: str, token: str) -> int:
    return sum(1 for row in rows if token.lower() in row.get(key, "").lower())


def pass_ratio(rows: list[dict[str, str]], drop_windows: list[str] | None = None) -> str:
    selected = rows
    if drop_windows is not None:
        wanted = set(drop_windows)
        selected = [row for row in rows if row.get("drop_window_ms") in wanted]
    passes = sum(int_value(row.get("pass_count")) for row in selected)
    runs = sum(int_value(row.get("runs")) for row in selected)
    return f"{passes}/{runs}" if runs else "0/0"


def mixed_windows(rows: list[dict[str, str]]) -> str:
    windows = []
    for row in rows:
        passes = int_value(row.get("pass_count"))
        fails = int_value(row.get("fail_count"))
        if passes > 0 and fails > 0:
            windows.append(f"{row['drop_window_ms']}ms {passes}/{passes + fails}")
    return ", ".join(windows) or "-"


def all_pass_windows(rows: list[dict[str, str]]) -> str:
    windows = []
    for row in rows:
        runs = int_value(row.get("runs"))
        passes = int_value(row.get("pass_count"))
        if runs and passes == runs:
            windows.append(f"{row['drop_window_ms']}ms")
    return ", ".join(windows) or "-"


def all_fail_windows(rows: list[dict[str, str]]) -> str:
    windows = []
    for row in rows:
        runs = int_value(row.get("runs"))
        fails = int_value(row.get("fail_count"))
        if runs and fails == runs:
            windows.append(f"{row['drop_window_ms']}ms")
    return ", ".join(windows) or "-"


def stable_and_fail_boundary(rows: list[dict[str, str]]) -> tuple[str, str]:
    all_pass = [
        row
        for row in rows
        if int_value(row.get("runs")) and int_value(row.get("pass_count")) == int_value(row.get("runs"))
    ]
    all_fail = [
        row
        for row in rows
        if int_value(row.get("runs")) and int_value(row.get("fail_count")) == int_value(row.get("runs"))
    ]
    stable = max((int_value(row.get("drop_window_ms")) for row in all_pass), default=0)
    first_fail = min(
        (
            int_value(row.get("drop_window_ms"))
            for row in all_fail
            if stable == 0 or int_value(row.get("drop_window_ms")) > stable
        ),
        default=0,
    )
    stable_text = f"{stable}ms" if stable else "-"
    fail_text = f"{first_fail}ms" if first_fail else "-"
    return stable_text, fail_text


def implementation_evidence(rows: list[dict[str, str]]) -> str:
    total = len(rows)
    active_yes = count_rows(rows, active_migration_api="yes")
    passive_yes = count_rows(rows, passive_migration="yes")
    tests_yes = count_rows(rows, tests="yes")
    high_usage = count_rows(rows, current_level="L4") + contains_count(rows, "current_level", "L5")
    names = ", ".join(row["name"] for row in rows[:5])
    return (
        f"{total} implementations surveyed; active_migration_api=yes for {active_yes}; "
        f"passive_migration=yes for {passive_yes}; tests=yes for {tests_yes}; "
        f"L4/L5-like levels in {high_usage}; top examples: {names}"
    )


def controlled_h3_evidence(experiments: list[dict[str, str]]) -> str:
    rows = [
        row
        for row in experiments
        if row.get("status") == "PASS"
        and row.get("protocol") == "HTTP/3 over QUIC"
        and row.get("path_validation_observed") == "true"
        and row.get("tuple_change_observed") == "true"
        and row.get("application_success") == "true"
        and ("Chrome" not in row.get("implementation", ""))
    ]
    tiers = sorted({row["deployment_tier"] for row in rows})
    tasks = sorted({row["application_task"] for row in rows})
    return f"{len(rows)} PASS rows with path validation, tuple change, and application success; tiers={tiers}; task classes={len(tasks)}"


def negative_control_evidence(experiments: list[dict[str, str]]) -> str:
    controls = [row for row in experiments if row.get("status") == "PASS_NEGATIVE_CONTROL"]
    layers = Counter(row.get("failure_layer", "") for row in controls)
    interesting = [
        "proxy-path-validation",
        "browser-alt-svc-h3-not-observed",
        "browser-multiple-quic-sessions-no-network-change",
        "return-path-loss-application-continuity",
        "transient-return-path-outage-threshold",
    ]
    details = "; ".join(f"{name}={layers[name]}" for name in interesting if layers[name])
    return f"{len(controls)} negative-control rows; {details}"


def workload_evidence(rows: list[dict[str, str]]) -> str:
    downlink = [row for row in rows if row.get("workload") == "downlink"]
    upload = [row for row in rows if row.get("workload") == "upload"]
    downlink_stable, downlink_fail = stable_and_fail_boundary(downlink)
    upload_stable, upload_fail = stable_and_fail_boundary(upload)
    return (
        f"downlink stable-through={downlink_stable}, first all-fail={downlink_fail}, mixed={mixed_windows(downlink)}; "
        f"upload stable-through={upload_stable}, first all-fail={upload_fail}, mixed={mixed_windows(upload)}"
    )


def application_recovery_evidence(rows: list[dict[str, str]]) -> str:
    parts = []
    for retry in ["0", "1", "2"]:
        selected = [row for row in rows if row.get("retry_attempts") == retry]
        stable, first_fail = stable_and_fail_boundary(selected)
        max_sessions = max((int_value(row.get("chrome_quic_sessions_max")) for row in selected), default=0)
        parts.append(f"{retry} retry stable-through={stable}, first all-fail={first_fail}, max Chrome sessions={max_sessions}")
    return "; ".join(parts)


def downlink_recovery_evidence(rows: list[dict[str, str]]) -> str:
    wait_rows = [row for row in rows if row.get("policy") == "wait_only_no_retry"]
    retry_rows = [row for row in rows if row.get("policy") == "retry_enabled_1x500ms"]
    return (
        f"wait-only 6000/9000ms PASS={pass_ratio(wait_rows, ['6000', '9000'])}; "
        f"retry-enabled 6000/9000ms PASS={pass_ratio(retry_rows, ['6000', '9000'])}; "
        f"retry classification={'; '.join(row.get('classification_summary', '') for row in retry_rows)}"
    )


def polling_evidence(rows: list[dict[str, str]]) -> str:
    short_pass = pass_ratio(rows, ["250", "1500", "3000"])
    mixed = mixed_windows(rows)
    all_fail = all_fail_windows(rows)
    max_sessions = max((int_value(row.get("chrome_quic_sessions_max")) for row in rows), default=0)
    return f"250-3000ms PASS={short_pass}; mixed={mixed}; all-fail={all_fail}; max Chrome sessions={max_sessions}"


def final_handover_evidence(requirements: Path, experiments: Path) -> tuple[str, str]:
    audit = build_final_trial_audit(requirements, experiments)
    blockers = "; ".join(audit["blockers"]) or "-"
    evidence = f"final protocol complete={audit['complete']}; requirements={audit['complete_count']}/{audit['requirement_count']}"
    return evidence, blockers


def build_matrix(
    experiments_path: Path,
    implementations_path: Path,
    workload_path: Path,
    application_recovery_path: Path,
    downlink_recovery_path: Path,
    polling_path: Path,
    requirements_path: Path,
) -> dict[str, object]:
    experiments = read_csv(experiments_path)
    implementations = read_csv(implementations_path)
    workload = read_csv(workload_path)
    application_recovery = read_csv(application_recovery_path)
    downlink_recovery = read_csv(downlink_recovery_path)
    polling = read_csv(polling_path)
    final_evidence, final_blockers = final_handover_evidence(requirements_path, experiments_path)

    rows = [
        ClaimRow(
            claim_id="implementation-maturity-is-real-but-heterogeneous",
            support_level="supported_scoped",
            claim_scope="implementation survey",
            source_artifacts=f"{implementations_path}",
            computed_evidence=implementation_evidence(implementations),
            safe_paper_wording=(
                "QUIC connection migration is not merely a paper feature: surveyed implementations expose "
                "path validation, migration or rebinding primitives, tests, and observability at different maturity levels."
            ),
            do_not_claim="Do not claim every HTTP/3 implementation exposes production-ready browser/mobile CM.",
            next_proof_needed="Tie each selected implementation to a runnable reproduction or source-level citation before final paper submission.",
        ),
        ClaimRow(
            claim_id="controlled-quic-http3-cm-can-preserve-workloads",
            support_level="supported_scoped",
            claim_scope="quic-go direct origin and AWS NLB controlled experiments",
            source_artifacts=f"{experiments_path}",
            computed_evidence=controlled_h3_evidence(experiments),
            safe_paper_wording=(
                "In controlled quic-go direct-origin and AWS NLB passthrough settings, explicit QUIC path migration preserved "
                "HTTP/3 request continuity and 1MiB mid-flight upload/download completion."
            ),
            do_not_claim="Do not generalize this result to unmanaged browsers, CDNs, or all load balancers.",
            next_proof_needed="Repeat with at least one non-quic-go server stack or cite why quic-go is the primary experimental implementation.",
        ),
        ClaimRow(
            claim_id="http3-support-alone-is-insufficient",
            support_level="negative_control_supported",
            claim_scope="negative controls across proxy, browser discovery, and outage cases",
            source_artifacts=f"{experiments_path}",
            computed_evidence=negative_control_evidence(experiments),
            safe_paper_wording=(
                "HTTP/3 availability and isolated transport artifacts are insufficient evidence of user-visible connection migration; "
                "negative controls show failure at proxy path validation, browser policy, session attribution, and return-path continuity."
            ),
            do_not_claim="Do not use Alt-Svc discovery, tuple change, or a qlog PATH event alone as browser CM success.",
            next_proof_needed="Keep the evidence chain gate in the final protocol and report each artifact class separately.",
        ),
        ClaimRow(
            claim_id="browser-local-h3-is-ready-but-final-handover-is-pending",
            support_level="not_supported_yet",
            claim_scope="Chrome/Safari/Android final browser handover protocol",
            source_artifacts=f"{experiments_path}; {requirements_path}",
            computed_evidence=final_evidence,
            safe_paper_wording=(
                "The repository has browser H3 baselines and final handover harnesses, but the final browser/mobile active path-change "
                "protocol is not complete yet."
            ),
            do_not_claim="Do not claim Chrome, Safari, or Android Wi-Fi/LTE handover CM success from the current corpus.",
            next_proof_needed=final_blockers,
        ),
        ClaimRow(
            claim_id="workload-direction-changes-continuity-boundary",
            support_level="supported_local_control",
            claim_scope="Chrome forced-H3 local UDP rebinding transient outage controls",
            source_artifacts=f"{workload_path}",
            computed_evidence=workload_evidence(workload),
            safe_paper_wording=(
                "Local outage tolerance is workload-sensitive: downlink and upload enter mixed/failure regions at different outage windows, "
                "so continuity must be measured per workload rather than with one global threshold."
            ),
            do_not_claim="Do not convert the local UDP rebinding boundary into a public network handover threshold.",
            next_proof_needed="Run the same downlink/upload workload pair on the controlled public active-path protocol.",
        ),
        ClaimRow(
            claim_id="application-retry-shifts-upload-boundary-with-session-cost",
            support_level="supported_local_control",
            claim_scope="Chrome forced-H3 local upload retry controls",
            source_artifacts=f"{application_recovery_path}",
            computed_evidence=application_recovery_evidence(application_recovery),
            safe_paper_wording=(
                "Application-level upload retry shifted the local completion boundary to longer outage windows, but it increased completion "
                "latency and Chrome QUIC session churn; this is task recovery, not single-session browser CM."
            ),
            do_not_claim="Do not describe retry-based completion as proof that the original browser QUIC session migrated.",
            next_proof_needed="Measure the same recovery policy under real active path change and compare manual-refresh requirement.",
        ),
        ClaimRow(
            claim_id="downlink-retry-effect-is-not-just-waiting",
            support_level="supported_local_control",
            claim_scope="Chrome forced-H3 local downlink wait-only versus retry controls",
            source_artifacts=f"{downlink_recovery_path}",
            computed_evidence=downlink_recovery_evidence(downlink_recovery),
            safe_paper_wording=(
                "Downlink retry-enabled completion cannot be explained by longer waiting alone: wait-only controls failed at the same "
                "6000ms/9000ms windows where retry-enabled rows completed."
            ),
            do_not_claim="Do not collapse retransmission-only completion and application retry completion into one mechanism.",
            next_proof_needed="Add public active-path downlink rows with retry counters and browser session attribution.",
        ),
        ClaimRow(
            claim_id="polling-dashboard-continuity-has-own-boundary",
            support_level="supported_local_control",
            claim_scope="Chrome forced-H3 local polling/dashboard controls",
            source_artifacts=f"{polling_path}",
            computed_evidence=polling_evidence(polling),
            safe_paper_wording=(
                "Dashboard-like polling has a separate transition zone: short local outages completed, 4000ms was mixed, and longer "
                "windows repeatedly failed; passing rows still need session attribution."
            ),
            do_not_claim="Do not treat polling completion via multiple sessions as single-session browser CM.",
            next_proof_needed="Run controlled public polling/no-change and active-path rows before using it as a browser handover result.",
        ),
        ClaimRow(
            claim_id="publication-ready-browser-cm-claim-remains-blocked",
            support_level="not_supported_yet",
            claim_scope="paper-level browser CM claim",
            source_artifacts=f"{experiments_path}; {requirements_path}",
            computed_evidence=final_evidence,
            safe_paper_wording=(
                "The current publishable contribution should be framed as a maturity, evidence-chain, and workload-continuity study with "
                "controlled implementation/deployment positives and browser handover blockers."
            ),
            do_not_claim="Do not write the final abstract as if real browser/mobile connection migration success has been demonstrated.",
            next_proof_needed=final_blockers,
        ),
    ]

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "rows": [asdict(row) for row in rows],
    }


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(value.replace("|", "\\|").replace("\n", " ") for value in row) + " |")
    return "\n".join(lines)


def emit_markdown(matrix: dict[str, object]) -> str:
    rows = list(matrix["rows"])  # type: ignore[arg-type]
    support_counts = Counter(row["support_level"] for row in rows)
    table_rows = [
        [
            f"`{row['claim_id']}`",
            f"`{row['support_level']}`",
            row["claim_scope"],
            row["computed_evidence"],
            row["safe_paper_wording"],
            row["do_not_claim"],
        ]
        for row in rows
    ]
    next_rows = [[f"`{row['claim_id']}`", row["next_proof_needed"]] for row in rows]
    sections = [
        "# Paper Claim Support Matrix",
        "",
        f"Generated: `{matrix['generated']}`",
        "",
        "This matrix is public-safe. It translates the current measured corpus into claim-level wording guidance so the paper can separate supported results from tempting overclaims.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| claims | `{len(rows)}` |",
        f"| support levels | `{dict(sorted(support_counts.items()))}` |",
        "",
        "## Claim Guidance",
        "",
        markdown_table(
            [
                "claim id",
                "support",
                "scope",
                "computed evidence",
                "safe paper wording",
                "do not claim",
            ],
            table_rows,
        ),
        "",
        "## Next Proof Needed",
        "",
        markdown_table(["claim id", "next proof"], next_rows),
        "",
        "## Interpretation",
        "",
        "- Positive implementation and controlled deployment claims are supported within their stated scope.",
        "- Browser/mobile active handover remains pending until the final protocol rows are completed.",
        "- Application-level recovery results are useful paper evidence only when reported separately from single-session browser CM.",
    ]
    return "\n".join(sections).rstrip() + "\n"


def write_csv(matrix: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(matrix["rows"])  # type: ignore[arg-type]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--implementations", default=DEFAULT_IMPLEMENTATIONS)
    parser.add_argument("--workload", default=DEFAULT_WORKLOAD)
    parser.add_argument("--application-recovery", default=DEFAULT_APPLICATION_RECOVERY)
    parser.add_argument("--downlink-recovery", default=DEFAULT_DOWNLINK_RECOVERY)
    parser.add_argument("--polling", default=DEFAULT_POLLING)
    parser.add_argument("--requirements", default=DEFAULT_REQUIREMENTS)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    args = parser.parse_args()

    matrix = build_matrix(
        Path(args.experiments),
        Path(args.implementations),
        Path(args.workload),
        Path(args.application_recovery),
        Path(args.downlink_recovery),
        Path(args.polling),
        Path(args.requirements),
    )
    write_csv(matrix, Path(args.csv_output))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(matrix), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
