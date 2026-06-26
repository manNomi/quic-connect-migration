# Final Browser Handover Run Plan

Generated: `2026-06-26`

## Summary

| field | value |
| --- | --- |
| config source | `public template` |
| public-safe default | `yes` |
| sensitive values redacted | `no` |
| Chrome active repetitions per variant | `3` |
| P1 feasibility target | `safari` |
| required trial groups | `6` |
| planned executions | `10` |

이 문서는 실험을 실행하지 않는다. 실제 도메인, 인증서 경로, network-change 명령을 추적 문서에 남기지 않기 위해 기본 출력은 public template 값으로 생성된다.

## Coverage

| requirement | phase | browser | min | planned | satisfies | accepted status |
| --- | --- | --- | ---: | ---: | --- | --- |
| `chrome-controlled-public-application-h3-baseline` | baseline | Chrome | 1 | 1 | `yes` | `PASS` |
| `chrome-downlink-noheartbeat-active-cm` | active-network-change | Chrome | 3 | 3 | `yes` | `PASS` |
| `chrome-downlink-heartbeat-active-cm` | active-network-change | Chrome | 3 | 3 | `yes` | `PASS` |
| `chrome-downlink-noheartbeat-nochange-baseline` | no-change-baseline | Chrome | 1 | 1 | `yes` | `PASS` |
| `chrome-downlink-heartbeat-nochange-baseline` | no-change-baseline | Chrome | 1 | 1 | `yes` | `PASS` |
| `p1-safari-or-android-feasibility` | active-network-change | Safari or Android Chrome | 1 | 1 | `yes` | `PASS_FEASIBILITY` |

## Execution Queue

| order | trial_id | requirement | phase | browser | heartbeat | expected requests |
| ---: | --- | --- | --- | --- | --- | ---: |
| 1 | `controlled-public-chrome-h3-baseline-001` | `chrome-controlled-public-application-h3-baseline` | baseline | Chrome | `n/a` | 4 |
| 2 | `controlled-public-chrome-downlink-noheartbeat-nochange-001` | `chrome-downlink-noheartbeat-nochange-baseline` | no-change-baseline | Chrome | `false` | 4 |
| 3 | `controlled-public-chrome-downlink-heartbeat-nochange-001` | `chrome-downlink-heartbeat-nochange-baseline` | no-change-baseline | Chrome | `true` | 6 |
| 4 | `controlled-public-chrome-downlink-noheartbeat-network-change-001` | `chrome-downlink-noheartbeat-active-cm` | active-network-change | Chrome | `false` | 2 |
| 5 | `controlled-public-chrome-downlink-noheartbeat-network-change-002` | `chrome-downlink-noheartbeat-active-cm` | active-network-change | Chrome | `false` | 2 |
| 6 | `controlled-public-chrome-downlink-noheartbeat-network-change-003` | `chrome-downlink-noheartbeat-active-cm` | active-network-change | Chrome | `false` | 2 |
| 7 | `controlled-public-chrome-downlink-heartbeat-network-change-001` | `chrome-downlink-heartbeat-active-cm` | active-network-change | Chrome | `true` | 3 |
| 8 | `controlled-public-chrome-downlink-heartbeat-network-change-002` | `chrome-downlink-heartbeat-active-cm` | active-network-change | Chrome | `true` | 3 |
| 9 | `controlled-public-chrome-downlink-heartbeat-network-change-003` | `chrome-downlink-heartbeat-active-cm` | active-network-change | Chrome | `true` | 3 |
| 10 | `controlled-public-safari-downlink-network-change-001` | `p1-safari-or-android-feasibility` | p1-feasibility | Safari | `false` | 2 |

## Trial Commands

### 1. `controlled-public-chrome-h3-baseline-001`

- requirement: `chrome-controlled-public-application-h3-baseline`
- artifact dir: `artifacts/controlled-public-chrome-h3-baseline-001`
- claim gate: status PASS; controlled_public_application_h3_confirmed; server qlog H3 confirmed
- registration: Record as PASS baseline before any active path-change trial.

Server/origin terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-h3-baseline-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-h3-baseline-001 \
PUBLIC_ORIGIN_HOST=h3.example.com \
PUBLIC_ORIGIN_PORT=443 \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
LISTEN_ADDR=0.0.0.0:443 \
TCP_ADDR=0.0.0.0:443 \
ALT_SVC='h3=":443"; ma=60' \
EXPECTED_REQUESTS=4 \
TIMEOUT=300s \
COMPLETION_GRACE=2s \
./scripts/run-controlled-public-h3-server.sh
```

Browser/client terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-h3-baseline-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-h3-baseline-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-chrome-h3-baseline-001 \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow' \
SECOND_URL='https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow' \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=4 \
REQUIRE_H3_ALT_SVC=1 \
REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3=1 \
./scripts/run-controlled-public-h3-browser-baseline.sh
```

### 2. `controlled-public-chrome-downlink-noheartbeat-nochange-001`

- requirement: `chrome-downlink-noheartbeat-nochange-baseline`
- artifact dir: `artifacts/controlled-public-chrome-downlink-noheartbeat-nochange-001`
- claim gate: no active network-change command; server/browser workload completes; classification no_path_change_baseline
- registration: Record migration_trigger as 'no network change' and notes with no_path_change_baseline. If heartbeat creates extra sessions or source tuples without a path-change command, keep it as baseline evidence, not CM success.

Server/origin terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-noheartbeat-nochange-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-nochange-001 \
PUBLIC_ORIGIN_HOST=h3.example.com \
PUBLIC_ORIGIN_PORT=443 \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
LISTEN_ADDR=0.0.0.0:443 \
TCP_ADDR=0.0.0.0:443 \
ALT_SVC='h3=":443"; ma=60' \
EXPECTED_REQUESTS=4 \
TIMEOUT=300s \
COMPLETION_GRACE=2s \
./scripts/run-controlled-public-h3-server.sh
```

Browser/client terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-noheartbeat-nochange-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-nochange-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-nochange-001 \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=false&heartbeat_delay_ms=5000&label=public-downlink-noheartbeat' \
SECOND_URL='https://h3.example.com/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=false&heartbeat_delay_ms=5000&label=public-downlink-noheartbeat' \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=4 \
REQUIRE_H3_ALT_SVC=1 \
REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3=1 \
./scripts/run-controlled-public-h3-browser-baseline.sh
```

### 3. `controlled-public-chrome-downlink-heartbeat-nochange-001`

- requirement: `chrome-downlink-heartbeat-nochange-baseline`
- artifact dir: `artifacts/controlled-public-chrome-downlink-heartbeat-nochange-001`
- claim gate: no active network-change command; server/browser workload completes; classification no_path_change_baseline
- registration: Record migration_trigger as 'no network change' and notes with no_path_change_baseline. If heartbeat creates extra sessions or source tuples without a path-change command, keep it as baseline evidence, not CM success.

Server/origin terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-heartbeat-nochange-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-heartbeat-nochange-001 \
PUBLIC_ORIGIN_HOST=h3.example.com \
PUBLIC_ORIGIN_PORT=443 \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
LISTEN_ADDR=0.0.0.0:443 \
TCP_ADDR=0.0.0.0:443 \
ALT_SVC='h3=":443"; ma=60' \
EXPECTED_REQUESTS=6 \
TIMEOUT=300s \
COMPLETION_GRACE=2s \
./scripts/run-controlled-public-h3-server.sh
```

Browser/client terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-heartbeat-nochange-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-heartbeat-nochange-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-heartbeat-nochange-001 \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=true&heartbeat_delay_ms=5000&label=public-downlink-heartbeat' \
SECOND_URL='https://h3.example.com/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=true&heartbeat_delay_ms=5000&label=public-downlink-heartbeat' \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=6 \
REQUIRE_H3_ALT_SVC=1 \
REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3=1 \
./scripts/run-controlled-public-h3-browser-baseline.sh
```

### 4. `controlled-public-chrome-downlink-noheartbeat-network-change-001`

- requirement: `chrome-downlink-noheartbeat-active-cm`
- artifact dir: `artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001`
- claim gate: classification possible_connection_migration; client_active_path_changed; server tuple changed; qlog path validation true
- registration: Reject as CM success if classifier reports reconnect_or_multiple_sessions or no_path_change_after_trigger.

Server/origin terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-noheartbeat-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
PUBLIC_ORIGIN_HOST=h3.example.com \
PUBLIC_ORIGIN_PORT=443 \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
LISTEN_ADDR=0.0.0.0:443 \
TCP_ADDR=0.0.0.0:443 \
ALT_SVC='h3=":443"; ma=60' \
EXPECTED_REQUESTS=2 \
TIMEOUT=300s \
COMPLETION_GRACE=2s \
./scripts/run-controlled-public-h3-server.sh
```

Browser/client terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-noheartbeat-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001 \
CONTROLLED_PUBLIC_BASELINE_SUMMARY=artifacts/controlled-public-chrome-h3-baseline-001/results/controlled-public-h3-baseline-summary.json \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=false&heartbeat_delay_ms=5000&label=public-downlink-noheartbeat' \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=2 \
REQUIRE_H3_ALT_SVC=1 \
REQUIRE_CONTROLLED_PUBLIC_BASELINE=1 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=18 \
CHROME_TIMEOUT_SECONDS=30 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
NETWORK_CHANGE_AFTER_SECONDS=3 \
NETWORK_CHANGE_CMD=... \
./scripts/run-controlled-public-h3-network-change.sh
```

### 5. `controlled-public-chrome-downlink-noheartbeat-network-change-002`

- requirement: `chrome-downlink-noheartbeat-active-cm`
- artifact dir: `artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-002`
- claim gate: classification possible_connection_migration; client_active_path_changed; server tuple changed; qlog path validation true
- registration: Reject as CM success if classifier reports reconnect_or_multiple_sessions or no_path_change_after_trigger.

Server/origin terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-noheartbeat-network-change-002 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-002 \
PUBLIC_ORIGIN_HOST=h3.example.com \
PUBLIC_ORIGIN_PORT=443 \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
LISTEN_ADDR=0.0.0.0:443 \
TCP_ADDR=0.0.0.0:443 \
ALT_SVC='h3=":443"; ma=60' \
EXPECTED_REQUESTS=2 \
TIMEOUT=300s \
COMPLETION_GRACE=2s \
./scripts/run-controlled-public-h3-server.sh
```

Browser/client terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-noheartbeat-network-change-002 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-002 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-002 \
CONTROLLED_PUBLIC_BASELINE_SUMMARY=artifacts/controlled-public-chrome-h3-baseline-001/results/controlled-public-h3-baseline-summary.json \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=false&heartbeat_delay_ms=5000&label=public-downlink-noheartbeat' \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=2 \
REQUIRE_H3_ALT_SVC=1 \
REQUIRE_CONTROLLED_PUBLIC_BASELINE=1 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=18 \
CHROME_TIMEOUT_SECONDS=30 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
NETWORK_CHANGE_AFTER_SECONDS=3 \
NETWORK_CHANGE_CMD=... \
./scripts/run-controlled-public-h3-network-change.sh
```

### 6. `controlled-public-chrome-downlink-noheartbeat-network-change-003`

- requirement: `chrome-downlink-noheartbeat-active-cm`
- artifact dir: `artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-003`
- claim gate: classification possible_connection_migration; client_active_path_changed; server tuple changed; qlog path validation true
- registration: Reject as CM success if classifier reports reconnect_or_multiple_sessions or no_path_change_after_trigger.

Server/origin terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-noheartbeat-network-change-003 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-003 \
PUBLIC_ORIGIN_HOST=h3.example.com \
PUBLIC_ORIGIN_PORT=443 \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
LISTEN_ADDR=0.0.0.0:443 \
TCP_ADDR=0.0.0.0:443 \
ALT_SVC='h3=":443"; ma=60' \
EXPECTED_REQUESTS=2 \
TIMEOUT=300s \
COMPLETION_GRACE=2s \
./scripts/run-controlled-public-h3-server.sh
```

Browser/client terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-noheartbeat-network-change-003 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-003 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-003 \
CONTROLLED_PUBLIC_BASELINE_SUMMARY=artifacts/controlled-public-chrome-h3-baseline-001/results/controlled-public-h3-baseline-summary.json \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=false&heartbeat_delay_ms=5000&label=public-downlink-noheartbeat' \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=2 \
REQUIRE_H3_ALT_SVC=1 \
REQUIRE_CONTROLLED_PUBLIC_BASELINE=1 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=18 \
CHROME_TIMEOUT_SECONDS=30 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
NETWORK_CHANGE_AFTER_SECONDS=3 \
NETWORK_CHANGE_CMD=... \
./scripts/run-controlled-public-h3-network-change.sh
```

### 7. `controlled-public-chrome-downlink-heartbeat-network-change-001`

- requirement: `chrome-downlink-heartbeat-active-cm`
- artifact dir: `artifacts/controlled-public-chrome-downlink-heartbeat-network-change-001`
- claim gate: classification possible_connection_migration; client_active_path_changed; server tuple changed; qlog path validation true; heartbeat response observed
- registration: Compare only against the heartbeat no-change baseline; do not treat extra sessions alone as CM.

Server/origin terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-heartbeat-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-heartbeat-network-change-001 \
PUBLIC_ORIGIN_HOST=h3.example.com \
PUBLIC_ORIGIN_PORT=443 \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
LISTEN_ADDR=0.0.0.0:443 \
TCP_ADDR=0.0.0.0:443 \
ALT_SVC='h3=":443"; ma=60' \
EXPECTED_REQUESTS=3 \
TIMEOUT=300s \
COMPLETION_GRACE=2s \
./scripts/run-controlled-public-h3-server.sh
```

Browser/client terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-heartbeat-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-heartbeat-network-change-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-heartbeat-network-change-001 \
CONTROLLED_PUBLIC_BASELINE_SUMMARY=artifacts/controlled-public-chrome-h3-baseline-001/results/controlled-public-h3-baseline-summary.json \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=true&heartbeat_delay_ms=5000&label=public-downlink-heartbeat' \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=3 \
REQUIRE_H3_ALT_SVC=1 \
REQUIRE_CONTROLLED_PUBLIC_BASELINE=1 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=18 \
CHROME_TIMEOUT_SECONDS=30 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
NETWORK_CHANGE_AFTER_SECONDS=3 \
NETWORK_CHANGE_CMD=... \
./scripts/run-controlled-public-h3-network-change.sh
```

### 8. `controlled-public-chrome-downlink-heartbeat-network-change-002`

- requirement: `chrome-downlink-heartbeat-active-cm`
- artifact dir: `artifacts/controlled-public-chrome-downlink-heartbeat-network-change-002`
- claim gate: classification possible_connection_migration; client_active_path_changed; server tuple changed; qlog path validation true; heartbeat response observed
- registration: Compare only against the heartbeat no-change baseline; do not treat extra sessions alone as CM.

Server/origin terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-heartbeat-network-change-002 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-heartbeat-network-change-002 \
PUBLIC_ORIGIN_HOST=h3.example.com \
PUBLIC_ORIGIN_PORT=443 \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
LISTEN_ADDR=0.0.0.0:443 \
TCP_ADDR=0.0.0.0:443 \
ALT_SVC='h3=":443"; ma=60' \
EXPECTED_REQUESTS=3 \
TIMEOUT=300s \
COMPLETION_GRACE=2s \
./scripts/run-controlled-public-h3-server.sh
```

Browser/client terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-heartbeat-network-change-002 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-heartbeat-network-change-002 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-heartbeat-network-change-002 \
CONTROLLED_PUBLIC_BASELINE_SUMMARY=artifacts/controlled-public-chrome-h3-baseline-001/results/controlled-public-h3-baseline-summary.json \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=true&heartbeat_delay_ms=5000&label=public-downlink-heartbeat' \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=3 \
REQUIRE_H3_ALT_SVC=1 \
REQUIRE_CONTROLLED_PUBLIC_BASELINE=1 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=18 \
CHROME_TIMEOUT_SECONDS=30 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
NETWORK_CHANGE_AFTER_SECONDS=3 \
NETWORK_CHANGE_CMD=... \
./scripts/run-controlled-public-h3-network-change.sh
```

### 9. `controlled-public-chrome-downlink-heartbeat-network-change-003`

- requirement: `chrome-downlink-heartbeat-active-cm`
- artifact dir: `artifacts/controlled-public-chrome-downlink-heartbeat-network-change-003`
- claim gate: classification possible_connection_migration; client_active_path_changed; server tuple changed; qlog path validation true; heartbeat response observed
- registration: Compare only against the heartbeat no-change baseline; do not treat extra sessions alone as CM.

Server/origin terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-heartbeat-network-change-003 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-heartbeat-network-change-003 \
PUBLIC_ORIGIN_HOST=h3.example.com \
PUBLIC_ORIGIN_PORT=443 \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
LISTEN_ADDR=0.0.0.0:443 \
TCP_ADDR=0.0.0.0:443 \
ALT_SVC='h3=":443"; ma=60' \
EXPECTED_REQUESTS=3 \
TIMEOUT=300s \
COMPLETION_GRACE=2s \
./scripts/run-controlled-public-h3-server.sh
```

Browser/client terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-downlink-heartbeat-network-change-003 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-heartbeat-network-change-003 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-heartbeat-network-change-003 \
CONTROLLED_PUBLIC_BASELINE_SUMMARY=artifacts/controlled-public-chrome-h3-baseline-001/results/controlled-public-h3-baseline-summary.json \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=true&heartbeat_delay_ms=5000&label=public-downlink-heartbeat' \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=3 \
REQUIRE_H3_ALT_SVC=1 \
REQUIRE_CONTROLLED_PUBLIC_BASELINE=1 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=18 \
CHROME_TIMEOUT_SECONDS=30 \
CHROME_NET_LOG_CAPTURE_MODE=Default \
NETWORK_CHANGE_AFTER_SECONDS=3 \
NETWORK_CHANGE_CMD=... \
./scripts/run-controlled-public-h3-network-change.sh
```

### 10. `controlled-public-safari-downlink-network-change-001`

- requirement: `p1-safari-or-android-feasibility`
- artifact dir: `artifacts/controlled-public-safari-downlink-network-change-001`
- claim gate: PASS_FEASIBILITY; server-qlog-only possible_connection_migration evidence
- registration: Record status as PASS_FEASIBILITY unless browser-internal QUIC evidence is added.

Server/origin terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-safari-downlink-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-safari-downlink-network-change-001 \
PUBLIC_ORIGIN_HOST=h3.example.com \
PUBLIC_ORIGIN_PORT=443 \
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem \
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem \
LISTEN_ADDR=0.0.0.0:443 \
TCP_ADDR=0.0.0.0:443 \
ALT_SVC='h3=":443"; ma=60' \
EXPECTED_REQUESTS=2 \
TIMEOUT=300s \
COMPLETION_GRACE=2s \
./scripts/run-controlled-public-h3-server.sh
```

Browser/client terminal:

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-safari-downlink-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-safari-downlink-network-change-001 \
CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR=artifacts/controlled-public-safari-downlink-network-change-001 \
CONTROLLED_PUBLIC_BASELINE_SUMMARY=artifacts/controlled-public-chrome-h3-baseline-001/results/controlled-public-h3-baseline-summary.json \
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=false&heartbeat_delay_ms=5000&label=p1-downlink-noheartbeat' \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=2 \
REQUIRE_H3_ALT_SVC=1 \
REQUIRE_CONTROLLED_PUBLIC_BASELINE=1 \
NETWORK_CHANGE_AFTER_SECONDS=3 \
NETWORK_CHANGE_CMD=... \
./scripts/run-safari-controlled-public-network-change.sh
```

## Post-run Verification

각 trial의 공개 가능한 요약 row를 `data/experiment-results.csv`에 등록한 뒤 다음을 실행한다.

```bash
python3 tools/audit_final_browser_handover_trials.py --output docs/results/final-browser-handover-trial-audit-20260624.md
python3 tools/build_paper_tables.py --output docs/results/paper-tables-20260624.md
python3 tools/audit_research_bundle.py --output docs/results/research-bundle-audit-20260624.md
python3 tools/verify_research_bundle.py --output docs/results/research-verification-report-20260624.md
python3 tools/validate_publication_bundle.py
```

최종 논문 Results에서 browser/mobile CM 본 실험 완료를 주장하려면 다음 명령이 exit 0이어야 한다.

```bash
python3 tools/audit_final_browser_handover_trials.py --require-complete
```
