#!/usr/bin/env python3
"""Regression tests for the final capture storage budget builder."""

from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

from build_final_capture_storage_budget import build_budget, emit_markdown, write_csv


def write_fixture(path: Path, text: str) -> None:
    path.write_text(dedent(text).lstrip(), encoding="utf-8")


def make_args(root: Path) -> argparse.Namespace:
    matrix = root / "matrix.csv"
    artifact_root = root / "artifacts"
    artifact_root.mkdir()
    (artifact_root / "sample.bin").write_bytes(b"x" * 1024)
    write_fixture(
        matrix,
        """
        order,trial_id,requirement_id,phase,browser,heartbeat,ready,state,required_gates,missing_gates
        1,t1,r1,baseline,Chrome,n/a,False,blocked,disk_ready,
        2,t2,r2,active-network-change,Chrome,false,False,blocked,disk_ready,
        3,t3,r3,active-network-change,Chrome,true,True,ready,disk_ready,
        """,
    )
    return argparse.Namespace(
        matrix=matrix.as_posix(),
        roots=[artifact_root.as_posix()],
        max_entries=5,
        per_trial_reserve_gib=0.001,
        min_free_gib=0.0,
    )


def test_budget_counts_remaining_rows_and_outputs_csv() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        budget = build_budget(make_args(root))
        rows = {row["scope"]: row for row in budget["rows"]}
        output = root / "budget.csv"
        write_csv(budget, output)
        assert budget["remaining_planned_executions"] == 2
        assert budget["next_trial"] == "t1"
        assert rows["next-planned-execution"]["planned_executions"] == 1
        assert rows["all-remaining-final-executions"]["planned_executions"] == 2
        assert output.exists()


def test_budget_markdown_is_public_safe() -> None:
    with TemporaryDirectory() as tmp:
        budget = build_budget(make_args(Path(tmp)))
        markdown = emit_markdown(budget)
        assert "Final Capture Storage Budget" in markdown
        assert "PRIVATE_KEY" not in markdown
        assert "AKIA" not in markdown


def main() -> int:
    test_budget_counts_remaining_rows_and_outputs_csv()
    test_budget_markdown_is_public_safe()
    print("build_final_capture_storage_budget=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
