# Controlled Public Origin Deploy Packet

Generated: `2026-06-30`

This packet is public-safe. It uses placeholders for hostnames, certificate paths, private key paths, and SSH targets.

## Summary

| field | value |
| --- | --- |
| package script | `harness/scripts/package-quic-go-ec2.sh` |
| package path | `harness/results/packages/<generated-quic-go-min-repro>.tar.gz` |
| package built now | `no` |
| SSH target placeholder | `ec2-user@<origin-host-or-ip>` |
| remote dir | `/home/ec2-user/quic-go-min-repro` |
| baseline run id | `controlled-public-chrome-h3-baseline-001` |
| expected requests | `2` |
| workload trial packet | `docs/results/noniphone-public-workload-trial-packet-20260701.md` |
| public safe | `yes` |

## 1. Build Local Package

```bash
harness/scripts/package-quic-go-ec2.sh
```

## 2. Prepare Origin Host

Origin host requirements:

- Public DNS name resolves to this host.
- TCP 443 and UDP 443 are open from the browser client.
- A WebPKI certificate chain and matching private key are installed locally on the origin host.
- The operator can SSH to the host.
- At least 7 GiB free disk is available for qlog/NetLog-related artifacts.

Upload package and bootstrap script:

```bash
scp harness/results/packages/<generated-quic-go-min-repro>.tar.gz ec2-user@<origin-host-or-ip>:/tmp/quic-go-min-repro.tar.gz
scp repro/quic-go-min-repro/scripts/ec2-bootstrap-go.sh ec2-user@<origin-host-or-ip>:/tmp/ec2-bootstrap-go.sh
```

Bootstrap Go/tcpdump and unpack the reproducibility package:

```bash
ssh ec2-user@<origin-host-or-ip> 'bash /tmp/ec2-bootstrap-go.sh'
ssh ec2-user@<origin-host-or-ip> 'rm -rf /home/ec2-user/quic-go-min-repro && mkdir -p /home/ec2-user/quic-go-min-repro && tar -xzf /tmp/quic-go-min-repro.tar.gz -C /home/ec2-user/quic-go-min-repro'
```

## 3. Start Controlled Public H3 Server

Run this on the origin host. Replace placeholders locally; do not commit real values.

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
  EXPECTED_REQUESTS=2 \
  TIMEOUT=300s \
  COMPLETION_GRACE=2s \
  MIN_ARTIFACT_FREE_GIB=7 \
  ./scripts/run-controlled-public-h3-server.sh'
```

## 4. Validate From Client Machine

Fill the ignored local config and run the readiness gates:

```bash
bash harness/scripts/init-controlled-public-config.sh
$EDITOR harness/config/controlled-public-origin.env
set -a
source harness/config/controlled-public-origin.env
set +a
python3 tools/check_controlled_public_config.py --require-baseline-ready
python3 tools/check_public_origin_readiness.py --url "$PUBLIC_ORIGIN_URL" --require-h3-alt-svc --redact-sensitive --format markdown
python3 tools/check_next_final_handover_trial_readiness.py --output docs/results/final-handover-next-trial-readiness-20260624.md
```

## 5. Run Baseline Browser Trial

First prove that the origin serves application HTTP/3 before attempting path-change workloads:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-h3-baseline-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-h3-baseline-001 \
PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_BOOTSTRAP_URL:-$PUBLIC_ORIGIN_BASE/browser-slow?duration_ms=3000&chunks=3&label=public-bootstrap}" \
SECOND_URL="${PUBLIC_ORIGIN_BASE:?set PUBLIC_ORIGIN_BASE like https://h3.example.com}/browser-slow?duration_ms=3000&chunks=3&label=public-h3-baseline" \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=2 \
REQUIRE_H3_ALT_SVC=1 \
RUN_CONTROLLED_PUBLIC_CLASSIFIER=1 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=25 \
CHROME_TIMEOUT_SECONDS=45 \
./scripts/run-controlled-public-h3-browser-baseline.sh
```

Then bind the baseline summary path for active controlled-public workload trials:

```bash
export CONTROLLED_PUBLIC_BASELINE_SUMMARY="artifacts/controlled-public-chrome-h3-baseline-001/results/controlled-public-h3-baseline-summary.json"
```

## 6. Run non-iPhone Public Workload Packet

Use the non-iPhone public workload packet for the exact range, upload, buffered-video, and music-like commands:

```bash
open docs/results/noniphone-public-workload-trial-packet-20260701.md
# Execute the packet order only after the baseline summary is PASS and a non-iPhone NETWORK_CHANGE_CMD is set.
```

Strong CM acceptance for each active row requires all of the following evidence:

1. application task completion is true for the workload-specific DOM metric
2. client active path changed according to route snapshots
3. server target H3 remote tuple count changed
4. server qlog records PATH_CHALLENGE and PATH_RESPONSE
5. Chrome target QUIC session count is one

## 7. Register Results Only After Classification

After each public workload finishes, classify the row and commit only public-safe summary documents:

```bash
python3 tools/classify_controlled_public_h3_network_change.py \
  --artifact-dir repro/quic-go-min-repro/artifacts/<trial-id> \
  --server-artifact-dir repro/quic-go-min-repro/artifacts/<trial-id>-server \
  --output docs/results/<trial-id>-validation.md \
  --json-output data/<trial-id>-validation.json
```

## Safe Handling

- Do not commit `harness/config/controlled-public-origin.env`.
- Do not commit certificate files, private keys, SSH keys, qlogs, keylogs, pcaps, NetLogs, or raw artifacts.
- If the origin host is not AWS-managed, this packet still applies as long as TCP/UDP 443 and WebPKI TLS are available.
- This packet is a deployment/run plan. It is not evidence that a public workload or browser Connection Migration trial has succeeded.
