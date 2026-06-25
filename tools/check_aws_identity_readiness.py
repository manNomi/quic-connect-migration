#!/usr/bin/env python3
"""Build a public-safe AWS identity readiness report for public-origin automation."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from research_clock import utc_date_iso


ACCOUNT_ID_RE = re.compile(r"\b\d{12}\b")
ACCESS_KEY_RE = re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")
AWS_ARN_RE = re.compile(r"\barn:aws:[^\s\"']+")


@dataclass(frozen=True)
class CommandResult:
    command: str
    found: bool
    exit_code: int | None
    stdout: str
    stderr: str


@dataclass(frozen=True)
class AwsIdentityReadiness:
    check_date: str
    public_safe: bool
    aws_cli_found: bool
    aws_cli_version: str
    region: str
    profile_state: str
    identity_ok: bool
    classification: str
    remediation: str
    account_id: str
    arn: str
    user_id: str
    redaction_applied: bool
    diagnostics_included: bool
    commands: dict[str, CommandResult]


def redact_aws_text(value: str | bytes) -> str:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="ignore")
    redacted = AWS_ARN_RE.sub("<aws-arn>", value)
    redacted = ACCESS_KEY_RE.sub("<aws-access-key-id>", redacted)
    redacted = ACCOUNT_ID_RE.sub("<aws-account-id>", redacted)
    return redacted


def tail(value: str, limit: int = 1200) -> str:
    if len(value) <= limit:
        return value
    return value[-limit:]


def run_command(args: list[str], timeout: float = 8.0, include_output: bool = False) -> CommandResult:
    found = shutil.which(args[0]) is not None or Path(args[0]).exists()
    command = " ".join(args)
    if not found:
        return CommandResult(command, False, None, "", "command not found")
    try:
        proc = subprocess.run(
            args,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        stdout = redact_aws_text(tail(proc.stdout.strip())) if include_output else ""
        stderr = redact_aws_text(tail(proc.stderr.strip())) if include_output else ""
        return CommandResult(command, True, proc.returncode, stdout, stderr)
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="ignore") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="ignore") if isinstance(exc.stderr, bytes) else (exc.stderr or "timeout")
        return CommandResult(
            command,
            True,
            124,
            redact_aws_text(tail(stdout.strip())) if include_output else "",
            redact_aws_text(tail(stderr.strip())) if include_output else "",
        )


def parse_identity(stdout: str) -> tuple[bool, str, str, str]:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return False, "", "", ""
    account = payload.get("Account") or ""
    arn = payload.get("Arn") or ""
    user_id = payload.get("UserId") or ""
    return (
        bool(account and arn),
        "<aws-account-id>" if account else "",
        redact_aws_text(arn) if arn else "",
        "<aws-user-id>" if user_id else "",
    )


def classify_sts_result(result: CommandResult) -> str:
    if not result.found:
        return "aws_cli_missing"
    if result.exit_code == 124:
        return "timeout"
    if result.exit_code == 0:
        ok, _, _, _ = parse_identity(result.stdout)
        return "ok" if ok else "malformed_identity_response"

    combined = f"{result.stdout}\n{result.stderr}".lower()
    if "invalidclienttokenid" in combined or "security token included in the request is invalid" in combined:
        return "invalid_client_token"
    if "expiredtoken" in combined or "token has expired" in combined or "expired token" in combined:
        return "expired_token"
    if "sso" in combined and ("login" in combined or "expired" in combined):
        return "sso_login_required"
    if "unable to locate credentials" in combined or "nocredentialserror" in combined:
        return "missing_credentials"
    if "accessdenied" in combined or "not authorized" in combined:
        return "access_denied"
    if (
        "could not connect" in combined
        or "endpoint" in combined
        or "name or service not known" in combined
        or "network" in combined
        or "ssl validation failed" in combined
    ):
        return "network_or_region_error"
    return "unknown_error"


def remediation_for(classification: str) -> str:
    messages = {
        "ok": "AWS identity is available; automated public-origin provisioning may proceed if IAM permissions also match the runbook.",
        "aws_cli_missing": "Install AWS CLI v2 or run the public origin manually without AWS automation.",
        "timeout": "Retry after checking local network access and AWS CLI credential providers.",
        "malformed_identity_response": "Re-run sts get-caller-identity and inspect the redacted local diagnostics before automation.",
        "invalid_client_token": "Refresh or replace the local AWS credentials, then rerun this checker.",
        "expired_token": "Refresh the session token or complete AWS SSO login, then rerun this checker.",
        "sso_login_required": "Run aws sso login for the selected profile, then rerun this checker.",
        "missing_credentials": "Configure a local profile, SSO session, or environment credentials before AWS automation.",
        "access_denied": "Use an identity allowed to call sts:GetCallerIdentity and the provisioning APIs required by the runbook.",
        "network_or_region_error": "Check region, DNS, proxy, and outbound network access before AWS automation.",
        "unknown_error": "Inspect redacted local diagnostics and rerun; do not commit raw AWS output.",
    }
    return messages.get(classification, messages["unknown_error"])


def profile_state_from_env() -> str:
    if os.environ.get("AWS_PROFILE") or os.environ.get("AWS_DEFAULT_PROFILE"):
        return "custom-profile-set"
    if os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_WEB_IDENTITY_TOKEN_FILE"):
        return "env-credentials-set"
    return "default-or-shared-config"


def build_readiness(
    region: str | None = None,
    include_redacted_diagnostics: bool = False,
    timeout: float = 8.0,
) -> AwsIdentityReadiness:
    resolved_region = region or os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "ap-northeast-2"
    env = dict(os.environ)
    env["AWS_REGION"] = resolved_region
    env["AWS_DEFAULT_REGION"] = resolved_region

    version = run_command(["aws", "--version"], timeout=timeout, include_output=True)
    sts_args = ["aws", "sts", "get-caller-identity", "--output", "json"]
    found = shutil.which(sts_args[0]) is not None
    command = " ".join(sts_args)
    if not found:
        sts = CommandResult(command, False, None, "", "command not found" if include_redacted_diagnostics else "")
        sts_for_classification = CommandResult(command, False, None, "", "command not found")
    else:
        try:
            proc = subprocess.run(
                sts_args,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
                env=env,
            )
            redacted_stdout = redact_aws_text(tail(proc.stdout.strip()))
            redacted_stderr = redact_aws_text(tail(proc.stderr.strip()))
            sts = CommandResult(
                command,
                True,
                proc.returncode,
                redacted_stdout,
                redacted_stderr if include_redacted_diagnostics else "",
            )
            sts_for_classification = CommandResult(command, True, proc.returncode, redacted_stdout, redacted_stderr)
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode("utf-8", errors="ignore") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode("utf-8", errors="ignore") if isinstance(exc.stderr, bytes) else (exc.stderr or "timeout")
            redacted_stdout = redact_aws_text(tail(stdout.strip()))
            redacted_stderr = redact_aws_text(tail(stderr.strip()))
            sts = CommandResult(
                command,
                True,
                124,
                redacted_stdout,
                redacted_stderr if include_redacted_diagnostics else "",
            )
            sts_for_classification = CommandResult(command, True, 124, redacted_stdout, redacted_stderr)

    classification = classify_sts_result(sts_for_classification)
    identity_ok = classification == "ok"
    _, account, arn, user_id = parse_identity(sts.stdout) if identity_ok else (False, "", "", "")

    return AwsIdentityReadiness(
        check_date=utc_date_iso(),
        public_safe=True,
        aws_cli_found=version.found,
        aws_cli_version=version.stdout.splitlines()[0] if version.stdout else "",
        region=resolved_region,
        profile_state=profile_state_from_env(),
        identity_ok=identity_ok,
        classification=classification,
        remediation=remediation_for(classification),
        account_id=account,
        arn=arn,
        user_id=user_id,
        redaction_applied=True,
        diagnostics_included=include_redacted_diagnostics,
        commands={
            "aws_version": version,
            "sts_get_caller_identity": sts,
        },
    )


def emit_markdown(readiness: AwsIdentityReadiness) -> str:
    lines = [
        "# AWS Identity Readiness",
        "",
        f"Generated: `{readiness.check_date}`",
        "",
        "This report is public-safe. It does not print AWS account IDs, ARNs, access keys, secret keys, session tokens, or profile names.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| AWS CLI found | `{'yes' if readiness.aws_cli_found else 'no'}` |",
        f"| identity ok | `{'yes' if readiness.identity_ok else 'no'}` |",
        f"| classification | `{readiness.classification}` |",
        f"| region | `{readiness.region}` |",
        f"| profile state | `{readiness.profile_state}` |",
        f"| diagnostics included | `{'yes' if readiness.diagnostics_included else 'no'}` |",
        "",
        "## Interpretation",
        "",
        readiness.remediation,
        "",
        "## Redacted Identity",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| account | `{readiness.account_id or '-'}` |",
        f"| arn | `{readiness.arn or '-'}` |",
        f"| user id | `{readiness.user_id or '-'}` |",
        "",
        "## Commands",
        "",
        "| command | found | exit | stdout | stderr |",
        "| --- | --- | ---: | --- | --- |",
    ]
    for result in readiness.commands.values():
        stdout = result.stdout.replace("|", "\\|") if result.stdout else "-"
        stderr = result.stderr.replace("|", "\\|") if result.stderr else "-"
        lines.append(
            f"| `{result.command}` | `{'yes' if result.found else 'no'}` | `{result.exit_code if result.exit_code is not None else '-'}` | `{stdout}` | `{stderr}` |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--region")
    parser.add_argument("--timeout", type=float, default=8.0)
    parser.add_argument("--include-redacted-diagnostics", action="store_true")
    parser.add_argument("--require-ok", action="store_true")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output")
    parser.add_argument("--json-output")
    args = parser.parse_args()

    readiness = build_readiness(
        region=args.region,
        include_redacted_diagnostics=args.include_redacted_diagnostics,
        timeout=args.timeout,
    )
    json_text = json.dumps(asdict(readiness), indent=2, ensure_ascii=False) + "\n"
    markdown = emit_markdown(readiness)
    if args.json_output:
        json_output = Path(args.json_output)
        json_output.parent.mkdir(parents=True, exist_ok=True)
        json_output.write_text(json_text, encoding="utf-8")
    text = json_text if args.format == "json" else markdown
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    if args.require_ok and not readiness.identity_ok:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
