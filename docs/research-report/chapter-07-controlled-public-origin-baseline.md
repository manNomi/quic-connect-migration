# Chapter 7. Controlled Public Origin 구축 및 HTTP/3 Baseline

작성일: `2026-06-30`

## 1. 이 챕터의 목적

Chapter 6의 local NAT rebinding control은 artifact 해석 규칙을 검증했지만, 실제 browser handover 논문 실험으로 쓰기에는 부족하다. 실제 실험에는 연구자가 제어하는 public WebPKI origin이 필요하다.

> Chrome browser handover 실험 전에, controlled public origin에서 application HTTP/3 no-change baseline이 먼저 증명되어야 한다.

이 챕터는 handover 결과가 아니다. active path-change 실험에 들어가기 전 precondition gate다.

## 2. 왜 controlled public origin이 필요한가

public third-party endpoint는 다음 한계가 있다.

| 문제 | 의미 |
| --- | --- |
| server qlog 없음 | application H3와 path validation을 직접 확인할 수 없음 |
| workload 제어 불가 | upload, streaming downlink, polling, range, media workload를 마음대로 만들 수 없음 |
| NetLog discovery overclaim 위험 | `dns_alpn_h3` discovery job과 실제 application `using_quic` job을 혼동할 수 있음 |
| origin path evidence 없음 | server request log와 tuple/qlog evidence를 함께 볼 수 없음 |

따라서 이 연구의 browser 실험은 third-party public H3 endpoint가 아니라 controlled public quic-go HTTP/3 origin을 기준으로 삼는다.

## 3. Baseline Gate 설계

controlled public baseline은 다음 evidence를 함께 요구한다.

| evidence | 기준 |
| --- | --- |
| public readiness | DNS, TCP/TLS 또는 curl HTTPS, `Alt-Svc: h3` 확인 |
| server request log | expected request count 이상 도달 |
| server qlog | `chosen_alpn`과 HTTP/3 frame evidence |
| Chrome NetLog | application `using_quic` job이 있으면 강한 browser-side evidence |
| combined classifier | `controlled_public_application_h3_confirmed` 또는 server qlog 기반 H3 confirmed |

중요한 점:

> Chrome NetLog에서 H3 discovery가 보이는 것만으로는 baseline PASS가 아니다. controlled server의 request log와 qlog가 application H3를 보여야 한다.

## 4. 현재 결과

현재 보고 가능한 핵심 결과는 다음이다.

| 항목 | 결과 | 해석 |
| --- | --- | --- |
| controlled public baseline unlock | PASS | `controlled_public_application_h3_confirmed` |
| final protocol count 가능 여부 | yes | baseline artifact bundle complete |
| fresh origin smoke | PASS | record-only smoke이며 final-counting trial은 아님 |
| config baseline readiness | yes | public origin/cert/listener/Alt-Svc/Chrome path shape는 준비됨 |
| active network-change config readiness | no | `NETWORK_CHANGE_CMD`가 missing |
| Android network-change config readiness | no | Android command도 missing |

따라서 Chapter 7의 결론은 다음이다.

> Controlled public application HTTP/3 baseline은 확보됐다. 그러나 이 baseline은 handover 성공이 아니며, active browser network-change 실험은 별도의 client path-change command와 secondary path readiness가 필요하다.

## 5. 날짜별 상태 해석

AWS/public origin 관련 문서는 point-in-time diagnostic이다. 날짜별로 다음처럼 해석해야 한다.

| 날짜 | 문서 | 해석 |
| --- | --- | --- |
| 2026-06-24 | controlled public origin plan/application H3 gate | controlled public origin이 필요한 이유와 baseline gate 정의 |
| 2026-06-25 | AWS provision report | EC2 origin, remote harness, temporary WebPKI path, baseline capture completed |
| 2026-06-26 | baseline unlock check | final-countable baseline PASS, active trial unlock 가능 |
| 2026-06-29 | fresh config check | baseline config ready, active network-change command missing |
| 2026-06-29 | fresh origin smoke | controlled public application H3 confirmed, record-only smoke |
| 2026-06-29 | origin access diagnostic | 특정 시점의 recovery/access diagnostic이며 CM evidence가 아님 |

이렇게 정리하는 이유는 "어느 날 access check가 실패했으니 baseline이 없다" 또는 "baseline이 PASS니까 handover도 됐다" 같은 양쪽 과장을 막기 위해서다.

## 6. 다음 챕터로 넘어가는 조건

Chapter 8 이후의 public handover 실험은 다음 조건을 만족해야 한다.

1. baseline summary가 `PASS`이고 allowed unlock classification이어야 한다.
2. artifact bundle이 complete여야 한다.
3. public origin readiness가 통과해야 한다.
4. `NETWORK_CHANGE_CMD`가 존재해야 한다.
5. client path snapshot에서 active path change가 관찰되어야 한다.
6. Chrome NetLog, server qlog, server request log, DOM completion을 함께 수집해야 한다.

이 조건 중 1-3은 상당 부분 확보됐다. 4-6은 active network-change trial의 책임이다.

## 7. 논문에 쓸 수 있는 주장

안전한 주장:

> A controlled public WebPKI HTTP/3 origin is required before browser handover experiments, because third-party H3 discovery alone cannot prove application H3 or provide server-side qlog/request evidence.

현재 결과 기반 주장:

> The controlled public Chrome application H3 baseline reached a final-countable PASS classification, but this baseline is a precondition for handover trials rather than evidence of connection migration.

피해야 할 주장:

| 피해야 할 주장 | 이유 |
| --- | --- |
| baseline PASS는 handover PASS다 | no-change application H3 precondition일 뿐이다. |
| Alt-Svc만 있으면 application H3다 | discovery와 application request는 분리해야 한다. |
| public origin access diagnostic은 CM evidence다 | reachability/recovery diagnostic이지 migration artifact가 아니다. |
| active network-change 실험 준비가 끝났다 | `NETWORK_CHANGE_CMD`와 active path change proof가 별도로 필요하다. |

## 8. 검수 결과

| 검수 항목 | 결과 |
| --- | --- |
| public origin baseline과 handover trial을 분리했는가? | PASS |
| third-party H3 discovery overclaim을 방지했는가? | PASS |
| baseline unlock classification을 명시했는가? | PASS |
| 민감정보를 새 문서에 복사하지 않았는가? | PASS |
| scanner/classifier trigger를 line-level로 문서화했는가? | PASS, `chapter-07-reference-and-evidence.md`와 trigger map 참조 |
