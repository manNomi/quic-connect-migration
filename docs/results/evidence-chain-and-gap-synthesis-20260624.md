# Evidence chain and gap synthesis

작성일: 2026-06-24

## 1. 목적

현재 연구 결과를 “된다/안 된다”로 먼저 정하지 않고, 논문에서 방어 가능한 claim 단위로 다시 정리한다.

핵심 질문:

> HTTP/3 Connection Migration이 실제 웹 작업 연속성으로 이어진다고 주장하려면 어떤 evidence chain이 필요한가?

관련 기준:

- [RFC 9000 QUIC](https://datatracker.ietf.org/doc/html/rfc9000): QUIC connection migration, peer address change, path validation, connection ID 사용의 기준점
- [RFC 9114 HTTP/3](https://datatracker.ietf.org/doc/html/rfc9114): HTTP semantics over QUIC와 HTTP/3 application request 판정의 기준점
- [Chromium NetLog event definitions](https://chromium.googlesource.com/chromium/src/+/HEAD/net/log/net_log_event_type_list.h): Chrome 내부 QUIC migration/session event 관찰 기준
- [HTTP/3 explained](https://http.dev/3): browser HTTP/3 discovery, fallback, deployment 해석 보조 기준
- [An Analysis of QUIC Connection Migration in the Wild](https://arxiv.org/html/2410.06066v1): public Internet에서 CM support가 불균등하며 failure reason 분석이 아직 열린 문제라는 anchor paper
- [Literature Refresh: Wild CM Support and NetLog Evidence Boundary](./literature-refresh-wild-cm-and-netlog-boundary-20260624.md): local Chrome NAT rebinding/NetLog evidence와 browser handover claim의 경계 정리

## 2. 현재까지 지지되는 claim

### 2.1 QUIC CM primitive는 구현체에 존재한다

현재 repo의 구현체 조사와 quic-go local/EC2/AWS 실험은 다음을 지지한다.

| claim | 근거 |
| --- | --- |
| quic-go direct-origin active migration 가능 | local transport, local HTTP/3, EC2 direct-origin에서 `AddPath -> Probe -> Switch` 성공 |
| path validation evidence 관찰 가능 | qlog에서 PATH_CHALLENGE/PATH_RESPONSE와 ALPN/H3 frame evidence 수집 |
| AWS NLB는 조건부로 continuity 가능 | `TCP_QUIC :443` + 올바른 QUIC-LB plaintext CID/Server ID에서 same-target continuity 관찰 |
| deployment routing은 실패 원인이 될 수 있음 | malformed CID, wrong Server ID negative control에서 application payload 실패 |

따라서 “CM이 안 쓰이는 이유는 구현이 전혀 없기 때문”이라고 쓰면 현재 증거와 맞지 않는다.

## 3. 현재까지 지지되지 않는 claim

다음은 아직 주장하면 안 된다.

| claim | 왜 아직 부족한가 |
| --- | --- |
| Chrome에서 실제 Wi-Fi/LTE handover 중 CM이 성공했다 | 현재 장비에는 active secondary path가 없고, Android device도 연결되어 있지 않다 |
| Safari에서 HTTP/3 CM이 성공했다 | Safari WebDriver readiness는 있지만 NetLog equivalent가 없고, controlled public origin baseline이 아직 없다 |
| tuple/source port 변화는 곧 CM이다 | Chrome CDP heartbeat no-change에서 network-change 없이도 server remote addr count 2, QUIC session count 2가 관찰됐다 |
| request-level tuple 변화가 없으면 rebinding/path validation도 없다 | Chrome streaming upload rebinding 3회에서 upload는 완료되고 qlog path validation은 있었지만 request-level remote tuple은 하나로 남았다 |
| inactive interface toggle은 handover 실험이다 | client path snapshot이 `no_client_path_change_observed`로 분류했다 |
| public third-party endpoint NetLog만으로 application H3를 확정할 수 있다 | Cloudflare/Google/YouTube public controls에서 discovery와 application H3를 분리해야 했다 |

## 4. 새로 얻은 중요한 negative evidence

### 4.1 Heartbeat는 no-change에서도 multiple QUIC sessions를 만들 수 있다

CDP real-time runner로 downlink streaming 중 heartbeat를 실행했다.

| condition | classification | server remote addr count | Chrome target QUIC sessions | qlog path validation |
| --- | --- | ---: | ---: | --- |
| no heartbeat, no network change | `no_path_change_baseline` | 1 | 1 | false |
| heartbeat, no network change | `multiple_quic_sessions_without_network_change` | 2 | 2 | false |
| heartbeat, inactive interface toggle | `multiple_quic_sessions_without_client_path_change` | 2 | 2 | false |

해석:

- heartbeat 자체는 application-level recovery 전략 후보지만, 관측 해석을 어렵게 만들 수 있다.
- server가 본 remote tuple이 늘어났다고 해서 곧바로 connection migration이라고 볼 수 없다.
- qlog path validation, Chrome session continuity, client active path change를 함께 요구해야 한다.
- NetLog migration 관련 event는 `QUIC_CONNECTION_MIGRATION_MODE` 같은 mode evidence와 실제 trigger/success/failure evidence를 분리해야 한다.

### 4.2 Inactive interface toggle은 path-change trigger가 아니다

inactive Thunderbolt Bridge toggle은 command exit 0이었다.

그러나 client path snapshot은 다음을 보였다.

| 항목 | before | after |
| --- | --- | --- |
| active interface | `en0` | `en0` |
| default interface | `en0` | `en0` |
| target route | `lo0` | `lo0` |
| classification | `no_client_path_change_observed` | `no_client_path_change_observed` |

따라서 이 실험은 handover가 아니라 no-op trigger 대조군이다.

### 4.3 Streaming upload rebinding은 request log 한계를 보여준다

Chrome forced-H3 page가 streaming `fetch()` upload를 수행하는 동안 local UDP rebinding proxy가 server-facing socket을 A에서 B로 전환했다.

| condition | runs | upload completion | proxy packet rebinding | request-level remote tuple count | Chrome target QUIC sessions | qlog path validation | Chrome target NetLog path frames |
| --- | ---: | --- | --- | ---: | ---: | --- | --- |
| streaming upload, local UDP rebinding | 3 | 3/3 PASS, each `/upload-sink` received 262144 bytes | true in every run; A/B client packet counts 87/159, 89/161, 90/161 | 1 in every run | 1 in every run | true in every run | PATH_CHALLENGE received / PATH_RESPONSE sent 1/1 in every run |

해석:

- client-sending workload에서도 Chrome forced-H3 request는 local NAT rebinding 중 완료될 수 있었다.
- proxy packet log는 A/B upstream forwarding을 직접 보여줬고 Chrome NetLog target source도 path validation frame을 기록했지만, server request log의 `RemoteAddr`는 request handler 관점 값이라 packet-level rebinding을 항상 드러내지 않는다.
- 따라서 browser-level CM 또는 NAT rebinding claim에는 request log, qlog path validation, Chrome NetLog session attribution, proxy/client path evidence를 함께 사용해야 한다.
- 이 결과는 local NAT rebinding control이며, 실제 Wi-Fi/LTE active handover 성공을 의미하지 않는다.

### 4.4 Chrome target NetLog path frames는 transport evidence이지 최종 handover evidence는 아니다

최신 rebinding summary는 Chrome target source에서 PATH_CHALLENGE 수신과 PATH_RESPONSE 송신을 반복 관찰했다.

| condition | repetitions | proxy packet rebinding | qlog path validation | Chrome target NetLog path validation |
| --- | ---: | --- | --- | --- |
| downlink forced-H3 local rebinding | 6 | 6/6 | 6/6 | 6/6 |
| streaming upload forced-H3 local rebinding | 3 | 3/3 | 3/3 | 3/3 |

해석:

- 이는 tuple-only evidence보다 강하다. proxy packet log, server qlog, Chrome NetLog가 서로 다른 관찰 지점에서 같은 local rebinding 현상을 지지한다.
- 그러나 RFC 9000의 path validation은 changed path reachability를 확인하는 transport 절차이지, 실제 Wi-Fi/LTE handover 또는 browser task continuity 보장을 의미하지 않는다.
- 따라서 논문에서는 “Chrome local forced-H3 NAT rebinding에서 target QUIC session의 path validation evidence를 확보했다”까지만 현재 결과로 쓰고, “Chrome Wi-Fi/LTE handover 성공”은 final browser handover protocol 완료 전까지 보류한다.

### 4.5 Rebinding timing은 packet 분포와 heartbeat 해석을 바꾼다

[Chrome H3 Local Rebinding Timing Sensitivity Summary](./chrome-h3-rebinding-timing-sensitivity-20260624.md)는 rebinding 시점을 early `500ms`와 late `5s`로 나누어 downlink/upload를 다시 실행했다.

| workload | timing | runs | PASS | proxy packet rebinding | qlog path validation | Chrome target NetLog path validation | avg B packet share |
| --- | --- | ---: | ---: | --- | --- | --- | ---: |
| downlink | early 500ms | 4 | 4/4 | 4/4 | 4/4 | 4/4 | 0.618 |
| downlink | late 5s | 4 | 4/4 | 4/4 | 4/4 | 4/4 | 0.172 |
| upload | early 500ms | 2 | 2/2 | 2/2 | 2/2 | 2/2 | 0.800 |
| upload | late 5s | 2 | 2/2 | 2/2 | 2/2 | 2/2 | 0.181 |

해석:

- early/late 모두 local NAT rebinding transport evidence는 재현됐다.
- packet share는 rebinding 시점에 따라 크게 달라지므로 packet-count 기반 해석은 timing parameter와 함께 보고해야 한다.
- heartbeat downlink는 early 조건에서 `nat_rebinding_multiple_quic_sessions`, late 조건에서 `nat_rebinding_path_validation_without_observed_tuple_change`로 갈라졌다. 즉 heartbeat 자체의 유무뿐 아니라 heartbeat가 rebinding 전후 어느 시점에 발생하는지도 browser session interpretation을 바꾼다.
- 이 결과는 application heartbeat/recovery 전략을 후속 연구로 다룰 때 timing-controlled protocol이 필요하다는 근거가 된다.

### 4.6 Old-path-drop local control은 완료와 session continuity를 다시 분리한다

[Chrome H3 Local Rebinding Old-Path Drop Summary](./chrome-h3-rebinding-old-path-drop-20260624.md)는 proxy switch 이후 upstream A의 server-to-client packet을 drop하는 조건을 추가했다.

| workload | PASS | dropped A server packets | Chrome QUIC sessions | qlog path validation | Chrome target NetLog path validation |
| --- | ---: | ---: | --- | --- | --- |
| downlink no-heartbeat | 4/4 | 0 | 1 in every row | 4/4 | 4/4 |
| downlink heartbeat | 3/3 | 0 | 2 in every row | 3/3 | 3/3 |
| upload | 4/4 | 60 total | smoke row 2; repeated rows 1 each | 4/4 | 4/4 |

해석:

- old path가 실제로 일부 차단된 upload control에서도 application task는 반복적으로 완료될 수 있었다.
- 반복 upload 3회는 Chrome target QUIC session 1개로 유지되어 local NAT rebinding evidence를 강화한다.
- 그러나 heartbeat downlink는 old-path-drop 조건에서도 Chrome target QUIC session 2개로 갈라졌으므로, task completion은 여전히 session continuity의 충분조건이 아니다.
- 이 결과는 final active handover protocol에서 “task completion + path validation + browser session continuity”를 동시에 요구해야 하는 근거를 더 강화한다.

### 4.7 Old-path-drop stress는 크기 확장 후에도 같은 evidence boundary를 유지한다

[Chrome H3 Local Rebinding Old-Path Drop Stress Summary](./chrome-h3-rebinding-old-path-drop-stress-20260624.md)는 old-path-drop 조건을 1MiB/4MiB downlink 및 upload workload로 확장했다.

| profile | workload | PASS | configured/received bytes | dropped A server packets | Chrome QUIC sessions | qlog path validation | Chrome target NetLog path validation |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| downlink-1m-noheartbeat | downlink | 1/1 | 1048576 configured | 39 | 1 | true | true |
| downlink-1m-heartbeat | downlink | 1/1 | 1048576 configured | 12 | 2 | true | true |
| downlink-4m-noheartbeat | downlink | 1/1 | 4194304 configured | 0 | 1 | true | true |
| upload-1m | upload | 1/1 | 1048576 received | 20 | 1 | true | true |
| upload-4m | upload | 1/1 | 4194304 received | 34 | 1 | true | true |

해석:

- 총 5/5 stress row가 완료됐고, upload는 총 5MiB가 server에 도달했다.
- 전체 stress row에서 old-path A-side server packet 105개, 74279 bytes가 drop됐는데도 application task는 완료됐다.
- no-heartbeat downlink와 upload는 Chrome target QUIC session 1개로 유지됐지만, heartbeat downlink는 stress 조건에서도 target session 2개로 갈라졌다.
- 따라서 이 결과는 “local NAT rebinding under old-path-unavailable control”의 강한 feasibility evidence로는 쓸 수 있지만, real Wi-Fi/LTE browser handover evidence로는 쓸 수 없다.

### 4.8 Return-path drop control은 transport evidence와 task completion의 분리를 검증한다

[Chrome H3 Local Rebinding Return-Path Drop Controls](./chrome-h3-rebinding-return-path-drop-controls-20260624.md)는 server-to-client packet drop 위치를 B-only와 A+B로 나누었다.

| condition | workload | expected | actual | app complete | dropped A/B server packets | transport evidence |
| --- | --- | --- | --- | --- | --- | --- |
| B-only drop | downlink 1MiB | PASS | PASS | true | 0/9 | qlog H3/path evidence, Chrome QUIC session |
| B-only drop | upload 1MiB | PASS | PASS | true | 0/9 | qlog H3/path evidence, Chrome QUIC session |
| A+B drop | downlink 1MiB | FAIL | FAIL | false | 103/7 | server request + qlog/NetLog still present |
| A+B drop | upload 1MiB | FAIL | FAIL | false | 54/24 | server request + qlog/NetLog still present |

해석:

- B-only server packet drop은 실패의 충분조건이 아니었다. old return path가 살아 있으면 application data가 계속 도달할 수 있다.
- A+B return path를 모두 차단하면 server request와 transport evidence가 있어도 browser application completion은 실패했다.
- 따라서 final protocol에서 qlog path validation, browser session evidence, application completion을 별도 기준으로 두는 것이 타당하다.

### 4.9 Transient return-path outage sweep은 local tolerance boundary를 제공한다

[Chrome H3 Local Rebinding Transient Return-Path Sweep](./chrome-h3-rebinding-transient-return-path-sweep-20260624.md)는 A+B server-to-client packet drop을 bounded window로 제한했다.

| drop window | workload rows | status | interpretation |
| ---: | ---: | --- | --- |
| 250ms | 2 | 2/2 PASS | 짧은 return-path outage는 1MiB downlink/upload 작업을 깨지 않았다. |
| 1500ms | 2 | 2/2 PASS | qlog path validation과 단일 Chrome target session이 유지된 채 완료됐다. |
| 3000ms | 2 | 2/2 PASS | 현재 local workload에서는 3초 outage까지 task completion이 유지됐다. |
| 4000ms | 2 | 2/2 PASS | 1MiB downlink/upload 모두 완료되어 local boundary의 하한을 4초까지 밀어 올렸다. |
| 5000ms | 2 | 2/2 FAIL | qlog H3/path evidence는 남았지만 DOM error timing이 기록되어 application completion은 실패했다. |
| 6000ms | 2 | 2/2 FAIL | qlog H3/path evidence가 남아도 DOM application completion은 false였다. |
| 9000ms | 2 | 2/2 FAIL | long outage는 permanent A+B loss와 같은 failure boundary를 보였다. |

해석:

- 이 sweep은 “CM이 된다/안 된다”가 아니라 outage duration과 application completion의 관계를 보여준다.
- 단일 sweep에서는 4초와 5초 사이에 local browser workload continuity boundary가 관찰됐다.
- PASS row의 DOM complete timing은 7545-11309ms였고, FAIL row의 DOM error timing은 6918-11122ms였다.
- public Wi-Fi/LTE handover claim으로 쓰려면 active client path change와 controlled public origin evidence가 추가로 필요하다.

[Chrome H3 Local Rebinding Transient Boundary Repetition](./chrome-h3-rebinding-transient-boundary-repetition-20260624.md)는 이 경계를 4000ms/4500ms/5000ms에서 각각 3회 반복했다.

| repeated window | downlink rows | upload rows | interpretation |
| ---: | --- | --- | --- |
| 4000ms | 3/3 PASS | 3/3 PASS | local 1MiB workload에서 stable PASS 영역으로 관찰됐다. |
| 4500ms | 3/3 PASS | 3/3 PASS | 4.5초 outage도 반복 실행에서는 downlink/upload 모두 완료됐다. |
| 5000ms | 3/3 PASS | 0/3 PASS | 5초는 단일 threshold가 아니라 workload-sensitive transition zone으로 갈렸다. |

반복 결과의 핵심:

- 전체 18개 row 중 15개가 완료됐고, 실패 3개는 모두 5000ms upload였다.
- 5초 downlink는 3/3 PASS였으므로 “5초부터 항상 실패”라고 표현하면 안 된다.
- 5초 upload 실패 row도 proxy switch와 qlog H3/path evidence를 남겼으므로, transport evidence와 application completion은 여전히 분리해야 한다.

[Chrome H3 Local Rebinding Downlink Fine Boundary](./chrome-h3-rebinding-transient-downlink-fine-boundary-20260624.md)는 downlink-only window를 5000ms/5500ms/6000ms로 세분화했다.

| downlink-only window | rows | status | interpretation |
| ---: | ---: | --- | --- |
| 5000ms | 3 | 2/3 PASS | downlink도 5초 근처에서 혼재 transition을 보였다. |
| 5500ms | 3 | 2/3 PASS | 더 긴 window에서도 PASS/FAIL이 갈려 단조 threshold가 아님을 보였다. |
| 6000ms | 3 | 0/3 PASS | 반복 실패 구간으로 관찰됐다. |

Downlink fine boundary의 핵심:

- 5000ms와 5500ms는 각각 2/3 PASS로 혼재했다.
- 6000ms는 3/3 FAIL이었다.
- PASS row는 12276-14114ms에 완료됐고, FAIL row는 6922-6927ms에 실패했다.
- 모든 row가 qlog H3/path evidence를 남겼으므로, downlink도 transport evidence와 DOM completion을 분리해야 한다.

[Chrome H3 Local Rebinding Transient Upload Fine Boundary](./chrome-h3-rebinding-transient-upload-fine-boundary-20260624.md)는 upload-only window를 4600ms/4750ms/4900ms/5000ms로 세분화했다.

| upload-only window | rows | status | interpretation |
| ---: | ---: | --- | --- |
| 4600ms | 3 | 3/3 PASS | local 1MiB upload의 stable completion 구간으로 관찰됐다. |
| 4750ms | 3 | 1/3 PASS | upload continuity가 이미 불안정해지는 transition 구간이다. |
| 4900ms | 3 | 0/3 PASS | 반복 실패 구간으로 들어섰다. |
| 5000ms | 3 | 0/3 PASS | broader boundary repetition의 upload 실패를 재현했다. |

Upload fine boundary의 핵심:

- upload 안정 완료 구간은 4600ms까지 관찰됐다.
- 4750ms부터 실패가 섞였고 4900ms 이상은 반복 실패했다.
- 실패 row의 DOM error timing은 6917-6922ms로 좁게 모였으며, 모든 실패 row에 qlog H3/path evidence가 남았다.

[Chrome H3 Local Rebinding Transient Upload Retry Boundary](./chrome-h3-rebinding-transient-upload-retry-boundary-20260624.md)는 같은 4900ms/5000ms failure region에서 upload page에 application-level retry를 1회 추가했다.

| retry condition | rows | status | browser session interpretation |
| --- | ---: | --- | --- |
| no retry, 4900ms/5000ms | 6 | 0/6 PASS | qlog H3/path evidence가 있어도 DOM upload는 실패했다. |
| one retry after 1000ms | 6 | 6/6 PASS | 작업 완료는 회복됐지만 Chrome target QUIC session은 모두 2개였다. |

Retry boundary의 핵심:

- application-level retry는 local upload failure region에서 사용자 작업 완료를 회복할 수 있다.
- 그러나 모든 retry PASS row가 `nat_rebinding_multiple_quic_sessions`였으므로, 이는 single-session browser CM success가 아니다.
- 논문에서는 "transport continuity", "browser session continuity", "application task recovery"를 별도 outcome으로 보고해야 한다.

[Chrome H3 Local Rebinding Transient Upload Retry Long Outage](./chrome-h3-rebinding-transient-upload-retry-long-outage-20260624.md)는 같은 retry strategy를 6000ms/9000ms로 확장했다.

Long-outage retry control의 핵심:

- 6000ms와 9000ms upload retry는 각각 3/3 PASS였다.
- 6000ms row는 약 15.5초, 9000ms row는 약 19.7초에 완료되어 recovery latency가 outage window와 함께 커졌다.
- Chrome target QUIC session count는 2-3개였으므로, long-outage retry도 browser CM success가 아니라 application-level recovery evidence다.

[Chrome H3 Local Rebinding Transient Upload Retry Stress Boundary](./chrome-h3-rebinding-transient-upload-retry-stress-boundary-20260624.md)는 one-retry strategy의 failure side를 확인했다.

Retry stress boundary의 핵심:

- 12000ms retry upload는 3/3 PASS였고 약 20.0초에 완료됐다.
- 15000ms retry upload는 3/3 FAIL이었고 DOM error timing은 15936-15943ms였다.
- 실패 row는 두 번째 `/upload-sink`가 서버에 도달하지 못했고 upload bytes가 0이었다.
- qlog H3/path evidence와 Chrome session evidence가 있어도 application retry recovery는 12-15초 사이에서 깨질 수 있다.

[Chrome H3 Local Rebinding Upload Retry2 15000ms Recovery](./chrome-h3-rebinding-transient-upload-retry2-15000ms-20260624.md)는 같은 15000ms failure region에서 retry budget을 2회로 늘려 재검수했다.

Retry2 15000ms recovery control의 핵심:

- 15000ms retry2 upload는 3/3 PASS였고 최종 1MiB body가 수신됐다.
- DOM complete timing은 24484-24503ms로 증가했다.
- Chrome target QUIC session count는 모두 4개였으므로, 이 결과는 browser single-session CM success가 아니라 higher-budget application recovery evidence다.
- 논문에서는 retry budget이 failure boundary를 오른쪽으로 밀 수 있지만, latency와 session churn cost를 동반한다고 표현한다.

[Chrome H3 Local Rebinding Upload Retry2 Stress Boundary](./chrome-h3-rebinding-transient-upload-retry2-stress-boundary-20260624.md)는 2회 retry strategy의 failure side를 18000ms/21000ms에서 확인했다.

Retry2 stress boundary의 핵심:

- 18000ms retry2 upload는 3/3 PASS였고 DOM complete timing은 28196-28199ms였다.
- 21000ms retry2 upload는 3/3 FAIL이었고 DOM error timing은 20950-20955ms였다.
- FAIL row에도 qlog H3/path evidence와 Chrome target QUIC session count 4가 남았지만, upload bytes는 0이었다.
- 2회 retry는 1회 retry보다 boundary를 오른쪽으로 밀지만, 이 local workload에서도 18-21초 사이에서 application continuity가 다시 깨진다.

[Application Recovery Tradeoff](./application-recovery-tradeoff-20260624.md)는 no-retry, 1회 retry, 2회 retry upload boundary CSV를 한 표로 합친다.

Application recovery tradeoff의 핵심:

- 최신 all-pass window는 no-retry 4600ms, 1회 retry 12000ms, 2회 retry 18000ms로 이동했다.
- 같은 지점의 DOM completion timing은 약 10.2초, 20.0초, 28.2초로 증가했다.
- Chrome target QUIC session count도 1개, 3개, 4개로 증가했다.
- 따라서 retry는 task completion을 개선하는 application strategy이지, browser single-session CM maturity의 대체 지표가 아니다.

[Workload Transition-Zone Synthesis](./workload-transition-zone-synthesis-20260624.md)는 downlink/upload fine-boundary control을 한 표로 합친다.

Workload transition-zone synthesis의 핵심:

- downlink는 5000ms/5500ms가 각각 2/3 PASS였고 6000ms는 0/3 PASS였다.
- upload는 4600ms가 3/3 PASS, 4750ms가 1/3 PASS, 4900ms/5000ms가 0/6 PASS였다.
- 따라서 local browser continuity boundary는 workload direction에 따라 달라진다.

## 5. 논문용 evidence chain

논문에서 browser-level HTTP/3 CM success를 주장하려면 최소 다음이 필요하다.

| 단계 | 필요한 evidence | 현재 상태 |
| --- | --- | --- |
| 1. Application H3 baseline | server request `HTTP/3.0`, TLS ALPN `h3`, qlog H3 frame, browser NetLog | local forced Chrome에서 관찰; controlled public origin은 pending |
| 2. 실제 client path 변화 | before/after route/interface/public IP 변화 | inactive toggle은 no-change; real active path pending |
| 3. 같은 logical QUIC connection 유지 | tuple change와 함께 qlog path validation, replacement session 아님 | quic-go controlled client에서 관찰; Chrome browser pending |
| 4. application task continuity | downlink/upload/polling task complete, manual refresh 없음 | local controls pass; retry can recover local upload failure via multiple sessions; public active path-change pending |
| 5. deployment continuity | LB/CDN/proxy가 changed tuple을 같은 logical backend로 유지 | AWS NLB TCP_QUIC positive/negative controls 있음; CDN pending |

machine-readable rubric은 [data/evidence-chain-rubric.csv](../../data/evidence-chain-rubric.csv)에 고정했다.

## 6. 연구 방향 결론

현재 연구는 “CM이 부족하니 개선하자”로 바로 가기보다, 다음 framing이 더 방어 가능하다.

> QUIC Connection Migration primitive는 구현체와 controlled deployment에서 작동하지만, browser/web application에서 CM success를 주장하려면 application H3 baseline, 실제 client path change, qlog path validation, browser session continuity, deployment routing continuity를 모두 확인해야 한다.

문헌상으로도 이 framing이 더 안전하다. ACM CCR 2025 wild-scan은 public support가 균등하지 않다는 사실을 보여주지만, 왜 어떤 endpoint가 실패하는지까지 완전히 분해하지는 않는다. 따라서 본 연구의 기여는 “CM 지원률 재측정”보다 “implementation, browser policy, deployment routing, application workload를 분리한 evidence-boundary methodology”에 두는 편이 좋다.

이 framing의 장점:

- 교수님 피드백의 “구현도 안 된 기술을 왜 안 쓰냐고 하면 안 된다”를 피한다.
- 구현체, browser policy, deployment routing, application workload를 계층별로 분리한다.
- 우리가 이미 만든 positive/negative control이 모두 논문에 쓰인다.

## 7. 다음 실험 우선순위

1. Controlled public WebPKI origin을 준비하고 Chrome application H3 baseline을 `PASS`로 만든다.
2. active secondary path를 준비한 뒤 CDP runner로 `WORKLOAD=downlink` no-heartbeat/heartbeat active path-change를 실행한다.
3. 같은 조건에서 polling interval을 바꿔 recovery detection delay를 비교한다.
4. Safari는 server qlog + packet capture + WebDriver result 중심으로 별도 evidence chain을 만든다.
5. Android Chrome/Cronet은 ADB device가 연결된 뒤 Wi-Fi/LTE handover로 확장한다.

현재 local 상태의 blockers:

| blocker | 현재 관찰 |
| --- | --- |
| secondary active path | `false`, active non-loopback IPv4는 `en0` 하나 |
| Android device | ADB device 없음 |
| AWS identity | caller identity unavailable |
| disk | 약 47.7 GiB free, 대형 packet capture 가능하지만 장시간 NetLog/qlog 반복 전 재확인 필요 |
