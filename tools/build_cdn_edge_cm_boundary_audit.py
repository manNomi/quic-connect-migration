#!/usr/bin/env python3
"""Build a public-safe CDN/edge Connection Migration boundary audit."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_OUTPUT = "docs/results/cdn-edge-cm-boundary-audit-20260701.md"
DEFAULT_JSON_OUTPUT = "data/cdn-edge-cm-boundary-audit-20260701.json"

AWS_CLOUDFRONT_DISTRIBUTION_SETTINGS_URL = (
    "https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/"
    "DownloadDistValuesGeneral.html"
)
AWS_CLOUDFRONT_API_DISTRIBUTION_CONFIG_URL = (
    "https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_DistributionConfig.html"
)
AWS_CLOUDFRONT_HTTP3_BLOG_URL = (
    "https://aws.amazon.com/blogs/aws/new-http-3-support-for-amazon-cloudfront/"
)
CLOUDFLARE_HTTP3_DOCS_URL = (
    "https://developers.cloudflare.com/speed/optimization/protocol/http3/"
)


@dataclass(frozen=True)
class Evidence:
    id: str
    source: str
    url: str
    lines: str
    topic: str
    observation: str
    implication: str


EVIDENCE = [
    Evidence(
        id="cloudfront-viewer-supported-http-versions",
        source="AWS CloudFront Developer Guide",
        url=AWS_CLOUDFRONT_DISTRIBUTION_SETTINGS_URL,
        lines="147-152",
        topic="Supported HTTP versions",
        observation=(
            "CloudFront documentation scopes supported HTTP versions to viewers communicating "
            "with CloudFront and states that CloudFront supports HTTP/3 connection migration."
        ),
        implication=(
            "This supports a viewer-to-edge migration claim, not an origin end-to-end QUIC "
            "Connection Migration claim."
        ),
    ),
    Evidence(
        id="cloudfront-api-httpversion-viewer-scope",
        source="AWS CloudFront API Reference",
        url=AWS_CLOUDFRONT_API_DISTRIBUTION_CONFIG_URL,
        lines="154-162",
        topic="DistributionConfig.HttpVersion",
        observation=(
            "The HttpVersion field controls the HTTP versions that viewers use to communicate "
            "with CloudFront and includes http3/http2and3 values."
        ),
        implication=(
            "Configuration evidence is viewer-facing; it does not prove the origin leg is QUIC "
            "or migration-preserving."
        ),
    ),
    Evidence(
        id="cloudfront-origin-fetch-boundary",
        source="AWS News Blog",
        url=AWS_CLOUDFRONT_HTTP3_BLOG_URL,
        lines="56-59",
        topic="Viewer HTTP/3 versus origin fetch",
        observation=(
            "The CloudFront HTTP/3 launch post describes client-side migration benefits, then "
            "separates viewer HTTP/3 requests to edge locations from origin fetches continuing "
            "over HTTP/1.1."
        ),
        implication=(
            "CloudFront HTTP/3 should be reported as edge-level continuity unless a separate "
            "experiment proves origin end-to-end QUIC semantics."
        ),
    ),
    Evidence(
        id="cloudfront-no-origin-change-enable",
        source="AWS News Blog",
        url=AWS_CLOUDFRONT_HTTP3_BLOG_URL,
        lines="59-64",
        topic="No origin changes for HTTP/3 enablement",
        observation=(
            "The launch post says HTTP/3 can be enabled for CloudFront distributions without "
            "origin changes."
        ),
        implication=(
            "A no-origin-change enablement model is strong evidence that the managed edge "
            "terminates or translates the protocol boundary."
        ),
    ),
    Evidence(
        id="cloudflare-user-edge-scope",
        source="Cloudflare Speed Docs",
        url=CLOUDFLARE_HTTP3_DOCS_URL,
        lines="118-129",
        topic="HTTP/3 setting scope",
        observation=(
            "Cloudflare's HTTP/3 page states that the setting is for the connection between "
            "the user and Cloudflare and that HTTP/3 connection to the origin is not yet supported."
        ),
        implication=(
            "Cloudflare managed-edge HTTP/3 evidence must not be written as origin end-to-end "
            "Connection Migration evidence."
        ),
    ),
    Evidence(
        id="cloudflare-dashboard-api-toggle",
        source="Cloudflare Speed Docs",
        url=CLOUDFLARE_HTTP3_DOCS_URL,
        lines="143-157",
        topic="HTTP/3 dashboard/API toggle",
        observation="Cloudflare exposes HTTP/3 as a zone setting through dashboard or API toggles.",
        implication=(
            "A CDN setting can make viewer-edge H3 visible while leaving origin transport "
            "semantics outside the application's direct control."
        ),
    ),
]


FORBIDDEN_PUBLIC_TERMS = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AKIA",
    "ASIA",
    "arn:aws:" + "iam::",
]


def build_audit() -> dict[str, Any]:
    evidence = [asdict(item) for item in EVIDENCE]
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "scope": "managed_cdn_edge_connection_migration_boundary",
        "implementations": ["AWS CloudFront", "Cloudflare managed edge"],
        "summary": {
            "evidence_items": len(evidence),
            "cloudfront_viewer_edge_http3_cm": "supported_by_official_docs",
            "cloudfront_origin_end_to_end_quic_cm": "not_established_by_official_docs",
            "cloudflare_viewer_edge_http3": "supported_by_official_docs",
            "cloudflare_origin_http3": "not_supported_in_inspected_official_doc",
            "live_edge_trial_completed": "no",
            "interpretation": (
                "Managed CDN HTTP/3 support is a deployment-layer boundary. It can support "
                "viewer-to-edge continuity while still terminating or translating the origin leg."
            ),
        },
        "conclusion": {
            "safe_cdn_claim": "viewer_edge_http3_continuity_or_capability",
            "unsafe_cdn_claim": "origin_end_to_end_quic_connection_migration_without_separate_origin_evidence",
            "paper_use": (
                "Use this audit to prevent CloudFront/Cloudflare HTTP/3 support from being "
                "misreported as end-to-end browser-origin Connection Migration."
            ),
        },
        "evidence": evidence,
        "reporting_boundary": {
            "safe_claim": (
                "CloudFront official docs support viewer-to-CloudFront HTTP/3 Connection Migration, "
                "and Cloudflare official docs scope HTTP/3 to the user-to-Cloudflare leg."
            ),
            "unsafe_claim": (
                "A CloudFront or Cloudflare HTTP/3 toggle proves end-to-end origin QUIC Connection "
                "Migration, origin qlog path validation, or application-origin single-session continuity."
            ),
            "next_non_iphone_gate": (
                "For CloudFront, run a viewer-edge continuity experiment and label it edge-level; "
                "for origin end-to-end CM, keep using direct-origin or CID-aware load-balancer paths "
                "with server qlog and backend routing evidence."
            ),
        },
    }


def emit_markdown(audit: dict[str, Any]) -> str:
    summary = audit["summary"]
    conclusion = audit["conclusion"]
    lines = [
        "# CDN Edge Connection Migration Boundary Audit",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This public-safe audit narrows the CDN part of the deployment-path claim. It separates viewer-edge HTTP/3 continuity from end-to-end origin QUIC Connection Migration.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| scope | `{audit['scope']}` |",
        f"| implementations | `{audit['implementations']}` |",
        f"| evidence items | `{summary['evidence_items']}` |",
        f"| CloudFront viewer-edge HTTP/3 CM | `{summary['cloudfront_viewer_edge_http3_cm']}` |",
        f"| CloudFront origin end-to-end QUIC CM | `{summary['cloudfront_origin_end_to_end_quic_cm']}` |",
        f"| Cloudflare viewer-edge HTTP/3 | `{summary['cloudflare_viewer_edge_http3']}` |",
        f"| Cloudflare origin HTTP/3 | `{summary['cloudflare_origin_http3']}` |",
        f"| live edge trial completed | `{summary['live_edge_trial_completed']}` |",
        f"| interpretation | {summary['interpretation']} |",
        "",
        "## Conclusion",
        "",
        "| claim axis | result |",
        "| --- | --- |",
        f"| safe CDN claim | `{conclusion['safe_cdn_claim']}` |",
        f"| unsafe CDN claim | `{conclusion['unsafe_cdn_claim']}` |",
        f"| paper use | {conclusion['paper_use']} |",
        "",
        "## Evidence Table",
        "",
        "| id | source | lines | topic | observation | implication |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in audit["evidence"]:
        lines.append(
            f"| `{item['id']}` | [{item['source']}]({item['url']}) | `{item['lines']}` | `{item['topic']}` | {item['observation']} | {item['implication']} |"
        )

    boundary = audit["reporting_boundary"]
    lines.extend(
        [
            "",
            "## Reporting Boundary",
            "",
            f"- Safe claim: {boundary['safe_claim']}",
            f"- Unsafe claim: {boundary['unsafe_claim']}",
            f"- Next non-iPhone gate: {boundary['next_non_iphone_gate']}",
            "",
            "## Paper Interpretation",
            "",
            "1. CDN HTTP/3 support is relevant because it is common in real web deployment, but it is not the same as direct browser-origin QUIC.",
            "2. CloudFront is useful as a managed viewer-edge continuity case; it should not replace direct-origin or CID-aware load-balancer experiments.",
            "3. Cloudflare is useful as a termination-boundary example because the inspected official doc explicitly separates user-to-Cloudflare HTTP/3 from origin HTTP/3.",
            "4. This strengthens the paper framing: CM may be implemented, yet deployment layers can hide, terminate, or translate the semantics that an application researcher wants to measure.",
        ]
    )
    text = "\n".join(lines).rstrip() + "\n"
    for forbidden in FORBIDDEN_PUBLIC_TERMS:
        if forbidden in text:
            raise ValueError(f"public output contains forbidden term: {forbidden}")
    return text


def write_outputs(output: Path, json_output: Path, audit: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(audit), encoding="utf-8")
    json_output.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    write_outputs(Path(args.output), Path(args.json_output), build_audit())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
