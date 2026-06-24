#!/usr/bin/env python3
"""Check AWS identity readiness without printing account-specific values."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path


DEFAULT_OUTPUT = "docs/results/aws-identity-public-safe-check-20260624.md"


@dataclass
class AwsIdentityCheck:
    check_date: str
    aws_cli_found: bool
    aws_cli_version_present: bool
    region_configured: bool
    credential_source_present: bool
    sts_identity_ok: bool
    sts_error_code: str
    public_safe: bool = True


def run_command(args: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def error_code(stderr: str) -> str:
    match = re.search(r"\(([^)]+)\)\s+when calling", stderr)
    if match:
        return match.group(1)
    if "Unable to locate credentials" in stderr:
        return "NoCredentials"
    if "ExpiredToken" in stderr:
        return "ExpiredToken"
    if "InvalidClientTokenId" in stderr:
        return "InvalidClientTokenId"
    return "unknown" if stderr.strip() else ""


def build_report(timeout: int) -> AwsIdentityCheck:
    aws_path = shutil.which("aws")
    region_configured = bool(os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION"))
    credential_source_present = bool(
        os.environ.get("AWS_ACCESS_KEY_ID")
        or os.environ.get("AWS_PROFILE")
        or Path.home().joinpath(".aws", "credentials").exists()
    )
    version_present = False
    sts_ok = False
    sts_error = ""

    if aws_path:
        version = run_command(["aws", "--version"], timeout)
        version_present = version.returncode == 0 and bool((version.stdout + version.stderr).strip())
        if not region_configured:
            configured_region = run_command(["aws", "configure", "get", "region"], timeout)
            region_configured = configured_region.returncode == 0 and bool(configured_region.stdout.strip())
        sts = run_command(["aws", "sts", "get-caller-identity", "--output", "json"], timeout)
        sts_ok = sts.returncode == 0
        if not sts_ok:
            sts_error = error_code(sts.stderr)

    return AwsIdentityCheck(
        check_date=date.today().isoformat(),
        aws_cli_found=bool(aws_path),
        aws_cli_version_present=version_present,
        region_configured=region_configured,
        credential_source_present=credential_source_present,
        sts_identity_ok=sts_ok,
        sts_error_code=sts_error,
    )


def emit_markdown(report: AwsIdentityCheck) -> str:
    rows = asdict(report)
    lines = [
        "# AWS Identity Public-Safe Check",
        "",
        f"Generated: `{report.check_date}`",
        "",
        "This report intentionally does not print AWS account IDs, ARNs, access keys, profiles, or credential file paths.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
    ]
    for key, value in rows.items():
        if isinstance(value, bool):
            rendered = "yes" if value else "no"
        else:
            rendered = value or "-"
        lines.append(f"| `{key}` | `{rendered}` |")

    if not report.sts_identity_ok:
        lines.extend(
            [
                "",
                "## Next Action",
                "",
                "- Refresh or replace local AWS credentials, then rerun `harness/scripts/aws-preflight.sh`.",
                "- If AWS automation is not needed, this does not block manual controlled-public origin setup.",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--require-ok", action="store_true")
    args = parser.parse_args()

    report = build_report(args.timeout)
    text = json.dumps(asdict(report), indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    if args.require_ok and not report.sts_identity_ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
