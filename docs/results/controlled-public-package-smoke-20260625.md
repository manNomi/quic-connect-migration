# Controlled Public Package Smoke

Generated: `2026-06-25`

This smoke check is public-safe. It verifies that the origin-host reproducibility package can be built locally without including raw browser/server artifacts.

## Summary

| field | value |
| --- | --- |
| package command | `harness/scripts/package-quic-go-ec2.sh` |
| status | `PASS` |
| package path | `harness/results/packages/quic-go-min-repro-20260625T073551Z.tar.gz` |
| manifest path | `harness/results/packages/quic-go-min-repro-20260625T073551Z.manifest.env` |
| package size | `44 KiB` |
| raw artifact paths found in tarball | `0` |
| sensitive capture markers found in tarball | `0` |

## Included Top-Level Paths

| path | purpose |
| --- | --- |
| `./go.mod`, `./go.sum` | Go module metadata |
| `./cmd/` | h3 server/client and UDP rebinding proxy commands |
| `./internal/` | shared Go helpers and tests |
| `./scripts/` | controlled-public, local, Safari, Android, and packaging wrappers |

## Interpretation

The package is ready to upload to a public origin host after the operator provides SSH access, a WebPKI hostname/certificate, and TCP/UDP 443 firewall access. It intentionally excludes `./artifacts/*`, NetLog, qlog, pcap, keylog, and other raw experiment outputs.
