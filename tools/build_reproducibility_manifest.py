#!/usr/bin/env python3
"""Build a public-safe reproducibility manifest for the research bundle."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_OUTPUT = "docs/results/reproducibility-manifest-20260624.md"
DEFAULT_JSON_OUTPUT = "data/reproducibility-manifest-20260624.json"


@dataclass
class GitState:
    commit: str
    branch: str


def run(args: list[str], timeout: int = 15) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def git_state() -> GitState:
    commit = run(["git", "rev-parse", "--short", "HEAD"]).stdout.strip() or "unknown"
    branch = run(["git", "branch", "--show-current"]).stdout.strip() or "unknown"
    return GitState(commit=commit, branch=branch)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def parse_markdown_summary(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    summary: dict[str, str] = {}
    in_summary = False
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if line == "## Summary":
            in_summary = True
            continue
        if in_summary and line.startswith("## "):
            break
        if not in_summary or not line.startswith("|") or line.startswith("| ---"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        if len(cells) == 2 and cells[0] != "field" and cells[0] != "check":
            summary[cells[0]] = cells[1]
    return summary


def newest_ci_summary() -> dict[str, str]:
    gh = run(["gh", "run", "list", "--repo", "manNomi/quic-connect-migration", "--limit", "1"], timeout=20)
    if gh.returncode != 0 or not gh.stdout.strip():
        return {"available": "no", "status": "unknown", "conclusion": "unknown", "run_id": "-"}
    # Format: status conclusion title workflow branch event id duration created
    line = gh.stdout.splitlines()[0]
    parts = line.split("\t")
    return {
        "available": "yes",
        "status": parts[0] if len(parts) > 0 else "unknown",
        "conclusion": parts[1] if len(parts) > 1 and parts[1] else "-",
        "workflow": parts[3] if len(parts) > 3 else "-",
        "branch": parts[4] if len(parts) > 4 else "-",
        "event": parts[5] if len(parts) > 5 else "-",
        "run_id": parts[6] if len(parts) > 6 else "-",
        "duration": parts[7] if len(parts) > 7 else "-",
    }


def build_manifest(include_ci: bool = False) -> dict[str, Any]:
    root = Path(".")
    git = git_state()
    experiments = read_csv(root / "data" / "experiment-results.csv")
    requirements = read_csv(root / "data" / "final-browser-handover-required-trials.csv")
    status_counts = Counter(row.get("status", "") for row in experiments)
    final_summary = parse_markdown_summary(root / "docs" / "results" / "research-bundle-audit-20260624.md")
    verification_summary = parse_markdown_summary(root / "docs" / "results" / "research-verification-report-20260624.md")
    external_inputs = parse_markdown_summary(root / "docs" / "results" / "final-handover-external-inputs-20260624.md")
    ci = newest_ci_summary() if include_ci else {"available": "not-requested"}

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "tracked_manifest_note": "The source commit is the commit used when generating this tracked manifest. Regenerate the manifest after checkout to bind it to a later commit.",
        "git": asdict(git),
        "experiment_corpus": {
            "total_trials": len(experiments),
            "status_counts": dict(sorted(status_counts.items())),
            "final_required_rows": len(requirements),
        },
        "verification": {
            "checks": verification_summary.get("checks", "-"),
            "passed": verification_summary.get("passed", "-"),
            "ok": verification_summary.get("verification ok", "-"),
        },
        "research_audit": {
            "publication_bundle_ok": final_summary.get("publication bundle ok", "-"),
            "required_files_ok": final_summary.get("required files ok", "-"),
            "paper_tables_current": final_summary.get("paper tables current", "-"),
            "final_browser_handover_trials": final_summary.get("final browser handover trials", "-"),
            "goal_complete": final_summary.get("goal complete", "-"),
        },
        "readiness": {
            "next_trial": external_inputs.get("next trial", "-"),
            "next_trial_ready": external_inputs.get("next trial ready", "-"),
            "codex_can_run_next_trial_now": external_inputs.get("Codex can run next trial now", "-"),
            "needed_now_inputs": external_inputs.get("needed-now inputs", "-"),
        },
        "ci": ci,
        "key_paths": {
            "audit": "docs/results/research-bundle-audit-20260624.md",
            "verification": "docs/results/research-verification-report-20260624.md",
            "status_dashboard": "docs/results/research-status-dashboard-20260624.md",
            "cm_operational_friction_matrix": "docs/results/cm-operational-friction-matrix-20260624.md",
            "final_protocol_readiness_matrix": "docs/results/final-protocol-readiness-matrix-20260624.md",
            "final_trial_acceptance_scorecard": "docs/results/final-trial-acceptance-scorecard-20260624.md",
            "paper_gap_register": "docs/results/paper-evidence-gap-register-20260624.md",
            "paper_claim_support_matrix": "docs/results/paper-claim-support-matrix-20260624.md",
            "replication_sufficiency_audit": "docs/results/replication-sufficiency-audit-20260624.md",
            "external_inputs": "docs/results/final-handover-external-inputs-20260624.md",
            "trial_packet": "docs/results/final-handover-trial-packet-20260624.md",
            "deploy_packet": "docs/results/controlled-public-origin-deploy-packet-20260624.md",
            "active_path_cookbook": "docs/results/active-path-change-operator-cookbook-20260624.md",
        },
    }


def emit_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Reproducibility Manifest",
        "",
        f"Generated: `{manifest['generated']}`",
        "",
        "This manifest is public-safe. It summarizes reproducibility state without printing domains, credentials, private keys, device IDs, qlogs, keylogs, pcaps, or NetLogs.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| source commit at generation | `{manifest['git']['commit']}` |",
        f"| branch | `{manifest['git']['branch']}` |",
        f"| total trials | `{manifest['experiment_corpus']['total_trials']}` |",
        f"| status counts | `{manifest['experiment_corpus']['status_counts']}` |",
        f"| verification | `{manifest['verification']['passed']}/{manifest['verification']['checks']} passed; ok={manifest['verification']['ok']}` |",
        f"| final browser handover | `{manifest['research_audit']['final_browser_handover_trials']}` |",
        f"| goal complete | `{manifest['research_audit']['goal_complete']}` |",
        f"| next trial | `{manifest['readiness']['next_trial']}` |",
        f"| next trial ready | `{manifest['readiness']['next_trial_ready']}` |",
        f"| needed-now inputs | `{manifest['readiness']['needed_now_inputs']}` |",
        f"| CI | `{manifest['ci'].get('status', '-')}/{manifest['ci'].get('conclusion', '-')}` |",
        "",
        "## Key Paths",
        "",
        "| item | path |",
        "| --- | --- |",
    ]
    for key, path in manifest["key_paths"].items():
        lines.append(f"| `{key}` | `{path}` |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- A green manifest does not mean the final browser handover protocol is complete.",
            "- Completion still requires final browser handover rows to satisfy the required trial protocol.",
            "- This manifest records the exact reproducibility state for the current commit and points to the authoritative audit documents.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--include-ci", action="store_true")
    args = parser.parse_args()

    manifest = build_manifest(include_ci=args.include_ci)
    markdown = emit_markdown(manifest)
    json_text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"

    if args.json_output:
        json_output = Path(args.json_output)
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json_text, encoding="utf-8")

    text = json_text if args.format == "json" else markdown
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
