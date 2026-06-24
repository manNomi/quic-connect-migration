#!/usr/bin/env python3
"""Run the safe, non-destructive verification suite for the research bundle."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class CheckResult:
    name: str
    command: list[str]
    expected_exit_codes: list[int]
    exit_code: int
    duration_seconds: float
    ok: bool
    stdout_tail: str
    stderr_tail: str


def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tail(text: str, limit: int = 2000) -> str:
    if len(text) <= limit:
        return text
    return text[-limit:]


def run_check(name: str, command: list[str], expected_exit_codes: set[int], timeout: int) -> CheckResult:
    started = time.monotonic()
    try:
        proc = subprocess.run(
            command,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        exit_code = proc.returncode
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = exc.stdout.decode("utf-8", errors="ignore") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="ignore") if isinstance(exc.stderr, bytes) else (exc.stderr or "timeout")
    duration = round(time.monotonic() - started, 3)
    return CheckResult(
        name=name,
        command=command,
        expected_exit_codes=sorted(expected_exit_codes),
        exit_code=exit_code,
        duration_seconds=duration,
        ok=exit_code in expected_exit_codes,
        stdout_tail=tail(stdout.strip()),
        stderr_tail=tail(stderr.strip()),
    )


def default_checks(python_bin: str, generated_dir: Path | None = None) -> list[tuple[str, list[str], set[int], int]]:
    paper_tables = "docs/results/paper-tables-20260624.md"
    final_trials = "docs/results/final-browser-handover-trial-audit-20260624.md"
    final_readiness = "docs/results/final-browser-handover-readiness-20260624.md"
    final_run_plan = "docs/results/final-browser-handover-run-plan-20260624.md"
    final_next_trial = "docs/results/final-handover-next-trial-20260624.md"
    final_next_trial_readiness = "docs/results/final-handover-next-trial-readiness-20260624.md"
    storage_report = "docs/results/artifact-storage-report-20260624.md"
    cleanup_dry_run = "docs/results/artifact-cleanup-dry-run-20260624.md"
    research_audit = "docs/results/research-bundle-audit-20260624.md"
    if generated_dir is not None:
        paper_tables = str(generated_dir / "paper-tables.md")
        final_trials = str(generated_dir / "final-browser-handover-trial-audit.md")
        final_readiness = str(generated_dir / "final-browser-handover-readiness.md")
        final_run_plan = str(generated_dir / "final-browser-handover-run-plan.md")
        final_next_trial = str(generated_dir / "final-handover-next-trial.md")
        final_next_trial_readiness = str(generated_dir / "final-handover-next-trial-readiness.md")
        storage_report = str(generated_dir / "artifact-storage-report.md")
        cleanup_dry_run = str(generated_dir / "artifact-cleanup-dry-run.md")
        research_audit = str(generated_dir / "research-bundle-audit.md")

    return [
        (
            "python_compile_core_tools",
            [
                python_bin,
                "-m",
                "py_compile",
                "tools/audit_final_browser_handover_trials.py",
                "tools/audit_research_bundle.py",
                "tools/append_final_handover_result_row.py",
                "tools/check_final_browser_handover_readiness.py",
                "tools/check_next_final_handover_trial_readiness.py",
                "tools/draft_final_handover_result_row.py",
                "tools/plan_artifact_cleanup.py",
                "tools/plan_final_browser_handover_runs.py",
                "tools/select_next_final_handover_trial.py",
                "tools/validate_final_handover_trial_artifact.py",
                "tools/test_append_final_handover_result_row.py",
                "tools/test_check_next_final_handover_trial_readiness.py",
                "tools/test_draft_final_handover_result_row.py",
                "tools/test_final_browser_handover_trial_audit.py",
                "tools/test_validate_final_handover_trial_artifact.py",
                "tools/test_select_next_final_handover_trial.py",
                "tools/verify_research_bundle.py",
                "tools/run_android_chrome_navigation.py",
                "tools/run_safari_webdriver_navigation.py",
            ],
            {0},
            30,
        ),
        ("publication_bundle", [python_bin, "tools/validate_publication_bundle.py"], {0}, 30),
        ("experiment_summary", [python_bin, "tools/summarize_experiment_results.py", "--format", "markdown"], {0}, 30),
        (
            "paper_tables_regeneration_check",
            [python_bin, "tools/build_paper_tables.py", "--output", paper_tables],
            {0},
            30,
        ),
        (
            "final_browser_handover_trial_audit",
            [
                python_bin,
                "tools/audit_final_browser_handover_trials.py",
                "--output",
                final_trials,
            ],
            {0},
            30,
        ),
        (
            "final_browser_handover_trial_audit_regression",
            [python_bin, "tools/test_final_browser_handover_trial_audit.py"],
            {0},
            30,
        ),
        (
            "final_handover_result_row_drafter_regression",
            [python_bin, "tools/test_draft_final_handover_result_row.py"],
            {0},
            30,
        ),
        (
            "final_handover_trial_artifact_validator_regression",
            [python_bin, "tools/test_validate_final_handover_trial_artifact.py"],
            {0},
            30,
        ),
        (
            "final_handover_result_row_append_regression",
            [python_bin, "tools/test_append_final_handover_result_row.py"],
            {0},
            30,
        ),
        (
            "final_handover_next_trial_selector_regression",
            [python_bin, "tools/test_select_next_final_handover_trial.py"],
            {0},
            30,
        ),
        (
            "final_handover_next_trial_readiness_regression",
            [python_bin, "tools/test_check_next_final_handover_trial_readiness.py"],
            {0},
            30,
        ),
        (
            "final_browser_handover_readiness_expected_incomplete",
            [python_bin, "tools/check_final_browser_handover_readiness.py", "--output", final_readiness],
            {1},
            60,
        ),
        (
            "final_handover_next_trial_readiness_expected_incomplete",
            [python_bin, "tools/check_next_final_handover_trial_readiness.py", "--output", final_next_trial_readiness],
            {1},
            60,
        ),
        (
            "final_browser_handover_run_plan",
            [python_bin, "tools/plan_final_browser_handover_runs.py", "--output", final_run_plan],
            {0},
            30,
        ),
        (
            "final_handover_next_trial_selector",
            [python_bin, "tools/select_next_final_handover_trial.py", "--output", final_next_trial],
            {0},
            30,
        ),
        (
            "artifact_storage_report",
            [python_bin, "tools/report_artifact_storage.py", "--output", storage_report],
            {0},
            60,
        ),
        (
            "artifact_cleanup_dry_run_plan",
            [python_bin, "tools/plan_artifact_cleanup.py", "--output", cleanup_dry_run],
            {0},
            60,
        ),
        (
            "research_bundle_audit",
            [python_bin, "tools/audit_research_bundle.py", "--output", research_audit],
            {0},
            60,
        ),
        (
            "research_bundle_require_complete_expected_incomplete",
            [python_bin, "tools/audit_research_bundle.py", "--require-complete"],
            {1},
            60,
        ),
        (
            "final_trials_require_complete_expected_incomplete",
            [python_bin, "tools/audit_final_browser_handover_trials.py", "--require-complete"],
            {1},
            30,
        ),
        ("handover_readiness", [python_bin, "tools/check_handover_readiness.py", "--format", "markdown"], {0}, 30),
        ("browser_observability", [python_bin, "tools/check_browser_cm_observability.py", "--format", "markdown"], {0}, 30),
        (
            "safari_network_change_script_syntax",
            ["bash", "-n", "repro/quic-go-min-repro/scripts/run-safari-controlled-public-network-change.sh"],
            {0},
            30,
        ),
        (
            "android_chrome_network_change_script_syntax",
            ["bash", "-n", "repro/quic-go-min-repro/scripts/run-android-chrome-controlled-public-network-change.sh"],
            {0},
            30,
        ),
        ("git_diff_check", ["git", "diff", "--check"], {0}, 30),
    ]


def build_report(results: list[CheckResult]) -> dict[str, Any]:
    return {
        "generated_at": now_utc(),
        "check_count": len(results),
        "passed_count": sum(1 for result in results if result.ok),
        "ok": all(result.ok for result in results),
        "results": [asdict(result) for result in results],
    }


def emit_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Research Verification Report",
        "",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Summary",
        "",
        "| check | value |",
        "| --- | --- |",
        f"| checks | `{report['check_count']}` |",
        f"| passed | `{report['passed_count']}` |",
        f"| verification ok | `{'yes' if report['ok'] else 'no'}` |",
        "",
        "## Checks",
        "",
        "| check | exit | expected | ok | duration s |",
        "| --- | ---: | --- | --- | ---: |",
    ]
    for result in report["results"]:
        expected = ",".join(str(code) for code in result["expected_exit_codes"])
        lines.append(
            f"| `{result['name']}` | {result['exit_code']} | `{expected}` | `{'yes' if result['ok'] else 'no'}` | {result['duration_seconds']} |"
        )
    lines.extend(["", "## Failed Output", ""])
    failures = [result for result in report["results"] if not result["ok"]]
    if not failures:
        lines.append("-")
    for result in failures:
        lines.extend(
            [
                f"### {result['name']}",
                "",
                "stdout:",
                "",
                "```text",
                result["stdout_tail"] or "",
                "```",
                "",
                "stderr:",
                "",
                "```text",
                result["stderr_tail"] or "",
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", default="docs/results/research-verification-report-20260624.md")
    parser.add_argument(
        "--scratch-dir",
        help="write generated intermediate reports under this directory instead of tracked docs/results paths",
    )
    parser.add_argument("--continue-on-failure", action="store_true")
    args = parser.parse_args()

    scratch_dir = Path(args.scratch_dir) if args.scratch_dir else None
    if scratch_dir is not None:
        scratch_dir.mkdir(parents=True, exist_ok=True)

    results: list[CheckResult] = []
    for name, command, expected, timeout in default_checks(args.python, scratch_dir):
        result = run_check(name, command, expected, timeout)
        results.append(result)
        if not result.ok and not args.continue_on_failure:
            break

    report = build_report(results)
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
