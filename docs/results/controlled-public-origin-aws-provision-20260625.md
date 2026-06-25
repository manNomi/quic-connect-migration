# Controlled Public Origin AWS Provision

Generated: `2026-06-25`

This report is public-safe. It records the controlled public origin provisioning state without exposing the AWS account, public IP address, SSH target, or key path.

## Summary

| field | value |
| --- | --- |
| AWS profile | `quic-cm-lab` |
| region | `ap-northeast-2` |
| Route53 zone for candidate domain | `not available in this AWS account` |
| candidate host | `<redacted-controlled-public-host>` |
| candidate URL | `<redacted-controlled-public-url>` |
| EC2 origin host | `provisioned` |
| security group | `provisioned` |
| SSH access | `ready` |
| remote quic-go harness | `deployed` |
| remote Go/certbot/tcpdump | `ready` |
| DNS record | `pending registrar update` |
| WebPKI certificate | `pending DNS propagation` |
| P0 Chrome baseline capture | `blocked until DNS and certificate are ready` |

## Candidate Classification

`https://i18nexus.pro/` is useful as a user-provided domain candidate, but the apex currently resolves to a managed Vercel deployment and does not advertise `Alt-Svc: h3`. It also cannot provide server-side qlog evidence for this study. Therefore, the apex is not a controlled public origin for the final browser handover protocol.

The controlled-origin path is to use a dedicated subdomain that points directly to the EC2 origin host. That host can run the quic-go server wrapper, expose TCP 443 and UDP 443, and produce server request/qlog artifacts.

## Required External Action

Create the following DNS record at the registrar/DNS provider for the candidate domain:

| type | name | value |
| --- | --- | --- |
| `A` | `<redacted-controlled-public-host>` | `<redacted-ec2-public-ip>` |

After DNS propagation, issue a WebPKI certificate on the EC2 host with certbot and then fill the ignored local `harness/config/controlled-public-origin.env` with the controlled host, URL, and certificate paths.

## Next Validation Commands

Run these after DNS propagation and certificate issuance:

```bash
python3 tools/check_public_origin_readiness.py \
  --url "$PUBLIC_ORIGIN_URL" \
  --require-h3-alt-svc \
  --redact-sensitive \
  --format markdown

RUN_ID=final-p0-baseline-preflight-after-dns \
CHECK_PUBLIC_ORIGIN=1 \
CHECK_LOCAL_FILES=0 \
USE_LOCAL_CONFIG_FOR_PLAN=1 \
REDACT_SENSITIVE=1 \
bash harness/scripts/final-p0-baseline-preflight.sh
```

## Interpretation

- AWS provisioning is no longer the blocker.
- DNS control is outside this AWS account because no Route53 hosted zone exists for the candidate domain.
- The next research gate remains the P0 controlled-public Chrome application H3 baseline.
