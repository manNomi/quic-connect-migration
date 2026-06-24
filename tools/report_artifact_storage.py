#!/usr/bin/env python3
"""Report local ignored artifact storage without reading artifact contents."""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import dataclass, asdict
from research_clock import utc_date_iso
from pathlib import Path
from typing import Iterable


DEFAULT_ROOTS = [
    "repro/quic-go-min-repro/artifacts",
    "harness/results",
]


@dataclass
class DirectorySize:
    path: str
    exists: bool
    total_bytes: int
    file_count: int
    directory_count: int


def iter_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    for path in root.rglob("*"):
        if path.is_file():
            yield path


def directory_size(root: Path) -> DirectorySize:
    if not root.exists():
        return DirectorySize(root.as_posix(), False, 0, 0, 0)
    total = 0
    files = 0
    dirs = 0
    for path in root.rglob("*"):
        try:
            if path.is_file():
                total += path.stat().st_size
                files += 1
            elif path.is_dir():
                dirs += 1
        except OSError:
            continue
    return DirectorySize(root.as_posix(), True, total, files, dirs)


def immediate_children(root: Path) -> list[DirectorySize]:
    if not root.exists():
        return []
    children = [path for path in root.iterdir() if path.is_dir()]
    return [directory_size(path) for path in children]


def human_size(size: int) -> str:
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} TiB"


def build_report(roots: list[str], max_entries: int) -> dict[str, object]:
    root_paths = [Path(root) for root in roots]
    root_reports = [directory_size(path) for path in root_paths]
    child_reports: list[DirectorySize] = []
    for path in root_paths:
        child_reports.extend(immediate_children(path))
    child_reports.sort(key=lambda item: item.total_bytes, reverse=True)
    disk = shutil.disk_usage(".")
    total_artifact_bytes = sum(item.total_bytes for item in root_reports)
    return {
        "check_date": utc_date_iso(),
        "disk": {
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
            "free_gib": round(disk.free / (1024**3), 2),
        },
        "artifact_roots": [asdict(item) for item in root_reports],
        "total_artifact_bytes": total_artifact_bytes,
        "top_artifact_dirs": [asdict(item) for item in child_reports[:max_entries]],
        "cleanup_note": "This report does not delete files. Artifact roots are ignored local experiment outputs; remove only after confirming the results are documented or no longer needed.",
    }


def emit_markdown(report: dict[str, object]) -> str:
    disk = report["disk"]
    lines = [
        "# Artifact Storage Report",
        "",
        f"Generated: `{report['check_date']}`",
        "",
        "## Summary",
        "",
        "| metric | value |",
        "| --- | --- |",
        f"| disk free | `{human_size(int(disk['free_bytes']))}` |",
        f"| disk free GiB | `{disk['free_gib']}` |",
        f"| local artifact roots total | `{human_size(int(report['total_artifact_bytes']))}` |",
        "",
        "## Artifact Roots",
        "",
        "| path | exists | size | files | directories |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for item in report["artifact_roots"]:
        lines.append(
            f"| `{item['path']}` | `{str(item['exists']).lower()}` | `{human_size(int(item['total_bytes']))}` | {item['file_count']} | {item['directory_count']} |"
        )
    lines.extend(
        [
            "",
            "## Largest Artifact Directories",
            "",
            "| path | size | files | directories |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for item in report["top_artifact_dirs"]:
        lines.append(
            f"| `{item['path']}` | `{human_size(int(item['total_bytes']))}` | {item['file_count']} | {item['directory_count']} |"
        )
    lines.extend(["", "## Cleanup Note", "", str(report["cleanup_note"])])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", action="append", dest="roots", help="artifact root to include; can be repeated")
    parser.add_argument("--max-entries", type=int, default=20)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    args = parser.parse_args()

    roots = args.roots or DEFAULT_ROOTS
    report = build_report(roots, args.max_entries)
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
