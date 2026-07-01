#!/usr/bin/env python3
"""Build a public-safe summary of implementation findings excluding quic-go."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_SURVEY = "data/implementation-survey.csv"
DEFAULT_OUTPUT = "docs/results/non-quicgo-implementation-findings-20260701.md"
DEFAULT_JSON_OUTPUT = "data/non-quicgo-implementation-findings-20260701.json"


CLAIM_ORDER = [
    "strong_cross_implementation_positive",
    "server_or_app_runtime_positive",
    "focused_or_partial_positive",
    "source_or_readiness_only",
    "negative_control",
    "managed_or_deployment_pending",
]


def read_survey(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def classify(row: dict[str, str]) -> str:
    name = row.get("name", "")
    status = row.get("evidence_status", "")
    level = row.get("current_level", "")
    category = row.get("category", "")

    if "negative" in status or name == "HAProxy QUIC":
        return "negative_control"
    if status in {"fresh_app_demo_20260630", "fresh_runtime_20260630", "fresh_runtime_20260701"}:
        return "server_or_app_runtime_positive"
    if status in {
        "fresh_rebind_demo_20260630",
        "fresh_focused_e2e_20260630",
        "fresh_focused_e2e_full_gate_20260701",
    } or "partial" in level:
        return "focused_or_partial_positive"
    if status == "fresh_rerun_20260630":
        return "strong_cross_implementation_positive"
    if status == "source_policy_audit_20260701":
        return "source_or_readiness_only"
    if status == "source_edge_boundary_audit_20260701":
        return "managed_or_deployment_pending"
    if "managed" in category or "lb_plus_server" in category or status == "partial_deferred":
        return "managed_or_deployment_pending"
    return "source_or_readiness_only"


def risk_note(row: dict[str, str]) -> str:
    name = row.get("name", "")
    if name == "Cloudflare quiche":
        return "Library/sample evidence is strong, but Cloudflare managed edge behavior is a separate deployment claim."
    if name == "AWS s2n-quic":
        return "Library tests are positive; live AWS NLB forwarding and active source migration remain separate phases."
    if name == "ngtcp2":
        return "Official osslclient/osslserver local HTTP/3 runtime row is positive; browser handover and managed deployment remain separate claims."
    if name == "LiteSpeed lsquic":
        return "Example app demos are positive; OpenLiteSpeed production-like deployment is still follow-up."
    if name == "MsQuic":
        return "NAT rebind/path validation tests are positive; API audit shows constrained local-address control, while QUIC-aware load balancing remains a deployment boundary."
    if name == "Chromium Chrome Cronet":
        return "Policy hooks, NetLog migration events, and Cronet default-disable evidence exist, but browser handover success still requires runtime rows."
    if name == "AWS CloudFront":
        return "Official docs support viewer-edge HTTP/3 Connection Migration, but origin end-to-end QUIC CM is not established."
    if name == "AWS NLB plus s2n-quic":
        return "Local CID provider proof exists, but live target forwarding and active migration are pending."
    if name == "mvfst":
        return "Focused source/test map is strong and a Linux focused-test runner is packaged; local build/test execution remains gated by Buck/getdeps/disk."
    if name == "nginx QUIC":
        return "Server runtime evidence is positive; Linux quic_bpf and browser handover are separate claims."
    if name == "quicly":
        return "Focused path-migration e2e is positive and a Linux full-e2e gate is packaged; full e2e PASS still requires validation=ok_full_e2e."
    if name == "XQUIC":
        return "NAT rebinding demo passed and Linux full-suite replay runner is packaged; full-suite PASS still requires a Linux ok artifact."
    if name == "HAProxy QUIC":
        return "HTTP/3 proxy success is a negative control for active migration support."
    if name == "aioquic":
        return "Readable passive/path-validation reference; not a primary active-migration API candidate."
    return "Use as implementation maturity evidence, not as browser or managed-deployment proof."


def build_findings(survey_path: Path) -> dict[str, Any]:
    rows = [row for row in read_survey(survey_path) if row.get("name") != "quic-go"]
    enriched: list[dict[str, str]] = []
    for row in rows:
        record = dict(row)
        record["claim_class"] = classify(row)
        record["risk_note"] = risk_note(row)
        enriched.append(record)

    by_class = Counter(row["claim_class"] for row in enriched)
    by_status = Counter(row.get("evidence_status", "-") for row in enriched)
    active_yes = sum(1 for row in enriched if row.get("active_migration_api") == "yes")
    passive_yes = sum(1 for row in enriched if row.get("passive_migration") == "yes")
    tests_yes = sum(1 for row in enriched if row.get("tests") == "yes")

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "source_path": survey_path.as_posix(),
        "summary": {
            "survey_rows_excluding_quic_go": len(enriched),
            "claim_class_counts": {key: by_class.get(key, 0) for key in CLAIM_ORDER},
            "evidence_status_counts": dict(sorted(by_status.items())),
            "active_migration_api_yes": active_yes,
            "passive_migration_yes": passive_yes,
            "tests_yes": tests_yes,
            "interpretation": "Non-quic-go evidence is broad enough to reject an implementation-absence explanation, but each stack has a different claim boundary.",
        },
        "implementations": enriched,
        "reporting_boundary": {
            "safe_claim": "quic-go is not the only implementation with CM evidence; multiple non-quic-go stacks expose tests, runtime demos, path validation, or policy hooks.",
            "unsafe_claim": "All non-quic-go implementations provide equal active migration behavior, browser continuity, or production deployment success.",
            "professor_answer": "We used quic-go as the deepest controllable positive control, then added non-quic-go evidence as cross-implementation maturity, server/app demos, readiness blockers, and negative controls.",
        },
    }


def emit_markdown(findings: dict[str, Any]) -> str:
    summary = findings["summary"]
    lines = [
        "# Non-quic-go Implementation Findings",
        "",
        f"Generated: `{findings['generated']}`",
        "",
        "This public-safe report answers the narrow question: what did we find outside quic-go? It uses `data/implementation-survey.csv` as the source of truth and intentionally separates implementation maturity from browser, CDN, LB, and application-continuity claims.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| survey rows excluding quic-go | `{summary['survey_rows_excluding_quic_go']}` |",
        f"| claim class counts | `{summary['claim_class_counts']}` |",
        f"| evidence status counts | `{summary['evidence_status_counts']}` |",
        f"| active migration API yes | `{summary['active_migration_api_yes']}` |",
        f"| passive migration yes | `{summary['passive_migration_yes']}` |",
        f"| tests yes | `{summary['tests_yes']}` |",
        f"| interpretation | {summary['interpretation']} |",
        "",
        "## Professor-facing Answer",
        "",
        findings["reporting_boundary"]["professor_answer"],
        "",
        "## Safe Boundary",
        "",
        f"- Safe claim: {findings['reporting_boundary']['safe_claim']}",
        f"- Unsafe claim: {findings['reporting_boundary']['unsafe_claim']}",
        "",
        "## Implementation Table",
        "",
        "| priority | name | claim class | evidence status | level | active API | passive | tests | risk note | next action |",
        "| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in findings["implementations"]:
        lines.append(
            "| {priority} | {name} | `{claim_class}` | `{evidence_status}` | `{current_level}` | `{active}` | `{passive}` | `{tests}` | {risk_note} | {next_action} |".format(
                priority=row.get("priority", "-"),
                name=row.get("name", "-"),
                claim_class=row.get("claim_class", "-"),
                evidence_status=row.get("evidence_status", "-"),
                current_level=row.get("current_level", "-"),
                active=row.get("active_migration_api", "-"),
                passive=row.get("passive_migration", "-"),
                tests=row.get("tests", "-"),
                risk_note=row.get("risk_note", "-"),
                next_action=row.get("next_action", "-"),
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "1. quic-go remains the deepest controllable AddPath/Probe/Switch positive control.",
            "2. Non-quic-go results are not empty: quiche, picoquic, s2n-quic, LSQUIC, nginx QUIC, MsQuic, ngtcp2, Quinn, Neqo, XQUIC, quicly, and aioquic all contribute different evidence levels.",
            "3. HAProxy is valuable because it is a negative control: ordinary HTTP/3 availability does not imply active Connection Migration support.",
            "4. Chromium/Cronet, CloudFront, AWS NLB+s2n, and mvfst should be reported as policy/deployment/readiness boundaries until their runtime gates open.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(output: Path, json_output: Path, findings: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(findings), encoding="utf-8")
    json_output.write_text(json.dumps(findings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--survey", default=DEFAULT_SURVEY)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    findings = build_findings(Path(args.survey))
    write_outputs(Path(args.output), Path(args.json_output), findings)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
