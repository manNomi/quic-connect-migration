#!/usr/bin/env python3
"""Summarize qlog evidence for QUIC migration and HTTP/3 workload runs."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


EVENT_PATTERNS = {
    "path_challenge": "path_challenge",
    "path_response": "path_response",
    "connection_started": "connection_started",
    "connection_closed": "connection_closed",
    "packet_sent": "packet_sent",
    "packet_received": "packet_received",
    "http3_frame": "http3:frame",
    "chosen_alpn": "chosen_alpn",
    "migration": "migration",
    "path": "path",
}


def iter_qlog_files(root: Path):
    if root.is_file():
        yield root
        return
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in {".sqlog", ".qlog", ".json", ".jsonl", ".txt"}:
            yield path


def count_file(path: Path) -> Counter[str]:
    counts: Counter[str] = Counter()
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return counts
    lowered = text.lower()
    for name, needle in EVENT_PATTERNS.items():
        counts[name] = lowered.count(needle.lower())
    return counts


def emit_markdown(rows: list[dict[str, object]]) -> None:
    headers = ["file", *EVENT_PATTERNS.keys()]
    print("| " + " | ".join(headers) + " |")
    print("| " + " | ".join(["---", *["---:" for _ in EVENT_PATTERNS]]) + " |")
    for row in rows:
        print("| " + " | ".join(str(row[h]).replace("|", "\\|") for h in headers) + " |")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="qlog files or directories")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    rows: list[dict[str, object]] = []
    missing: list[str] = []
    for raw_path in args.paths:
        root = Path(raw_path).expanduser().resolve()
        if not root.exists():
            missing.append(raw_path)
            continue
        for path in iter_qlog_files(root):
            counts = count_file(path)
            row: dict[str, object] = {"file": path.as_posix()}
            row.update({name: counts[name] for name in EVENT_PATTERNS})
            rows.append(row)

    if missing:
        for path in missing:
            print(f"missing path: {path}", file=sys.stderr)
        return 2

    rows.sort(key=lambda row: str(row["file"]))
    if args.format == "json":
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        emit_markdown(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
