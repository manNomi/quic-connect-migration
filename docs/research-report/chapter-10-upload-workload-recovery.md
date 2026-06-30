# Chapter 10. Upload Workload Recovery

작성일: `2026-06-30`

## 1. 이 챕터의 목적

Chapter 8과 Chapter 9는 download 계열 workload를 다뤘다. Chapter 10은 upload workload를 본다. upload는 사진, 영상, 현장 기록처럼 사용자가 직접 만든 데이터를 서버로 보내는 작업이므로, path change 중 실패하면 사용자 영향이 더 직접적이다.

핵심 질문은 다음이다.

> active Wi-Fi to iPhone USB path change가 upload stream을 끊을 때, application-level retry가 사용자 관점의 upload task completion을 회복하는가?

이 챕터도 transport claim과 application claim을 분리한다.

| claim layer | 질문 |
| --- | --- |
| transport | 같은 QUIC connection이 path validation과 함께 migration했는가? |
| browser/session | Chrome이 동일 target QUIC session을 유지했는가, 아니면 replacement/multiple session을 만들었는가? |
| application | upload task가 최종적으로 complete됐는가? |

## 2. Public iPhone USB Upload Pilot And Replication

핵심 public result는 2026-06-26 upload retry pilot and replication이다. 보고용 문서는 raw hostname, public IP, local interface 이름을 새로 복사하지 않고 public-safe summary만 사용한다.

### Short Pilot

| condition | trigger | retry | app result | upload bytes | retry used | target H3 tuples | Chrome QUIC sessions | qlog path validation |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| short upload | 2s | 0 | failed | partial generated, 0 received | 0 | 1 | 1 | 0 |
| short upload | 2s | 1 | succeeded | full received | 0 | 1 | 1 | 0 |

short retry=1 row는 retry recovery의 강한 증거가 아니다. retry path를 실제로 쓰지 않고 성공했기 때문이다. 이 row는 timing variability evidence로 해석한다.

### Long Replication

더 강한 조건은 16s/64KB upload, 4s trigger다. network cutover가 upload stream 중간에 발생하도록 만든 조건이다.

| condition | repetitions | application success | retry used | partial first-attempt bytes | target H3 tuples | Chrome QUIC sessions | qlog path validation |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| retry=0 | 3 | 0/3 | 0/3 | 28672, 45056, 40960 | 1 in every row | 1 in every row | 0/3 |
| retry=1 | 3 | 3/3 | 3/3 | final 65536 bytes in every row | 2 in every row | 2 in every row | 1/3 |

핵심 관찰:

1. retry=0은 matched long upload condition에서 3/3 실패했다.
2. retry=1은 같은 조건에서 3/3 성공했고, 모든 성공 row가 retry를 실제로 사용했다.
3. retry=1 성공 row는 target H3 tuple count와 Chrome target QUIC session count가 모두 2였다.
4. qlog path validation이 나타난 row도 Chrome target QUIC session이 2개였기 때문에 single-session browser CM evidence가 아니다.

## 3. 왜 Upload 결과가 중요한가

download의 byte-range retry는 "이미 받은 byte 이후부터 다시 받기"가 가능하다. 반면 upload는 client가 보낸 body가 서버에 얼마나 도착했는지, 첫 번째 request가 실패했을 때 재시도 body가 같은 의미를 갖는지, 서버가 idempotency나 duplicate handling을 어떻게 처리하는지가 중요하다.

이 repo의 upload workload는 단순화된 synthetic upload지만, 다음을 분명히 보여준다.

| 관찰 | 의미 |
| --- | --- |
| retry=0 long upload 0/3 success | path change가 upload task failure로 직접 드러남 |
| retry=1 long upload 3/3 success | application retry가 task completion을 회복할 수 있음 |
| retry=1 uses two target sessions | recovery cost가 replacement/multiple-session behavior로 나타남 |
| qlog path validation 1/3 but sessions 2 | path validation만으로 single-session browser CM이라고 할 수 없음 |

## 4. Local Upload Controls와의 관계

local Chrome NAT rebinding upload controls는 packet-level rebinding과 path validation을 더 잘 관찰하게 해준다. 그러나 local proxy control은 실제 Wi-Fi to iPhone USB client route change가 아니므로, public upload handover와 같은 claim으로 쓰면 안 된다.

| evidence source | 역할 | claim boundary |
| --- | --- | --- |
| local upload rebinding summary | packet rebinding, qlog/NetLog path frame, upload sink bytes 검수 | real handover success 아님 |
| public iPhone USB upload replication | 실제 client path change 중 application retry effect 검수 | single-session CM success 아님 |

두 evidence를 합치면 다음 결론이 가능하다.

> Upload continuity must be evaluated with both transport/session evidence and application retry outcome, because upload retry can restore user-visible completion even when browser single-session CM is not demonstrated.

## 5. Fresh non-iPhone local upload refresh

2026-06-30에는 iPhone 없이 Chrome desktop local UDP rebinding upload control을 새로 실행했다.

| run | status | classification | upload complete | retry used | upload bytes | remote tuples | Chrome sessions | qlog C/R | NetLog C/R | proxy A/B packets |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `chrome-desktop-noniphone-upload-drop3000-retry0-20260630` | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 0 | 131072 | 1 | 1 | 1/1 | 1/1 | 29/110 |

이 row는 public upload retry replication의 대체물이 아니다. 대신 upload workload에서 artifact 해석이 얼마나 섬세해야 하는지 보강한다. 같은 target QUIC session에서 upload는 완료됐고 qlog/NetLog에는 path validation이 있었지만, request-level server remote tuple은 1개로 유지됐다. 그러므로 upload에서 server request log만 보면 packet-level rebinding을 놓칠 수 있다.

## 6. Fresh 2026-06-29 Upload Row의 위치

2026-06-29 fresh upload no-retry row는 local workspace에 validation file이 있지만, active row가 server artifact missing으로 분류되어 최종 근거로 쓰기 어렵다. 따라서 Chapter 10의 중심 근거는 2026-06-26 repeated upload replication이다.

이 구분은 중요하다.

| row type | 논문 사용 |
| --- | --- |
| 2026-06-26 repeated upload replication | application retry recovery evidence |
| 2026-06-30 local upload refresh | local proxy artifact interpretation evidence |
| 2026-06-29 server-artifact-missing active row | failed/diagnostic record, main claim 근거 아님 |

## 7. 논문에서 쓸 수 있는 주장

안전한 주장:

> In the public iPhone USB upload replication, long upload tasks failed without application retry but completed with one retry in all matched repetitions, while the successful retry rows showed replacement or multiple-session behavior rather than proven single-session browser QUIC migration.

더 강한 research framing:

> Upload continuity exposes the gap between transport continuity and web task continuity: retry can recover the user's task, but it changes session attribution and latency, so it must be reported separately from QUIC Connection Migration.

피해야 할 주장:

| 피해야 할 주장 | 이유 |
| --- | --- |
| upload retry success proves CM | 성공 row는 multiple target QUIC sessions 또는 tuple-only evidence다. |
| qlog path validation alone proves Chrome CM | qlog path validation이 있던 row도 Chrome session count가 2였다. |
| retry=1 always works | 현재 evidence는 matched long upload condition 3회 반복에 한정된다. |
| fresh 2026-06-29 upload row validates the claim | server artifact missing이라 main evidence가 아니다. |

## 8. 다음 챕터로 넘어가는 이유

upload/download는 task failure가 선명하다. 그러나 사용자가 처음에 말한 streaming service 관점에서는 media workload가 더 중요할 수 있다. 다음 챕터는 media segment와 buffered media를 다루면서, completion뿐 아니라 startup delay, buffer depth, rebuffer event, retry/session churn까지 QoE 관점으로 정리해야 한다.

## 9. 검수 결과

| 검수 항목 | 결과 |
| --- | --- |
| retry=0과 retry=1을 분리했는가? | PASS |
| upload application recovery와 CM success를 분리했는가? | PASS |
| qlog path validation과 Chrome session count를 함께 해석했는가? | PASS |
| raw hostname/IP/interface를 새 문서에 복사하지 않았는가? | PASS |
| scanner/classifier trigger를 line-level로 문서화했는가? | PASS, `chapter-10-reference-and-evidence.md`와 trigger map 참조 |
