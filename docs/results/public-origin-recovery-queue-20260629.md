# Public Origin Recovery Queue

Generated: `2026-06-29`

## Current State

The client-side path-change trigger is ready, but the controlled public origin is not.

| gate | current result |
| --- | --- |
| iPhone USB latent failover | `ready`, `en0 -> en8`, `1321ms` |
| controlled public origin DNS | `resolved` |
| controlled public origin TCP 443 | `connection_refused` |
| AWS identity | `invalid_client_token` |
| SSH recovery | `auth_failed` for probed users |
| local WebPKI cert/key | not readable on this Mac |
| final browser protocol | `3/6` requirements complete |

Interpretation: do not run the final Chrome active network-change wrapper while the origin returns `connection_refused`. That would create an origin-readiness failure artifact, not a meaningful browser CM row.

## Recovery Path A: AWS Credentials Become Valid

Use this when local AWS credentials are refreshed.

```bash
bash harness/scripts/aws-preflight.sh
python3 tools/check_controlled_public_origin_access.py \
  --config harness/config/controlled-public-origin.env \
  --format markdown \
  --output docs/results/controlled-public-origin-access-check-rerun-20260629.md
```

If AWS identity is valid but the existing origin still refuses TCP 443, recover or reprovision the controlled origin using the existing deploy packet:

```bash
open docs/results/controlled-public-origin-deploy-packet-20260629.md
```

Required recovered-origin properties:

- TCP 443 and UDP 443 reachable from this Mac.
- WebPKI certificate and matching private key installed on the origin host.
- `Alt-Svc: h3=":443"; ma=60` advertised.
- Server artifacts retained on the origin host until client artifacts are copied or summarized.

## Recovery Path B: SSH Becomes Available

Use this when the existing origin host can be reached over SSH.

```bash
scp harness/results/packages/quic-go-min-repro-20260629T052407Z.tar.gz \
  ec2-user@<origin-host-or-ip>:/tmp/quic-go-min-repro.tar.gz
scp repro/quic-go-min-repro/scripts/ec2-bootstrap-go.sh \
  ec2-user@<origin-host-or-ip>:/tmp/ec2-bootstrap-go.sh

ssh ec2-user@<origin-host-or-ip> 'bash /tmp/ec2-bootstrap-go.sh'
ssh ec2-user@<origin-host-or-ip> 'rm -rf /home/ec2-user/quic-go-min-repro && mkdir -p /home/ec2-user/quic-go-min-repro && tar -xzf /tmp/quic-go-min-repro.tar.gz -C /home/ec2-user/quic-go-min-repro'
```

Then start the controlled public H3 server on the origin host, replacing placeholders locally and never committing real values:

```bash
ssh ec2-user@<origin-host-or-ip> 'cd /home/ec2-user/quic-go-min-repro && sudo env \
  RUN_ID=controlled-public-chrome-h3-baseline-001 \
  ARTIFACT_DIR=artifacts/controlled-public-chrome-h3-baseline-001 \
  PUBLIC_ORIGIN_HOST=<public-origin-host> \
  PUBLIC_ORIGIN_PORT=443 \
  TLS_CERT_FILE=<webpki-fullchain-path> \
  TLS_KEY_FILE=<webpki-private-key-path> \
  LISTEN_ADDR=0.0.0.0:443 \
  TCP_ADDR=0.0.0.0:443 \
  ALT_SVC='"'"'h3=\":443\"; ma=60'"'"' \
  EXPECTED_REQUESTS=4 \
  TIMEOUT=300s \
  COMPLETION_GRACE=2s \
  MIN_ARTIFACT_FREE_GIB=7 \
  ./scripts/run-controlled-public-h3-server.sh'
```

## Client-Side Gate After Recovery

Run these from the repository root after the server is up:

```bash
python3 tools/check_public_origin_readiness.py \
  --url "$PUBLIC_ORIGIN_URL" \
  --require-h3-alt-svc \
  --redact-sensitive \
  --format markdown

ALLOW_LATENT_SECONDARY_PATH=1 \
NETWORK_CHANGE_CMD="networksetup -setairportpower 'en0' off" \
bash harness/scripts/controlled-public-preflight.sh
```

Proceed only if:

- public origin readiness passes,
- `h3` Alt-Svc is present,
- controlled public baseline summary is current or rerun,
- latent iPhone USB trigger is ready,
- artifact free space remains above the configured minimum.

## First Trial Queue After Recovery

Run fresh baseline first, then active path-change rows.

| order | trial | purpose |
| ---: | --- | --- |
| 1 | fresh Chrome controlled public H3 baseline | prove the recovered origin serves application HTTP/3 now |
| 2 | Chrome downlink no-heartbeat active path-change, 3 reps | test silent-client downlink behavior without recovery help |
| 3 | Chrome downlink heartbeat active path-change, 3 reps | test whether heartbeat changes failure/recovery behavior |
| 4 | Range/resumable download active path-change | compare byte-range recovery against local Range control |
| 5 | buffered-media active path-change | compare streaming QoE against local buffered-media control |
| 6 | Safari or Android feasibility | fill the P1 non-Chrome browser/mobile requirement |

Recommended first active command shape:

```bash
CHROME_RUNNER=cdp \
NETWORK_CHANGE_READY_EXPR='Number(document.body.dataset.downlinkBytes || "0") > 0' \
NETWORK_CHANGE_AFTER_SECONDS=0 \
NETWORK_CHANGE_AFTER_SNAPSHOT_COUNT=4 \
NETWORK_CHANGE_AFTER_SNAPSHOT_INTERVAL_SECONDS=1 \
NETWORK_CHANGE_CMD="networksetup -setairportpower 'en0' off" \
bash harness/scripts/final-chrome-network-change-run.sh
```

## Claim Boundary

Only count a recovered-origin active row as browser single-session CM if the same row shows:

- application HTTP/3 target request,
- client path changed from Wi-Fi to iPhone USB/cellular,
- target Chrome QUIC session count remains one,
- server tuple evidence is consistent with the changed client path,
- qlog path validation or equivalent migration evidence appears,
- workload completes without application retry masking replacement-session behavior.

Otherwise, classify it as application recovery, replacement-session continuity, or failed workload continuity according to the artifact evidence.
