# Chapter 11 Scanner Trigger Map

작성일: `2026-06-30`

이 표는 Chapter 11 streaming/media workload에서 어떤 scanner/classifier가 어떤 evidence를 읽는지 line-level로 정리한다.

## 1. Media Workload Implementation

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [h3server/main.go#L446-L483](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L446-L483) | `/browser-media-segments` query params | media segment HTML workload | segment fetch task |
| [h3server/main.go#L484-L532](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L484-L532) | `/browser-buffered-media` query params | buffered playback HTML workload | buffer/playback model |
| [h3server/main.go#L533-L555](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L533-L555) | `/media-segment` query params | segment binary response | actual media-like transfer |
| [h3server/main.go#L911-L929](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L911-L929) | segment fetch loop, retry budget | `mediaCompletedCount`, `mediaRetriesUsed`, `mediaComplete`, `mediaError` | segment task outcome |
| [h3server/main.go#L931-L955](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L931-L955) | buffered fetch/playback loops | startup, rebuffer, played count, complete/error datasets | QoE outcome |

## 2. Media Segment Summarizer

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [summarize_chrome_rebinding_media_matrix.py#L18-L45](../../../tools/summarize_chrome_rebinding_media_matrix.py#L18-L45) | CSV fields | segment/retry/session/qlog output schema | reproducible table shape |
| [summarize_chrome_rebinding_media_matrix.py#L85-L109](../../../tools/summarize_chrome_rebinding_media_matrix.py#L85-L109) | server request labels | duplicate segment count and notes | duplicate segment evidence |
| [summarize_chrome_rebinding_media_matrix.py#L112-L154](../../../tools/summarize_chrome_rebinding_media_matrix.py#L112-L154) | summary JSON, server JSON, DOM dump, qlog, proxy | per-run media row | artifact-to-table chain |
| [summarize_chrome_rebinding_media_matrix.py#L188-L216](../../../tools/summarize_chrome_rebinding_media_matrix.py#L188-L216) | grouped rows | PASS/runs, media complete, median elapsed, session range | aggregate result |
| [summarize_chrome_rebinding_media_matrix.py#L219-L293](../../../tools/summarize_chrome_rebinding_media_matrix.py#L219-L293) | rows and CSV output | report markdown with interpretation boundary | overclaim guard |
| [test_summarize_chrome_rebinding_media_matrix.py#L18-L68](../../../tools/test_summarize_chrome_rebinding_media_matrix.py#L18-L68) | synthetic media artifact | field extraction test | parser behavior locked |
| [test_summarize_chrome_rebinding_media_matrix.py#L71-L112](../../../tools/test_summarize_chrome_rebinding_media_matrix.py#L71-L112) | synthetic grouped result | boundary wording test | CM overclaim guard locked |

## 3. Buffered Media Summarizer

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [summarize_chrome_rebinding_buffered_media_matrix.py#L18-L45](../../../tools/summarize_chrome_rebinding_buffered_media_matrix.py#L18-L45) | CSV fields | startup/rebuffer/session/qlog output schema | QoE table shape |
| [summarize_chrome_rebinding_buffered_media_matrix.py#L80-L95](../../../tools/summarize_chrome_rebinding_buffered_media_matrix.py#L80-L95) | complete, rebuffer, startup, sessions | note text | QoE interpretation |
| [summarize_chrome_rebinding_buffered_media_matrix.py#L98-L137](../../../tools/summarize_chrome_rebinding_buffered_media_matrix.py#L98-L137) | DOM dump and summary JSON | per-run buffered media row | artifact-to-table chain |
| [summarize_chrome_rebinding_buffered_media_matrix.py#L166-L207](../../../tools/summarize_chrome_rebinding_buffered_media_matrix.py#L166-L207) | grouped rows | startup median, elapsed median, rebuffer range, session range | aggregate QoE result |
| [test_summarize_chrome_rebinding_buffered_media_matrix.py#L18-L55](../../../tools/test_summarize_chrome_rebinding_buffered_media_matrix.py#L18-L55) | synthetic buffered artifact | field extraction test | parser behavior locked |
| [test_summarize_chrome_rebinding_buffered_media_matrix.py#L58-L99](../../../tools/test_summarize_chrome_rebinding_buffered_media_matrix.py#L58-L99) | synthetic grouped result | playback/QoE boundary wording test | completion-only overclaim guard locked |

## 4. Classifier Guards

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [classify_controlled_public_h3_baseline.py#L119-L122](../../../tools/classify_controlled_public_h3_baseline.py#L119-L122) | keys starting with `media`, `mediaComplete` | workload `media`, complete/success booleans | media application success criterion |
| [classify_controlled_public_h3_network_change.py#L24-L28](../../../tools/classify_controlled_public_h3_network_change.py#L24-L28) | `browser-media-segments`, `browser-buffered-media`, `media-segment` target workloads | target H3 tuple filter | future public media rows |
| [classify_chrome_h3_artifacts.py#L193-L205](../../../tools/classify_chrome_h3_artifacts.py#L193-L205) | local DOM dump | media complete check | local control success criterion |
| [classify_chrome_h3_artifacts.py#L226-L236](../../../tools/classify_chrome_h3_artifacts.py#L226-L236) | workload prefix | media timing field extraction | latency/error timing |

## 5. False-Positive Guards

| guard | 코드 근거 | 방지하는 오해 |
| --- | --- | --- |
| Media DOM completion is application-only | [classify_controlled_public_h3_baseline.py#L119-L122](../../../tools/classify_controlled_public_h3_baseline.py#L119-L122) | `mediaComplete`를 transport CM으로 해석하는 것 |
| multiple-session note | [summarize_chrome_rebinding_media_matrix.py#L97-L109](../../../tools/summarize_chrome_rebinding_media_matrix.py#L97-L109) | media complete row를 single-session CM으로 과장하는 것 |
| buffered QoE note | [summarize_chrome_rebinding_buffered_media_matrix.py#L80-L95](../../../tools/summarize_chrome_rebinding_buffered_media_matrix.py#L80-L95) | playback complete만 보고 user impact가 없다고 말하는 것 |
| local control boundary | [summarize_chrome_rebinding_media_matrix.py#L283-L287](../../../tools/summarize_chrome_rebinding_media_matrix.py#L283-L287) | local NAT rebinding을 public handover로 혼동하는 것 |
