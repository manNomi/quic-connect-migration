#!/usr/bin/env python3
"""Regression tests for the replication run plan builder."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

from build_replication_run_plan import add_disk_guard, build_plan, emit_markdown, write_csv


def write_fixture(path: Path, text: str) -> None:
    path.write_text(dedent(text).lstrip(), encoding="utf-8")


def test_plan_keeps_public_handover_first_and_selects_transition_rows() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        audit = root / "audit.csv"
        write_fixture(
            audit,
            """
            source,condition_id,condition_label,pass_count,runs,pass_rate,wilson_low_95,wilson_high_95,evidence_role,paper_use,additional_same_outcome_runs_for_rule_of_thumb,next_action
            workload_transition,upload-4750ms,upload mixed,1,3,0.333,0.061,0.792,transition_zone,transition-zone evidence,-,refine
            upload_recovery,upload-retry1-12000ms,retry stable,3,3,1.000,0.438,1.000,stable_candidate,directional,13,repeat
            polling_transition,poll-250ms,poll stable,3,3,1.000,0.438,1.000,stable_candidate,directional,13,repeat
            """,
        )
        plan = build_plan(audit)
        rows = plan["rows"]
        assert rows[0]["stage"] == "P0-public-browser-handover"
        assert rows[0]["priority"] == 0
        assert any(row["condition_id"] == "upload-4750ms" for row in rows)
        assert any(row["condition_id"] == "upload-retry1-12000ms" for row in rows)
        assert not any(row["condition_id"] == "poll-250ms" for row in rows)


def test_plan_is_public_safe_and_writable() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        audit = root / "audit.csv"
        output = root / "plan.csv"
        write_fixture(
            audit,
            """
            source,condition_id,condition_label,pass_count,runs,pass_rate,wilson_low_95,wilson_high_95,evidence_role,paper_use,additional_same_outcome_runs_for_rule_of_thumb,next_action
            polling_transition,poll-4000ms,poll mixed,1,3,0.333,0.061,0.792,transition_zone,transition-zone evidence,-,refine
            downlink_recovery,downlink-wait_only_no_retry-6000ms,wait fail,0,3,0.000,0.000,0.562,failure_candidate,directional,13,repeat
            """,
        )
        plan = build_plan(audit)
        markdown = emit_markdown(plan)
        write_csv(plan, output)
        assert "controlled-public final protocol" in markdown
        assert "PRIVATE_KEY" not in markdown
        assert "AKIA" not in markdown
        assert output.exists()


def test_transition_rows_with_target_repetitions_are_marked_reviewed() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        audit = root / "audit.csv"
        write_fixture(
            audit,
            """
            source,condition_id,condition_label,pass_count,runs,pass_rate,wilson_low_95,wilson_high_95,evidence_role,paper_use,additional_same_outcome_runs_for_rule_of_thumb,next_action
            polling_transition,poll-4000ms,poll mixed,1,6,0.167,0.030,0.564,transition_zone,transition-zone evidence,-,refine
            """,
        )
        plan = build_plan(audit)
        row = next(item for item in plan["rows"] if item["condition_id"] == "poll-4000ms")
        assert row["stage"] == "L1-transition-zone-reviewed"
        assert row["priority"] == 3
        assert row["suggested_repetitions"] == "0"
        markdown = emit_markdown(plan)
        assert "L1 transition-zone reviewed rows" in markdown


def test_disk_guard_can_hold_optional_local_replication() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        audit = root / "audit.csv"
        write_fixture(
            audit,
            """
            source,condition_id,condition_label,pass_count,runs,pass_rate,wilson_low_95,wilson_high_95,evidence_role,paper_use,additional_same_outcome_runs_for_rule_of_thumb,next_action
            polling_transition,poll-4000ms,poll mixed,1,6,0.167,0.030,0.564,transition_zone,transition-zone evidence,-,refine
            """,
        )
        plan = add_disk_guard(build_plan(audit), root, min_optional_local_free_gib=999999.0)
        disk = plan["local_optional_replication_disk"]
        assert disk["ready"] is False
        assert disk["recommendation"] == "hold-local-optional-replication"
        markdown = emit_markdown(plan)
        assert "optional local replication disk" in markdown
        assert "hold-local-optional-replication" in markdown


def main() -> int:
    test_plan_keeps_public_handover_first_and_selects_transition_rows()
    test_plan_is_public_safe_and_writable()
    test_transition_rows_with_target_repetitions_are_marked_reviewed()
    test_disk_guard_can_hold_optional_local_replication()
    print("build_replication_run_plan=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
