# Controlled Public Origin Access Check

Generated: `2026-06-29`

This report is public-safe. It does not print hostnames, IP addresses, certificate paths, private key paths, SSH targets, AWS account IDs, or raw command output.

## Summary

| field | value |
| --- | --- |
| config exists | `yes` |
| public host configured | `yes` |
| public port configured | `yes` |
| DNS classification | `resolved` |
| DNS address count | `1` |
| TCP classification | `connection_refused` |
| TLS cert local readable | `no` |
| TLS key local readable | `no` |
| SSH recovery ready | `no` |
| AWS identity ready | `no` |
| local TLS material ready | `no` |
| any recovery path ready | `no` |

## SSH Probes

| user label | attempted | classification |
| --- | --- | --- |
| `ec2-user` | `yes` | `auth_failed` |
| `ubuntu` | `yes` | `auth_failed` |

## AWS

| field | value |
| --- | --- |
| attempted | `yes` |
| AWS CLI found | `yes` |
| identity OK | `no` |
| classification | `invalid_client_token` |
| region | `ap-northeast-2` |
| profile state | `default-or-shared-config` |

## Blockers

- public origin TCP 443 is not accepting connections: connection_refused
- configured WebPKI cert/key are not readable on this machine
- SSH access to configured public origin was not available with probed users
- AWS identity is not available for recovery/provisioning: invalid_client_token

## Claim Boundary

This is an origin access diagnostic, not QUIC migration evidence.
