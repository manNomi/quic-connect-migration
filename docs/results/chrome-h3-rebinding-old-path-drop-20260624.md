# Chrome H3 Local Rebinding Old-Path Drop Summary

Generated: `2026-06-24`

This summary records local Chrome forced-H3 UDP rebinding runs where the proxy was configured to drop server-to-client packets arriving on upstream A after client traffic switched to upstream B. It is a local NAT-rebinding control, not a public Wi-Fi/LTE handover result.

## Purpose

The earlier rebinding proxy tests changed the server-facing client UDP socket from A to B, but old upstream A remained deliverable. This run adds an old-path-unavailable variant:

```bash
DROP_A_SERVER_AFTER_SWITCH=1 ./scripts/run-chrome-h3-rebinding-proxy.sh
```

This does not create a real client route/interface change. It only checks whether the local proxy can remove old-path server delivery after the rebinding trigger.

## Results

| workload | status | classification | remote tuples | Chrome QUIC sessions | qlog PATH C/R | NetLog target PATH C/R | client packets A/B | server packets A/B | dropped A server packets | upload bytes |
| --- | --- | --- | ---: | ---: | --- | --- | --- | --- | ---: | ---: |
| downlink | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 1 | 1/1 | 1/1 | 17/27 | 26/35 | 0 | - |
| upload | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | 1 | 2 | 1/1 | 1/1 | 54/198 | 31/49 | 21 | 262144 |

## Interpretation

- Both downlink and upload completed with proxy packet rebinding, qlog path validation, and Chrome target NetLog path-validation frames.
- In the downlink run, no A-side server packet arrived after the switch, so the drop option did not need to discard old-path packets.
- In the upload run, the proxy dropped 21 A-side server packets after the switch and the upload still completed.
- The upload run also reported two Chrome target QUIC sessions. Therefore task completion under old-path drop is not sufficient browser session-continuity evidence.

## Claim Boundary

Safe wording:

> In a local forced-H3 old-path-drop proxy control, Chrome HTTP/3 downlink and upload workloads completed while the proxy forwarded client packets through upstream B and qlog/NetLog recorded path-validation frames; the upload run dropped 21 old-path A-side server packets after switch.

Unsafe wording:

> Chrome completed real Wi-Fi/LTE handover.

The result remains a local proxy control and does not satisfy the final controlled-public active handover protocol.
