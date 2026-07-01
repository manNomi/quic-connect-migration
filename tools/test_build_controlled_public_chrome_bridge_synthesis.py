#!/usr/bin/env python3
"""Regression tests for controlled-public Chrome bridge synthesis."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_controlled_public_chrome_bridge_synthesis import (
    build_synthesis,
    emit_markdown,
    parse_draft_csv_row,
    write_outputs,
)


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def test_draft_csv_parser_reads_one_row() -> None:
    sample = """## Draft CSV Row

```csv
trial_id,date,status,implementation,deployment_tier,protocol,migration_trigger,path_validation_observed,tuple_change_observed,application_task,application_success,manual_intervention_required,failure_layer,artifact_dir,notes
trial-1,2026-06-29,PASS,Chrome,tier,HTTP/3,no network change,false,true,GET /x,true,false,none,artifacts,classification ok; server remote addr count 2
```
"""
    row = parse_draft_csv_row(sample)
    assert row["trial_id"] == "trial-1"
    assert row["application_success"] == "true"


def test_synthesis_keeps_controlled_public_claim_boundary() -> None:
    synthesis = build_synthesis()
    assert synthesis["public_safe"] is True
    assert synthesis["trial_count"] >= 10
    assert synthesis["active_network_change_count"] >= 1
    assert synthesis["nochange_baseline_count"] >= 1
    assert synthesis["baseline_h3_confirmed_count"] >= 1
    assert synthesis["strong_cm_success_count"] == 0
    assert synthesis["task_failed_without_path_validation_count"] >= 1
    assert "PASS_NEGATIVE_CONTROL" in synthesis["status_counts"]
    assert "controlled-public Chrome single-session Connection Migration success" in synthesis["interpretation"]["not_supported"]
    assert all(record["source_path"].startswith("docs/results/controlled-public-chrome-") for record in synthesis["records"])


def test_markdown_is_public_safe() -> None:
    markdown = emit_markdown(build_synthesis())
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "Claim Boundary" in markdown
    assert "do not yet close" in markdown


def test_outputs_are_valid() -> None:
    synthesis = build_synthesis()
    with tempfile.TemporaryDirectory() as tmpdir:
        md = Path(tmpdir) / "synthesis.md"
        js = Path(tmpdir) / "synthesis.json"
        csv = Path(tmpdir) / "synthesis.csv"
        write_outputs(md, js, csv, synthesis)
        assert md.read_text(encoding="utf-8").startswith("# Controlled Public Chrome Bridge Synthesis")
        parsed = json.loads(js.read_text(encoding="utf-8"))
        assert parsed["trial_count"] == synthesis["trial_count"]
        assert csv.read_text(encoding="utf-8").splitlines()[0].startswith("source_path,trial_id,date")


def main() -> int:
    test_draft_csv_parser_reads_one_row()
    test_synthesis_keeps_controlled_public_claim_boundary()
    test_markdown_is_public_safe()
    test_outputs_are_valid()
    print("build_controlled_public_chrome_bridge_synthesis=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
