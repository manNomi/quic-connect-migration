#!/usr/bin/env python3
"""Scan public HTTPS endpoints for DNS/TLS/Alt-Svc readiness."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path

import check_public_origin_readiness


def read_urls(args: argparse.Namespace) -> list[str]:
    urls: list[str] = []
    if args.url_file:
        for line in Path(args.url_file).read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                urls.append(stripped)
    urls.extend(args.urls)
    unique: list[str] = []
    seen: set[str] = set()
    for url in urls:
        if url not in seen:
            unique.append(url)
            seen.add(url)
    return unique


def result_row(result: check_public_origin_readiness.PublicOriginReadiness) -> dict[str, object]:
    payload = asdict(result)
    status_code = ""
    status_parts = result.final_status.split()
    if len(status_parts) >= 2 and status_parts[1].isdigit():
        status_code = status_parts[1]
    browser_h3_candidate = result.ok and result.has_h3_alt_svc
    workload_candidate = browser_h3_candidate and status_code.startswith("2")
    payload["https_readiness_ok"] = result.ok
    payload["browser_h3_candidate"] = browser_h3_candidate
    payload["workload_candidate"] = workload_candidate
    payload["dns_addresses"] = " ".join(result.dns_addresses)
    payload["errors"] = " | ".join(result.errors)
    return payload


def emit_csv(results: list[check_public_origin_readiness.PublicOriginReadiness]) -> str:
    if not results:
        return ""
    import io

    rows = [result_row(result) for result in results]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def emit_markdown(results: list[check_public_origin_readiness.PublicOriginReadiness]) -> str:
    lines = [
        "| url | final status | HTTPS OK | h3 Alt-Svc | browser H3 candidate | workload candidate |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for result in results:
        lines.append(
            "| {url} | `{status}` | {https_ok} | {h3} | {browser} | {workload} |".format(
                url=result.url,
                status=result.final_status or "-",
                https_ok="true" if result.tcp_tls_ok else "false",
                h3="true" if result.has_h3_alt_svc else "false",
                browser="true" if result_row(result)["browser_h3_candidate"] else "false",
                workload="true" if result_row(result)["workload_candidate"] else "false",
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

    results = [check_public_origin_readiness.build_result(url, args.timeout) for url in urls]
    if args.format == "csv":
        text = emit_csv(results)
    elif args.format == "json":
        text = json.dumps([result_row(result) for result in results], indent=2, ensure_ascii=False) + "\n"
    else:
        text = emit_markdown(results)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
