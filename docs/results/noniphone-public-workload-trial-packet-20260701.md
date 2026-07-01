# Non-iPhone Public Workload Trial Packet

Generated: `2026-06-30 UTC / 2026-07-01 KST`

This public-safe packet converts the local non-iPhone workload/QoE synthesis into the next controlled-public Chrome trial order. It intentionally excludes iPhone-based triggers and does not include hostnames, IP addresses, credentials, qlogs, NetLogs, pcaps, or keylogs.

## Summary

| field | value |
| --- | --- |
| synthesis CSV | `data/noniphone-workload-qoe-continuity-synthesis-20260701.csv` |
| trial templates | `9` |
| active trial repetitions | `18` |
| claim boundary | This packet is a run plan. It is not evidence that any public workload or browser Connection Migration trial has succeeded. |

## Preconditions

1. PUBLIC_ORIGIN_BASE points to a WebPKI HTTPS origin that advertises Alt-Svc h3.
2. PUBLIC_ORIGIN_BOOTSTRAP_URL reaches the same origin and passes controlled-public H3 baseline.
3. CONTROLLED_PUBLIC_BASELINE_SUMMARY points to a prior PASS baseline summary.
4. NETWORK_CHANGE_CMD performs a non-iPhone active path change on the desktop client.
5. Raw qlog, NetLog, pcap, keylog, private hosts, and credentials remain outside committed files.

## Strong CM Acceptance

1. application task completion is true for the workload-specific DOM metric
2. client active path changed according to before/after route snapshots
3. server target H3 remote tuple count changed
4. server qlog records PATH_CHALLENGE and PATH_RESPONSE
5. Chrome target QUIC session count is one

## Trial Order

| rank | trial id pattern | phase | workload | runs | expected requests | ready expression | local synthesis | acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | controlled-public-chrome-h3-baseline-001 | baseline | public H3 bootstrap | 1 | 2 | - | - | PASS baseline with application H3 confirmed by server log/qlog and Chrome NetLog. |
| 1 | controlled-public-chrome-range-nochange-001 | no-change-baseline | large byte-range download | 1 | 9 | - | 2/2; sessions 1-1; single 2; multi 0; path-validation 2; elapsed median 3608ms | PASS no-change workload baseline; no active path-change claim. |
| 2 | controlled-public-chrome-range-network-change-00{1..3} | active-network-change | large byte-range download | 3 | 9 | Number(document.body.dataset.rangeCompletedChunks \|\| "0") >= 1 | 2/2; sessions 1-1; single 2; multi 0; path-validation 2; elapsed median 3608ms | Strong CM row requires application completion, client active path change, target H3 tuple change, server qlog PATH_CHALLENGE/PATH_RESPONSE, and one Chrome target QUIC session. |
| 3 | controlled-public-chrome-upload-nochange-001 | no-change-baseline | large upload | 1 | 2 | - | 1/1; sessions 1-1; single 1; multi 0; path-validation 1; upload bytes 131072-131072; request tuples 1-1 | PASS no-change workload baseline; no active path-change claim. |
| 4 | controlled-public-chrome-upload-network-change-00{1..3} | active-network-change | large upload | 3 | 2 | Number(document.body.dataset.uploadBytes \|\| "0") > 0 | 1/1; sessions 1-1; single 1; multi 0; path-validation 1; upload bytes 131072-131072; request tuples 1-1 | Strong CM row requires application completion, client active path change, target H3 tuple change, server qlog PATH_CHALLENGE/PATH_RESPONSE, and one Chrome target QUIC session. |
| 5 | controlled-public-chrome-buffered-low-network-change-00{1..3} | active-network-change | buffered video playback | 3 | 9 | Number(document.body.dataset.bufferedMediaFetchedCount \|\| "0") >= 1 | 14/14; sessions 2-3; single 0; multi 14; path-validation 13; rebuffer 1-14; startup median 89ms | Strong CM row requires application completion, client active path change, target H3 tuple change, server qlog PATH_CHALLENGE/PATH_RESPONSE, and one Chrome target QUIC session. |
| 6 | controlled-public-chrome-buffered-high-network-change-00{1..3} | active-network-change | buffered video playback | 3 | 9 | Number(document.body.dataset.bufferedMediaFetchedCount \|\| "0") >= 1 | 14/14; sessions 2-3; single 0; multi 14; path-validation 13; rebuffer 1-14; startup median 89ms | Strong CM row requires application completion, client active path change, target H3 tuple change, server qlog PATH_CHALLENGE/PATH_RESPONSE, and one Chrome target QUIC session. |
| 7 | controlled-public-chrome-musiclike-retry0-network-change-00{1..3} | active-network-change | music-like segment | 3 | 9 | Number(document.body.dataset.mediaCompletedCount \|\| "0") >= 1 | 4/8; sessions 2-3; single 0; multi 8; path-validation 0; elapsed median 14084ms | Strong CM row requires application completion, client active path change, target H3 tuple change, server qlog PATH_CHALLENGE/PATH_RESPONSE, and one Chrome target QUIC session. |
| 8 | controlled-public-chrome-musiclike-retry1-network-change-00{1..3} | active-network-change | music-like segment | 3 | 9 | Number(document.body.dataset.mediaCompletedCount \|\| "0") >= 1 | 4/8; sessions 2-3; single 0; multi 8; path-validation 0; elapsed median 14084ms | Strong CM row requires application completion, client active path change, target H3 tuple change, server qlog PATH_CHALLENGE/PATH_RESPONSE, and one Chrome target QUIC session. |

## Command Templates

Set `PUBLIC_ORIGIN_BASE`, `PUBLIC_ORIGIN_BOOTSTRAP_URL`, `CONTROLLED_PUBLIC_BASELINE_SUMMARY`, and `NETWORK_CHANGE_CMD` in an ignored shell or terminal session before using the active templates.

### controlled-public-chrome-h3-baseline-001

Why now: Every public workload trial depends on a fresh H3/Alt-Svc baseline.

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

### controlled-public-chrome-range-nochange-001

Why now: Local range rows have the cleanest single-session path-validation evidence among browser workloads.

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-range-nochange-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-range-nochange-001 \
PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_BOOTSTRAP_URL:-$PUBLIC_ORIGIN_BASE/browser-slow?duration_ms=3000&chunks=3&label=public-bootstrap}" \
SECOND_URL="${PUBLIC_ORIGIN_BASE:?set PUBLIC_ORIGIN_BASE like https://h3.example.com}/browser-range-download?bytes=1048576&range_bytes=131072&range_duration_ms=250&range_chunks=2&retry_attempts=0&retry_delay_ms=500&label=public-range-nochange" \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=9 \
REQUIRE_H3_ALT_SVC=1 \
RUN_CONTROLLED_PUBLIC_CLASSIFIER=1 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=25 \
CHROME_TIMEOUT_SECONDS=45 \
./scripts/run-controlled-public-h3-browser-baseline.sh
```

### controlled-public-chrome-range-network-change-00{1..3}

Why now: Range is the first active public workload because its completion and byte accounting are crisp.

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-range-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-range-network-change-001 \
PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_BASE:?set PUBLIC_ORIGIN_BASE like https://h3.example.com}/browser-range-download?bytes=1048576&range_bytes=131072&range_duration_ms=250&range_chunks=2&retry_attempts=0&retry_delay_ms=500&label=public-range-active" \
PUBLIC_ORIGIN_BOOTSTRAP_URL="${PUBLIC_ORIGIN_BOOTSTRAP_URL:-$PUBLIC_ORIGIN_BASE/browser-slow?duration_ms=3000&chunks=3&label=public-bootstrap}" \
CONTROLLED_PUBLIC_BASELINE_SUMMARY="${CONTROLLED_PUBLIC_BASELINE_SUMMARY:?set a prior PASS baseline summary}" \
NETWORK_CHANGE_CMD="${NETWORK_CHANGE_CMD:?set a non-iPhone active path-change command}" \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=9 \
REQUIRE_H3_ALT_SVC=1 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=45 \
CHROME_TIMEOUT_SECONDS=70 \
NETWORK_CHANGE_READY_EXPR='Number(document.body.dataset.rangeCompletedChunks || "0") >= 1' \
./scripts/run-controlled-public-h3-network-change.sh
```

### controlled-public-chrome-upload-nochange-001

Why now: Upload is user-visible task continuity and request tuple logs can miss packet-level rebinding.

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-upload-nochange-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-upload-nochange-001 \
PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_BOOTSTRAP_URL:-$PUBLIC_ORIGIN_BASE/browser-slow?duration_ms=3000&chunks=3&label=public-bootstrap}" \
SECOND_URL="${PUBLIC_ORIGIN_BASE:?set PUBLIC_ORIGIN_BASE like https://h3.example.com}/browser-upload?bytes=131072&duration_ms=3000&chunks=6&retry_attempts=0&retry_delay_ms=500&label=public-upload-nochange" \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=2 \
REQUIRE_H3_ALT_SVC=1 \
RUN_CONTROLLED_PUBLIC_CLASSIFIER=1 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=25 \
CHROME_TIMEOUT_SECONDS=45 \
./scripts/run-controlled-public-h3-browser-baseline.sh
```

### controlled-public-chrome-upload-network-change-00{1..3}

Why now: Upload is the second active workload because it tests client-sending continuity.

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-upload-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-upload-network-change-001 \
PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_BASE:?set PUBLIC_ORIGIN_BASE like https://h3.example.com}/browser-upload?bytes=131072&duration_ms=3000&chunks=6&retry_attempts=0&retry_delay_ms=500&label=public-upload-active" \
PUBLIC_ORIGIN_BOOTSTRAP_URL="${PUBLIC_ORIGIN_BOOTSTRAP_URL:-$PUBLIC_ORIGIN_BASE/browser-slow?duration_ms=3000&chunks=3&label=public-bootstrap}" \
CONTROLLED_PUBLIC_BASELINE_SUMMARY="${CONTROLLED_PUBLIC_BASELINE_SUMMARY:?set a prior PASS baseline summary}" \
NETWORK_CHANGE_CMD="${NETWORK_CHANGE_CMD:?set a non-iPhone active path-change command}" \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=2 \
REQUIRE_H3_ALT_SVC=1 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=45 \
CHROME_TIMEOUT_SECONDS=70 \
NETWORK_CHANGE_READY_EXPR='Number(document.body.dataset.uploadBytes || "0") > 0' \
./scripts/run-controlled-public-h3-network-change.sh
```

### controlled-public-chrome-buffered-low-network-change-00{1..3}

Why now: Low-buffer playback exposes visible QoE cost instead of hiding disruption behind startup delay.

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-buffered-low-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-buffered-low-network-change-001 \
PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_BASE:?set PUBLIC_ORIGIN_BASE like https://h3.example.com}/browser-buffered-media?count=8&bytes=8192&segment_duration_ms=50&segment_chunks=1&playback_interval_ms=1000&startup_buffer_segments=1&max_buffer_segments=1&retry_attempts=0&retry_delay_ms=500&label=public-buffered-low-active" \
PUBLIC_ORIGIN_BOOTSTRAP_URL="${PUBLIC_ORIGIN_BOOTSTRAP_URL:-$PUBLIC_ORIGIN_BASE/browser-slow?duration_ms=3000&chunks=3&label=public-bootstrap}" \
CONTROLLED_PUBLIC_BASELINE_SUMMARY="${CONTROLLED_PUBLIC_BASELINE_SUMMARY:?set a prior PASS baseline summary}" \
NETWORK_CHANGE_CMD="${NETWORK_CHANGE_CMD:?set a non-iPhone active path-change command}" \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=9 \
REQUIRE_H3_ALT_SVC=1 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=45 \
CHROME_TIMEOUT_SECONDS=70 \
NETWORK_CHANGE_READY_EXPR='Number(document.body.dataset.bufferedMediaFetchedCount || "0") >= 1' \
./scripts/run-controlled-public-h3-network-change.sh
```

### controlled-public-chrome-buffered-high-network-change-00{1..3}

Why now: High-buffer playback checks whether buffering hides disruption while changing startup/rebuffer tradeoffs.

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-buffered-high-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-buffered-high-network-change-001 \
PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_BASE:?set PUBLIC_ORIGIN_BASE like https://h3.example.com}/browser-buffered-media?count=8&bytes=8192&segment_duration_ms=50&segment_chunks=1&playback_interval_ms=1000&startup_buffer_segments=4&max_buffer_segments=6&retry_attempts=0&retry_delay_ms=500&label=public-buffered-high-active" \
PUBLIC_ORIGIN_BOOTSTRAP_URL="${PUBLIC_ORIGIN_BOOTSTRAP_URL:-$PUBLIC_ORIGIN_BASE/browser-slow?duration_ms=3000&chunks=3&label=public-bootstrap}" \
CONTROLLED_PUBLIC_BASELINE_SUMMARY="${CONTROLLED_PUBLIC_BASELINE_SUMMARY:?set a prior PASS baseline summary}" \
NETWORK_CHANGE_CMD="${NETWORK_CHANGE_CMD:?set a non-iPhone active path-change command}" \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=9 \
REQUIRE_H3_ALT_SVC=1 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=45 \
CHROME_TIMEOUT_SECONDS=70 \
NETWORK_CHANGE_READY_EXPR='Number(document.body.dataset.bufferedMediaFetchedCount || "0") >= 1' \
./scripts/run-controlled-public-h3-network-change.sh
```

### controlled-public-chrome-musiclike-retry0-network-change-00{1..3}

Why now: The local corpus shows music-like retry0 is a useful failure/control boundary.

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-musiclike-retry0-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-musiclike-retry0-network-change-001 \
PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_BASE:?set PUBLIC_ORIGIN_BASE like https://h3.example.com}/browser-media-segments?count=8&interval_ms=1000&bytes=8192&segment_duration_ms=50&segment_chunks=1&retry_attempts=0&retry_delay_ms=500&label=public-musiclike-retry0-active" \
PUBLIC_ORIGIN_BOOTSTRAP_URL="${PUBLIC_ORIGIN_BOOTSTRAP_URL:-$PUBLIC_ORIGIN_BASE/browser-slow?duration_ms=3000&chunks=3&label=public-bootstrap}" \
CONTROLLED_PUBLIC_BASELINE_SUMMARY="${CONTROLLED_PUBLIC_BASELINE_SUMMARY:?set a prior PASS baseline summary}" \
NETWORK_CHANGE_CMD="${NETWORK_CHANGE_CMD:?set a non-iPhone active path-change command}" \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=9 \
REQUIRE_H3_ALT_SVC=1 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=45 \
CHROME_TIMEOUT_SECONDS=70 \
NETWORK_CHANGE_READY_EXPR='Number(document.body.dataset.mediaCompletedCount || "0") >= 1' \
./scripts/run-controlled-public-h3-network-change.sh
```

### controlled-public-chrome-musiclike-retry1-network-change-00{1..3}

Why now: Retry1 should follow retry0 to separate application recovery from transport continuity.

```bash
cd repro/quic-go-min-repro
RUN_ID=controlled-public-chrome-musiclike-retry1-network-change-001 \
ARTIFACT_DIR=artifacts/controlled-public-chrome-musiclike-retry1-network-change-001 \
PUBLIC_ORIGIN_URL="${PUBLIC_ORIGIN_BASE:?set PUBLIC_ORIGIN_BASE like https://h3.example.com}/browser-media-segments?count=8&interval_ms=1000&bytes=8192&segment_duration_ms=50&segment_chunks=1&retry_attempts=1&retry_delay_ms=500&label=public-musiclike-retry1-active" \
PUBLIC_ORIGIN_BOOTSTRAP_URL="${PUBLIC_ORIGIN_BOOTSTRAP_URL:-$PUBLIC_ORIGIN_BASE/browser-slow?duration_ms=3000&chunks=3&label=public-bootstrap}" \
CONTROLLED_PUBLIC_BASELINE_SUMMARY="${CONTROLLED_PUBLIC_BASELINE_SUMMARY:?set a prior PASS baseline summary}" \
NETWORK_CHANGE_CMD="${NETWORK_CHANGE_CMD:?set a non-iPhone active path-change command}" \
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=9 \
REQUIRE_H3_ALT_SVC=1 \
CHROME_RUNNER=cdp \
CHROME_HOLD_SECONDS=45 \
CHROME_TIMEOUT_SECONDS=70 \
NETWORK_CHANGE_READY_EXPR='Number(document.body.dataset.mediaCompletedCount || "0") >= 1' \
./scripts/run-controlled-public-h3-network-change.sh
```

## Interpretation Rules

- `controlled-public-chrome-h3-baseline-001` success: The public origin is usable for controlled Chrome HTTP/3 workload trials.
- `controlled-public-chrome-h3-baseline-001` non-strong-CM: A failed baseline is infrastructure evidence, not Connection Migration evidence.
- `controlled-public-chrome-range-nochange-001` success: The public origin can serve the resumable-download workload before active path-change trials.
- `controlled-public-chrome-range-nochange-001` non-strong-CM: No-change rows are controls and must not be used as migration success evidence.
- `controlled-public-chrome-range-network-change-00{1..3}` success: A strong row can support public browser single-session CM only if the full evidence chain passes.
- `controlled-public-chrome-range-network-change-00{1..3}` non-strong-CM: Multiple sessions or missing qlog path validation should be reported as recovery/reconnect or negative-control evidence.
- `controlled-public-chrome-upload-nochange-001` success: The public origin can receive upload workloads before active path-change trials.
- `controlled-public-chrome-upload-nochange-001` non-strong-CM: No-change upload rows are public workload baselines, not CM rows.
- `controlled-public-chrome-upload-network-change-00{1..3}` success: A strong row can support public browser upload continuity under single-session CM.
- `controlled-public-chrome-upload-network-change-00{1..3}` non-strong-CM: If upload completes with replacement sessions, report task recovery separately from CM.
- `controlled-public-chrome-buffered-low-network-change-00{1..3}` success: A complete row is QoE continuity evidence; it is CM evidence only if the single-session chain also passes.
- `controlled-public-chrome-buffered-low-network-change-00{1..3}` non-strong-CM: Playback completion with multiple sessions is replacement-session or application-level continuity evidence.
- `controlled-public-chrome-buffered-high-network-change-00{1..3}` success: Use as QoE comparison against low-buffer playback, not as automatic CM success.
- `controlled-public-chrome-buffered-high-network-change-00{1..3}` non-strong-CM: If sessions churn, report buffer-masked recovery rather than transport continuity.
- `controlled-public-chrome-musiclike-retry0-network-change-00{1..3}` success: Unexpected retry0 success should be examined for path timing, buffering, and session count.
- `controlled-public-chrome-musiclike-retry0-network-change-00{1..3}` non-strong-CM: Failure without retry is still useful workload-boundary evidence.
- `controlled-public-chrome-musiclike-retry1-network-change-00{1..3}` success: Completion with retry should be framed as application recovery unless the single-session chain passes.
- `controlled-public-chrome-musiclike-retry1-network-change-00{1..3}` non-strong-CM: Multiple sessions or retries must not be described as pure QUIC CM success.
