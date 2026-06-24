# AWS Identity Public-Safe Check

Generated: `2026-06-24`

This report intentionally does not print AWS account IDs, ARNs, access keys, profiles, or credential file paths.

## Summary

| field | value |
| --- | --- |
| `check_date` | `2026-06-24` |
| `aws_cli_found` | `yes` |
| `aws_cli_version_present` | `yes` |
| `region_configured` | `yes` |
| `credential_source_present` | `yes` |
| `sts_identity_ok` | `no` |
| `sts_error_code` | `InvalidClientTokenId` |
| `public_safe` | `yes` |

## Next Action

- Refresh or replace local AWS credentials, then rerun `harness/scripts/aws-preflight.sh`.
- If AWS automation is not needed, this does not block manual controlled-public origin setup.
