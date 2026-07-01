# Chrome Desktop Non-iPhone Range Local Refresh

Generated: `2026-06-30`

## Scope

This report summarizes local Chrome forced-H3 byte-range download workloads under UDP rebinding and transient server-to-client packet loss. It models resumable large-download recovery. These rows are local proxy controls, not public Wi-Fi-to-cellular browser handover trials.

## Purpose

This refresh complements the media local refresh with a large-download-like byte-range workload that can be executed without iPhone input. The question is narrower than public handover:

> Can Chrome desktop complete a byte-range workload across local UDP rebinding while preserving single target-session path evidence?

## Commands

Fast range run:

```bash
WORKLOAD=range \
RUN_ID=chrome-desktop-noniphone-range-drop3000-retry0-20260630 \
REBIND_AFTER=1s \
DROP_A_SERVER_AFTER_SWITCH=1 \
DROP_A_SERVER_AFTER_SWITCH_FOR=3000ms \
RANGE_TOTAL_BYTES=1048576 \
RANGE_CHUNK_BYTES=131072 \
RANGE_CHUNK_DURATION_MS=250 \
RANGE_RESPONSE_CHUNKS=2 \
RANGE_RETRY_ATTEMPTS=0 \
CHROME_HOLD_SECONDS=12 \
CHROME_TIMEOUT_SECONDS=30 \
TIMEOUT=40s \
repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh
```

Slow range run:

```bash
WORKLOAD=range \
RUN_ID=chrome-desktop-noniphone-range-slow-drop3000-retry0-20260630 \
REBIND_AFTER=1s \
DROP_A_SERVER_AFTER_SWITCH=1 \
DROP_A_SERVER_AFTER_SWITCH_FOR=3000ms \
RANGE_TOTAL_BYTES=1048576 \
RANGE_CHUNK_BYTES=131072 \
RANGE_CHUNK_DURATION_MS=1000 \
RANGE_RESPONSE_CHUNKS=4 \
RANGE_RETRY_ATTEMPTS=0 \
CHROME_HOLD_SECONDS=18 \
CHROME_TIMEOUT_SECONDS=40 \
TIMEOUT=50s \
repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh
```

## Grouped Result

| profile | drop window | retry | PASS/runs | range complete | retry used | median elapsed ms | median error ms | Chrome sessions | classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| range-noniphone-local-refresh | 3000ms | 0 | 2/2 | 2/2 | 0/2 | 3608 | - | 1-1 | nat_rebinding_possible_session_continuity=2 |

## Run Detail

| profile | trial | drop | retry | status | classification | complete | bytes | retries used | elapsed ms | error ms | Chrome sessions | qlog C/R | dropped A/B |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| range-noniphone-local-refresh | chrome-desktop-noniphone-range-drop3000-retry0-20260630 | 3000ms | 0 | PASS | nat_rebinding_possible_session_continuity | true | 1048576/1048576 | 0 | 1095 | - | 1 | 1/1 | 0/0 |
| range-noniphone-local-refresh | chrome-desktop-noniphone-range-slow-drop3000-retry0-20260630 | 3000ms | 0 | PASS | nat_rebinding_possible_session_continuity | true | 1048576/1048576 | 0 | 6122 | - | 1 | 1/1 | 0/0 |

## Proxy Path Observation

| trial | elapsed ms | Chrome sessions | remote tuples | qlog C/R | server packets A/B | dropped A/B |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `chrome-desktop-noniphone-range-drop3000-retry0-20260630` | 1095 | 1 | 2 | 1/1 | 701/114 | 0/0 |
| `chrome-desktop-noniphone-range-slow-drop3000-retry0-20260630` | 6122 | 1 | 2 | 1/1 | 170/683 | 0/0 |

The slow row is the more useful one for path interpretation: although A-side server packet drop was enabled for 3000ms after the proxy switch, the observed server traffic shifted mostly to upstream B, so no A-side server packets were dropped. This supports local path transition evidence, not outage-tolerance proof.

## Interpretation Boundary

A completed range row is resumable application-level download continuity. It is not single-session QUIC Connection Migration unless the same row also shows one target QUIC session, changed path/tuple evidence, qlog path validation, and no replacement-session behavior.

The expected paper use is to compare recovery semantics: a full-stream retry restarts a long response, while byte-range retry can resume from the failed chunk. Both still need session attribution before being called QUIC CM.

Paper-safe statement:

> In two fresh local Chrome forced-H3 byte-range controls, the 1MiB task completed without application retry across local UDP rebinding with one target QUIC session, two server-observed remote tuples, and qlog path validation. These runs strengthen browser artifact interpretation but do not prove public Wi-Fi/LTE handover continuity.

## Data

- CSV: `data/chrome-desktop-noniphone-range-local-refresh-20260630.csv`
