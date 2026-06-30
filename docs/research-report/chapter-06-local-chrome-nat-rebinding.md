# Chapter 6. Local Chrome NAT Rebinding Control

작성일: `2026-06-30`

## 1. 이 챕터의 목적

Chapter 5는 브라우저 CM claim에 필요한 관찰성 기준을 정했다. Chapter 6는 그 기준을 local Chrome forced-H3 환경에 적용한 대조군이다.

> Chrome HTTP/3 workload가 local UDP NAT rebinding과 return-path disruption을 만났을 때, transport evidence와 application completion은 어떻게 갈라지는가?

이 챕터는 실제 Wi-Fi/LTE handover 결과가 아니다. client의 실제 route/interface/public IP가 바뀌지 않는 local proxy control이다. 따라서 결론은 "Chrome handover 성공"이 아니라 "browser artifact 해석 규칙과 workload-sensitive failure boundary를 검증했다"에 가깝다.

## 2. 실험 설계

구성:

| 구성 요소 | 역할 |
| --- | --- |
| Chrome desktop | forced HTTP/3 workload 실행, NetLog 생성 |
| UDP rebinding proxy | client-to-server packet을 upstream A에서 B로 전환 |
| quic-go HTTP/3 server | request log, qlog, workload endpoint 제공 |
| classifier | NetLog, qlog, proxy log, DOM dump, server request를 합쳐 판정 |

proxy는 첫 client packet 이후 지정된 시간까지 upstream A를 사용하고, 이후 client-to-server packet을 upstream B로 보낸다. 추가 control에서는 switch 이후 server-to-client packet을 A, B, 또는 A+B에서 drop한다. 이 구조는 NAT rebinding과 return-path loss를 분리해서 관찰하게 해준다.

## 3. 핵심 결과

### 3.1 Rebinding repetition

| 조건 | runs | PASS | proxy packet rebinding | qlog path validation | Chrome target NetLog path validation | 해석 |
| --- | ---: | ---: | --- | --- | --- | --- |
| downlink no-heartbeat | 3 | 3/3 | 3/3 | 3/3 | 3/3 | single target session으로 보이는 local path validation |
| downlink heartbeat | 3 | 3/3 | 3/3 | 3/3 | 3/3 | task는 완료됐지만 Chrome QUIC session이 2개로 갈라짐 |

핵심:

> heartbeat가 있으면 task completion은 유지되어도 session attribution이 나빠질 수 있다. 따라서 heartbeat/retry는 application recovery evidence이지 single-session CM evidence가 아니다.

### 3.2 Rebinding timing sensitivity

| workload | timing | runs | PASS | packet rebinding | qlog path validation | NetLog target path validation | 평균 B packet share |
| --- | --- | ---: | ---: | --- | --- | --- | ---: |
| downlink | early | 4 | 4/4 | 4/4 | 4/4 | 4/4 | 0.618 |
| downlink | late | 4 | 4/4 | 4/4 | 4/4 | 4/4 | 0.172 |
| upload | early | 2 | 2/2 | 2/2 | 2/2 | 2/2 | 0.800 |
| upload | late | 2 | 2/2 | 2/2 | 2/2 | 2/2 | 0.181 |

핵심:

> 같은 local rebinding이라도 switch timing에 따라 B-side packet share가 크게 달라진다. 따라서 packet count 기반 해석에는 rebind timing을 함께 보고해야 한다.

### 3.3 Old-path drop control

| workload | runs | PASS | old-path A drop | qlog path validation | NetLog path validation | dropped A-side server packets |
| --- | ---: | ---: | --- | --- | --- | ---: |
| downlink/upload aggregate | 11 | 11/11 | 11/11 | 11/11 | 11/11 | 60 |

핵심:

> old return path 일부가 제거되어도 local workload는 완료될 수 있었다. 하지만 heartbeat downlink는 여러 Chrome target QUIC session으로 갈라졌으므로, application completion은 single-session continuity의 충분조건이 아니다.

### 3.4 Return-path drop controls

| condition | workload rows | expected | actual | application complete | 해석 |
| --- | ---: | --- | --- | --- | --- |
| B-only server-to-client drop | 2 | PASS | PASS | 2/2 | old return path가 살아 있으면 task completion 가능 |
| A+B server-to-client drop | 2 | FAIL | FAIL | 0/2 | 양쪽 return path가 모두 막히면 DOM task 실패 |

핵심:

> qlog/path evidence가 있어도 return path가 충분히 오래 막히면 application task는 실패한다.

### 3.5 Transient outage boundary

| sweep | 결과 | 해석 |
| --- | --- | --- |
| broad sweep | 14 rows, 8 PASS / 6 FAIL | 250-4000ms는 PASS, 5000ms 이상은 초기 sweep에서 FAIL |
| repeated 4000/4500/5000ms | 18 rows, 15 PASS / 3 FAIL | 5000ms가 단일 threshold가 아니라 workload-sensitive transition zone임 |
| downlink fine boundary | 9 rows, 4 PASS / 5 FAIL | 5000/5500ms는 혼재, 6000ms는 3/3 FAIL |
| upload fine boundary | 12 rows, 4 PASS / 8 FAIL | 4600ms는 3/3 PASS, 4750ms 혼재, 4900/5000ms는 6/6 FAIL |

핵심:

> local browser workload continuity boundary는 단조 threshold가 아니다. upload는 downlink보다 더 이른 지점에서 깨지는 경향을 보였고, 모든 failure row에도 qlog H3/path evidence가 남을 수 있었다.

### 3.6 Fresh non-iPhone media refresh

2026-06-30에 iPhone 없이 Chrome desktop local media control을 한 번 더 실행했다.

| run | status | classification | app complete | remote tuples | Chrome sessions | qlog C/R | NetLog C/R | proxy A/B packets |
| --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| `chrome-desktop-noniphone-media-drop3000-retry0-20260630` | PASS | `nat_rebinding_possible_session_continuity` | true | 2 | 1 | 1/1 | 1/1 | 63/24 |

이 row는 local proxy control 안에서는 꽤 강한 browser artifact다. target Chrome QUIC session이 1개이고, server tuple이 2개이며, qlog와 NetLog 양쪽에 path challenge/response가 있다. 하지만 여전히 실제 public handover가 아니므로 Chapter 5의 browser claim ceiling은 유지한다.

### 3.7 Fresh non-iPhone range refresh

같은 날 byte-range workload도 2회 실행했다.

| run | status | classification | range complete | retry used | remote tuples | Chrome sessions | qlog C/R | elapsed ms |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |
| `chrome-desktop-noniphone-range-drop3000-retry0-20260630` | PASS | `nat_rebinding_possible_session_continuity` | true | 0 | 2 | 1 | 1/1 | 1095 |
| `chrome-desktop-noniphone-range-slow-drop3000-retry0-20260630` | PASS | `nat_rebinding_possible_session_continuity` | true | 0 | 2 | 1 | 1/1 | 6122 |

두 row 모두 retry 없이 완료됐고 target Chrome QUIC session은 1개였다. 느린 row에서는 server packet이 A/B `170/683`으로 B 경로에 집중되어 local path transition evidence가 더 선명했다. 다만 local UDP rebinding control이므로 public route/interface handover 성공으로 확장하지 않는다.

### 3.8 Fresh non-iPhone upload refresh

upload workload도 iPhone 없이 한 번 더 재실행했다.

| run | status | classification | app complete | upload bytes | remote tuples | Chrome sessions | qlog C/R | NetLog C/R | proxy A/B packets |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |
| `chrome-desktop-noniphone-upload-drop3000-retry0-20260630` | PASS | `nat_rebinding_path_validation_without_observed_tuple_change` | true | 131072 | 1 | 1 | 1/1 | 1/1 | 29/110 |

이 row는 upload에서 특히 중요한 해석 경계를 다시 보여준다. server request log 기준 remote tuple은 1개라서 request-level log만 보면 rebinding이 없었던 것처럼 보인다. 그러나 proxy packet은 A/B 양쪽 upstream으로 나뉘었고, qlog와 Chrome NetLog target session에는 PATH_CHALLENGE/PATH_RESPONSE가 있었다. 따라서 upload 분석에서는 request log, proxy packet log, qlog, NetLog를 함께 봐야 한다.

## 4. 논문에 쓸 수 있는 주장

안전한 주장:

> In a local Chrome forced-H3 UDP rebinding control, packet-level rebinding, server qlog path validation, Chrome NetLog path-validation evidence, and DOM-level task completion can be collected jointly. The results show that transport evidence and application completion must be reported as separate outcomes.

조건부 주장:

> Local NAT rebinding controls are useful positive/negative controls for browser artifact interpretation, but they do not substitute for a controlled public Wi-Fi/cellular handover trial.

피해야 할 주장:

| 피해야 할 주장 | 이유 |
| --- | --- |
| local rebinding PASS는 실제 Wi-Fi/LTE handover PASS다 | 실제 client active path change가 없다. |
| qlog path validation이 있으면 웹 작업은 성공한다 | A+B drop 및 transient failure row와 충돌한다. |
| heartbeat/retry PASS는 single-session CM success다 | multiple Chrome QUIC session이 관찰될 수 있다. |
| 5초가 절대 실패 threshold다 | repeated/downlink fine boundary에서 PASS/FAIL이 혼재한다. |

## 5. 검수 결과

| 검수 항목 | 결과 |
| --- | --- |
| local control과 public handover claim을 분리했는가? | PASS |
| proxy packet evidence, qlog, NetLog, DOM completion을 분리했는가? | PASS |
| positive/negative control을 모두 포함했는가? | PASS, rebinding repetition/old-path drop/return-path drop/transient outage |
| scanner/classifier trigger를 line-level로 문서화했는가? | PASS, `chapter-06-reference-and-evidence.md`와 trigger map 참조 |
| 코드 검증을 수행했는가? | PASS, Go test와 summarizer tests 실행 |
