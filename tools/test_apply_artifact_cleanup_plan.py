#!/usr/bin/env python3
"""Regression tests for reviewed artifact cleanup application."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

from apply_artifact_cleanup_plan import CONFIRM_TOKEN, apply_cleanup, emit_markdown


def write_fixture(path: Path, text: str) -> None:
    path.write_text(dedent(text).lstrip(), encoding="utf-8")


def args_for(root: Path, experiments: Path, execute: bool = False, confirm: str = "") -> argparse.Namespace:
    target_free_gib = (shutil.disk_usage(".").free + 1024) / (1024**3)
    return argparse.Namespace(
        roots=[root.as_posix()],
        target_free_gib=target_free_gib,
        candidate_policy="review-unreferenced",
        experiments=experiments.as_posix(),
        repetitions=3,
        prefer_p1="safari",
        execute=execute,
        confirm=confirm,
    )


def make_fixture(tmp: str) -> tuple[Path, Path, Path, Path]:
    root = Path(tmp)
    artifacts = root / "artifacts"
    kept = artifacts / "kept-run"
    free = artifacts / "free-run"
    kept.mkdir(parents=True)
    free.mkdir(parents=True)
    (kept / "qlog.txt").write_bytes(b"x" * 4096)
    (free / "netlog.json").write_bytes(b"y" * 4096)
    experiments = root / "experiment-results.csv"
    write_fixture(
        experiments,
        f"""
        trial_id,status,artifact_dir
        kept-trial,PASS,{kept.as_posix()}
        """,
    )
    return artifacts, experiments, kept, free


def test_dry_run_does_not_delete_selected_candidate() -> None:
    with TemporaryDirectory() as tmp:
        artifacts, experiments, kept, free = make_fixture(tmp)
        report = apply_cleanup(args_for(artifacts, experiments))
        markdown = emit_markdown(report)
        assert report["mode"] == "dry-run"
        assert report["executed"] is False
        assert report["selected_count"] == 1
        assert kept.exists()
        assert free.exists()
        assert "would-delete" in markdown


def test_execute_requires_exact_confirmation() -> None:
    with TemporaryDirectory() as tmp:
        artifacts, experiments, kept, free = make_fixture(tmp)
        report = apply_cleanup(args_for(artifacts, experiments, execute=True, confirm="wrong"))
        assert report["executed"] is False
        assert report["refusal_reasons"]
        assert kept.exists()
        assert free.exists()


def test_execute_deletes_only_review_unreferenced_candidate() -> None:
    with TemporaryDirectory() as tmp:
        artifacts, experiments, kept, free = make_fixture(tmp)
        report = apply_cleanup(args_for(artifacts, experiments, execute=True, confirm=CONFIRM_TOKEN))
        assert report["executed"] is True
        assert report["deleted_count"] == 1
        assert kept.exists()
        assert not free.exists()


def main() -> int:
    test_dry_run_does_not_delete_selected_candidate()
    test_execute_requires_exact_confirmation()
    test_execute_deletes_only_review_unreferenced_candidate()
    print("apply_artifact_cleanup_plan=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
