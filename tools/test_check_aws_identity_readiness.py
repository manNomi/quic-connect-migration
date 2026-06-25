#!/usr/bin/env python3
"""Regression tests for public-safe AWS identity readiness classification."""

from __future__ import annotations

import json

from check_aws_identity_readiness import (
    CommandResult,
    classify_sts_result,
    emit_markdown,
    parse_identity,
    redact_aws_text,
    remediation_for,
)


ACCOUNT = "123456" + "789012"
ARN = "arn:aws:sts::" + ACCOUNT + ":assumed-role/ResearchRole/session"


def result(exit_code: int | None, stdout: str = "", stderr: str = "", found: bool = True) -> CommandResult:
    return CommandResult("aws sts get-caller-identity --output json", found, exit_code, stdout, stderr)


def test_invalid_client_token_is_classified() -> None:
    stderr = "An error occurred (InvalidClientTokenId) when calling the GetCallerIdentity operation: The security token included in the request is invalid."
    assert classify_sts_result(result(255, stderr=redact_aws_text(stderr))) == "invalid_client_token"
    assert "Refresh or replace" in remediation_for("invalid_client_token")


def test_expired_token_is_classified() -> None:
    stderr = "An error occurred (ExpiredToken) when calling the GetCallerIdentity operation: The security token included in the request is expired"
    assert classify_sts_result(result(255, stderr=redact_aws_text(stderr))) == "expired_token"


def test_missing_cli_is_classified() -> None:
    assert classify_sts_result(result(None, found=False)) == "aws_cli_missing"


def test_success_identity_is_redacted_and_markdown_safe() -> None:
    stdout = json.dumps({"Account": ACCOUNT, "Arn": ARN, "UserId": "AROATEST:session"})
    redacted_stdout = redact_aws_text(stdout)
    ok, account, arn, user_id = parse_identity(redacted_stdout)
    assert ok
    assert account == "<aws-account-id>"
    assert arn == "<aws-arn>"
    assert user_id == "<aws-user-id>"
    assert ACCOUNT not in redacted_stdout
    assert "ResearchRole" not in redacted_stdout


def test_markdown_does_not_leak_identity_values() -> None:
    from check_aws_identity_readiness import AwsIdentityReadiness

    readiness = AwsIdentityReadiness(
        check_date="2026-06-25",
        public_safe=True,
        aws_cli_found=True,
        aws_cli_version="aws-cli/2.x Python/3.x",
        region="ap-northeast-2",
        profile_state="custom-profile-set",
        identity_ok=True,
        classification="ok",
        remediation=remediation_for("ok"),
        account_id="<aws-account-id>",
        arn="<aws-arn>",
        user_id="<aws-user-id>",
        redaction_applied=True,
        diagnostics_included=False,
        commands={
            "sts": result(0, stdout=redact_aws_text(json.dumps({"Account": ACCOUNT, "Arn": ARN, "UserId": "AROATEST:session"}))),
        },
    )
    markdown = emit_markdown(readiness)
    assert ACCOUNT not in markdown
    assert ARN not in markdown
    assert "ResearchRole" not in markdown
    assert "<aws-account-id>" in markdown


def main() -> int:
    test_invalid_client_token_is_classified()
    test_expired_token_is_classified()
    test_missing_cli_is_classified()
    test_success_identity_is_redacted_and_markdown_safe()
    test_markdown_does_not_leak_identity_values()
    print("check_aws_identity_readiness=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
