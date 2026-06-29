#!/usr/bin/env python3
"""Diagnose controlled-public origin access without exposing host secrets."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from check_aws_identity_readiness import build_readiness as build_aws_readiness
from check_final_browser_handover_readiness import parse_env_file
from research_clock import utc_date_iso


DEFAULT_CONFIG = "harness/config/controlled-public-origin.env"
DEFAULT_OUTPUT = "docs/results/controlled-public-origin-access-check-20260629.md"
DEFAULT_SSH_USERS = "ec2-user,ubuntu"


@dataclass(frozen=True)
class FileAccess:
    configured: bool
    exists: bool
    readable: bool


@dataclass(frozen=True)
class DnsAccess:
    attempted: bool
    configured: bool
    resolved: bool
    address_count: int
    classification: str


@dataclass(frozen=True)
class TcpAccess:
    attempted: bool
    configured: bool
    connected: bool
    classification: str


@dataclass(frozen=True)
class SshAccess:
    attempted: bool
    user_label: str
    ok: bool
    classification: str


@dataclass(frozen=True)
class AwsAccess:
    attempted: bool
    aws_cli_found: bool
    identity_ok: bool
    classification: str
    region: str
    profile_state: str


def file_access(raw_path: str) -> FileAccess:
    if not raw_path:
        return FileAccess(False, False, False)
    path = Path(raw_path)
    return FileAccess(True, path.exists(), path.is_file() and os.access(path, os.R_OK))


def dns_access(host: str, port: int, probe: bool) -> DnsAccess:
    if not host:
        return DnsAccess(False, False, False, 0, "not_configured")
    if not probe:
        return DnsAccess(False, True, False, 0, "not_probed")
    try:
        infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        return DnsAccess(True, True, False, 0, "dns_failed")
    except OSError:
        return DnsAccess(True, True, False, 0, "resolver_error")
    return DnsAccess(True, True, bool(infos), len(infos), "resolved" if infos else "dns_empty")


def classify_tcp_exception(exc: BaseException) -> str:
    if isinstance(exc, ConnectionRefusedError):
        return "connection_refused"
    if isinstance(exc, TimeoutError):
        return "timeout"
    if isinstance(exc, socket.gaierror):
        return "dns_failed"
    if isinstance(exc, OSError):
        lowered = str(exc).lower()
        if "timed out" in lowered:
            return "timeout"
        if "refused" in lowered:
            return "connection_refused"
        if "network is unreachable" in lowered or "no route to host" in lowered:
            return "network_unreachable"
    return "other_failure"


def tcp_access(host: str, port: int, timeout: float, probe: bool) -> TcpAccess:
    if not host:
        return TcpAccess(False, False, False, "not_configured")
    if not probe:
        return TcpAccess(False, True, False, "not_probed")
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return TcpAccess(True, True, True, "ok")
    except BaseException as exc:  # noqa: BLE001 - public-safe diagnostic classification.
        return TcpAccess(True, True, False, classify_tcp_exception(exc))


def ssh_user_label(user: str, index: int) -> str:
    if user in {"ec2-user", "ubuntu", "admin", "debian"}:
        return user
    return f"user-{index}"


def classify_ssh_stderr(stderr: str, exit_code: int) -> str:
    lowered = stderr.lower()
    if exit_code == 0:
        return "ok"
    if "permission denied" in lowered or "publickey" in lowered:
        return "auth_failed"
    if "connection refused" in lowered:
        return "connection_refused"
    if "timed out" in lowered or "operation timed out" in lowered:
        return "timeout"
    if "could not resolve" in lowered or "name or service not known" in lowered:
        return "dns_failed"
    if "no route to host" in lowered or "network is unreachable" in lowered:
        return "network_unreachable"
    return "other_failure"


def ssh_access(host: str, users: list[str], timeout: float, probe: bool) -> list[SshAccess]:
    if not host:
        return [SshAccess(False, ssh_user_label(user, index), False, "not_configured") for index, user in enumerate(users, 1)]
    if not probe:
        return [SshAccess(False, ssh_user_label(user, index), False, "not_probed") for index, user in enumerate(users, 1)]
    results: list[SshAccess] = []
    for index, user in enumerate(users, 1):
        command = [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            f"ConnectTimeout={int(timeout)}",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            f"{user}@{host}",
            "true",
        ]
        try:
            proc = subprocess.run(
                command,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout + 3,
                check=False,
            )
            classification = classify_ssh_stderr(proc.stderr, proc.returncode)
            results.append(SshAccess(True, ssh_user_label(user, index), proc.returncode == 0, classification))
        except subprocess.TimeoutExpired:
            results.append(SshAccess(True, ssh_user_label(user, index), False, "timeout"))
    return results


def aws_access(probe: bool, timeout: float) -> AwsAccess:
    if not probe:
        return AwsAccess(False, False, False, "not_probed", "", "")
    readiness = build_aws_readiness(timeout=timeout, include_redacted_diagnostics=False)
    return AwsAccess(
        True,
        readiness.aws_cli_found,
        readiness.identity_ok,
        readiness.classification,
        readiness.region,
        readiness.profile_state,
    )


def parse_port(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 443


def build_report(
    config_path: Path,
    *,
    timeout: float,
    ssh_users: list[str],
    probe_network: bool = True,
    probe_ssh: bool = True,
    probe_aws: bool = True,
) -> dict[str, Any]:
    values = parse_env_file(config_path)
    host = values.get("PUBLIC_ORIGIN_HOST", "")
    port = parse_port(values.get("PUBLIC_ORIGIN_PORT", "443"))
    cert = file_access(values.get("TLS_CERT_FILE", ""))
    key = file_access(values.get("TLS_KEY_FILE", ""))
    dns = dns_access(host, port, probe_network)
    tcp = tcp_access(host, port, timeout, probe_network)
    ssh = ssh_access(host, ssh_users, timeout, probe_ssh)
    aws = aws_access(probe_aws, timeout)
    ssh_ready = any(item.ok for item in ssh)
    local_tls_ready = cert.readable and key.readable
    recovery_ready = ssh_ready or aws.identity_ok or local_tls_ready
    blockers: list[str] = []
    if not config_path.exists():
        blockers.append("controlled public config file is missing")
    if not dns.resolved:
        blockers.append(f"public origin DNS is not ready: {dns.classification}")
    if not tcp.connected:
        blockers.append(f"public origin TCP 443 is not accepting connections: {tcp.classification}")
    if not local_tls_ready:
        blockers.append("configured WebPKI cert/key are not readable on this machine")
    if not ssh_ready:
        blockers.append("SSH access to configured public origin was not available with probed users")
    if not aws.identity_ok:
        blockers.append(f"AWS identity is not available for recovery/provisioning: {aws.classification}")

    return {
        "check_date": utc_date_iso(),
        "public_safe": True,
        "config_path": config_path.as_posix(),
        "config_exists": config_path.exists(),
        "host_configured": bool(host),
        "port_configured": bool(values.get("PUBLIC_ORIGIN_PORT")),
        "tls_cert": asdict(cert),
        "tls_key": asdict(key),
        "dns": asdict(dns),
        "tcp": asdict(tcp),
        "ssh": [asdict(item) for item in ssh],
        "aws": asdict(aws),
        "recovery_paths": {
            "remote_ssh_ready": ssh_ready,
            "aws_identity_ready": aws.identity_ok,
            "local_tls_material_ready": local_tls_ready,
            "any_recovery_path_ready": recovery_ready,
        },
        "blockers": blockers,
        "claim_boundary": "This is an origin access diagnostic, not QUIC migration evidence.",
    }


def yes(value: bool) -> str:
    return "yes" if value else "no"


def emit_markdown(report: dict[str, Any]) -> str:
    ssh_rows = report["ssh"]
    blockers = report["blockers"] or ["-"]
    lines = [
        "# Controlled Public Origin Access Check",
        "",
        f"Generated: `{report['check_date']}`",
        "",
        "This report is public-safe. It does not print hostnames, IP addresses, certificate paths, private key paths, SSH targets, AWS account IDs, or raw command output.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| config exists | `{yes(report['config_exists'])}` |",
        f"| public host configured | `{yes(report['host_configured'])}` |",
        f"| public port configured | `{yes(report['port_configured'])}` |",
        f"| DNS classification | `{report['dns']['classification']}` |",
        f"| DNS address count | `{report['dns']['address_count']}` |",
        f"| TCP classification | `{report['tcp']['classification']}` |",
        f"| TLS cert local readable | `{yes(report['tls_cert']['readable'])}` |",
        f"| TLS key local readable | `{yes(report['tls_key']['readable'])}` |",
        f"| SSH recovery ready | `{yes(report['recovery_paths']['remote_ssh_ready'])}` |",
        f"| AWS identity ready | `{yes(report['recovery_paths']['aws_identity_ready'])}` |",
        f"| local TLS material ready | `{yes(report['recovery_paths']['local_tls_material_ready'])}` |",
        f"| any recovery path ready | `{yes(report['recovery_paths']['any_recovery_path_ready'])}` |",
        "",
        "## SSH Probes",
        "",
        "| user label | attempted | classification |",
        "| --- | --- | --- |",
    ]
    for item in ssh_rows:
        lines.append(f"| `{item['user_label']}` | `{yes(item['attempted'])}` | `{item['classification']}` |")
    lines.extend(
        [
            "",
            "## AWS",
            "",
            "| field | value |",
            "| --- | --- |",
            f"| attempted | `{yes(report['aws']['attempted'])}` |",
            f"| AWS CLI found | `{yes(report['aws']['aws_cli_found'])}` |",
            f"| identity OK | `{yes(report['aws']['identity_ok'])}` |",
            f"| classification | `{report['aws']['classification']}` |",
            f"| region | `{report['aws']['region'] or '-'}` |",
            f"| profile state | `{report['aws']['profile_state'] or '-'}` |",
            "",
            "## Blockers",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in blockers)
    lines.extend(["", "## Claim Boundary", "", str(report["claim_boundary"]), ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=5)
    parser.add_argument("--ssh-users", default=DEFAULT_SSH_USERS)
    parser.add_argument("--skip-network", action="store_true")
    parser.add_argument("--skip-ssh", action="store_true")
    parser.add_argument("--skip-aws", action="store_true")
    args = parser.parse_args()

    users = [item.strip() for item in args.ssh_users.split(",") if item.strip()]
    report = build_report(
        Path(args.config),
        timeout=args.timeout,
        ssh_users=users,
        probe_network=not args.skip_network,
        probe_ssh=not args.skip_ssh,
        probe_aws=not args.skip_aws,
    )
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="" if text.endswith("\n") else "\n")
    return 0 if report["recovery_paths"]["any_recovery_path_ready"] and report["tcp"]["connected"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
