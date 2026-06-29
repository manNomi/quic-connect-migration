# AWS Credential CSV Import Guide

Generated: `2026-06-29`

## Purpose

The current public-origin blocker is not the iPhone USB path-change trigger. The latest local checks show that the Mac can fail over from Wi-Fi `en0` to iPhone USB `en8`. The remaining automation blocker is AWS identity: `aws sts get-caller-identity` returns `InvalidClientTokenId`.

This guide explains how to load a new AWS credential CSV without committing secrets to the repository.

## Public-Safe Dry Run

Run this first. It prints only the credential shape, not the secret key or session token.

```bash
python3 tools/import_aws_credentials_csv.py ~/Downloads/YOUR_AWS_CREDENTIALS.csv
```

Expected useful fields:

| field | expected |
| --- | --- |
| parsed | `yes` |
| access key kind | `long-lived-AKIA` or `temporary-ASIA` |
| session token present | `yes` if this is a temporary credential |
| error | `-` |

## Write To The Local AWS Profile

Only run this if the dry run parsed the CSV correctly.

```bash
python3 tools/import_aws_credentials_csv.py ~/Downloads/YOUR_AWS_CREDENTIALS.csv \
  --profile default \
  --region ap-northeast-2 \
  --write \
  --validate
```

The tool writes only to local AWS files:

- `~/.aws/credentials`
- `~/.aws/config`

It does not write credentials into this repository. If an existing credentials file is present, the tool creates a timestamped backup unless `--no-backup` is explicitly set.

## Verify

```bash
python3 tools/check_aws_identity_readiness.py --require-ok
```

If this passes, rerun the public-origin recovery/preflight path:

```bash
python3 tools/check_public_origin_readiness.py \
  --url 'https://43-203-244-29.sslip.io/browser-downlink?duration_ms=15000' \
  --timeout 8 \
  --format markdown
```

If the origin still returns `connection_refused`, AWS identity is fixed but the EC2/origin service still needs to be recovered or reprovisioned.

## Safety Boundary

- Do not commit the AWS CSV.
- Do not paste access keys into tracked markdown.
- Do not run final Chrome CM trials while the public origin returns `connection_refused`; that would create an infrastructure-failure artifact, not a meaningful CM row.
