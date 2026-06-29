# AWS EC2 Fresh Controlled-Origin Provision

Generated: `2026-06-29`

This report is public-safe. It intentionally omits the AWS account, instance ID,
public IP address, public hostname, SSH target, key path, and certificate
hostname.

## Summary

| field | value |
| --- | --- |
| AWS profile | `quic-cm-lab` |
| region | `ap-northeast-2` |
| fresh EC2 origin | `provisioned` |
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
| local private state | `harness/results/aws-origin-20260629/state.env` |
| local ignored config | `harness/config/controlled-public-origin.env` |

## Actions Performed

1. Confirmed that the `quic-cm-lab` AWS profile is valid.
2. Reused the previous controlled-public-origin subnet, security group, and SSH
   key to minimize testbed drift.
3. Launched a fresh EC2 instance with public IPv4 enabled.
4. Built and uploaded the current quic-go reproducibility package.
5. Installed Go `1.26.4`, `tcpdump`, and `certbot` on the origin.
6. Issued a WebPKI certificate for a temporary `sslip.io` origin name.
7. Updated ignored local origin config to point at the fresh EC2 origin.
8. Started the controlled public H3 server through `systemd-run`.
9. Verified HTTPS readiness and `Alt-Svc: h3`.
10. Ran a Chrome baseline probe against the fresh origin.

## Validation Results

| check | result |
| --- | --- |
| EC2 instance status check | `PASS` |
| SSH connectivity | `PASS` |
| remote quic-go harness deployed | `PASS` |
| WebPKI certificate readable on origin | `PASS` |
| public HTTPS/curl readiness | `PASS` |
| `Alt-Svc: h3` advertised | `PASS` |
| Chrome public H3 baseline | `PASS` |
| combined browser/server H3 classifier | `PASS` |
| final active network-change readiness | `BLOCKED` |

The Chrome baseline classified as `public_natural_h3_observed`. The combined
browser/server classifier classified as
`controlled_public_application_h3_confirmed`.

## Important Caveat

The fresh origin is publicly reachable on TCP/UDP 443. During the first combined
baseline run, unsolicited HTTP/1.1 scanner traffic reached the server and
contributed to the server request counter. Therefore, this run is strong
evidence that the fresh origin is restored and can serve browser-observed H3,
but it should not be treated as a clean final-countable handover trial.

For paper-grade active network-change evidence, run the next trial with:

- a fresh server run id,
- a higher or workload-filtered expected request policy,
- remote server artifacts collected immediately after the browser run,
- explicit path-change command evidence, and
- iPhone USB/Wi-Fi failover measurement recorded before the trial.

## Generated Public-Safe Artifacts

- `docs/results/controlled-public-origin-fresh-readiness-20260629.md`
- `docs/results/controlled-public-config-check-fresh-20260629.md`
- `docs/results/final-handover-next-trial-readiness-fresh-20260629.md`

## Remaining Required Gates

| gate | status |
| --- | --- |
| active path-change command | `missing` |
| desktop path-change readiness | `not ready` |
| clean final-countable baseline summary | `needs rerun/collection` |
