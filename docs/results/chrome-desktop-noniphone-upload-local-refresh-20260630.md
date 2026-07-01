# Chrome H3 Local UDP Rebinding Upload Summary

Generated: `2026-06-30`

This summary aggregates local Chrome forced-H3 streaming upload repetitions through a UDP rebinding proxy. It is a local NAT-rebinding control, not a public Wi-Fi/LTE handover result.

## Purpose

This fresh row fills the non-iPhone upload gap after the media and byte-range local refreshes. The workload is a client-sending upload stream, so the main question is whether Chrome, qlog, NetLog, and proxy artifacts still expose packet-level rebinding when request-level server logs show only one remote tuple.

## Command

```bash
WORKLOAD=upload \
RUN_ID=chrome-desktop-noniphone-upload-drop3000-retry0-20260630 \
REBIND_AFTER=1s \
DROP_A_SERVER_AFTER_SWITCH=1 \
DROP_A_SERVER_AFTER_SWITCH_FOR=3000ms \
UPLOAD_DURATION_MS=8000 \
UPLOAD_CHUNKS=8 \
UPLOAD_BYTES=131072 \
UPLOAD_RETRY_ATTEMPTS=0 \
CHROME_HOLD_SECONDS=16 \
CHROME_TIMEOUT_SECONDS=35 \
TIMEOUT=45s \
repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh
```

## Aggregate

| field | value |
| --- | --- |
| runs | `1` |
| status counts | `{'PASS': 1}` |
| classification counts | `{'nat_rebinding_path_validation_without_observed_tuple_change': 1}` |
| upload request counts | `{'1': 1}` |
| packet rebinding observed counts | `{'true': 1}` |
| NetLog target path validation counts | `{'true': 1}` |

## Runs

| run | status | classification | remote tuples | Chrome QUIC sessions | upload sink requests | upload bytes | qlog PATH_CHALLENGE/PATH_RESPONSE | NetLog target PATH C/R | proxy client packets A/B | packet rebind |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- |
| chrome-desktop-noniphone-upload-drop3000-retry0-20260630 | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1 | 131072 | 1/1 | 1/1 | 29/110 | true |

## Interpretation Boundary

Use these rows as a client-sending local control. Each run records client packets forwarded through both proxy upstream sockets, while the request-level server tuple remains stable. Chrome NetLog target-session path frames align with server qlog path validation, strengthening the evidence boundary: request logs alone may miss packet-level rebinding, so qlog, proxy packet logs, and browser NetLog remain required. These rows do not complete the final controlled-public browser handover protocol.

## Paper Use

Use this result as a fresh reproducibility check for the local upload control: Chrome completed the upload without application retry, the target QUIC session count stayed at one, and qlog/NetLog path challenge-response evidence was present. Do not use it as public Wi-Fi/LTE handover evidence because the client route, interface, and public address did not change.
