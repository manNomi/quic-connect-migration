#!/usr/bin/env python3
"""Scan public HTTPS endpoints for HTTP/3 Alt-Svc advertisement."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


@dataclass
class ScanResult:
    scan_date: str
    url: str
    curl_exit: int
    final_status: str
    has_h3_alt_svc: bool
    alt_svc_headers: str
    server_headers: str
    location_headers: str
    error: str


def run_curl(url: str, timeout: int) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["curl", "-sSIL", "--max-time", str(timeout), url],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr.strip()


def parse_headers(url: str, stdout: str, stderr: str, exit_code: int, scan_date: str) -> ScanResult:
    statuses: list[str] = []
    alt_svc: list[str] = []
    servers: list[str] = []
    locations: list[str] = []

    for raw_line in stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        lower = line.lower()
        if lower.startswith("http/"):
            statuses.append(line)
        elif lower.startswith("alt-svc:"):
            alt_svc.append(line.split(":", 1)[1].strip())
        elif lower.startswith("server:"):
            servers.append(line.split(":", 1)[1].strip())
        elif lower.startswith("location:"):
            locations.append(line.split(":", 1)[1].strip())

    alt_joined = " | ".join(alt_svc)
    return ScanResult(
        scan_date=scan_date,
        url=url,
        curl_exit=exit_code,
        final_status=statuses[-1] if statuses else "",
        has_h3_alt_svc="h3" in alt_joined.lower(),
        alt_svc_headers=alt_joined,
        server_headers=" | ".join(servers),
        location_headers=" | ".join(locations),
        error=stderr,
    )


def read_urls(args: argparse.Namespace) -> list[str]:
    urls: list[str] = []
    if args.url_file:
        for line in Path(args.url_file).read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                urls.append(stripped)
    urls.extend(args.urls)
    seen: set[str] = set()
    unique: list[str] = []
    for url in urls:
        if url not in seen:
            unique.append(url)
            seen.add(url)
    return unique


def emit_csv(results: list[ScanResult]) -> str:
    if not results:
        return ""
    import io

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(asdict(results[0]).keys()))
    writer.writeheader()
    for result in results:
        writer.writerow(asdict(result))
    return output.getvalue()


def emit_markdown(results: list[ScanResult]) -> str:
    lines = [
        "| url | final status | h3 Alt-Svc | server | Alt-Svc |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for result in results:
        lines.append(
            "| {url} | `{status}` | {h3} | `{server}` | `{alt}` |".format(
                url=result.url,
                status=result.final_status or "-",
                h3="true" if result.has_h3_alt_svc else "false",
                server=(result.server_headers or "-").replace("|", "\\|"),
                alt=(result.alt_svc_headers or "-").replace("|", "\\|"),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="*")
    parser.add_argument("--url-file")
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--format", choices=["csv", "json", "markdown"], default="markdown")
    parser.add_argument("--output")
    args = parser.parse_args()

    urls = read_urls(args)
    if not urls:
        parser.error("at least one URL or --url-file is required")

    scan_date = date.today().isoformat()
    results = [
        parse_headers(url, stdout, stderr, exit_code, scan_date)
        for url in urls
        for exit_code, stdout, stderr in [run_curl(url, args.timeout)]
    ]

    if args.format == "csv":
        text = emit_csv(results)
    elif args.format == "json":
        text = json.dumps([asdict(result) for result in results], indent=2, ensure_ascii=False) + "\n"
    else:
        text = emit_markdown(results)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
