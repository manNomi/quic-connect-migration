#!/usr/bin/env python3
"""Build a public-safe dashboard for the current QUIC CM research state."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT = "docs/results/research-status-dashboard-20260624.md"
DEFAULT_JSON_OUTPUT = "data/research-status-dashboard-20260624.json"
DEFAULT_EXPERIMENTS = "data/experiment-results.csv"
DEFAULT_MATRIX = "data/final-protocol-readiness-matrix-20260624.csv"
DEFAULT_SCORECARD = "data/final-trial-acceptance-scorecard-20260624.csv"
DEFAULT_MANIFEST = "data/reproducibility-manifest-20260624.json"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def split_cell(value: str) -> list[str]:
    return [item for item in (value or "").split(";") if item]


def missing_gate_counts(matrix_rows: list[dict[str, str]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for row in matrix_rows:
        for gate in split_cell(row.get("missing_gates", "")):
            counts[gate] += 1
    return dict(sorted(counts.items()))


def first_action_from_missing_gates(counts: dict[str, int]) -> str:
    ordered_actions = [
        (
            ["controlled_public_config_present", "public_origin_host_configured", "public_origin_url_configured", "tls_config_present"],
            "Create and fill the ignored controlled-public origin env file, then validate baseline config.",
        ),
        (
            ["baseline_summary_ready"],
            "Run and register the controlled-public Chrome application H3 baseline.",
        ),
        (
            ["network_change_command_present", "desktop_secondary_path_ready"],
            "Prepare an active secondary path and an operator-approved NETWORK_CHANGE_CMD.",
        ),
        (
            ["android_adb_ready", "android_network_change_command_present"],
            "Connect Android over ADB and provide an Android network-change command if Android P1 is selected.",
        ),
    ]
    for gates, action in ordered_actions:
        if any(gate in counts for gate in gates):
            return action
    return "No missing gate was detected in the matrix."


def build_dashboard(args: argparse.Namespace) -> dict[str, Any]:
    experiments = read_csv(Path(args.experiments))
    matrix = read_csv(Path(args.matrix))
    scorecard = read_csv(Path(args.scorecard))
    manifest = read_json(Path(args.manifest))

    experiment_status_counts = dict(sorted(Counter(row.get("status", "") for row in experiments).items()))
    matrix_state_counts = dict(sorted(Counter(row.get("state", "") for row in matrix).items()))
    scorecard_paper_use_counts = dict(sorted(Counter(row.get("paper_use", "") for row in scorecard).items()))
    missing_counts = missing_gate_counts(matrix)
    final_handover = (manifest.get("research_audit") or {}).get("final_browser_handover_trials", "-")
    verification = manifest.get("verification") or {}
    ci = manifest.get("ci") or {}

    return {
        "generated": date.today().isoformat(),
        "public_safe": True,
        "experiment_trials": len(experiments),
        "experiment_status_counts": experiment_status_counts,
        "verification": {
            "checks": verification.get("checks", "-"),
            "passed": verification.get("passed", "-"),
            "ok": verification.get("ok", "-"),
        },
        "ci": {
            "available": ci.get("available", "-"),
            "status": ci.get("status", "-"),
            "conclusion": ci.get("conclusion", "-"),
            "run_id": ci.get("run_id", "-"),
        },
        "final_browser_handover": final_handover,
        "planned_execution_state_counts": matrix_state_counts,
        "scorecard_paper_use_counts": scorecard_paper_use_counts,
        "missing_gate_counts": missing_counts,
        "next_operator_action": first_action_from_missing_gates(missing_counts),
        "safe_claim_boundary": (
            "Do not claim Chrome/Safari/Android browser handover CM success until the final browser handover protocol has countable rows."
        ),
        "key_paths": {
            "manifest": args.manifest,
            "readiness_matrix": args.matrix,
            "acceptance_scorecard": args.scorecard,
            "experiment_results": args.experiments,
        },
    }


def emit_markdown(dashboard: dict[str, Any]) -> str:
    verification = dashboard["verification"]
    ci = dashboard["ci"]
    lines = [
        "# Research Status Dashboard",
        "",
        f"Generated: `{dashboard['generated']}`",
        "",
        "This dashboard is public-safe. It summarizes tracked, redacted research state without printing private domains, TLS paths, network-change commands, qlogs, NetLogs, pcaps, device IDs, or credentials.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| experiment trials | `{dashboard['experiment_trials']}` |",
        f"| experiment status counts | `{dashboard['experiment_status_counts']}` |",
        f"| verification | `{verification['passed']}/{verification['checks']} passed; ok={verification['ok']}` |",
        f"| CI | `{ci['status']}/{ci['conclusion']} ({ci['run_id']})` |",
        f"| final browser handover | `{dashboard['final_browser_handover']}` |",
        f"| planned execution states | `{dashboard['planned_execution_state_counts']}` |",
        f"| paper-use scorecard | `{dashboard['scorecard_paper_use_counts']}` |",
        "",
        "## Next Operator Action",
        "",
        dashboard["next_operator_action"],
        "",
        "## Missing Gate Counts",
        "",
        "| gate | blocked planned executions |",
        "| --- | ---: |",
    ]
    if dashboard["missing_gate_counts"]:
        for gate, count in dashboard["missing_gate_counts"].items():
            lines.append(f"| `{gate}` | {count} |")
    else:
        lines.append("| - | 0 |")

    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            dashboard["safe_claim_boundary"],
            "",
            "## Key Paths",
            "",
            "| item | path |",
            "| --- | --- |",
        ]
    )
    for item, path in dashboard["key_paths"].items():
        lines.append(f"| `{item}` | `{path}` |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--matrix", default=DEFAULT_MATRIX)
    parser.add_argument("--scorecard", default=DEFAULT_SCORECARD)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    dashboard = build_dashboard(args)
    if args.json_output:
        json_output = Path(args.json_output)
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json.dumps(dashboard, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    text = json.dumps(dashboard, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(dashboard)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
