#!/usr/bin/env python3
"""Build a public-safe deploy packet for a controlled public H3 origin."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from research_clock import utc_date_iso
from pathlib import Path


DEFAULT_OUTPUT = "docs/results/controlled-public-origin-deploy-packet-20260624.md"
DEFAULT_PACKAGE_SCRIPT = "harness/scripts/package-quic-go-ec2.sh"
DEFAULT_WORKLOAD_PACKET = "docs/results/noniphone-public-workload-trial-packet-20260701.md"


@dataclass
class DeployPacket:
    generated: str
    package_script: str
    package_path: str
    package_built: bool
    ssh_user: str
    origin_host_placeholder: str
    remote_dir: str
    run_id: str
    artifact_dir: str
    expected_requests: int
    workload_packet: str
    public_safe: bool


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def rel(path: Path) -> str:
    root = repo_root()
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def package_command(script: str) -> list[str]:
    return ["bash", script]


def parse_package_path(stdout: str) -> str:
    package_path = ""
    for line in stdout.splitlines():
        if line.startswith("package_path="):
            package_path = line.split("=", 1)[1].strip()
        elif line.strip().endswith((".tar.gz", ".tgz")):
            package_path = line.strip()
    return package_path


def build_package(script: str, timeout: int) -> str:
    proc = subprocess.run(
        package_command(script),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"package command failed with exit {proc.returncode}")
    package_path = parse_package_path(proc.stdout)
    if not package_path:
        raise RuntimeError("package command did not print a package path")
    return rel(Path(package_path))


def build_packet(args: argparse.Namespace) -> DeployPacket:
    package_path = args.package_path
    package_built = False
    if args.build_package:
        package_path = build_package(args.package_script, args.package_timeout)
        package_built = True

    if not package_path:
        package_path = "harness/results/packages/<generated-quic-go-min-repro>.tar.gz"

    return DeployPacket(
        generated=utc_date_iso(),
        package_script=args.package_script,
        package_path=package_path,
        package_built=package_built,
        ssh_user=args.ssh_user,
        origin_host_placeholder=args.origin_host_placeholder,
        remote_dir=args.remote_dir,
        run_id=args.run_id,
        artifact_dir=f"artifacts/{args.run_id}",
        expected_requests=args.expected_requests,
        workload_packet=args.workload_packet,
        public_safe=True,
    )


def remote(packet: DeployPacket) -> str:
    return f"{packet.ssh_user}@{packet.origin_host_placeholder}"


def emit_markdown(packet: DeployPacket) -> str:
    remote_target = remote(packet)
    remote_package = "/tmp/quic-go-min-repro.tar.gz"
    remote_bootstrap = "/tmp/ec2-bootstrap-go.sh"
    lines = [
        "# Controlled Public Origin Deploy Packet",
        "",
        f"Generated: `{packet.generated}`",
        "",
        "This packet is public-safe. It uses placeholders for hostnames, certificate paths, private key paths, and SSH targets.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| package script | `{packet.package_script}` |",
        f"| package path | `{packet.package_path}` |",
        f"| package built now | `{'yes' if packet.package_built else 'no'}` |",
        f"| SSH target placeholder | `{remote_target}` |",
        f"| remote dir | `{packet.remote_dir}` |",
        f"| baseline run id | `{packet.run_id}` |",
        f"| expected requests | `{packet.expected_requests}` |",
        f"| workload trial packet | `{packet.workload_packet}` |",
        f"| public safe | `{'yes' if packet.public_safe else 'no'}` |",
        "",
        "## 1. Build Local Package",
        "",
        "```bash",
        packet.package_script,
        "```",
        "",
        "## 2. Prepare Origin Host",
        "",
        "Origin host requirements:",
        "",
        "- Public DNS name resolves to this host.",
        "- TCP 443 and UDP 443 are open from the browser client.",
        "- A WebPKI certificate chain and matching private key are installed locally on the origin host.",
        "- The operator can SSH to the host.",
        "- At least 7 GiB free disk is available for qlog/NetLog-related artifacts.",
        "",
        "Upload package and bootstrap script:",
        "",
        "```bash",
        f"scp {packet.package_path} {remote_target}:{remote_package}",
        f"scp repro/quic-go-min-repro/scripts/ec2-bootstrap-go.sh {remote_target}:{remote_bootstrap}",
        "```",
        "",
        "Bootstrap Go/tcpdump and unpack the reproducibility package:",
        "",
        "```bash",
        f"ssh {remote_target} 'bash {remote_bootstrap}'",
        f"ssh {remote_target} 'rm -rf {packet.remote_dir} && mkdir -p {packet.remote_dir} && tar -xzf {remote_package} -C {packet.remote_dir}'",
        "```",
        "",
        "## 3. Start Controlled Public H3 Server",
        "",
        "Run this on the origin host. Replace placeholders locally; do not commit real values.",
        "",
        "```bash",
        f"ssh {remote_target} 'cd {packet.remote_dir} && sudo env \\",
        f"  RUN_ID={packet.run_id} \\",
        f"  ARTIFACT_DIR={packet.artifact_dir} \\",
        "  PUBLIC_ORIGIN_HOST=<public-origin-host> \\",
        "  PUBLIC_ORIGIN_PORT=443 \\",
        "  TLS_CERT_FILE=<webpki-fullchain-path> \\",
        "  TLS_KEY_FILE=<webpki-private-key-path> \\",
        "  LISTEN_ADDR=0.0.0.0:443 \\",
        "  TCP_ADDR=0.0.0.0:443 \\",
        "  ALT_SVC='\"'\"'h3=\\\":443\\\"; ma=60'\"'\"' \\",
        f"  EXPECTED_REQUESTS={packet.expected_requests} \\",
        "  TIMEOUT=300s \\",
        "  COMPLETION_GRACE=2s \\",
        "  MIN_ARTIFACT_FREE_GIB=7 \\",
        "  ./scripts/run-controlled-public-h3-server.sh'",
        "```",
        "",
        "## 4. Validate From Client Machine",
        "",
        "Fill the ignored local config and run the readiness gates:",
        "",
        "```bash",
        "bash harness/scripts/init-controlled-public-config.sh",
        "$EDITOR harness/config/controlled-public-origin.env",
        "set -a",
        "source harness/config/controlled-public-origin.env",
        "set +a",
        "python3 tools/check_controlled_public_config.py --require-baseline-ready",
        "python3 tools/check_public_origin_readiness.py --url \"$PUBLIC_ORIGIN_URL\" --require-h3-alt-svc --redact-sensitive --format markdown",
        "python3 tools/check_next_final_handover_trial_readiness.py --output docs/results/final-handover-next-trial-readiness-20260624.md",
        "```",
        "",
        "## 5. Run Baseline Browser Trial",
        "",
        "First prove that the origin serves application HTTP/3 before attempting path-change workloads:",
        "",
        "```bash",
        "cd repro/quic-go-min-repro",
        f"RUN_ID={packet.run_id} \\",
        f"ARTIFACT_DIR={packet.artifact_dir} \\",
        "PUBLIC_ORIGIN_URL=\"${PUBLIC_ORIGIN_BOOTSTRAP_URL:-$PUBLIC_ORIGIN_BASE/browser-slow?duration_ms=3000&chunks=3&label=public-bootstrap}\" \\",
        "SECOND_URL=\"${PUBLIC_ORIGIN_BASE:?set PUBLIC_ORIGIN_BASE like https://h3.example.com}/browser-slow?duration_ms=3000&chunks=3&label=public-h3-baseline\" \\",
        f"CONTROLLED_PUBLIC_EXPECTED_REQUESTS={packet.expected_requests} \\",
        "REQUIRE_H3_ALT_SVC=1 \\",
        "RUN_CONTROLLED_PUBLIC_CLASSIFIER=1 \\",
        "CHROME_RUNNER=cdp \\",
        "CHROME_HOLD_SECONDS=25 \\",
        "CHROME_TIMEOUT_SECONDS=45 \\",
        "./scripts/run-controlled-public-h3-browser-baseline.sh",
        "```",
        "",
        "Then bind the baseline summary path for active controlled-public workload trials:",
        "",
        "```bash",
        f"export CONTROLLED_PUBLIC_BASELINE_SUMMARY=\"{packet.artifact_dir}/results/controlled-public-h3-baseline-summary.json\"",
        "```",
        "",
        "## 6. Run non-iPhone Public Workload Packet",
        "",
        "Use the non-iPhone public workload packet for the exact range, upload, buffered-video, and music-like commands:",
        "",
        "```bash",
        f"open {packet.workload_packet}",
        "# Execute the packet order only after the baseline summary is PASS and a non-iPhone NETWORK_CHANGE_CMD is set.",
        "```",
        "",
        "Strong CM acceptance for each active row requires all of the following evidence:",
        "",
        "1. application task completion is true for the workload-specific DOM metric",
        "2. client active path changed according to route snapshots",
        "3. server target H3 remote tuple count changed",
        "4. server qlog records PATH_CHALLENGE and PATH_RESPONSE",
        "5. Chrome target QUIC session count is one",
        "",
        "## 7. Register Results Only After Classification",
        "",
        "After each public workload finishes, classify the row and commit only public-safe summary documents:",
        "",
        "```bash",
        "python3 tools/classify_controlled_public_h3_network_change.py \\",
        "  --artifact-dir repro/quic-go-min-repro/artifacts/<trial-id> \\",
        "  --server-artifact-dir repro/quic-go-min-repro/artifacts/<trial-id>-server \\",
        "  --output docs/results/<trial-id>-validation.md \\",
        "  --json-output data/<trial-id>-validation.json",
        "```",
        "",
        "## Safe Handling",
        "",
        "- Do not commit `harness/config/controlled-public-origin.env`.",
        "- Do not commit certificate files, private keys, SSH keys, qlogs, keylogs, pcaps, NetLogs, or raw artifacts.",
        "- If the origin host is not AWS-managed, this packet still applies as long as TCP/UDP 443 and WebPKI TLS are available.",
        "- This packet is a deployment/run plan. It is not evidence that a public workload or browser Connection Migration trial has succeeded.",
    ]
    return "\n".join(lines).rstrip() + "\n"


def write_output(text: str, output_arg: str | None) -> None:
    if output_arg == "-":
        sys.stdout.write(text)
        return
    if not output_arg:
        sys.stdout.write(text)
        return
    output = Path(output_arg)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--package-script", default=DEFAULT_PACKAGE_SCRIPT)
    parser.add_argument("--package-path", default="")
    parser.add_argument("--build-package", action="store_true")
    parser.add_argument("--package-timeout", type=int, default=60)
    parser.add_argument("--ssh-user", default="ec2-user")
    parser.add_argument("--origin-host-placeholder", default="<origin-host-or-ip>")
    parser.add_argument("--remote-dir", default="/home/ec2-user/quic-go-min-repro")
    parser.add_argument("--run-id", default="controlled-public-chrome-h3-baseline-001")
    parser.add_argument("--expected-requests", type=int, default=2)
    parser.add_argument("--workload-packet", default=DEFAULT_WORKLOAD_PACKET)
    args = parser.parse_args()

    packet = build_packet(args)
    text = json.dumps(asdict(packet), indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(packet)
    write_output(text, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
