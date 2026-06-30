# HTTP/3/QUIC Connection Migration 연구 중간보고서

작성일: `2026-06-29`

이 문서는 교수님께 연구 방향 결정을 받기 위한 중간보고서다. 추가 실험을 더 진행하기 전에, 현재까지의 구현체 조사, 문헌 검토, AWS controlled public origin 실험, Chrome handover 실험 결과를 정리하고 다음 의사결정 지점을 명확히 한다.

이 보고서는 공개 저장소에 올릴 수 있도록 작성했다. AWS 계정, 인스턴스 ID, 공인 IP, hostname, SSH target, 로컬 네트워크 주소, 인증서 경로, credential 값은 포함하지 않는다.

## 1. 연구 질문의 현재 형태

초기 질문은 “HTTP/3 Connection Migration이 불안정한 모바일 환경에서 웹 작업 연속성을 보장하는가”였다. 그러나 조사와 실험을 진행하면서 이 질문은 그대로 쓰기 어렵다는 점이 확인되었다.

현재 더 방어 가능한 질문은 다음이다.

1. 주요 QUIC 구현체는 Connection Migration을 어느 정도 구현하고 검증 가능한가?
2. Chrome 같은 실제 브라우저 HTTP/3 환경에서 Wi-Fi에서 cellular path로 바뀔 때 single-session QUIC Connection Migration을 관찰할 수 있는가?
3. 브라우저 수준 CM이 관찰되지 않거나 불확실할 때, upload, download, Range resume, streaming 같은 웹 작업은 어떤 application-level recovery로 연속성을 회복하는가?

즉, 본 연구는 “CM이 무조건 된다/안 된다”를 증명하는 방향보다, `transport CM evidence`와 `user-visible task continuity`를 분리해서 평가하는 방향으로 이동했다.

## 2. 교수님 피드백 반영 상태

### 2.1 “CM이 왜 안 쓰이는가”에 대한 현재 답

현재 결론은 “기능이 아예 없어서 안 쓰인다”가 아니다. 표준과 구현체에는 CM primitive가 존재한다. 다만 실제 웹 서비스에서 user-visible continuity로 나타나려면 여러 계층이 동시에 맞아야 한다.

주요 friction은 다음과 같다.

| 계층 | 확인된 문제 |
| --- | --- |
| 구현체/런타임 | path validation, NAT rebinding, active migration primitive는 존재하지만 구현체와 기본 정책이 다르다. |
| 브라우저 | HTTP/3를 쓴다는 사실과 CM을 수행한다는 사실은 다르다. Chrome은 NetLog로 관찰성이 있지만, Safari/Android는 같은 수준의 session attribution이 어렵다. |
| 배포 경로 | Load balancer, proxy, CDN edge가 QUIC을 terminate하거나 CID-aware routing을 하지 않으면 end-to-end CM 의미가 약해진다. |
| 보안/운영 | CM은 5-tuple 기반 방화벽, NAT, rate limit, 모니터링, abuse detection 정책과 충돌할 수 있다. |
| 애플리케이션 | 많은 웹 작업은 retry, Range resume, buffering, reconnect로 복구되므로 transport CM 부재가 가려질 수 있다. |
| 측정 방법 | server tuple change, task completion, qlog path validation, browser session continuity가 각각 다른 의미를 가진다. 하나만으로 CM 성공이라고 말할 수 없다. |

따라서 논문에서는 `HTTP/3 지원 = CM 지원`으로 쓰면 안 된다. 또한 `task completion = QUIC CM success`로도 쓰면 안 된다.

### 2.2 구현체별 CM 성숙도 조사

구현체 조사는 총 18개 구현체를 대상으로 진행했다. Apple 구현체는 비공개이므로 제외했다.

조사 기준은 다음과 같다.

| Level | 의미 |
| --- | --- |
| L0 | CM 관련 근거 없음 |
| L1 | PATH_CHALLENGE/PATH_RESPONSE, CID, transport parameter 등 primitive 일부 확인 |
| L2 | NAT rebinding 또는 peer address change 처리 가능 |
| L3 | client가 의도적으로 migration을 시작할 수 있는 API 또는 내부 API 존재 |
| L4 | test, qlog, event, failure handling 등 검증 가능성 존재 |
| L5 | LB/CDN/cloud/production 배포 근거까지 존재 |

요약하면 다음과 같다.

| 구현체/스택 | 현재 판정 | 의미 |
| --- | --- | --- |
| quic-go | L4 | 명시적 path add/probe/switch와 qlog evidence를 갖춘 controlled positive control로 적합하다. |
| Cloudflare quiche | L4 | migration API와 PathEvent 관찰성이 좋고 local migration test가 가능하다. |
| picoquic | L4-L5 후보 | NAT rebinding, migration failure, preferred address 등 edge-case test가 풍부하다. |
| s2n-quic | L4, AWS L5 후보 | connection migration test와 AWS 배포 연구 연결성이 좋다. |
| ngtcp2 | L4 | RFC 구현체로 migration API와 path validation 근거가 있다. |
| Quinn | L3-L4 | UDP socket rebind와 path validation 테스트 근거가 있다. |
| Neqo | L4 | Mozilla 계열 QUIC stack으로 migration test가 많다. |
| aioquic | L2-L3 | passive path validation reference로 유용하나 active migration 주력 후보는 아니다. |
| mvfst | L5 후보 | 대규모 서비스 지향 구현체로 source-level migration 근거가 있다. |
| MsQuic | L4-L5 caveat | 운영체제/서버 환경에서 강하지만 배포 정책과 LB 구성이 중요하다. |
| lsquic | L4-L5 후보 | LiteSpeed 생태계에서 passive migration/NAT rebinding 근거가 있다. |
| nginx QUIC | L4 server runtime | 웹 서버 관점의 passive migration/path validation source 근거와 quiche active migration runtime demo 근거가 있다. |
| quicly | L3-L4 | path validation/promotion 근거가 있다. |
| XQUIC | L2-L4 | rebinding/path validation/preferred-address 계열 근거가 있다. |
| Chromium/Cronet | L4 client runtime | runtime policy와 NetLog 관찰성이 있으나 실제 Chrome browser CM 성공은 별도 실험이 필요하다. |
| HAProxy QUIC | L1-L2 | HTTP/3 proxy/load balancer 반례로 중요하다. 공식적으로 CM 지원을 넓게 말하기 어렵다. |

핵심 해석은 다음이다.

> QUIC CM은 구현체 수준에서는 “없는 기능”이 아니다. 그러나 브라우저, 배포 경로, 운영 정책, application recovery가 얽히기 때문에 실제 웹 작업 연속성으로 관찰하기 어렵다.

## 3. AWS controlled public origin 구축 결과

교수님 피드백 중 “AWS 환경에서 실제로 구축해서 CM이 제대로 동작하는지 검수”하라는 요구에 대응하기 위해 controlled public origin을 새로 구축했다.

구축 결과:

| 항목 | 결과 |
| --- | --- |
| Cloud | AWS EC2 |
| Region | Seoul region |
| Instance | small general-purpose instance |
| Server | quic-go HTTP/3 harness |
| TLS | WebPKI certificate |
| Chrome smoke trial | PASS |
| Application H3 baseline | PASS |
| Server-side H3 evidence | confirmed |

이 단계의 의미는 “실험 인프라가 public browser HTTP/3를 받을 수 있다”는 것이다. 이 자체가 CM 성공을 의미하지는 않는다. 하지만 active handover 실험을 수행하기 위한 baseline gate는 통과했다.

## 4. Chrome + iPhone USB handover 실험 결과

현재 가장 중요한 실험은 macOS Chrome에서 Wi-Fi를 끄고 iPhone USB cellular path로 넘어가게 만든 controlled public handover 실험이다.

실험 해석 기준은 다음과 같이 분리했다.

| Evidence | 의미 |
| --- | --- |
| Application HTTP/3 | 대상 웹 요청이 실제 HTTP/3로 수행되었는가 |
| Client path change | 클라이언트의 active network path가 바뀌었는가 |
| Server tuple change | 서버가 다른 remote tuple을 보았는가 |
| qlog path validation | QUIC PATH_CHALLENGE/PATH_RESPONSE 등 path validation 근거가 있는가 |
| Browser session continuity | 같은 browser QUIC session이 유지되었는가 |
| Task completion | 사용자 작업이 완료되었는가 |

CM 성공을 주장하려면 위 항목이 같은 row에서 함께 맞아야 한다. 현재 Chrome public handover 결과는 그 기준을 만족하지 못했다.

### 4.1 Full-response downlink

단일 긴 response stream을 받는 workload다. Range resume이나 retry 없이 하나의 fetch/read stream이 살아남아야 한다.

| 조건 | 반복 | 결과 | qlog path validation | 작업 완료 |
| --- | ---: | --- | --- | --- |
| no-change baseline | 1 | PASS | false, 정상 baseline | 1/1 |
| Wi-Fi to iPhone USB | 2 | PASS_NEGATIVE_CONTROL | false | 0/2 |

해석:

- active path change는 관찰되었다.
- 그러나 qlog path validation은 관찰되지 않았다.
- full-response downlink는 active handover에서 두 번 모두 실패했다.
- 따라서 이 결과는 Chrome browser-level CM 성공이 아니라, `application_task_failed_without_quic_path_validation`으로 해석해야 한다.

### 4.2 Byte-range download, retry 없음

Range 기반 다운로드지만 retry budget을 0으로 둔 조건이다.

| 조건 | 반복 | 결과 | qlog path validation | 작업 완료 |
| --- | ---: | --- | --- | --- |
| no-change baseline | 1 | PASS | false, 정상 baseline | 1/1 |
| Wi-Fi to iPhone USB | 2 | PASS_NEGATIVE_CONTROL | false | 0/2 |

해석:

- no-change에서는 정상 완료된다.
- active handover에서는 모두 중간 실패한다.
- retry가 없으면 Range 구조만으로는 작업 연속성을 보장하지 못했다.

### 4.3 Byte-range download, retry budget 2

동일한 Range workload에 retry budget을 2로 둔 조건이다.

| 조건 | 반복 | 결과 | qlog path validation | 작업 완료 |
| --- | ---: | --- | --- | --- |
| no-change baseline | 1 | PASS | false, 정상 baseline | 1/1 |
| Wi-Fi to iPhone USB | 3 | PASS_NEGATIVE_CONTROL mixed | false in all runs | 2/3 |

세부 해석:

- 성공한 active row 2개는 한 번의 fetch 실패 후 남은 Range를 다시 받아 전체 작업을 완료했다.
- 서버는 target H3 remote tuple이 바뀐 것을 관찰했다.
- 그러나 qlog path validation은 관찰되지 않았다.
- 따라서 성공 원인은 browser single-session CM이 아니라 application-level Range retry/recovery로 해석해야 한다.

이 결과는 논문에서 매우 중요하다. 같은 path-change 조건에서 transport CM 증거는 없지만, workload semantics와 retry budget에 따라 user-visible task completion이 달라졌다.

### 4.4 Upload workload

Upload no-change baseline은 PASS로 확인되었다. 그러나 active network-change upload row는 실행 중 중단되어 server artifact가 누락되었고, 현재 countable result로 쓰면 안 된다.

| 조건 | 결과 | 논문 사용 |
| --- | --- | --- |
| upload no-change baseline | PASS | baseline record로 사용 가능 |
| upload active handover | server artifact missing | 실패 원인 분석 또는 final claim에는 사용 금지 |

따라서 upload는 다음 의사결정 이후 반복해야 할 우선 실험이다.

## 5. Streaming/Media workload에 대한 현재 판단

사용자 관점에서는 CM이 streaming에서 중요해 보일 수 있다. 그러나 실험과 분석 결과, streaming은 오히려 가장 조심해서 다뤄야 한다.

이유는 다음과 같다.

| workload | 특징 |
| --- | --- |
| 동영상/VOD | segment fetch와 buffer가 transport failure를 숨길 수 있다. 완료 여부만 보면 CM처럼 보일 수 있다. |
| 음악 | 작은 segment와 긴 buffer가 있으면 disruption을 숨기지만, low-bitrate/small segment no-retry 조건에서는 반복 실패도 가능했다. |
| live/low-latency media | startup delay, rebuffer, segment retry, session churn을 함께 봐야 한다. |
| 대용량 업로드/다운로드 | 단일 작업 실패가 사용자에게 직접 보이므로 CM 또는 recovery 필요성이 가장 직접적으로 드러난다. |

따라서 streaming은 중요한 후속 장이지만, 논문 중심 claim으로 바로 세우기보다는 upload/download/Range로 먼저 CM과 application recovery를 분리한 뒤 확장하는 편이 안전하다.

## 6. 현재까지의 결론

현재 결과로 강하게 말할 수 있는 내용은 다음이다.

1. QUIC Connection Migration은 RFC와 구현체 수준에서 존재하는 기능이다.
2. 주요 구현체 다수는 path validation, NAT rebinding, active/passive migration, qlog/event/test를 제공한다.
3. 하지만 실제 브라우저 HTTP/3 handover에서 CM 성공을 주장하려면 application H3, client path change, server tuple, qlog path validation, browser session continuity, task completion을 같은 실험 row에서 보여야 한다.
4. 현재 macOS Chrome + controlled public origin + iPhone USB handover 실험에서는 browser-level single-session CM 성공 증거를 관찰하지 못했다.
5. full-response downlink와 retry 없는 Range download는 active handover에서 실패했다.
6. retry가 있는 Range download는 3회 중 2회 사용자 작업을 완료했지만, 이는 QUIC CM 성공이 아니라 application-level recovery로 해석해야 한다.
7. 따라서 “HTTP/3 CM이 웹 작업 연속성을 보장한다”는 표현은 현재 증거로는 과하다.

현재 결과로 말하면 안 되는 내용은 다음이다.

1. Chrome이 Wi-Fi에서 iPhone USB/cellular로 바뀌는 동안 원래 HTTP/3 connection을 성공적으로 migration했다.
2. HTTP/3를 지원하는 서버나 CDN은 CM을 지원한다.
3. Range retry로 다운로드가 완료되었으므로 QUIC CM이 성공했다.
4. streaming이 완료되었으므로 CM이 media continuity를 보장한다.
5. Mac+iPhone USB failover가 모든 모바일 handover를 대표한다.

## 7. 논문 방향 제안

현재 가장 방어 가능한 논문 방향은 다음이다.

### 제안 제목

한국어:

> HTTP/3/QUIC Connection Migration의 구현 성숙도와 웹 작업 연속성: Chrome 공용 Origin Handover 및 Application Recovery 분석

영어:

> Implementation Maturity and Web Task Continuity of HTTP/3/QUIC Connection Migration: A Controlled Chrome Handover and Application Recovery Study

### 제안 연구 질문

RQ1. 주요 QUIC 구현체와 배포 스택은 Connection Migration을 어떤 수준까지 구현하고 관찰 가능하게 제공하는가?

RQ2. controlled public origin과 실제 Chrome browser handover 환경에서 single-session QUIC Connection Migration evidence를 관찰할 수 있는가?

RQ3. browser-level CM evidence가 없거나 불확실한 경우, upload, download, Range resume, streaming workload의 user-visible continuity는 application-level recovery 전략에 따라 어떻게 달라지는가?

### 핵심 기여로 만들 수 있는 것

| Contribution | 내용 |
| --- | --- |
| CM maturity audit | 구현체별 CM 지원, API, test, qlog/event, deployment caveat 정리 |
| Evidence chain | browser CM 성공을 주장하기 위한 계층별 증거 기준 제안 |
| Controlled public handover result | Chrome + public quic-go origin + iPhone USB handover에서 negative/control 결과 제시 |
| Workload recovery taxonomy | full-response, Range retry, upload, media에서 transport CM과 application recovery를 분리 |
| Practical guidance | 개발자/운영자가 HTTP/3 CM을 기대할 때 어떤 조건과 한계를 확인해야 하는지 제시 |

## 8. 교수님께 받을 의사결정

다음 단계로 넘어가기 전에 교수님께 아래 결정을 받는 것이 좋다.

1. 논문 방향을 `CM 성공 증명`이 아니라 `CM 구현 성숙도와 browser/web workload evidence chain`으로 잡아도 되는가?
2. Chrome에서 single-session CM 성공이 아직 관찰되지 않은 결과를 negative finding으로 논문에 포함해도 되는가?
3. application-level Range retry/recovery 결과를 “CM의 대체재 또는 보완재”로 논문 중심 기여에 포함해도 되는가?
4. 후속 실험의 우선순위를 upload/download/Range에 둘지, streaming/Safari/Android까지 확장할지 결정이 필요한가?
5. Safari는 browser-internal QUIC session evidence가 약하므로 `feasibility/supporting row`로만 다뤄도 되는가?
6. Android Chrome/Cronet은 실제 mobile browser claim을 위해 추가해야 하는가, 아니면 본 논문에서는 future work로 남길 것인가?

## 9. 의사결정 이후 추천 작업

교수님이 현재 방향을 승인한다면 다음 순서로 진행한다.

1. Upload active handover를 다시 실행해서 countable row를 만든다.
2. Range retry public handover를 추가 반복해 sample size를 늘린다.
3. streaming/media는 completion뿐 아니라 startup delay, rebuffer, retry count, session churn을 측정하는 QoE row로 설계한다.
4. Safari는 `PASS_FEASIBILITY` 수준으로만 비교하고, Android Chrome/Cronet은 장비/ADB/logging 경로가 준비될 때 별도 장으로 둔다.
5. 논문 본문은 “구현체 성숙도 -> 측정 방법론 -> controlled public handover -> workload recovery taxonomy -> 한계와 실무적 시사점” 순서로 구성한다.

## 10. 현재 보고 가능한 한 문장 결론

현재까지의 연구 결과는 QUIC Connection Migration이 표준과 구현체 수준에서는 충분히 실재하지만, 실제 브라우저 HTTP/3 웹 작업에서 이를 user-visible continuity로 관찰하려면 훨씬 강한 evidence chain이 필요함을 보여준다. Chrome controlled public handover 실험에서는 single-session CM 성공을 관찰하지 못했고, 대신 Range retry 같은 application-level recovery가 작업 완료 여부를 바꿀 수 있음을 확인했다.

## 관련 산출물

- `docs/results/cm-operational-friction-matrix-20260624.md`
- `docs/results/browser-cm-observability-matrix-20260624.md`
- `docs/results/literature-claim-positioning-20260629.md`
- `docs/results/aws-ec2-refresh-origin-20260629.md`
- `docs/results/controlled-public-full-downlink-iphone-usb-handover-20260629.md`
- `docs/results/controlled-public-range-retry-iphone-usb-handover-20260629.md`
- `docs/results/streaming-workload-case-analysis-20260629.md`
