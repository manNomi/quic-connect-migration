# Chapter 9. Byte-Range Download And Retry Recovery

작성일: `2026-06-30`

## 1. 이 챕터의 목적

Chapter 8에서 full-response downlink는 Wi-Fi to iPhone USB path change 중 2/2 실패했다. Chapter 9는 같은 controlled public origin과 같은 browser handover 조건에서 byte-range download가 어떻게 달라지는지 검수한다.

핵심 질문은 다음이다.

> browser-level QUIC Connection Migration evidence가 관찰되지 않는 상황에서도, byte-range retry가 사용자 관점의 download task completion을 회복할 수 있는가?

이 질문은 transport claim과 application claim을 분리한다.

| claim layer | 질문 |
| --- | --- |
| transport | 같은 QUIC connection이 path validation과 함께 migration했는가? |
| application | path change 중 끊긴 byte range를 retry해서 사용자의 download task가 완료됐는가? |

## 2. 실험 환경

| 항목 | 값 |
| --- | --- |
| client | `macOS Chrome` |
| secondary path | `iPhone USB` |
| origin | controlled public EC2 origin |
| server | quic-go HTTP/3 harness |
| TLS | WebPKI certificate on temporary `sslip.io` origin |
| retry=0 baseline | `controlled-public-chrome-range-noretry-nochange-fresh-20260629-001` |
| retry=0 active trials | `controlled-public-chrome-range-noretry-network-change-page-ready-fresh-20260629-001` through `002` |
| retry=2 baseline | `controlled-public-chrome-range-retry-nochange-fresh-20260629-001` |
| retry=2 active trials | `controlled-public-chrome-range-retry-network-change-page-ready-fresh-20260629-001` through `003` |
| active trigger | at least `131072` completed bytes |
| network change action | Wi-Fi disabled, wrapper restored Wi-Fi after run |

Workload:

| 항목 | 값 |
| --- | --- |
| page | `GET /browser-range-download` |
| range transfer | repeated `GET /range-download` |
| total bytes | `524288` |
| range size | `131072` |
| retry budgets | `0`, `2` |

## 3. 전체 결과

| condition | retry budget | runs | status | classification | qlog path validation | application result |
| --- | ---: | ---: | --- | --- | --- | --- |
| no-change baseline | 0 | 1 | `PASS` | `controlled_public_application_h3_confirmed` | `false` | `1/1` completed |
| no-change baseline | 2 | 1 | `PASS` | `controlled_public_application_h3_confirmed` | `false` | `1/1` completed |
| Wi-Fi to iPhone USB | 0 | 2 | `PASS_NEGATIVE_CONTROL` | `application_task_failed_without_quic_path_validation` | `false` in all runs | `0/2` completed |
| Wi-Fi to iPhone USB | 2 | 3 | `PASS_NEGATIVE_CONTROL` | mixed negative controls | `false` in all runs | `2/3` completed |

가장 중요한 관찰은 다음이다.

> retry budget을 0에서 2로 올리자 active handover 중 download task completion이 0/2에서 2/3으로 바뀌었다. 그러나 qlog path validation은 모든 active run에서 관찰되지 않았다.

## 4. Retry=2 Active Repetitions

| trial | immediate client path | eventual client path | target H3 tuples | application success | completed bytes | retries | classification |
| --- | --- | --- | ---: | --- | ---: | ---: | --- |
| `001` | `client_active_path_changed` | `no_client_path_change_observed` | 2 | `true` | 524288 | 1 | `tuple_changed_without_path_validation` |
| `002` | `interface_set_changed_without_route_change` | `client_active_path_changed` | 1 | `false` | 262144 | 0 | `application_task_failed_without_quic_path_validation` |
| `003` | `client_active_path_changed` | `client_active_path_changed` | 2 | `true` | 524288 | 1 | `tuple_changed_without_path_validation` |

성공한 `001`, `003`은 사용자 관점의 download task는 완료했다. 하지만 classifier는 둘 다 `PASS_NEGATIVE_CONTROL`로 남긴다. 이유는 target H3 remote tuple이 2개였더라도 qlog path validation이 없었기 때문이다.

즉, 이 결과는 다음을 말한다.

> byte-range retry can recover task completion, but the current artifacts do not prove same-connection QUIC Connection Migration.

## 5. Retry=0 Active Repetitions

| trial | immediate client path | eventual client path | target H3 tuples | application success | completed bytes | retries | classification |
| --- | --- | --- | ---: | --- | ---: | ---: | --- |
| `001` | `client_active_path_changed` | `client_active_path_changed` | 1 | `false` | 262144 | 0 | `application_task_failed_without_quic_path_validation` |
| `002` | `client_active_path_changed` | `client_active_path_changed` | 1 | `false` | 262144 | 0 | `application_task_failed_without_quic_path_validation` |

retry=0에서는 path change가 실제로 관찰됐지만 task는 모두 실패했다. 이 결과는 Chapter 8 full-response downlink와 같은 방향이다.

## 6. Full-Response Downlink와의 비교

| workload | retry budget | active runs | completed active runs | typical signal | CM evidence |
| --- | ---: | ---: | ---: | --- | --- |
| full-response downlink | 0 | 2 | 0 | `downlinkError` after 17528 bytes | no qlog path validation |
| byte-range download | 0 | 2 | 0 | `rangeError` after 262144 bytes | no qlog path validation |
| byte-range download | 2 | 3 | 2 | `rangeComplete=true`, `rangeRetriesUsed=1` in successful runs | no qlog path validation |

이 비교는 논문에서 매우 중요하다. 같은 "download"라도 full-response stream과 byte-range resume은 failure semantics가 다르다.

| download type | 실패 의미 | recovery 가능성 |
| --- | --- | --- |
| full-response stream | stream이 끊기면 전체 fetch/read task가 실패 | 낮음, whole response retry 필요 |
| byte-range download | 특정 range request 실패 | 높음, 실패 range만 retry 가능 |

## 7. Timing 해석

원본 결과에는 trial `003` 직전 local failover probe가 iPhone USB가 default path가 되는 데 약 `675 ms`가 걸렸다고 기록되어 있다. 이는 `002` 실패를 "iPhone USB가 아예 불가능했다"가 아니라 "secondary path activation timing과 retry window가 맞지 않았을 수 있다"로 해석하게 해준다.

따라서 Chapter 9의 결론은 deterministic success가 아니라 timing-dependent recovery다.

## 8. 논문에서 쓸 수 있는 주장

안전한 주장:

> In the controlled public Chrome trials, byte-range retry changed user-visible download completion under path change, while qlog path-validation evidence remained absent.

더 강한 연구 framing:

> Application-level recovery mechanisms such as byte-range retry can mask or compensate for missing browser-level QUIC Connection Migration evidence, so task continuity must be evaluated separately from transport migration.

피해야 할 주장:

| 피해야 할 주장 | 이유 |
| --- | --- |
| retry=2 성공은 QUIC CM 성공이다 | qlog path validation이 없고 validator가 negative-control로 분류했다. |
| tuple count 2는 곧 migration이다 | `tuple_changed_without_path_validation`은 CM success에서 제외된다. |
| retry를 넣으면 항상 복구된다 | retry=2 active run도 1/3 실패했다. |
| download continuity는 하나의 metric이다 | full-response, byte-range, media segment, buffered media는 서로 다른 semantics를 가진다. |

## 9. 다음 챕터로 넘어가는 이유

다운로드 계열에서는 byte-range retry가 completion을 바꿀 수 있음을 확인했다. 다음은 upload workload다. upload는 이미 보낸 bytes, request body streaming, browser retry policy, application retry policy가 얽혀 있어 download와 다른 실패 양상을 보일 수 있다.

## 10. 검수 결과

| 검수 항목 | 결과 |
| --- | --- |
| retry=0과 retry=2를 분리했는가? | PASS |
| application success와 CM success를 분리했는가? | PASS |
| qlog path validation 부재를 명시했는가? | PASS |
| tuple change를 migration으로 과장하지 않았는가? | PASS |
| scanner/classifier trigger를 line-level로 문서화했는가? | PASS, `chapter-09-reference-and-evidence.md`와 trigger map 참조 |
