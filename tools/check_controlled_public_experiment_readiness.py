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


def public_origin_payload(result: PublicOriginReadiness | None) -> dict[str, object] | None:
    if result is None:
        return None
    payload = asdict(result)
    payload["ok"] = result.ok
    return payload


def command_preview(command: str) -> str:
    stripped = command.strip()
    if len(stripped) <= 120:
        return stripped
    return stripped[:117] + "..."


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


def emit_markdown(readiness: ControlledPublicExperimentReadiness) -> str:
    active = ", ".join(
        f"{item['name']}({','.join(item['ipv4'])})"
        for item in readiness.active_ipv4_interfaces
    ) or "-"
    blockers = "; ".join(readiness.blockers) or "-"
    public_origin = readiness.public_origin or {}
    lines = [
        "| check | value |",
        "| --- | --- |",
        f"| public origin URL | `{readiness.public_origin_url or '-'}` |",
        f"| controlled public origin ready | `{str(readiness.controlled_public_origin_ready).lower()}` |",
        f"| h3 Alt-Svc | `{str(public_origin.get('has_h3_alt_svc', False)).lower()}` |",
        f"| final status | `{public_origin.get('final_status') or '-'}` |",
        f"| application H3 baseline ready | `{str(readiness.application_h3_baseline_ready).lower()}` |",
        f"| network-change harness ready | `{str(readiness.network_change_harness_ready).lower()}` |",
        f"| Chrome found | `{str(readiness.chrome_found).lower()}` |",
        f"| active IPv4 interfaces | `{active}` |",
        f"| secondary path ready | `{str(readiness.secondary_path_ready).lower()}` |",
        f"| NETWORK_CHANGE_CMD present | `{str(readiness.network_change_command_present).lower()}` |",
        f"| can run application H3 baseline | `{str(readiness.can_run_application_h3_baseline).lower()}` |",
        f"| can run network-change | `{str(readiness.can_run_network_change).lower()}` |",
        f"| baseline summary | `{readiness.baseline_summary.status or readiness.baseline_summary.error or '-'}` |",
        f"| server artifact | `{readiness.server_artifact.status or readiness.server_artifact.error or '-'}` |",
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
        text = json.dumps(asdict(readiness), indent=2, ensure_ascii=False) + "\n"
    else:
        text = emit_markdown(readiness)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0 if readiness.can_run_network_change else 1


if __name__ == "__main__":
    raise SystemExit(main())
