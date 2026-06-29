# AWS EC2 Controlled-Origin Refresh

Generated: `2026-06-29`

This report is public-safe. It intentionally omits the AWS account, instance ID,
public IP address, public hostname, SSH target, local SSH key path, and concrete
temporary TLS hostname.

## Summary

| field | value |
| --- | --- |
| AWS profile | `quic-cm-lab` |
| region | `ap-northeast-2` |
| new EC2 origin | `provisioned` |
| instance class | `t3.small` |
| OS image | `Amazon Linux 2023 x86_64` |
| root volume | `20 GiB gp3, delete-on-termination` |
| security group | `reused controlled-public-origin SG` |
| SSH key | `reused existing lab key` |
| SSH access | `ready` |
| quic-go package | `uploaded` |
| Go/tcpdump/certbot | `ready` |
| temporary WebPKI DNS | `ready via sslip.io` |
| WebPKI certificate | `issued` |
| default local state | `harness/results/aws-origin-20260629/state.env` |
| default ignored config | `harness/config/controlled-public-origin.env` |

## Validation

| check | result |
| --- | --- |
| EC2 instance status check | `PASS` |
| SSH connectivity | `PASS` |
| remote quic-go harness deployed | `PASS` |
| WebPKI certificate readable on origin | `PASS` |
| Chrome smoke trial | `PASS` |
| combined browser/server H3 classifier | `PASS` |
| remote transient service after smoke | `inactive` |

Smoke trial:

- Trial id: `controlled-public-chrome-fresh-origin-smoke-20260629-005`
- Summary status: `PASS`
- Classification: `controlled_public_application_h3_confirmed`
- Browser classification: `public_natural_h3_observed`
- Application workload: `downlink`
- Application result: `complete=true`, `success=true`
- Server request count: `5`
- Server H3 application evidence: `true`
- Server path validation evidence: `false` (expected for a no-change smoke)

Validation artifact:

- `docs/results/controlled-public-chrome-fresh-origin-smoke-20260629-005-validation.md`

## Operational Notes

The default local state and ignored controlled-public config now point to the
new origin. Previous local state/config files were kept only under ignored
`harness/results/` backup paths.

During smoke testing, public scanner traffic reached TCP/443 on early attempts.
The final countable smoke used a clean expected request count and succeeded with
only the controlled Chrome workload counted.

There are older controlled-origin EC2 instances still running in the same lab
security group. They should be stopped or terminated only after confirming that
their artifacts are no longer needed.
