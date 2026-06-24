#!/usr/bin/env python3
"""Scan QUIC implementation trees for connection-migration evidence.

This is not a conformance test. It is a reproducible first-pass evidence
scanner that turns the manual keyword checks used during the survey into a
repeatable table. Use it on checked-out implementation repositories, then read
the reported files before making a maturity claim.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "artifacts",
    "results",
    "qlog",
    "keylog",
    "node_modules",
    "vendor",
    "target",
    "dist",
    "build",
    "__pycache__",
}

SKIP_SUFFIXES = {
    ".a",
    ".bin",
    ".class",
    ".dylib",
    ".exe",
    ".gif",
    ".gz",
    ".ico",
    ".jpg",
    ".jpeg",
    ".o",
    ".pdf",
    ".png",
    ".so",
    ".tar",
    ".wasm",
    ".zip",
}

PATTERNS: dict[str, list[str]] = {
    "path_validation": [
        r"\bPATH_CHALLENGE\b",
        r"\bPATH_RESPONSE\b",
        r"path validation",
        r"path_validat",
        r"ErrPathNotValidated",
    ],
    "active_migration_api": [
        r"\bAddPath\b",
        r"\bProbe\(",
        r"\bSwitch\(",
        r"path\.Probe",
        r"path\.Switch",
        r"migrate_source",
        r"perform[-_ ]migration",
        r"active migration",
        r"probe_path",
    ],
    "passive_rebinding": [
        r"NAT rebinding",
        r"\brebinding\b",
        r"peer address",
        r"remote address",
        r"address change",
        r"tuple change",
    ],
    "disable_migration_policy": [
        r"disable_active_migration",
        r"DisableActiveMigration",
        r"disable migration",
        r"migration disabled",
    ],
    "preferred_address": [
        r"preferred address",
        r"preferred_address",
        r"PreferredAddress",
    ],
    "cid_and_load_balancing": [
        r"ConnectionIDGenerator",
        r"connection id generator",
        r"QuicServerId",
        r"Server ID",
        r"QUIC[-_ ]LB",
        r"load balanc",
        r"Connection ID",
    ],
    "observability": [
        r"\bqlog\b",
        r"PathEvent",
        r"NetLog",
        r"tracing",
        r"event::",
        r"path event",
    ],
    "tests": [
        r"migration.*test",
        r"test.*migration",
        r"path.*test",
        r"rebinding.*test",
    ],
}


@dataclass
class CategoryResult:
    category: str
    matches: int
    files: set[str]
    examples: list[str]


def iter_files(root: Path, max_file_bytes: int) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            if path.stat().st_size > max_file_bytes:
                continue
        except OSError:
            continue
        yield path


def scan_root(root: Path, max_file_bytes: int, max_examples: int) -> list[dict[str, object]]:
    compiled = {
        category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        for category, patterns in PATTERNS.items()
    }
    results = {
        category: CategoryResult(category, 0, set(), [])
        for category in PATTERNS
    }

    for path in iter_files(root, max_file_bytes):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for line_no, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            for category, regexes in compiled.items():
                if any(regex.search(stripped) for regex in regexes):
                    result = results[category]
                    result.matches += 1
                    result.files.add(rel)
                    if len(result.examples) < max_examples:
                        snippet = stripped[:160]
                        result.examples.append(f"{rel}:{line_no}: {snippet}")

    rows: list[dict[str, object]] = []
    for category in PATTERNS:
        result = results[category]
        rows.append(
            {
                "root": root.as_posix(),
                "category": category,
                "matches": result.matches,
                "files": len(result.files),
                "example_files": "; ".join(sorted(result.files)[:5]),
                "examples": result.examples,
            }
        )
    return rows


def emit_markdown(rows: list[dict[str, object]]) -> None:
    print("| root | category | matches | files | example files |")
    print("| --- | --- | ---: | ---: | --- |")
    for row in rows:
        print(
            "| {root} | {category} | {matches} | {files} | {example_files} |".format(
                root=str(row["root"]).replace("|", "\\|"),
                category=row["category"],
                matches=row["matches"],
                files=row["files"],
                example_files=str(row["example_files"]).replace("|", "\\|"),
            )
        )

    print("\n## Examples")
    for row in rows:
        examples = row["examples"]
        if not examples:
            continue
        print(f"\n### {row['root']} / {row['category']}")
        for example in examples:
            print(f"- `{example}`")


def emit_csv(rows: list[dict[str, object]]) -> None:
    writer = csv.DictWriter(
        sys.stdout,
        fieldnames=["root", "category", "matches", "files", "example_files", "examples"],
    )
    writer.writeheader()
    for row in rows:
        out = dict(row)
        out["examples"] = " | ".join(row["examples"])
        writer.writerow(out)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("roots", nargs="+", help="checked-out implementation directories to scan")
    parser.add_argument("--format", choices=["markdown", "csv", "json"], default="markdown")
    parser.add_argument("--max-file-bytes", type=int, default=2_000_000)
    parser.add_argument("--max-examples", type=int, default=5)
    args = parser.parse_args()

    rows: list[dict[str, object]] = []
    missing: list[str] = []
    for raw_root in args.roots:
        root = Path(raw_root).expanduser().resolve()
        if not root.exists() or not root.is_dir():
            missing.append(raw_root)
            continue
        rows.extend(scan_root(root, args.max_file_bytes, args.max_examples))

    if missing:
        for root in missing:
            print(f"missing directory: {root}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    elif args.format == "csv":
        emit_csv(rows)
    else:
        emit_markdown(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
