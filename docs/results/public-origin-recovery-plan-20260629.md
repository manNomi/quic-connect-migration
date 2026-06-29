# Public Origin Recovery Plan

Generated: `2026-06-29`

This report is public-safe. It does not print hostnames, IP addresses, AWS account IDs, SSH targets, TLS paths, private keys, or raw command output.

## Current Gate Summary

| gate | value |
| --- | --- |
| DNS | `resolved` |
| TCP 443 | `connection_refused` |
| public readiness | `not_ready` |
| h3 Alt-Svc | `no` |
| AWS identity | `invalid_client_token` |
| SSH recovery | `no` |
| any recovery path | `no` |
| baseline ready | `yes` |
| final protocol | `3/6` |

## Step Status

| step | status | reason | success gate |
| --- | --- | --- | --- |
| aws-credentials | `blocked` | AWS identity is not usable yet: invalid_client_token. | tools/check_aws_identity_readiness.py reports identity ok |
| public-origin-reachable | `blocked` | Public origin is not reachable yet; current TCP classification is connection_refused and no recovery path is ready. | check_public_origin_readiness reports ok=true and has_h3_alt_svc=true |
| fresh-public-baseline | `waiting` | Baseline cannot be refreshed until the public origin is reachable. | public origin readiness ok=true |
| active-browser-trials | `waiting` | Do not run active browser rows while the origin is unreachable. | public origin and fresh baseline are ready |

## Next Action

`aws-credentials`: AWS identity is not usable yet: invalid_client_token.

```bash
python3 tools/import_aws_credentials_csv.py ~/Downloads/YOUR_AWS_CREDENTIALS.csv
python3 tools/import_aws_credentials_csv.py ~/Downloads/YOUR_AWS_CREDENTIALS.csv \
  --profile default \
  --region ap-northeast-2 \
  --write \
  --validate
bash harness/scripts/aws-preflight.sh
```

## Final Protocol Blockers

- chrome-downlink-noheartbeat-active-cm: 0/3
- chrome-downlink-heartbeat-active-cm: 0/3
- p1-safari-or-android-feasibility: 0/1

## Claim Boundary

This planner selects recovery actions. It is not QUIC migration evidence; only final trial artifacts can support browser CM claims.
