#!/usr/bin/env python3
"""Regression tests for artifact cleanup dry-run planning."""

from __future__ import annotations

import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

from plan_artifact_cleanup import build_plan, emit_markdown


def write_fixture(path: Path, text: str) -> None:
    path.write_text(dedent(text).lstrip(), encoding="utf-8")


def test_review_unreferenced_policy_excludes_csv_referenced_artifacts() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        artifacts = root / "artifacts"
        referenced = artifacts / "kept-run"
        unreferenced = artifacts / "free-run"
        referenced.mkdir(parents=True)
        unreferenced.mkdir(parents=True)
        (referenced / "qlog.txt").write_bytes(b"x" * 4096)
        (unreferenced / "netlog.json").write_bytes(b"y" * 4096)
        experiments = root / "experiment-results.csv"
        write_fixture(
            experiments,
            f"""
            trial_id,status,artifact_dir
            referenced-trial,PASS,{referenced.as_posix()}
            """,
        )
        target_free_gib = (shutil.disk_usage(".").free + 1024) / (1024**3)
        plan = build_plan(
            [artifacts.as_posix()],
            target_free_gib,
            candidate_policy="review-unreferenced",
            experiments_path=experiments,
        )
        selected_paths = [item["path"] for item in plan["selected_candidates"]]
        markdown = emit_markdown(plan)
        assert selected_paths == [unreferenced.as_posix()]
        assert referenced.as_posix() not in selected_paths
        assert "candidate_policy=review-unreferenced" in markdown


def main() -> int:
    test_review_unreferenced_policy_excludes_csv_referenced_artifacts()
    print("plan_artifact_cleanup=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
