#!/usr/bin/env python3
"""Build a public-safe evidence bundle that maps artifacts to claim boundaries."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_OUTPUT = "docs/results/sanitized-evidence-bundle-20260630.md"
DEFAULT_JSON_OUTPUT = "data/sanitized-evidence-bundle-20260630.json"


@dataclass(frozen=True)
class EvidenceItem:
    id: str
    chapter: str
    category: str
    implementation: str
    evidence_doc: str
    runner_or_tool: str
    local_artifact_id: str
    claim_strength: str
    supports: str
    do_not_claim: str
    next_gap: str


EVIDENCE_ITEMS = [
    EvidenceItem(
        id="quic-go-active-migration-positive-control",
        chapter="3",
        category="implementation-positive-control",
        implementation="quic-go",
        evidence_doc="docs/results/quic-go-minimum-reproduction-results.md",
        runner_or_tool="harness/scripts/run-local-quic-go.sh",
        local_artifact_id="chapter3-local-quic-go-rerun-20260630",
        claim_strength="strong_local_positive",
        supports="Controlled AddPath/Probe/Switch active migration with qlog path validation and before/after payload continuity.",
        do_not_claim="Chrome, Safari, Android, CDN, or managed deployment handover success.",
        next_gap="Keep as transport positive control; browser and deployment evidence must stay separate.",
    ),
    EvidenceItem(
        id="cross-implementation-fresh-rerun",
        chapter="1",
        category="implementation-maturity",
        implementation="quiche, picoquic, s2n-quic, MsQuic, ngtcp2, aioquic, Quinn, Neqo",
        evidence_doc="docs/results/implementation-rerun-results-20260630.md",
        runner_or_tool="data/implementation-survey.csv",
        local_artifact_id="impl-rerun-20260630T070249Z",
        claim_strength="broad_test_suite",
        supports="Multiple QUIC stacks implement and test path validation, rebinding, migration, and related primitives.",
        do_not_claim="All implementations have identical app-level migration behavior or production deployment readiness.",
        next_gap="Promote selected source-only or partial candidates with focused runtime checks.",
    ),
    EvidenceItem(
        id="quiche-path-event-observability",
        chapter="1",
        category="implementation-observability",
        implementation="Cloudflare quiche",
        evidence_doc="docs/results/quiche-path-event-timeline-20260623.md",
        runner_or_tool="data/quiche-path-event-timeline.csv",
        local_artifact_id="quiche-local-success",
        claim_strength="observability_positive",
        supports="Path lifecycle can be observed with migration/path validation events and qlog-compatible evidence.",
        do_not_claim="Cloudflare managed edge or browser handover semantics.",
        next_gap="Use as lifecycle vocabulary baseline, not as CDN deployment evidence.",
    ),
    EvidenceItem(
        id="lsquic-preferred-address-app-demo",
        chapter="1",
        category="implementation-app-demo",
        implementation="LiteSpeed LSQUIC",
        evidence_doc="docs/results/lsquic-preferred-address-app-demo-20260630.md",
        runner_or_tool="harness/scripts/run-lsquic-preferred-address-demo.sh",
        local_artifact_id="lsquic-preferred-address-script-20260630T095500Z",
        claim_strength="app_level_positive",
        supports="LSQUIC example HTTP/3 client/server completed an app workload with preferred-address path transition evidence.",
        do_not_claim="OpenLiteSpeed production server success.",
        next_gap="Run production-like OpenLiteSpeed server demo on Linux or EC2.",
    ),
    EvidenceItem(
        id="lsquic-nat-rebinding-app-demo",
        chapter="1",
        category="implementation-app-demo",
        implementation="LiteSpeed LSQUIC",
        evidence_doc="docs/results/lsquic-nat-rebinding-app-demo-20260630.md",
        runner_or_tool="harness/scripts/run-lsquic-nat-rebinding-demo.sh",
        local_artifact_id="lsquic-nat-rebinding-demo-20260630T102751Z",
        claim_strength="app_level_positive",
        supports="LSQUIC example HTTP/3 workload completed through local UDP proxy NAT rebinding with new-path validation evidence.",
        do_not_claim="Mobile handover or production OpenLiteSpeed continuity.",
        next_gap="Compare with production-like server integration.",
    ),
    EvidenceItem(
        id="quicly-focused-e2e-path-migration",
        chapter="1",
        category="implementation-focused-e2e",
        implementation="quicly",
        evidence_doc="docs/results/quicly-e2e-path-migration-20260630.md",
        runner_or_tool="harness/scripts/run-quicly-e2e-path-migration-check.sh",
        local_artifact_id="quicly-e2e-path-migration-local-20260630",
        claim_strength="focused_e2e_positive",
        supports="quicly `path-migration` e2e subtest passed, including CID sequence 1 first path probe check.",
        do_not_claim="Full quicly `t/e2e.t` success; the full e2e still fails an unrelated `slow-start` subtest on this host.",
        next_gap="Use Linux/upstream-compatible timing environment to check full e2e cleanliness.",
    ),
    EvidenceItem(
        id="nginx-active-client-migration-runtime",
        chapter="1",
        category="server-runtime-positive-control",
        implementation="nginx QUIC",
        evidence_doc="docs/results/nginx-quic-active-migration-runtime-20260630.md",
        runner_or_tool="harness/scripts/run-nginx-quic-active-migration-demo.sh",
        local_artifact_id="nginx-quic-active-migration-20260630T104724Z",
        claim_strength="server_runtime_positive",
        supports="nginx HTTP/3 server handled quiche active source-port migration and completed a 1MiB response.",
        do_not_claim="Browser handover, client active migration API, or Linux quic_bpf production routing success.",
        next_gap="Run Linux quic_bpf packet-routing deployment check.",
    ),
    EvidenceItem(
        id="haproxy-http3-negative-control",
        chapter="4",
        category="deployment-negative-control",
        implementation="HAProxy QUIC",
        evidence_doc="docs/results/haproxy-http3-negative-control-rerun-20260630.md",
        runner_or_tool="harness/scripts/run-haproxy-http3-negative-control.sh",
        local_artifact_id="haproxy-http3-negative-control-20260630T110201Z",
        claim_strength="negative_control",
        supports="HTTP/3 proxy availability is insufficient evidence of active Connection Migration support.",
        do_not_claim="All future HAProxy versions lack migration support.",
        next_gap="Keep as proxy termination boundary and version-scoped negative control.",
    ),
    EvidenceItem(
        id="nginx-quic-bpf-readiness",
        chapter="4",
        category="deployment-readiness",
        implementation="nginx QUIC",
        evidence_doc="docs/results/nginx-quic-bpf-readiness-20260630.md",
        runner_or_tool="harness/scripts/check-nginx-quic-bpf-readiness.sh",
        local_artifact_id="nginx-quic-bpf-readiness-local-20260630-commitcheck",
        claim_strength="readiness_blocked",
        supports="Current repo separates nginx local runtime evidence from Linux/eBPF quic_bpf production-routing claim.",
        do_not_claim="quic_bpf production deployment success on macOS.",
        next_gap="Rerun on Linux with suitable eBPF/root or capability setup.",
    ),
    EvidenceItem(
        id="nginx-quic-bpf-linux-runner",
        chapter="4",
        category="deployment-runtime-readiness",
        implementation="nginx QUIC",
        evidence_doc="docs/results/nginx-quic-bpf-linux-runner-20260630.md",
        runner_or_tool="harness/scripts/run-nginx-quic-bpf-linux-demo.sh",
        local_artifact_id="nginx-quic-bpf-linux-demo-local-blocked-20260630",
        claim_strength="readiness_blocked",
        supports="The repo has a Linux fail-closed runner that enables nginx `quic_bpf on;` with `listen ... reuseport` and reuses the active migration HTTP/3 workload when host gates are open.",
        do_not_claim="Linux/eBPF quic_bpf migration success on the current macOS host.",
        next_gap="Run the Linux runner on EC2 or another Linux host with root/capability and writable /sys/fs/bpf.",
    ),
    EvidenceItem(
        id="aws-nlb-cid-aware-positive-control",
        chapter="4",
        category="deployment-positive-control",
        implementation="AWS NLB + quic-go",
        evidence_doc="docs/results/aws-nlb-quic-data-plane-results-20260624.md",
        runner_or_tool="harness/scripts/run-aws-nlb-quic-data-plane.sh",
        local_artifact_id="aws-nlb-quic-data-plane-20260624",
        claim_strength="deployment_positive",
        supports="CID-aware NLB passthrough can preserve backend continuity when routable CID layout matches the load balancer contract.",
        do_not_claim="All AWS HTTP/3, CloudFront, or CDN paths preserve end-to-end Connection Migration.",
        next_gap="Repeat with s2n-quic backend once AWS credentials and dedicated runner are ready.",
    ),
    EvidenceItem(
        id="aws-nlb-negative-controls",
        chapter="4",
        category="deployment-negative-control",
        implementation="AWS NLB + malformed/mismatched CID",
        evidence_doc="docs/results/aws-nlb-quic-negative-control-results-20260624.md",
        runner_or_tool="harness/scripts/run-aws-nlb-quic-data-plane.sh",
        local_artifact_id="aws-nlb-cid-negative-20260624",
        claim_strength="negative_control",
        supports="Target health or QUIC listener support is not enough when CID layout or Server ID registration is wrong.",
        do_not_claim="NLB failure under valid routable CID configuration.",
        next_gap="Keep paired with NLB positive control in deployment chapter.",
    ),
    EvidenceItem(
        id="aws-nlb-http3-workload",
        chapter="4",
        category="deployment-application-bridge",
        implementation="AWS NLB + quic-go HTTP/3",
        evidence_doc="docs/results/aws-nlb-http3-workload-results-20260624.md",
        runner_or_tool="repro/quic-go-min-repro/cmd/h3client/main.go",
        local_artifact_id="aws-nlb-http3-workload-20260624",
        claim_strength="application_bridge_positive",
        supports="Transport-level NLB continuity can be extended to a controlled HTTP/3 before/after workload.",
        do_not_claim="Browser-level task continuity or service-worker recovery behavior.",
        next_gap="Compare with browser public-origin handover evidence when device/network setup is available.",
    ),
    EvidenceItem(
        id="s2n-nlb-cid-provider-proof",
        chapter="4",
        category="deployment-prerequisite",
        implementation="s2n-quic",
        evidence_doc="docs/results/s2n-quic-nlb-cid-provider-rerun-20260630.md",
        runner_or_tool="harness/scripts/run-local-s2n-nlb-cid-proof.sh",
        local_artifact_id="local-data-plane-20260630T101625Z",
        claim_strength="local_prerequisite_positive",
        supports="s2n-quic can use an AWS NLB-compatible plaintext CID provider in a local data-plane proof.",
        do_not_claim="Live AWS NLB+s2n target forwarding or active migration success.",
        next_gap="Run the dedicated live AWS NLB+s2n target A/B forwarding runner after credentials are refreshed.",
    ),
    EvidenceItem(
        id="s2n-nlb-live-readiness",
        chapter="4",
        category="deployment-readiness",
        implementation="AWS NLB + s2n-quic",
        evidence_doc="docs/results/s2n-nlb-live-readiness-20260630.md",
        runner_or_tool="harness/scripts/check-s2n-nlb-live-readiness.sh",
        local_artifact_id="s2n-nlb-live-readiness-after-runner-proof-20260630",
        claim_strength="readiness_blocked",
        supports="Current live AWS+s2n experiment is fail-closed because AWS identity is invalid; local proof and dedicated runner readiness are present.",
        do_not_claim="Live AWS resource creation or live s2n NLB migration evidence.",
        next_gap="Refresh AWS credentials and execute the dedicated s2n live NLB forwarding runner.",
    ),
    EvidenceItem(
        id="aws-s2n-nlb-live-runner",
        chapter="4",
        category="deployment-live-runner",
        implementation="AWS NLB + s2n-quic",
        evidence_doc="docs/results/aws-s2n-nlb-live-runner-20260630.md",
        runner_or_tool="harness/scripts/run-aws-s2n-nlb-live-data-plane.sh",
        local_artifact_id="aws-s2n-nlb-live-local-blocked-20260630",
        claim_strength="readiness_blocked",
        supports="The repo has a dedicated AWS NLB+s2n live runner with compiling server/client binaries, a local echo smoke, and a pre-resource AWS identity gate.",
        do_not_claim="Live AWS NLB forwarding success, active migration success, or browser handover.",
        next_gap="Refresh AWS credentials and run the live forwarding echo before designing an active path-change variant.",
    ),
    EvidenceItem(
        id="s2n-active-migration-api-audit",
        chapter="4",
        category="implementation-api-audit",
        implementation="s2n-quic",
        evidence_doc="docs/results/s2n-active-migration-api-audit-20260630.md",
        runner_or_tool="tools/audit_s2n_active_migration_feasibility.py",
        local_artifact_id="s2n-connection-migration-tests-20260630",
        claim_strength="source_test_audit",
        supports="s2n-quic has connection migration/rebinding tests and active-path observability, while the current public app API does not expose a quic-go-like AddPath/Probe/Switch trigger.",
        do_not_claim="AWS NLB+s2n active migration execution, public application-triggered active migration, or browser handover.",
        next_gap="Run live NLB forwarding echo after credential refresh, then design a lower-level active path-change variant or wait for a public API.",
    ),
    EvidenceItem(
        id="openlitespeed-runtime-runner",
        chapter="4",
        category="deployment-readiness",
        implementation="OpenLiteSpeed + LSQUIC",
        evidence_doc="docs/results/openlitespeed-active-migration-runner-20260630.md",
        runner_or_tool="harness/scripts/run-openlitespeed-active-migration-demo.sh",
        local_artifact_id="openlitespeed-active-migration-local-blocked-20260630",
        claim_strength="readiness_blocked",
        supports="The repo has a Linux/EC2 runner for a production-like OpenLiteSpeed active-migration demo and records the current macOS blocker.",
        do_not_claim="OpenLiteSpeed runtime CM success or failure.",
        next_gap="Run on Linux/EC2 with OpenLiteSpeed binary and sufficient disk.",
    ),
    EvidenceItem(
        id="mvfst-source-audit",
        chapter="1",
        category="source-audit",
        implementation="mvfst",
        evidence_doc="docs/results/mvfst-cm-source-audit-20260630.md",
        runner_or_tool="tools/scan_implementation_evidence.py",
        local_artifact_id="mvfst-source-audit-20260630",
        claim_strength="source_test_audit",
        supports="mvfst has dedicated path manager, client active migration flow, server passive migration state machine, qlog/stat hooks, and migration tests.",
        do_not_claim="Local mvfst build/test success.",
        next_gap="Run focused mvfst migration tests on Linux builder.",
    ),
    EvidenceItem(
        id="mvfst-migration-test-readiness",
        chapter="1",
        category="implementation-readiness",
        implementation="mvfst",
        evidence_doc="docs/results/mvfst-migration-test-readiness-20260630.md",
        runner_or_tool="tools/check_mvfst_migration_test_readiness.py",
        local_artifact_id="mvfst-migration-test-readiness-20260630",
        claim_strength="readiness_blocked",
        supports="mvfst latest HEAD has focused migration/path-manager test files, 106 observed test cases, and BUCK targets for path-manager, client active migration, and server passive migration coverage.",
        do_not_claim="Local mvfst build/test success or runtime migration behavior.",
        next_gap="Run BUCK focused targets or getdeps build/test on a Linux or sufficiently provisioned builder.",
    ),
    EvidenceItem(
        id="chromium-cronet-policy-evidence",
        chapter="5",
        category="browser-policy-source",
        implementation="Chromium/Cronet",
        evidence_doc="docs/results/chromium-cronet-source-evidence-20260624.md",
        runner_or_tool="tools/check_browser_cm_observability.py",
        local_artifact_id="chromium-cronet-source-evidence-20260624",
        claim_strength="source_policy_evidence",
        supports="Browser/client stack has migration hooks and NetLog events, but runtime policy controls whether migration occurs.",
        do_not_claim="Chrome or Cronet handover success from source hooks alone.",
        next_gap="Run real browser/network-change trial when non-iPhone path is ready.",
    ),
    EvidenceItem(
        id="safari-webdriver-session-readiness",
        chapter="5",
        category="browser-readiness",
        implementation="Safari desktop + safaridriver",
        evidence_doc="docs/results/safari-webdriver-session-readiness-20260630.md",
        runner_or_tool="tools/check_browser_cm_observability.py",
        local_artifact_id="safari-webdriver-local-smoke-20260630",
        claim_strength="readiness_blocked",
        supports="Safari and safaridriver binaries are present and packet-capture tooling is available, but real WebDriver session creation currently fails because Safari Allow remote automation is not enabled.",
        do_not_claim="Safari controlled-public baseline execution, Safari network-change execution, or Safari browser-internal QUIC session continuity.",
        next_gap="Enable Safari Allow remote automation, rerun session smoke, then run controlled-public Safari baseline.",
    ),
    EvidenceItem(
        id="user-provided-public-origin-readiness",
        chapter="7",
        category="public-origin-readiness",
        implementation="user-provided public HTTPS origin",
        evidence_doc="docs/results/user-provided-public-origin-readiness-20260630.md",
        runner_or_tool="tools/check_public_origin_readiness.py",
        local_artifact_id="user-provided-public-origin-readiness-20260630",
        claim_strength="readiness_blocked",
        supports="The user-provided public HTTPS origin is reachable over HTTPS but does not currently advertise `Alt-Svc: h3`, so it is not a ready controlled-public H3 target.",
        do_not_claim="Chrome controlled-public H3 baseline, browser Connection Migration, or usable public-origin workload continuity.",
        next_gap="Configure a controlled H3 origin with WebPKI TLS, Alt-Svc, and workload endpoints, then rerun readiness with `--require-h3-alt-svc`.",
    ),
    EvidenceItem(
        id="non-iphone-gate-rerun-20260701",
        chapter="7",
        category="cross-gate-readiness",
        implementation="AWS NLB+s2n, Safari desktop, user-provided public origin",
        evidence_doc="docs/results/non-iphone-gate-rerun-20260701.md",
        runner_or_tool="tools/build_non_iphone_gate_rerun_report.py",
        local_artifact_id="non-iphone-gate-rerun-20260701",
        claim_strength="readiness_blocked",
        supports="The current non-iPhone gates were rerun: AWS remains credential-blocked, Safari WebDriver session remains disabled, and the user-provided public origin remains non-H3-ready.",
        do_not_claim="AWS NLB live forwarding, Safari controlled-public execution, Chrome public-origin H3 baseline, or browser Connection Migration.",
        next_gap="Open one gate: refresh AWS credentials, configure a controlled H3 public origin, or enable Safari Allow remote automation.",
    ),
    EvidenceItem(
        id="controlled-public-chrome-bridge-synthesis",
        chapter="7-9",
        category="browser-deployment-bridge-synthesis",
        implementation="Chrome + controlled public quic-go H3",
        evidence_doc="docs/results/controlled-public-chrome-bridge-synthesis-20260701.md",
        runner_or_tool="tools/build_controlled_public_chrome_bridge_synthesis.py",
        local_artifact_id="tracked-controlled-public-chrome-validation-docs-20260629",
        claim_strength="bridge_gap_negative_controls",
        supports="Tracked controlled-public Chrome validation records include H3 no-change baselines and active network-change negative controls; none combine active network change, application continuity, tuple change, and QUIC path validation.",
        do_not_claim="Controlled-public Chrome single-session Connection Migration success, final browser handover success, or upload coverage from untracked local validation notes.",
        next_gap="Open a controlled public H3 origin and rerun page-ready media/range/upload trials with artifact-bundle validation.",
    ),
    EvidenceItem(
        id="chrome-local-rebinding-workload-controls",
        chapter="6",
        category="browser-local-control",
        implementation="Chrome + quic-go local UDP rebinding proxy",
        evidence_doc="docs/results/workload-sensitivity-synthesis-20260629.md",
        runner_or_tool="repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh",
        local_artifact_id="chrome-h3-rebinding-20260624-20260629-series",
        claim_strength="local_browser_control",
        supports="Local Chrome H3 workload controls expose workload-sensitive completion, retry, and session-attribution boundaries.",
        do_not_claim="Real Wi-Fi/cellular handover or single-session browser CM success.",
        next_gap="Use as workload prioritization basis for future controlled public/browser trials.",
    ),
    EvidenceItem(
        id="chrome-desktop-noniphone-media-local-refresh",
        chapter="6/11",
        category="browser-local-media-control",
        implementation="Chrome + quic-go local UDP rebinding proxy",
        evidence_doc="docs/results/chrome-desktop-noniphone-media-local-refresh-20260630.md",
        runner_or_tool="repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh",
        local_artifact_id="chrome-desktop-noniphone-media-drop3000-retry0-20260630",
        claim_strength="local_browser_positive_control",
        supports="A fresh Chrome desktop forced-H3 media run completed across local UDP rebinding with one target QUIC session, two server-observed remote tuples, qlog path validation, and NetLog target path challenge/response evidence.",
        do_not_claim="Public Wi-Fi/LTE handover, iPhone handover, or general browser CM deployment success.",
        next_gap="Run controlled-public page-ready media/upload/range handover once public origin and active path-change gates are open.",
    ),
    EvidenceItem(
        id="chrome-desktop-noniphone-musiclike-local-refresh",
        chapter="11",
        category="browser-local-music-control",
        implementation="Chrome + quic-go local UDP rebinding proxy",
        evidence_doc="docs/results/chrome-desktop-noniphone-musiclike-local-refresh-20260701.md",
        runner_or_tool="repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh",
        local_artifact_id="chrome-desktop-noniphone-musiclike-20260701-pair",
        claim_strength="local_browser_recovery_control",
        supports="Fresh Chrome desktop music-like segment rows reconfirm that a 6000ms local outage fails without segment retry but completes with one retry via multiple QUIC sessions.",
        do_not_claim="Music streaming is protected by single-session browser Connection Migration, public Wi-Fi/LTE handover, or transport-level continuity.",
        next_gap="Run controlled-public page-ready media/music handover once an H3-ready public origin and active path-change gate are available.",
    ),
    EvidenceItem(
        id="chrome-desktop-noniphone-buffered-media-local-refresh",
        chapter="11",
        category="browser-local-buffered-media-control",
        implementation="Chrome + quic-go local UDP rebinding proxy",
        evidence_doc="docs/results/chrome-desktop-noniphone-buffered-media-local-refresh-20260701.md",
        runner_or_tool="repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh",
        local_artifact_id="chrome-desktop-noniphone-buffered-media-20260701-pair",
        claim_strength="local_browser_qoe_control",
        supports="Fresh Chrome desktop buffered-media rows completed playback across a 6000ms local outage, but low/high buffer policies produced different rebuffer counts and both rows used multiple Chrome target QUIC sessions.",
        do_not_claim="Video playback was protected by single-session browser Connection Migration, public Wi-Fi/LTE handover, or zero-QoE-impact continuity.",
        next_gap="Run controlled-public page-ready buffered-media handover and report startup delay, rebuffer events, retry count, session count, and qlog path evidence together.",
    ),
    EvidenceItem(
        id="chrome-desktop-noniphone-range-local-refresh",
        chapter="6/9",
        category="browser-local-range-control",
        implementation="Chrome + quic-go local UDP rebinding proxy",
        evidence_doc="docs/results/chrome-desktop-noniphone-range-local-refresh-20260630.md",
        runner_or_tool="repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh",
        local_artifact_id="chrome-desktop-noniphone-range-20260630-pair",
        claim_strength="local_browser_positive_control",
        supports="Two fresh Chrome desktop forced-H3 byte-range runs completed a 1MiB range task without application retry across local UDP rebinding with one target QUIC session, two server-observed remote tuples, and qlog path validation.",
        do_not_claim="Public Wi-Fi/LTE handover, iPhone handover, or general browser CM deployment success.",
        next_gap="Run controlled-public page-ready byte-range handover once public origin and active path-change gates are open.",
    ),
    EvidenceItem(
        id="chrome-desktop-noniphone-upload-local-refresh",
        chapter="6/10",
        category="browser-local-upload-control",
        implementation="Chrome + quic-go local UDP rebinding proxy",
        evidence_doc="docs/results/chrome-desktop-noniphone-upload-local-refresh-20260630.md",
        runner_or_tool="repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh",
        local_artifact_id="chrome-desktop-noniphone-upload-drop3000-retry0-20260630",
        claim_strength="local_browser_positive_control",
        supports="A fresh Chrome desktop forced-H3 upload run completed without application retry while proxy packets crossed both upstream sockets and qlog/NetLog path validation was observed, even though request-level server remote tuple count stayed at one.",
        do_not_claim="Public Wi-Fi/LTE handover, iPhone handover, or request-log-only proof of packet-level rebinding.",
        next_gap="Run controlled-public page-ready upload handover once public origin and active path-change gates are open.",
    ),
]


def path_exists(path: str) -> bool:
    return bool(path) and Path(path).exists()


def build_bundle() -> dict[str, Any]:
    items = []
    for item in EVIDENCE_ITEMS:
        record = asdict(item)
        record["evidence_doc_exists"] = path_exists(item.evidence_doc)
        record["runner_or_tool_exists"] = path_exists(item.runner_or_tool)
        record["public_safe_note"] = "No raw qlog, keylog, pcap, private host, credential, account ID, or device identifier is included."
        items.append(record)

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "item_count": len(items),
        "claim_strength_counts": dict(sorted(Counter(item["claim_strength"] for item in items).items())),
        "category_counts": dict(sorted(Counter(item["category"] for item in items).items())),
        "missing_evidence_docs": [item["id"] for item in items if not item["evidence_doc_exists"]],
        "missing_runners_or_tools": [item["id"] for item in items if item["runner_or_tool"] and not item["runner_or_tool_exists"]],
        "items": items,
    }


def emit_markdown(bundle: dict[str, Any]) -> str:
    lines = [
        "# Sanitized Evidence Bundle",
        "",
        f"Generated: `{bundle['generated']}`",
        "",
        "This bundle is public-safe. It maps committed result documents and reproducible runners/tools to the claim each artifact can support and the claim it must not be used to support.",
        "",
        "It intentionally does not copy raw qlogs, keylogs, pcaps, NetLogs, private hostnames, account IDs, device IDs, public IPs, or credentials.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| item count | `{bundle['item_count']}` |",
        f"| claim strength counts | `{bundle['claim_strength_counts']}` |",
        f"| category counts | `{bundle['category_counts']}` |",
        f"| missing evidence docs | `{bundle['missing_evidence_docs']}` |",
        f"| missing runners/tools | `{bundle['missing_runners_or_tools']}` |",
        "",
        "## Evidence Items",
        "",
        "| id | implementation | strength | evidence doc | runner/tool | supports | do not claim | next gap |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in bundle["items"]:
        evidence_status = "yes" if item["evidence_doc_exists"] else "missing"
        runner_status = "yes" if item["runner_or_tool_exists"] else "missing"
        evidence = f"`{item['evidence_doc']}` ({evidence_status})"
        runner = f"`{item['runner_or_tool']}` ({runner_status})" if item["runner_or_tool"] else "-"
        lines.append(
            "| {id} | {implementation} | `{claim_strength}` | {evidence} | {runner} | {supports} | {do_not_claim} | {next_gap} |".format(
                id=f"`{item['id']}`",
                implementation=item["implementation"],
                claim_strength=item["claim_strength"],
                evidence=evidence,
                runner=runner,
                supports=item["supports"],
                do_not_claim=item["do_not_claim"],
                next_gap=item["next_gap"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This bundle is an evidence-to-claim map, not a raw artifact archive.",
            "- A strong implementation positive control does not imply browser or managed CDN continuity.",
            "- Negative controls are first-class evidence because they prevent overclaiming HTTP/3 support as Connection Migration support.",
            "- Readiness-blocked items are useful because they record why a live claim is not yet available.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_outputs(output: Path, json_output: Path, bundle: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(bundle), encoding="utf-8")
    json_output.write_text(json.dumps(bundle, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    bundle = build_bundle()
    write_outputs(Path(args.output), Path(args.json_output), bundle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
