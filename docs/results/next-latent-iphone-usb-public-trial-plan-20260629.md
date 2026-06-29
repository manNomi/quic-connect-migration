# Next Latent iPhone USB Public Trial Plan

Date: `2026-06-29`

## Current Gate Status

Latest local preflight with `ALLOW_LATENT_SECONDARY_PATH=1`:

| gate | status |
| --- | --- |
| Chrome found | `pass` |
| application H3 baseline summary | `PASS` |
| network-change harness | `pass` |
| strict active secondary path | `not ready` |
| latent iPhone USB candidate | `ready` |
| desktop path-change mode | `latent-iphone-usb-failover` |
| `NETWORK_CHANGE_CMD` | `present when provided via env` |
| controlled public origin readiness | `failed in current preflight` |
| active server artifact | `missing` |

Preflight artifact:

`repro/quic-go-min-repro/artifacts/controlled-public-preflight-latent-iphone-usb-with-cmd-fixed-20260629/results/controlled-public-experiment-readiness.md`

## Current Server Diagnosis

Public-safe local checks show:

| check | result |
| --- | --- |
| public origin DNS | `resolves` |
| TCP 443 from client | `connection refused` |
| local TLS cert file | `missing on this Mac` |
| local TLS key file | `missing on this Mac` |
| AWS caller identity | `invalid_client_token` |

Interpretation: the public host exists, but the controlled origin server is not currently listening on 443. The WebPKI cert/key paths are not available on this Mac, so the server likely needs to be restarted on the origin host where the cert/key live, or AWS credentials need to be refreshed to provision/recover a new origin.

Prepared package/deploy packet:

- `harness/results/packages/quic-go-min-repro-20260629T052407Z.tar.gz`
- `docs/results/controlled-public-origin-deploy-packet-20260629.md`

## Required Next Inputs

The path-change command for this Mac+iPhone setup should be:

```bash
NETWORK_CHANGE_CMD="networksetup -setairportpower 'en0' off"
```

Restore command after a run:

```bash
networksetup -setairportpower 'en0' on
```

The public origin server must be running and reachable before the active trial. The current config has baseline fields and a baseline summary, but the active server artifact was missing during preflight.

## Recommended First Trial

Use a downlink no-heartbeat trial first because prior iPhone USB rows showed failures without application retry and because downlink gives a clean client path-loss case.

Suggested ready trigger:

```bash
NETWORK_CHANGE_READY_EXPR='Number(document.body.dataset.downlinkBytes || "0") > 0'
```

Suggested browser/network run shape:

```bash
ALLOW_LATENT_SECONDARY_PATH=1 \
NETWORK_CHANGE_CMD="networksetup -setairportpower 'en0' off" \
bash harness/scripts/controlled-public-preflight.sh
```

Then run the controlled public server and Chrome network-change wrapper with:

```bash
CHROME_RUNNER=cdp \
NETWORK_CHANGE_READY_EXPR='Number(document.body.dataset.downlinkBytes || "0") > 0' \
NETWORK_CHANGE_AFTER_SECONDS=0 \
NETWORK_CHANGE_AFTER_SNAPSHOT_COUNT=4 \
NETWORK_CHANGE_AFTER_SNAPSHOT_INTERVAL_SECONDS=1 \
NETWORK_CHANGE_CMD="networksetup -setairportpower 'en0' off" \
bash harness/scripts/final-chrome-network-change-run.sh
```

## Interpretation Rule

Do not label this as pure simultaneous-path QUIC Connection Migration. Label the environment as:

`latent Wi-Fi-loss-to-iPhone-USB cellular failover`

Count it as single-session QUIC CM only if the final artifact shows all of:

- client path changed from Wi-Fi to iPhone USB/cellular,
- target Chrome QUIC session count remains one,
- server qlog includes path validation or equivalent path migration evidence,
- server tuple evidence is consistent with a changed client path,
- workload completes without application-level retry masking the transport behavior.

If the workload completes with multiple Chrome target QUIC sessions, classify it as recovery/replacement-session continuity rather than single-session CM.
