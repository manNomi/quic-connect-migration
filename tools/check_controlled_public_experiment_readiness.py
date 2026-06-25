#!/usr/bin/env python3
"""Check readiness for controlled public Chrome HTTP/3 migration experiments."""

from __future__ import annotations

import argparse
import json
import shutil
from dataclasses import asdict, dataclass
from research_clock import utc_date_iso
from pathlib import Path

from check_handover_readiness import HandoverReadiness, build_readiness
from check_public_origin_readiness import PublicOriginReadiness, build_result
from check_public_origin_readiness import payload as public_origin_readiness_payload


@dataclass
class ArtifactCheck:
    path: str
    exists: bool
    status: str
    classification: str
    error: str


@dataclass
class ControlledPublicExperimentReadiness:
    check_date: str
    public_origin_url: str
    controlled_public_origin_ready: bool
    application_h3_baseline_ready: bool
    network_change_harness_ready: bool
    desktop_handover_ready: bool
    can_run_application_h3_baseline: bool
    can_run_network_change: bool
    chrome_found: bool
    secondary_path_ready: bool
    active_ipv4_interfaces: list[dict[str, object]]
    network_change_command_present: bool
    network_change_command_preview: str
    baseline_summary: ArtifactCheck
    server_artifact: ArtifactCheck
    public_origin: dict[str, object] | None
    blockers: list[str]


def load_summary(path: str | None) -> ArtifactCheck:
    if not path:
        return ArtifactCheck("", False, "", "", "not provided")
    summary_path = Path(path)
    if not summary_path.exists():
        return ArtifactCheck(path, False, "", "", "missing")
    try:
        data = json.loads(summary_path.read_text(encoding="utf-8", errors="ignore"))
    except (OSError, json.JSONDecodeError) as exc:
        return ArtifactCheck(path, True, "", "", f"read failed: {exc}")
    return ArtifactCheck(
        path=path,
        exists=True,
        status=str(data.get("status") or ""),
        classification=str(data.get("classification") or ""),
        error=str(data.get("error") or data.get("server_result_error") or ""),
    )


def server_artifact_check(path: str | None) -> ArtifactCheck:
    if not path:
        return ArtifactCheck("", False, "", "", "not provided")
    server_path = Path(path) / "results" / "server.json"
    if not server_path.exists():
        return ArtifactCheck(server_path.as_posix(), False, "", "", "missing")
    try:
        data = json.loads(server_path.read_text(encoding="utf-8", errors="ignore"))
    except (OSError, json.JSONDecodeError) as exc:
        return ArtifactCheck(server_path.as_posix(), True, "", "", f"read failed: {exc}")
    return ArtifactCheck(
        path=server_path.as_posix(),
        exists=True,
        status="PASS" if data.get("ok") is True else "FAIL",
        classification="server_ok" if data.get("ok") is True else "server_not_ok",
        error=str(data.get("error") or ""),
    )


def public_origin_payload(result: PublicOriginReadiness | None, redact_sensitive: bool = False) -> dict[str, object] | None:
    if result is None:
        return None
    return public_origin_readiness_payload(result, redact_sensitive)


def command_preview(command: str) -> str:
    stripped = command.strip()
    if len(stripped) <= 120:
        return stripped
    return stripped[:117] + "..."


def redacted_configured(value: str) -> str:
    return "<configured>" if value else ""


def redact_public_origin_dict(public_origin: dict[str, object]) -> dict[str, object]:
    redacted = dict(public_origin)
    tokens: list[str] = []
    for key in ("url", "host", "tls_subject", "tls_issuer"):
        value = public_origin.get(key)
        if isinstance(value, str) and value:
            tokens.append(value)
    dns_addresses = public_origin.get("dns_addresses")
    if isinstance(dns_addresses, list):
        tokens.extend(str(address) for address in dns_addresses if address)

    def scrub(value: str) -> str:
        clean = value
        for token in tokens:
            clean = clean.replace(token, "<redacted>")
        return clean

    if public_origin.get("url"):
        redacted["url"] = "<redacted-url>"
    if public_origin.get("host"):
        redacted["host"] = "<redacted-host>"
    if isinstance(dns_addresses, list):
        redacted["dns_addresses"] = ["<redacted-address>"] if dns_addresses else []
    if public_origin.get("tls_subject"):
        redacted["tls_subject"] = "<redacted-tls-subject>"
    if public_origin.get("tls_issuer"):
        redacted["tls_issuer"] = "<redacted-tls-issuer>"
    alt_svc_headers = public_origin.get("alt_svc_headers")
    if isinstance(alt_svc_headers, str):
        redacted["alt_svc_headers"] = scrub(alt_svc_headers)
    errors = public_origin.get("errors")
    if isinstance(errors, list):
        redacted["errors"] = [scrub(str(error)) for error in errors]
    redacted["redacted"] = True
    return redacted


def redact_readiness_text(value: str, readiness: ControlledPublicExperimentReadiness) -> str:
    tokens = [
        readiness.public_origin_url,
        readiness.network_change_command_preview,
        readiness.baseline_summary.path,
        readiness.server_artifact.path,
    ]
    if readiness.public_origin:
        for key in ("url", "host", "tls_subject", "tls_issuer"):
            item = readiness.public_origin.get(key)
            if isinstance(item, str):
                tokens.append(item)
        dns_addresses = readiness.public_origin.get("dns_addresses")
        if isinstance(dns_addresses, list):
            tokens.extend(str(address) for address in dns_addresses if address)
    clean = value
    for token in tokens:
        if token:
            clean = clean.replace(token, "<redacted>")
    return clean


def redact_active_interfaces(items: list[dict[str, object]]) -> list[dict[str, object]]:
    redacted: list[dict[str, object]] = []
    for item in items:
        next_item = dict(item)
        ipv4 = next_item.get("ipv4")
        if isinstance(ipv4, list):
            next_item["ipv4"] = ["<redacted-address>"] if ipv4 else []
        redacted.append(next_item)
    return redacted


def active_interface_summary(items: list[dict[str, object]], redact_sensitive: bool) -> str:
    summaries: list[str] = []
    for item in items:
        name = str(item.get("name") or "-")
        ipv4 = item.get("ipv4")
        addresses = [str(address) for address in ipv4] if isinstance(ipv4, list) else []
        if redact_sensitive:
            count = len(addresses)
            suffix = "es" if count != 1 else ""
            address_text = f"<redacted:{count} address{suffix}>" if count else "-"
        else:
            address_text = ",".join(addresses)
        summaries.append(f"{name}({address_text})")
    return ", ".join(summaries) or "-"


def artifact_summary(check: ArtifactCheck, redact_sensitive: bool) -> str:
    if check.status:
        return check.status
    if check.error:
        return check.error
    if redact_sensitive and check.path:
        return "<configured>"
    return "-"


def build_experiment_readiness(
    public_origin_url: str,
    baseline_summary_path: str | None,
    server_artifact_dir: str | None,
    network_change_cmd: str,
    chrome_bin: str,
    timeout: int,
) -> ControlledPublicExperimentReadiness:
    handover: HandoverReadiness = build_readiness(chrome_bin, include_command_output=False)
    blockers: list[str] = []
    public_origin: PublicOriginReadiness | None = None
    if public_origin_url:
        try:
            public_origin = build_result(public_origin_url, timeout)
        except Exception as exc:  # noqa: BLE001 - readiness output should include the exact blocker.
            blockers.append(f"public origin readiness failed: {exc}")
    else:
        blockers.append("public origin URL is not provided")

    baseline = load_summary(baseline_summary_path)
    server = server_artifact_check(server_artifact_dir)
    network_change_command_present = bool(network_change_cmd.strip()) and network_change_cmd.strip() != "..."
    harness_ready = shutil.which("python3") is not None and Path("repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh").exists()
    controlled_origin_ready = public_origin.ok if public_origin else False
    baseline_ready = baseline.exists and baseline.status == "PASS"
    can_run_baseline = handover.chrome_found and controlled_origin_ready
    can_run_network_change = can_run_baseline and baseline_ready and handover.secondary_path_ready and network_change_command_present and harness_ready

    if not handover.chrome_found:
        blockers.append("Chrome binary not found")
    if public_origin is not None and not public_origin.ok:
        blockers.append("controlled public origin HTTPS readiness failed")
    if public_origin is not None and not public_origin.has_h3_alt_svc:
        blockers.append("controlled public origin does not advertise h3 Alt-Svc")
    if not baseline_ready:
        blockers.append("controlled public application H3 baseline summary is not PASS")
    if not handover.secondary_path_ready:
        blockers.append("active secondary network path is not ready")
    if not network_change_command_present:
        blockers.append("NETWORK_CHANGE_CMD is not provided")
    if not harness_ready:
        blockers.append("controlled public network-change harness is missing")
    if server_artifact_dir and not server.exists:
        blockers.append("server artifact directory does not contain results/server.json")

    return ControlledPublicExperimentReadiness(
        check_date=utc_date_iso(),
        public_origin_url=public_origin_url,
        controlled_public_origin_ready=controlled_origin_ready,
        application_h3_baseline_ready=baseline_ready,
        network_change_harness_ready=harness_ready,
        desktop_handover_ready=handover.desktop_handover_ready,
        can_run_application_h3_baseline=can_run_baseline,
        can_run_network_change=can_run_network_change,
        chrome_found=handover.chrome_found,
        secondary_path_ready=handover.secondary_path_ready,
        active_ipv4_interfaces=[asdict(info) for info in handover.active_ipv4_interfaces],
        network_change_command_present=network_change_command_present,
        network_change_command_preview=command_preview(network_change_cmd),
        baseline_summary=baseline,
        server_artifact=server,
        public_origin=public_origin_payload(public_origin),
        blockers=blockers,
    )


def payload(readiness: ControlledPublicExperimentReadiness, redact_sensitive: bool = False) -> dict[str, object]:
    data = asdict(readiness)
    data["redacted"] = redact_sensitive
    if redact_sensitive:
        data["public_origin_url"] = redacted_configured(readiness.public_origin_url)
        data["network_change_command_preview"] = redacted_configured(readiness.network_change_command_preview)
        data["baseline_summary"]["path"] = redacted_configured(readiness.baseline_summary.path)
        data["server_artifact"]["path"] = redacted_configured(readiness.server_artifact.path)
        data["active_ipv4_interfaces"] = redact_active_interfaces(readiness.active_ipv4_interfaces)
        data["blockers"] = [redact_readiness_text(str(blocker), readiness) for blocker in readiness.blockers]
        if readiness.public_origin:
            data["public_origin"] = redact_public_origin_dict(readiness.public_origin)
    return data


def emit_markdown(readiness: ControlledPublicExperimentReadiness, redact_sensitive: bool = False) -> str:
    active = active_interface_summary(readiness.active_ipv4_interfaces, redact_sensitive)
    blocker_items = (
        [redact_readiness_text(blocker, readiness) for blocker in readiness.blockers]
        if redact_sensitive
        else readiness.blockers
    )
    blockers = "; ".join(blocker_items) or "-"
    public_origin = readiness.public_origin or {}
    public_origin_url = redacted_configured(readiness.public_origin_url) if redact_sensitive else readiness.public_origin_url
    network_change_preview = (
        redacted_configured(readiness.network_change_command_preview)
        if redact_sensitive
        else readiness.network_change_command_preview
    )
    baseline_summary = artifact_summary(readiness.baseline_summary, redact_sensitive)
    server_artifact = artifact_summary(readiness.server_artifact, redact_sensitive)
    lines = [
        "| check | value |",
        "| --- | --- |",
        f"| public origin URL | `{public_origin_url or '-'}` |",
        f"| controlled public origin ready | `{str(readiness.controlled_public_origin_ready).lower()}` |",
        f"| h3 Alt-Svc | `{str(public_origin.get('has_h3_alt_svc', False)).lower()}` |",
        f"| final status | `{public_origin.get('final_status') or '-'}` |",
        f"| application H3 baseline ready | `{str(readiness.application_h3_baseline_ready).lower()}` |",
        f"| network-change harness ready | `{str(readiness.network_change_harness_ready).lower()}` |",
        f"| Chrome found | `{str(readiness.chrome_found).lower()}` |",
        f"| active IPv4 interfaces | `{active}` |",
        f"| secondary path ready | `{str(readiness.secondary_path_ready).lower()}` |",
        f"| NETWORK_CHANGE_CMD present | `{str(readiness.network_change_command_present).lower()}` |",
        f"| NETWORK_CHANGE_CMD preview | `{network_change_preview or '-'}` |",
        f"| can run application H3 baseline | `{str(readiness.can_run_application_h3_baseline).lower()}` |",
        f"| can run network-change | `{str(readiness.can_run_network_change).lower()}` |",
        f"| baseline summary | `{baseline_summary}` |",
        f"| server artifact | `{server_artifact}` |",
        f"| blockers | `{blockers}` |",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public-origin-url", default="")
    parser.add_argument("--baseline-summary")
    parser.add_argument("--server-artifact-dir")
    parser.add_argument("--network-change-cmd", default="")
    parser.add_argument("--chrome-bin", default="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    parser.add_argument("--timeout", type=int, default=8)
    parser.add_argument("--redact-sensitive", action="store_true")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output")
    args = parser.parse_args()

    readiness = build_experiment_readiness(
        args.public_origin_url,
        args.baseline_summary,
        args.server_artifact_dir,
        args.network_change_cmd,
        args.chrome_bin,
        args.timeout,
    )
    if args.format == "json":
        text = json.dumps(payload(readiness, args.redact_sensitive), indent=2, ensure_ascii=False) + "\n"
    else:
        text = emit_markdown(readiness, redact_sensitive=args.redact_sensitive)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if readiness.can_run_network_change else 1


if __name__ == "__main__":
    raise SystemExit(main())
