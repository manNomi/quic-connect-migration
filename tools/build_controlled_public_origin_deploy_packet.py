#!/usr/bin/env python3
"""Build a public-safe deploy packet for a controlled public H3 origin."""

from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from research_clock import utc_date_iso
from pathlib import Path


DEFAULT_OUTPUT = "docs/results/controlled-public-origin-deploy-packet-20260624.md"
DEFAULT_PACKAGE_SCRIPT = "harness/scripts/package-quic-go-ec2.sh"


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
        "python3 tools/check_public_origin_readiness.py --url \"$PUBLIC_ORIGIN_URL\" --require-h3-alt-svc --format markdown",
        "python3 tools/check_next_final_handover_trial_readiness.py --output docs/results/final-handover-next-trial-readiness-20260624.md",
        "```",
        "",
        "## 5. Run Baseline Browser Trial",
        "",
        "Use the generated final handover trial packet for the exact server/client commands:",
        "",
        "```bash",
        "python3 tools/build_final_handover_trial_packet.py --use-local-config --output docs/results/final-handover-trial-packet-20260624.md",
        "```",
        "",
        "After the browser baseline finishes, register only if the artifact bundle and final-countable gates pass:",
        "",
        "```bash",
        f"python3 tools/check_final_handover_trial_artifact_bundle.py --trial-id {packet.run_id} --artifact-dir repro/quic-go-min-repro/{packet.artifact_dir} --require-final-countable --require-complete",
        f"python3 tools/append_final_handover_result_row.py --trial-id {packet.run_id} --artifact-dir repro/quic-go-min-repro/{packet.artifact_dir} --require-final-countable --require-artifact-bundle --apply",
        "python3 tools/audit_final_browser_handover_trials.py --output docs/results/final-browser-handover-trial-audit-20260624.md",
        "python3 tools/verify_research_bundle.py --output docs/results/research-verification-report-20260624.md",
        "```",
        "",
        "## Safe Handling",
        "",
        "- Do not commit `harness/config/controlled-public-origin.env`.",
        "- Do not commit certificate files, private keys, SSH keys, qlogs, keylogs, pcaps, NetLogs, or raw artifacts.",
        "- If the origin host is not AWS-managed, this packet still applies as long as TCP/UDP 443 and WebPKI TLS are available.",
    ]
    return "\n".join(lines).rstrip() + "\n"


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
    parser.add_argument("--expected-requests", type=int, default=4)
    args = parser.parse_args()

    packet = build_packet(args)
    text = json.dumps(asdict(packet), indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(packet)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
