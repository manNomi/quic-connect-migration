# Chapter 8. Full-Response Downlink Public Handover

작성일: `2026-06-30`

## 1. 이 챕터의 목적

Chapter 7에서 controlled public HTTP/3 baseline을 확보했기 때문에, 이제 실제 client path change가 있는 browser workload를 검수할 수 있다. Chapter 8은 macOS Chrome에서 Wi-Fi를 끄고 iPhone USB path로 넘어가는 동안, 하나의 긴 HTTP/3 downlink response가 웹 작업으로 끝까지 완료되는지를 본다.

핵심 질문은 다음이다.

> browser-level QUIC Connection Migration evidence가 관찰되지 않는 상황에서, full-response downlink workload는 Wi-Fi to iPhone USB path change를 견디는가?

이 챕터는 byte-range download와 비교하기 위한 기준 workload다. byte-range는 실패한 chunk를 retry할 수 있지만, full-response downlink는 하나의 fetch/read stream이 끊기면 작업 전체가 실패하기 쉽다.

## 2. 실험 환경

| 항목 | 값 |
| --- | --- |
| client | `macOS Chrome` |
| secondary path | `iPhone USB` |
| origin | controlled public EC2 origin |
| server | quic-go HTTP/3 harness |
| TLS | WebPKI certificate on temporary `sslip.io` origin |
| baseline trial | `controlled-public-chrome-downlink-full-nochange-fresh-20260629-001` |
| active trials | `controlled-public-chrome-downlink-full-network-change-page-ready-fresh-20260629-001` through `002` |
| active trigger | first observed `downlinkBytes` |
| network change action | Wi-Fi disabled, wrapper restored Wi-Fi after run |

Workload:

| 항목 | 값 |
| --- | --- |
| page | `GET /browser-downlink` |
| stream | `GET /downlink-stream` |
| stream duration | `15000 ms` |
| chunks | `15` |
| retry budget | `0` |

## 3. 실험 결과

| condition | runs | status | classification | client path change | target H3 tuples | qlog path validation | application result |
| --- | ---: | --- | --- | --- | ---: | --- | --- |
| no-change baseline | 1 | `PASS` | `controlled_public_application_h3_confirmed` | `n/a` | `n/a` | `false` | `1/1` completed |
| Wi-Fi to iPhone USB | 2 | `PASS_NEGATIVE_CONTROL` | `application_task_failed_without_quic_path_validation` | `client_active_path_changed` in both runs | `1` in both runs | `false` in both runs | `0/2` completed |

Active trial detail:

| trial | client path | target H3 tuples | application success | bytes before error | terminal error | classification |
| --- | --- | ---: | --- | ---: | --- | --- |
| `001` | `client_active_path_changed` | 1 | `false` | 17528 | `downlinkError` | `application_task_failed_without_quic_path_validation` |
| `002` | `client_active_path_changed` | 1 | `false` | 17528 | `downlinkError` | `application_task_failed_without_quic_path_validation` |

해석은 명확하다.

1. client path change는 실제로 관찰됐다.
2. application workload는 두 active run 모두 실패했다.
3. server qlog에서 QUIC path validation evidence는 관찰되지 않았다.
4. 따라서 이 결과는 browser QUIC Connection Migration 성공이 아니다.

## 4. 왜 `PASS_NEGATIVE_CONTROL`인가

여기서 `PASS_NEGATIVE_CONTROL`은 "실험이 성공했다"는 뜻이 아니다. artifact bundle이 남았고, classifier가 의도한 방식으로 실패를 분류했다는 뜻이다.

분류 기준은 다음과 같다.

| evidence | observed | 의미 |
| --- | --- | --- |
| network-change command | executed | active handover trial 조건 충족 |
| client route/interface/public-path evidence | changed | Wi-Fi to iPhone USB path change 관찰 |
| application success | false | user-visible task failed |
| qlog path validation | false | transport-level CM evidence 없음 |
| target H3 remote tuples | 1 | target workload에서 tuple migration evidence 없음 |

따라서 논문에는 다음처럼 써야 한다.

> In Chrome full-response downlink trials, active client path change was observed, but the application task failed and server qlog did not show path validation. These rows are negative controls rather than successful browser QUIC Connection Migration.

## 5. Byte-Range Download와의 비교

같은 controlled public origin과 같은 iPhone USB handover mechanism에서 byte-range download 결과는 달랐다.

| workload | retry budget | active runs | completed active runs | typical signal | CM evidence |
| --- | ---: | ---: | ---: | --- | --- |
| full-response downlink | 0 | 2 | 0 | `downlinkError` after 17528 bytes | no qlog path validation |
| byte-range download | 0 | 2 | 0 | `rangeError` after 262144 bytes | no qlog path validation |
| byte-range download | 2 | 3 | 2 | `rangeComplete=true` after one retry in successful runs | no qlog path validation |

이 비교가 현재 연구에서 가장 중요한 application-layer 근거 중 하나다.

> transport-level CM evidence가 없어도, workload semantics와 retry budget에 따라 사용자 관점의 작업 완료 여부가 달라질 수 있다.

즉, "HTTP/3 Connection Migration이 된다/안 된다"라는 이분법보다 다음 세 층을 분리해야 한다.

| 층 | 질문 | Chapter 8 답 |
| --- | --- | --- |
| transport migration | 같은 QUIC connection이 path validation과 함께 migration했는가? | evidence 없음 |
| browser behavior | path change 중 Chrome fetch/read stream이 유지됐는가? | full-response downlink는 실패 |
| application continuity | 사용자가 수행하던 다운로드 작업이 완료됐는가? | retry 없는 full-response는 실패 |

## 6. 논문에서 쓸 수 있는 주장

안전한 주장:

> Full-response HTTP/3 downlink over Chrome did not preserve the application task across the observed Wi-Fi to iPhone USB path change in the current controlled-public trials.

더 강한 연구 framing:

> The results motivate evaluating web task continuity by workload semantics, because byte-range retry changed user-visible completion while full-response streaming failed under the same broad handover setup.

피해야 할 주장:

| 피해야 할 주장 | 이유 |
| --- | --- |
| Chrome CM이 실패했다고 일반화 | 현재는 특정 macOS Chrome, 특정 path-change method, 특정 workload의 관찰 결과다. |
| QUIC CM 자체가 쓸모없다 | 구현체 positive control과 local rebinding control에서는 path validation이 관찰됐다. |
| byte-range 성공은 CM 성공이다 | retry=2 성공 run에도 qlog path validation이 없었다. |
| application continuity가 보장된다 | full-response downlink active run은 0/2 completed다. |

## 7. 다음 챕터로 넘어가는 이유

Chapter 8만으로는 "다운로드는 실패한다"라고 결론내릴 수 없다. Chapter 9에서는 byte-range download와 retry budget을 다루어, 같은 network-change event에서도 workload recovery logic이 결과를 어떻게 바꾸는지 검수해야 한다.

## 8. 검수 결과

| 검수 항목 | 결과 |
| --- | --- |
| baseline과 active handover를 분리했는가? | PASS |
| client path change evidence를 확인했는가? | PASS |
| qlog path validation 부재를 명시했는가? | PASS |
| application failure를 CM failure와 혼동하지 않았는가? | PASS |
| scanner/classifier trigger를 line-level로 문서화했는가? | PASS, `chapter-08-reference-and-evidence.md`와 trigger map 참조 |
