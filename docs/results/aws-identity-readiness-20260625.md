# AWS Identity Readiness

Generated: `2026-06-26`

This report is public-safe. It does not print AWS account IDs, ARNs, access keys, secret keys, session tokens, or profile names.

## Summary

| field | value |
| --- | --- |
| AWS CLI found | `yes` |
| identity ok | `no` |
| classification | `invalid_client_token` |
| region | `ap-northeast-2` |
| profile state | `default-or-shared-config` |
| diagnostics included | `no` |

## Interpretation

Refresh or replace the local AWS credentials, then rerun this checker.

## Redacted Identity

| field | value |
| --- | --- |
| account | `-` |
| arn | `-` |
| user id | `-` |

## Commands

| command | found | exit | stdout | stderr |
| --- | --- | ---: | --- | --- |
| `aws --version` | `yes` | `0` | `aws-cli/2.34.38 Python/3.14.4 Darwin/24.6.0 source/arm64` | `-` |
| `aws sts get-caller-identity --output json` | `yes` | `254` | `-` | `-` |
