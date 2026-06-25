# Controlled Public Origin Deploy Packet

Generated: `2026-06-25`

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
| expected requests | `4` |
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
- At least 5 GiB free disk is available for qlog/NetLog-related artifacts.

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
  EXPECTED_REQUESTS=4 \
  TIMEOUT=300s \
  COMPLETION_GRACE=2s \
  MIN_ARTIFACT_FREE_GIB=5 \
  ./scripts/run-controlled-public-h3-server.sh'
```

## 4. Validate From Client Machine

Fill the ignored local config and run the readiness gates:

```bash
cp harness/config/controlled-public-origin.env.example harness/config/controlled-public-origin.env
$EDITOR harness/config/controlled-public-origin.env
set -a
source harness/config/controlled-public-origin.env
set +a
python3 tools/check_controlled_public_config.py --require-baseline-ready
python3 tools/check_public_origin_readiness.py --url "$PUBLIC_ORIGIN_URL" --require-h3-alt-svc --format markdown
python3 tools/check_next_final_handover_trial_readiness.py --output docs/results/final-handover-next-trial-readiness-20260624.md
```

## 5. Run Baseline Browser Trial

Use the generated final handover trial packet for the exact server/client commands:

```bash
python3 tools/build_final_handover_trial_packet.py --use-local-config --output docs/results/final-handover-trial-packet-20260624.md
```

After the browser baseline finishes, register only if the artifact bundle and final-countable gates pass:

```bash
python3 tools/check_final_handover_trial_artifact_bundle.py --trial-id controlled-public-chrome-h3-baseline-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001 --require-final-countable --require-complete
python3 tools/append_final_handover_result_row.py --trial-id controlled-public-chrome-h3-baseline-001 --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001 --require-final-countable --require-artifact-bundle --apply
python3 tools/audit_final_browser_handover_trials.py --output docs/results/final-browser-handover-trial-audit-20260624.md
python3 tools/verify_research_bundle.py --output docs/results/research-verification-report-20260624.md
```

## Safe Handling

- Do not commit `harness/config/controlled-public-origin.env`.
- Do not commit certificate files, private keys, SSH keys, qlogs, keylogs, pcaps, NetLogs, or raw artifacts.
- If the origin host is not AWS-managed, this packet still applies as long as TCP/UDP 443 and WebPKI TLS are available.
