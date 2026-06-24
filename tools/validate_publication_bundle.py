#!/usr/bin/env python3
"""Validate that this public research bundle is reproducible and safe to publish."""

from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


FORBIDDEN_SUFFIXES = (
    ".keys",
    ".pem",
    ".pcap",
    ".pcapng",
    ".sqlog",
    ".tar.gz",
    ".tgz",
)
FORBIDDEN_FILENAMES = {"aws.env", "experiment.env", "credentials", "config"}
SECRET_PATTERNS = {
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "aws_secret_key_label": re.compile(r"AWS_" r"SECRET_ACCESS_KEY|aws_" r"secret_access_key", re.IGNORECASE),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    "private_key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "iam_account_arn": re.compile(r"arn:aws:iam::\d{12}:"),
}
TEXT_SUFFIXES = {
    ".csv",
    ".env",
    ".example",
    ".go",
    ".js",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".sum",
    ".mod",
    ".txt",
    ".yaml",
    ".yml",
}
LINK_PATTERN = re.compile(r"!?\[[^\]]+\]\(([^)]+)\)")


def is_forbidden_artifact(path: Path, root: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    if any(rel.endswith(suffix) for suffix in FORBIDDEN_SUFFIXES):
        return True
    if path.name in FORBIDDEN_FILENAMES and not path.name.endswith(".example"):
        if path.as_posix().endswith("harness/config/aws.env.example"):
            return False
        if path.as_posix().endswith("harness/config/experiment.env.example"):
            return False
        return True
    return False


def git_tracked_files(root: Path) -> list[Path] | None:
    try:
        proc = subprocess.run(
            ["git", "-C", root.as_posix(), "ls-files", "-z"],
            check=True,
            capture_output=True,
            text=False,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    files: list[Path] = []
    for raw in proc.stdout.split(b"\0"):
        if not raw:
            continue
        rel = raw.decode("utf-8", errors="ignore")
        files.append(root / rel)
    return files


def iter_files(root: Path, include_untracked: bool):
    if not include_untracked:
        tracked = git_tracked_files(root)
        if tracked is not None:
            for path in tracked:
                if path.is_file():
                    yield path
            return

    for path in root.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_file():
            yield path


def check_forbidden_artifacts(root: Path, include_untracked: bool) -> list[str]:
    errors: list[str] = []
    for path in iter_files(root, include_untracked):
        if is_forbidden_artifact(path, root):
            errors.append(f"forbidden artifact included: {path.relative_to(root)}")
    return errors


def check_secret_patterns(root: Path, include_untracked: bool) -> list[str]:
    errors: list[str] = []
    for path in iter_files(root, include_untracked):
        if path.suffix and path.suffix not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for name, regex in SECRET_PATTERNS.items():
            if regex.search(text):
                errors.append(f"possible secret pattern {name}: {path.relative_to(root)}")
    return errors


def check_csv_files(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted(root.glob("data/*.csv")) + sorted(root.glob("harness/manifests/*.csv")):
        try:
            with path.open(newline="", encoding="utf-8") as fp:
                rows = list(csv.DictReader(fp))
        except Exception as exc:  # noqa: BLE001 - report validation failure verbatim.
            errors.append(f"csv parse failed: {path.relative_to(root)}: {exc}")
            continue
        if not rows:
            errors.append(f"csv has no data rows: {path.relative_to(root)}")
    return errors


def normalize_link(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    return unquote(target.split("#", 1)[0])


def check_markdown_links(root: Path, include_untracked: bool) -> list[str]:
    errors: list[str] = []
    md_files = [path for path in iter_files(root, include_untracked) if path.suffix == ".md"]
    for md_path in sorted(md_files):
        if ".git" in md_path.parts:
            continue
        text = md_path.read_text(encoding="utf-8", errors="ignore")
        for match in LINK_PATTERN.finditer(text):
            target = normalize_link(match.group(1))
            if not target:
                continue
            parsed = urlparse(target)
            if parsed.scheme or target.startswith("#"):
                continue
            if target.startswith("/"):
                # Absolute paths in historical result notes are not portable,
                # but they are not repository links. The reproducibility guide
                # uses relative links for all current instructions.
                continue
            link_path = (md_path.parent / target).resolve()
            try:
                link_path.relative_to(root)
            except ValueError:
                continue
            if not link_path.exists():
                errors.append(f"broken markdown link: {md_path.relative_to(root)} -> {target}")
    return errors


def check_public_harness_paths(root: Path) -> list[str]:
    errors: list[str] = []
    for path in sorted((root / "harness" / "scripts").glob("*.sh")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "$PROJECT_ROOT/experiments/quic-go-min-repro" in text:
            errors.append(f"stale public repro path in {path.relative_to(root)}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--include-untracked",
        action="store_true",
        help="scan the whole working tree instead of only git-tracked files",
    )
    args = parser.parse_args()

    root = Path(args.root).resolve()
    checks = {
        "forbidden_artifacts": check_forbidden_artifacts(root, args.include_untracked),
        "secret_patterns": check_secret_patterns(root, args.include_untracked),
        "csv_files": check_csv_files(root),
        "markdown_links": check_markdown_links(root, args.include_untracked),
        "public_harness_paths": check_public_harness_paths(root),
    }

    failed = False
    for name, errors in checks.items():
        if errors:
            failed = True
            print(f"{name}=FAIL")
            for error in errors:
                print(f"  - {error}")
        else:
            print(f"{name}=ok")

    if failed:
        return 1
    print("publication_bundle=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
