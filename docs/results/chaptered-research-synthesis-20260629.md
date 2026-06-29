# QUIC Connection Migration 연구 챕터별 종합 정리

작성일: `2026-06-29`

목적: 지금까지 수행한 QUIC Connection Migration 연구를 챕터별로 정리한다. 각 챕터는 `이전 챕터의 결과 -> 새 질문 -> 수행한 조사/실험 -> 결과 -> 다음 챕터로 넘어간 이유`의 흐름을 따른다. 이 문서는 교수님께 연구 방향을 설명하고, 논문 본문 구조를 잡기 위한 중간 종합본이다.

공개 안전성: 이 문서는 AWS 계정, 인스턴스 ID, 공인 IP, hostname, SSH target, 인증서 경로, credential, 로컬 네트워크 주소를 포함하지 않는다.

## 전체 연구 흐름

현재 연구는 다음 흐름으로 진행되었다.

| 순서 | 챕터 | 핵심 질문 | 다음 챕터로 넘어간 이유 |
| ---: | --- | --- | --- |
| 1 | Connection Migration 성숙도 조사 | CM은 실제 QUIC 구현체에 구현되어 있는가? | 구현체에는 primitive가 있으므로, 왜 실제 웹에서는 잘 보이지 않는지 물어야 했다. |
| 2 | CM이 덜 쓰이는 이유 분석 | 구현체가 있는데도 왜 배포/브라우저에서 잘 보이지 않는가? | 원인이 여러 계층에 있으므로 controlled positive control이 필요했다. |
| 3 | 구현체 positive control | 통제된 QUIC client/server에서는 CM이 실제로 되는가? | 라이브러리 성공을 브라우저 성공으로 일반화할 수 없어서 배포 경로를 봐야 했다. |
| 4 | 배포 경로와 LB/CDN 검수 | CID-aware routing 또는 edge termination은 CM 해석을 어떻게 바꾸는가? | 배포 계층을 통제한 뒤 실제 브라우저 evidence chain이 필요했다. |
| 5 | 브라우저 관찰성 기준 | Chrome/Safari/Android에서 CM을 어떻게 검증할 수 있는가? | Chrome은 관찰 가능성이 있어 실제 handover 실험 대상으로 적합했다. |
| 6 | 로컬 Chrome NAT rebinding control | 브라우저가 local rebinding에서는 path validation/복구를 보이는가? | local control은 강하지만 실제 Wi-Fi/cellular handover가 아니므로 public origin 실험이 필요했다. |
| 7 | AWS controlled public origin | 실제 Chrome이 접근하는 public HTTP/3 origin을 만들 수 있는가? | baseline이 확보되었으므로 active path-change 실험을 실행할 수 있었다. |
| 8 | Full-response downlink handover | 단일 긴 response stream은 path change 중 살아남는가? | 실패가 관찰되어, resumable workload와 비교할 필요가 생겼다. |
| 9 | Range download/retry handover | byte-range retry는 작업 연속성을 회복하는가? | recovery는 되었지만 CM은 아니어서 workload taxonomy가 필요해졌다. |
| 10 | Upload workload | 업로드는 CM/retry 필요성이 어떻게 드러나는가? | no-change baseline은 있으나 active row가 부족해 후속 우선순위로 남았다. |
| 11 | Streaming/media workload | video/music은 CM 연구의 중심 use case가 될 수 있는가? | completion만으로는 오해가 커서 QoE metric과 session attribution이 필요했다. |
| 12 | 문헌과 claim positioning | 기존 연구와 비교해 어떤 주장이 방어 가능한가? | 논문 방향을 success proof가 아니라 maturity/evidence-chain 연구로 잡아야 했다. |
| 13 | 현재 결론과 다음 의사결정 | 지금까지 결과로 무엇을 말할 수 있고, 무엇은 못 말하는가? | 교수님께 방향 결정을 받은 뒤 남은 실험을 선택해야 한다. |

## Chapter 1. Connection Migration 성숙도 조사

### 1.1 이전 상태

초기 교수님 피드백의 핵심은 “Connection Migration이 왜 안 쓰이는지 알려면, 먼저 구현체에 실제로 구현되어 있는지 확인해야 한다”는 것이었다. 따라서 첫 챕터의 질문은 매우 단순했다.

> QUIC Connection Migration은 실제 구현체에 구현되어 있는가?

### 1.2 조사 방법

조사는 두 단계로 수행했다.

| 방법 | 대상 | 확인 항목 |
| --- | --- | --- |
| 소스/문서 검수 | mvfst, MsQuic, lsquic, nginx QUIC, quicly, XQUIC, Chromium/Cronet, HAProxy 등 | migration API, path validation, NAT rebinding, preferred address, qlog/event, test, 운영 문서 |
| 로컬 실행 검수 | quic-go, Cloudflare quiche, picoquic, s2n-quic, aioquic, ngtcp2, Quinn, Neqo | migration test, sample client/server, custom reproduction, qlog/path event |

Apple QUIC stack은 비공개 성격이 강하므로 구현체 성숙도 matrix에서는 제외했다.

### 1.3 성숙도 기준

| Level | 의미 |
| --- | --- |
| L0 | CM 관련 근거 없음 |
| L1 | PATH_CHALLENGE/PATH_RESPONSE, CID, transport parameter 등 primitive 일부 확인 |
| L2 | NAT rebinding 또는 peer address change 처리 가능 |
| L3 | client active migration API 또는 명확한 내부 API 존재 |
| L4 | test, qlog, event, failure handling 등 검증 가능성 존재 |
| L5 | LB/CDN/cloud/production 배포 근거까지 존재 |

### 1.4 주요 결과

| 구현체/스택 | 현재 판정 | 연구상 의미 |
| --- | --- | --- |
| quic-go | L4 | explicit path add/probe/switch와 qlog evidence가 있어 controlled positive control에 적합하다. |
| Cloudflare quiche | L4 | path event와 migration API가 명확해 quic-go와 교차 검증 후보가 된다. |
| picoquic | L4-L5 후보 | NAT rebinding, failed migration, preferred address 등 edge-case test가 풍부하다. |
| s2n-quic | L4, AWS L5 후보 | AWS/NLB 배포 경로 연구와 연결하기 좋다. |
| ngtcp2 | L4 | RFC QUIC 구현체 비교군으로 적합하다. |
| Quinn | L3-L4 | Rust async application stack 후보로 볼 수 있다. |
| Neqo | L4 | Mozilla 계열 QUIC stack이며 migration test가 풍부하다. |
| aioquic | L2-L3 | Python 기반 분석/프로토타입 및 passive validation reference로 적합하다. |
| mvfst | L5 후보 | 대규모 서비스/데이터센터 지향 구현체로 production 후보군이다. |
| MsQuic | L4-L5 caveat | 운영 환경 친화적이나 runtime/deployment policy가 중요하다. |
| lsquic | L4-L5 후보 | LiteSpeed ecosystem과 연결되는 server-side 후보군이다. |
| nginx QUIC | L3-L4 | 실제 웹 서버 관점의 passive migration 검수 대상이다. |
| quicly | L3-L4 | H2O 계열 server stack 비교군이다. |
| XQUIC | L2-L4 | rebinding/path validation/preferred-address 근거가 있다. |
| Chromium/Cronet | L4 client runtime | browser runtime policy와 NetLog 관찰성이 핵심이다. |
| HAProxy QUIC | L1-L2 | HTTP/3 proxy 지원이 CM 지원을 의미하지 않는 반례로 중요하다. |

### 1.5 챕터 결론

CM은 “애초에 구현도 안 된 기술”이 아니다. 여러 구현체가 path validation, NAT rebinding, active/passive migration, qlog/event/test를 제공한다. 다만 구현체마다 default policy, API 공개 수준, production 배포 경로, 관찰성이 다르다.

### 1.6 다음 챕터로 넘어간 이유

구현체에 기능이 존재한다면 다음 질문은 “그런데 왜 웹에서는 잘 안 보이는가?”가 된다. 따라서 Chapter 2에서는 underuse/deployment friction을 분석했다.

근거 문서:

- `docs/results/local-implementation-test-results.md`
- `docs/results/professor-decision-brief-20260629.md`
- `docs/results/cm-operational-friction-matrix-20260624.md`

## Chapter 2. 성숙도 조사 결과를 바탕으로 본 CM 미사용/저가시성 원인

### 2.1 새 질문

> CM primitive가 있는데도 왜 실제 웹 브라우저나 서비스에서는 CM이 잘 보이지 않는가?

### 2.2 분석 방법

성숙도 조사 결과, 실험 corpus, 문헌 tracker를 함께 묶어 friction matrix를 만들었다. friction은 한 가지 원인으로 환원하지 않고 구현체, 브라우저, 네트워크, 배포 경로, 보안, application workload, 관찰성 계층으로 나눴다.

### 2.3 주요 friction

| 계층 | friction | 의미 |
| --- | --- | --- |
| 구현체/정책 | CM primitive는 있지만 implementation/runtime policy가 다르다. | API가 있어도 기본 브라우저 정책이 migration을 하지 않을 수 있다. |
| HTTP/3 discovery | application request가 실제 H3로 갔는지 먼저 증명해야 한다. | Alt-Svc나 H3 capability만으로는 CM 실험이 아니다. |
| active path proof | interface toggle이 실제 active path를 바꾸지 않을 수 있다. | route/interface/public path 변화 증거가 필요하다. |
| session attribution | tuple 변화는 replacement session일 수 있다. | server remote tuple 증가만으로 CM이라고 말할 수 없다. |
| CID-aware LB | load balancer는 tuple 변화 후에도 같은 backend로 보내야 한다. | 5-tuple 기반 라우팅은 migration packet을 다른 backend로 보낼 수 있다. |
| proxy/CDN | HTTP/3 proxy나 CDN edge는 end-to-end CM을 끊을 수 있다. | edge-level continuity와 origin end-to-end CM을 구분해야 한다. |
| middlebox | CM은 firewall/NAT/rate-limit의 5-tuple 가정을 흔든다. | 운영자가 보수적으로 설정할 수 있다. |
| security | preferred address, path migration은 abuse/security concern을 만든다. | 무조건 활성화하기 어려운 운영상 이유가 있다. |
| application workload | retry, Range resume, buffering이 transport failure를 숨길 수 있다. | task completion은 CM success가 아니다. |
| observability | qlog, NetLog, request log, route snapshot이 각각 다른 layer를 본다. | combined evidence chain이 필요하다. |

### 2.4 챕터 결론

“CM이 왜 안 쓰이는가?”의 현재 답은 “구현이 없어서”가 아니라 다음에 가깝다.

> QUIC CM은 transport primitive로 존재하지만, 브라우저 runtime policy, endpoint discovery, client path change, session attribution, CID-aware routing, proxy/CDN termination, middlebox policy, application recovery가 모두 맞아야 user-visible continuity로 나타난다.

### 2.5 다음 챕터로 넘어간 이유

원인이 여러 계층에 있다면, 가장 먼저 해야 할 일은 “통제된 환경에서는 CM이 진짜 되는가?”를 positive control로 확인하는 것이다. 그래서 Chapter 3에서는 quic-go/quiche 등 구현체 positive control을 정리했다.

근거 문서:

- `docs/results/cm-operational-friction-matrix-20260624.md`
- `docs/results/literature-claim-positioning-20260629.md`
- `docs/paper/cm-underuse-and-deployment-friction-ko-20260629.md`

## Chapter 3. 구현체 Positive Control 연구 결과

### 3.1 새 질문

> 브라우저와 복잡한 배포 계층을 제거한 controlled QUIC client/server에서는 CM이 실제로 동작하는가?

### 3.2 수행한 검수

대표적으로 다음 구현체에서 직접 실행 또는 source/test 검수를 수행했다.

| 구현체 | 확인한 내용 | 결과 |
| --- | --- | --- |
| quic-go | AddPath -> Probe -> Switch, before/after payload, qlog PATH_CHALLENGE/PATH_RESPONSE | PASS |
| quiche | migration library tests, sample client/server, PathEvent, qlog | PASS |
| picoquic | NAT rebinding, migration, migration failure, preferred address, disabled migration 등 13개 test | PASS |
| s2n-quic | connection_migration test, IP/port rebinding, blocked migration, zero-length CID | PASS |
| ngtcp2/Quinn/Neqo/aioquic | path validation, rebinding, migration tests/API | 근거 확인 |

### 3.3 핵심 결과

controlled implementation에서는 다음이 가능했다.

- path validation evidence 수집
- source port/path 변경
- 같은 connection 또는 같은 controlled migration flow에서 before/after payload 전달
- qlog/event/log 기반 검증
- 실패 조건의 명확한 분류

### 3.4 챕터 결론

이 결과는 “CM primitive가 실제 구현체에서 동작한다”는 positive control이다. 그러나 이것은 browser HTTP/3 handover 성공을 의미하지 않는다. CLI/library client는 browser policy, fetch lifecycle, service worker, network stack policy, OS route change, CDN/LB를 포함하지 않는다.

### 3.5 다음 챕터로 넘어간 이유

구현체 positive control이 확보되었으므로, 다음은 production-like deployment path다. 특히 load balancer가 tuple 변화 후에도 같은 backend로 라우팅할 수 있는지가 중요하다.

근거 문서:

- `docs/results/local-implementation-test-results.md`
- `docs/results/quic-go-minimum-reproduction-results.md`
- `docs/results/professor-decision-brief-20260629.md`

## Chapter 4. 배포 경로 연구: AWS NLB, proxy, CDN 해석

### 4.1 새 질문

> CM이 transport library에서는 되더라도, 실제 배포 경로의 LB/CDN/proxy는 이를 보존하는가?

### 4.2 AWS NLB HTTP/3 workload 결과

AWS NLB `TCP_QUIC` 경로에서 QUIC-LB plaintext CID 기반 same-target routing을 검수했다.

결과 요약:

| 항목 | 결과 |
| --- | --- |
| workload | HTTP/3 |
| before task | POST upload |
| migration | active source-port migration |
| after task | GET download |
| same target continuity | PASS |
| qlog path validation | observed |
| 의미 | CID-aware deployment path에서는 post-migration HTTP/3 request continuity가 가능했다. |

중요한 boundary:

- 이것은 controlled client와 AWS NLB 조건에서의 deployment positive control이다.
- mid-flight upload/download survival은 별도 실험이 필요하다.
- Chrome browser handover success로 일반화하면 안 된다.

### 4.3 proxy/CDN 해석

HAProxy, CloudFront/Cloudflare 같은 관리형 edge/CDN은 HTTP/3를 지원하더라도 end-to-end QUIC CM과 다를 수 있다.

| 배포 유형 | 해석 |
| --- | --- |
| direct origin | browser-origin 사이의 QUIC path evidence를 직접 볼 수 있다. |
| CID-aware LB | tuple 변화 후 같은 backend로 가는지 확인해야 한다. |
| reverse proxy | proxy가 QUIC을 terminate하면 origin까지의 CM은 끊긴다. |
| CDN edge | viewer-edge continuity일 수 있으며 origin end-to-end CM이 아니다. |

### 4.4 챕터 결론

배포 경로는 CM 성숙도에서 독립 변수다. 구현체가 CM을 지원해도 LB가 CID-aware routing을 하지 못하면 실패할 수 있고, CDN이 edge에서 QUIC을 끝내면 end-to-end CM claim을 할 수 없다.

### 4.5 다음 챕터로 넘어간 이유

구현체와 배포 positive control을 확보한 뒤에도 실제 논문의 중심은 browser web application이다. 따라서 브라우저에서 어떤 증거가 있어야 CM이라고 말할 수 있는지 기준을 세워야 했다.

근거 문서:

- `docs/results/aws-nlb-http3-workload-results-20260624.md`
- `docs/results/aws-nlb-quic-data-plane-results-20260624.md`
- `docs/results/haproxy-http3-negative-control-results-20260623.md`
- `docs/results/cm-operational-friction-matrix-20260624.md`

## Chapter 5. 브라우저 CM 관찰성 기준

### 5.1 새 질문

> Chrome, Safari, Android Chrome에서 browser-level CM을 어떤 evidence로 검증할 수 있는가?

### 5.2 Browser observability matrix

| 대상 | 자동화/관찰성 | session continuity 판정 | 현재 claim ceiling |
| --- | --- | --- | --- |
| Chrome desktop | CDP + Chrome NetLog | 가능 | controlled public active row가 충족되면 countable 후보 |
| Android Chrome | ADB + Cronet/Chrome logging 필요 | 미확정 | logging path 확보 전에는 not countable |
| Safari macOS | safaridriver 가능, NetLog equivalent 없음 | 제한적 | server/qlog/pcap 중심 PASS_FEASIBILITY |
| Safari iOS | Appium/rvictl/remote capture 필요 | 현재 불가 | not countable |
| quic-go controlled client | client state + qlog | 가능 | browser claim이 아니라 implementation positive control |

### 5.3 CM 성공 row에 필요한 evidence chain

브라우저에서 CM 성공을 주장하려면 최소한 다음이 같은 row에 있어야 한다.

| Evidence | 필요한 이유 |
| --- | --- |
| Application HTTP/3 | 대상 workload가 실제 HTTP/3로 갔는지 확인 |
| Client active path change | 네트워크 전환이 실제로 발생했는지 확인 |
| Server tuple change 또는 path evidence | 서버 관점에서 path 변화가 있었는지 확인 |
| qlog path validation | QUIC transport path validation 여부 확인 |
| Browser session continuity | replacement session이 아니라 같은 session인지 확인 |
| Task completion | 사용자 작업이 완료되었는지 확인 |

### 5.4 챕터 결론

Chrome desktop은 현재 가장 좋은 browser target이다. NetLog로 browser-internal QUIC session evidence를 볼 수 있기 때문이다. Safari와 Android는 가치가 있지만, 현재 harness에서는 Chrome 수준의 session attribution이 부족하다.

### 5.5 다음 챕터로 넘어간 이유

Chrome이 가장 계측 가능한 대상이라면, 먼저 로컬에서 Chrome이 path validation/rebinding을 보이는지 확인해야 했다. 그래서 Chapter 6에서 local forced-H3 NAT rebinding control을 수행했다.

근거 문서:

- `docs/results/browser-cm-observability-matrix-20260624.md`
- `docs/results/evidence-chain-and-gap-synthesis-20260624.md`

## Chapter 6. Local Chrome NAT Rebinding Control

### 6.1 새 질문

> 실제 Wi-Fi/cellular handover 이전에, Chrome forced-H3가 local UDP rebinding 상황에서 path validation과 task completion을 보이는가?

### 6.2 수행한 실험

로컬 UDP rebinding proxy를 두고 Chrome forced-H3 workload를 실행했다. 이 실험은 public Wi-Fi/cellular handover가 아니라 local NAT rebinding control이다.

주요 workload:

- downlink forced-H3
- streaming upload
- old-path-drop
- transient return-path outage
- timeout/retry sweep
- Range download control
- media segment control

### 6.3 Upload local rebinding 결과

| 항목 | 결과 |
| --- | --- |
| runs | 3 |
| status | 3/3 PASS |
| upload bytes | 각 262144 bytes |
| Chrome QUIC sessions | 1 in each run |
| proxy packet rebinding | true in every run |
| qlog PATH_CHALLENGE/PATH_RESPONSE | observed |
| NetLog path frames | observed |

해석:

- Chrome forced-H3는 local NAT rebinding 중 upload task를 완료할 수 있었다.
- request-level remote tuple만 보면 rebinding이 보이지 않을 수 있다.
- qlog, proxy packet log, NetLog를 함께 봐야 한다.

### 6.4 Transient outage/timing 결과

로컬 return-path outage sweep은 application completion과 transport evidence가 다르다는 점을 보여줬다.

| drop window | 결과 해석 |
| ---: | --- |
| 짧은 outage | downlink/upload completion 유지 |
| 4초 전후 | local workload가 대체로 버팀 |
| 5초 이상 | workload별 transition zone. upload는 더 취약하게 나타남 |

핵심은 “path validation evidence가 있어도 application completion은 실패할 수 있고, application completion이 있어도 single-session CM이라고 단정할 수 없다”는 점이다.

### 6.5 챕터 결론

local control은 Chrome이 QUIC path validation/rebinding 관련 transport behavior를 보일 수 있음을 보여준다. 그러나 local proxy 기반 NAT rebinding은 실제 OS route change, Wi-Fi/cellular failover, public origin, WebPKI, CDN/LB를 포함하지 않는다.

### 6.6 다음 챕터로 넘어간 이유

local control만으로는 논문에서 원하는 “실제 브라우저 + public origin + real path change” claim을 만들 수 없다. 따라서 AWS controlled public origin을 구축하고 active path-change 실험으로 넘어갔다.

근거 문서:

- `docs/results/chrome-h3-rebinding-upload-summary-20260624.md`
- `docs/results/chrome-h3-rebinding-range-download-control-20260629.md`
- `docs/results/evidence-chain-and-gap-synthesis-20260624.md`

## Chapter 7. AWS Controlled Public Origin 구축 및 H3 Baseline

### 7.1 새 질문

> 실제 Chrome이 WebPKI HTTPS origin으로 접근하는 controlled public HTTP/3 실험 환경을 만들 수 있는가?

### 7.2 구축 결과

| 항목 | 결과 |
| --- | --- |
| cloud | AWS EC2 |
| server | quic-go HTTP/3 harness |
| TLS | WebPKI certificate |
| Chrome smoke trial | PASS |
| application H3 baseline | PASS |
| server H3 evidence | confirmed |
| remote service after smoke | inactive |

### 7.3 의미

이 결과는 active handover 실험의 baseline gate를 통과했다는 뜻이다. 즉 Chrome이 controlled public origin에 HTTP/3로 접속하고, server artifact로 이를 확인할 수 있었다.

### 7.4 챕터 결론

public controlled origin은 구축되었고, no-change smoke baseline은 성공했다. 따라서 이후 active Wi-Fi-to-iPhone-USB handover 실험이 countable row가 될 수 있는 환경이 마련되었다.

### 7.5 다음 챕터로 넘어간 이유

baseline이 확보되었으므로, 가장 취약하고 해석이 쉬운 workload인 full-response downlink부터 active handover를 수행했다.

근거 문서:

- `docs/results/aws-ec2-refresh-origin-20260629.md`
- `docs/results/controlled-public-chrome-fresh-origin-smoke-20260629-005-validation.md`

## Chapter 8. Full-Response Downlink Public Handover 결과

### 8.1 새 질문

> 하나의 긴 HTTP/3 response stream은 Wi-Fi에서 iPhone USB path로 바뀌는 동안 살아남는가?

### 8.2 실험 설계

| 항목 | 값 |
| --- | --- |
| client | macOS Chrome |
| secondary path | iPhone USB |
| origin | fresh controlled public EC2 origin |
| workload | GET `/browser-downlink`, GET `/downlink-stream` |
| stream duration | 15000ms |
| retry budget | 0 |
| active trigger | downlink bytes가 관찰된 뒤 Wi-Fi disable |

### 8.3 결과

| 조건 | 반복 | 결과 | client path change | target H3 tuples | qlog path validation | application result |
| --- | ---: | --- | --- | ---: | --- | --- |
| no-change baseline | 1 | PASS | n/a | n/a | false | 1/1 completed |
| Wi-Fi to iPhone USB | 2 | PASS_NEGATIVE_CONTROL | observed in both | 1 in both | false | 0/2 completed |

세부 active row:

| trial | bytes before error | terminal error | classification |
| --- | ---: | --- | --- |
| 001 | 17528 | downlinkError | application_task_failed_without_quic_path_validation |
| 002 | 17528 | downlinkError | application_task_failed_without_quic_path_validation |

### 8.4 챕터 결론

full-response downlink는 active handover에서 반복 실패했다. 중요한 점은 이것을 “Chrome CM 실패”라고 과하게 말하지 않는 것이다. 정확한 표현은 다음이다.

> 현재 controlled Chrome public handover row에서는 active client path change가 관찰되었지만, qlog path validation과 browser single-session CM evidence 없이 application task가 실패했다.

### 8.5 다음 챕터로 넘어간 이유

단일 긴 stream은 실패했다. 그렇다면 application이 resumable semantics를 가진 경우에는 사용자 작업이 살아날 수 있는지 봐야 한다. 그래서 Chapter 9에서 byte-range retry를 실험했다.

근거 문서:

- `docs/results/controlled-public-full-downlink-iphone-usb-handover-20260629.md`

## Chapter 9. Byte-Range Download 및 Retry Recovery 결과

### 9.1 새 질문

> transport-level browser CM evidence가 없을 때도, byte-range retry는 사용자의 다운로드 작업을 완료시킬 수 있는가?

### 9.2 실험 설계

| 항목 | 값 |
| --- | --- |
| workload | browser range download |
| total bytes | 524288 |
| range size | 131072 |
| retry budgets | 0, 2 |
| active trigger | 131072 bytes 이상 완료 후 Wi-Fi disable |

### 9.3 결과 요약

| 조건 | retry budget | 반복 | qlog path validation | application result |
| --- | ---: | ---: | --- | --- |
| no-change baseline | 0 | 1 | false | 1/1 completed |
| no-change baseline | 2 | 1 | false | 1/1 completed |
| active handover | 0 | 2 | false in all | 0/2 completed |
| active handover | 2 | 3 | false in all | 2/3 completed |

retry=2 active 상세:

| trial | client path | target H3 tuples | success | completed bytes | retries | classification |
| --- | --- | ---: | --- | ---: | ---: | --- |
| 001 | changed | 2 | true | 524288 | 1 | tuple_changed_without_path_validation |
| 002 | delayed/changed eventually | 1 | false | 262144 | 0 | application_task_failed_without_quic_path_validation |
| 003 | changed | 2 | true | 524288 | 1 | tuple_changed_without_path_validation |

retry=0 active 상세:

| trial | client path | target H3 tuples | success | completed bytes | retries | classification |
| --- | --- | ---: | --- | ---: | ---: | --- |
| 001 | changed | 1 | false | 262144 | 0 | application_task_failed_without_quic_path_validation |
| 002 | changed | 1 | false | 262144 | 0 | application_task_failed_without_quic_path_validation |

### 9.4 챕터 결론

Range retry는 user-visible completion을 회복할 수 있었다. 하지만 qlog path validation이 없었고, 성공 row는 tuple change/replacement behavior로 분류되었다. 따라서 이 결과는 CM 성공이 아니라 application-level recovery evidence다.

논문에서의 안전한 표현:

> 동일한 controlled public handover 조건에서 full-response와 retry 없는 Range는 실패했지만, retry-enabled Range는 3회 중 2회 완료되었다. 이 차이는 browser-level CM이 아니라 resumable application semantics의 효과로 해석해야 한다.

### 9.5 다음 챕터로 넘어간 이유

대용량 download에서 application recovery 효과가 보였으므로, 다음으로는 upload를 봐야 한다. 업로드는 사진/영상/작업 기록 전송처럼 사용자에게 직접적인 실패를 만들기 때문이다.

근거 문서:

- `docs/results/controlled-public-range-retry-iphone-usb-handover-20260629.md`
- `docs/results/chrome-h3-rebinding-range-download-control-20260629.md`

## Chapter 10. Upload Workload 연구 상태

### 10.1 새 질문

> upload workload에서는 active handover 중 CM 또는 application retry 필요성이 어떻게 나타나는가?

### 10.2 현재 확보된 결과

| 범위 | 결과 | 해석 |
| --- | --- | --- |
| local Chrome NAT rebinding upload | 3/3 PASS, single Chrome QUIC session, qlog/NetLog path validation observed | local control로는 강한 positive evidence |
| controlled public upload no-change baseline | PASS | public origin upload workload baseline 확보 |
| controlled public upload active handover | server artifact missing | countable result로 사용 금지 |

### 10.3 해석

업로드는 연구상 매우 중요하다. 사용자가 사진, 영상, 기록을 업로드하는 도중 path change가 발생하면 실패가 바로 작업 실패로 이어질 가능성이 크다. 또한 upload는 client-sending workload이기 때문에 path validation이나 migration probe가 downlink-only workload보다 빨리 유도될 가능성도 있다.

그러나 현재 public active upload row는 실행 중 중단되어 server artifact가 누락되었다. 따라서 final claim에는 넣으면 안 된다.

### 10.4 챕터 결론

upload는 후속 실험 1순위다. 현재 쓸 수 있는 것은 no-change baseline과 local rebinding positive control뿐이며, public active handover 반복 row가 필요하다.

### 10.5 다음 챕터로 넘어간 이유

upload/download 다음으로 사용자가 직관적으로 중요하게 생각하는 것은 video/music streaming이다. 다만 streaming은 buffer와 segment retry 때문에 completion 해석이 어려워 별도 taxonomy가 필요하다.

근거 문서:

- `docs/results/chrome-h3-rebinding-upload-summary-20260624.md`
- `docs/results/professor-decision-brief-20260629.md`

## Chapter 11. Streaming/Media Workload 연구 결과

### 11.1 새 질문

> CM은 video/music streaming에서 가장 중요한가, 아니면 streaming은 application buffering/retry 때문에 별도로 해석해야 하는가?

### 11.2 Harness 확장

media segment workload를 추가했다.

| endpoint | 의미 |
| --- | --- |
| `/browser-media-segments` | browser page에서 segment-like binary fetch 수행 |
| `/media-segment` | 개별 segment response |

측정값:

- `mediaCompletedCount`
- `mediaRetriesUsed`
- `mediaBytes`
- `mediaElapsedMs`
- `mediaComplete`
- `mediaLastError`
- `mediaErrorElapsedMs`

### 11.3 Local media 결과

Video-like segment profile:

| drop window | retry | PASS/runs | media complete | Chrome sessions | classification |
| --- | ---: | ---: | ---: | --- | --- |
| 3000ms | 0 | 3/3 | 3/3 | 2-2 | nat_rebinding_multiple_quic_sessions |
| 6000ms | 0 | 3/3 | 3/3 | 2-3 | nat_rebinding_multiple_quic_sessions |

Music-like smaller segment profile:

| drop window | retry | PASS/runs | media complete | Chrome sessions | classification |
| --- | ---: | ---: | ---: | --- | --- |
| 6000ms | 0 | 0/3 | 0/3 | 2-2 | browser_h3_request_failed |
| 6000ms | 1 | 3/3 | 3/3 | 3-3 | nat_rebinding_multiple_quic_sessions |

Buffered playback profile:

| drop window | retry | startup/max buffer | PASS/runs | playback complete | QoE 해석 |
| --- | ---: | --- | ---: | ---: | --- |
| 3000ms | 0 | 1/1 | 3/3 | 3/3 | 빠른 시작, rebuffer 다수 |
| 3000ms | 0 | 4/6 | 3/3 | 3/3 | 느린 시작, rebuffer 없음 |
| 3000ms | 2 | 1/1 | 3/3 | 3/3 | retry로 일부 rebuffer 감소 |
| 3000ms | 2 | 4/6 | 3/3 | 3/3 | 느린 시작, rebuffer 없음 |

### 11.4 해석

Streaming은 “작업 완료 여부”만 보면 오해가 크다. segment retry, buffer depth, startup delay, rebuffering, multiple sessions가 모두 user-visible continuity를 바꾼다.

현재 결과는 다음을 보여준다.

1. media completion은 single-session CM success가 아니다.
2. 작은/music-like segment는 no-retry 조건에서 더 취약할 수 있다.
3. buffer depth는 startup delay와 rebuffer 사이의 trade-off를 만든다.
4. streaming 연구는 QoE metric이 필요하다.

### 11.5 챕터 결론

Streaming은 중요한 use case지만 논문의 첫 claim으로 두기에는 위험하다. upload/download/Range로 transport CM과 application recovery를 먼저 분리한 뒤, streaming은 QoE-aware extension으로 다루는 것이 안전하다.

### 11.6 다음 챕터로 넘어간 이유

workload별 결과가 모두 모였으므로, 이제 기존 논문과 비교해서 어떤 claim이 방어 가능한지 정해야 한다.

근거 문서:

- `docs/results/streaming-workload-case-analysis-20260629.md`
- `docs/results/chrome-h3-rebinding-media-segment-replication-20260629.md`
- `docs/results/chrome-h3-rebinding-music-like-media-control-20260629.md`
- `docs/results/chrome-h3-rebinding-buffered-media-control-20260629.md`

## Chapter 12. 문헌 기반 Claim Positioning

### 12.1 새 질문

> 기존 연구와 비교했을 때, 현재 결과로 어떤 논문 주장이 방어 가능한가?

### 12.2 문헌 anchor

가장 중요한 anchor는 `An Analysis of QUIC Connection Migration in the Wild`이다. 이 논문은 Internet-wide QUIC CM support가 균등하지 않다는 점을 보여주며, failure layer 분석의 필요성을 뒷받침한다.

추가 anchor:

| source axis | 본 연구에서의 역할 |
| --- | --- |
| RFC 9000 | QUIC path validation, CID, migration primitive의 기준 |
| RFC 9114 | HTTP/3 application request와 discovery의 기준 |
| RFC 9308/9312 | QUIC 운영/관리성, NAT, UDP, CID 관련 caution |
| Chromium/Cronet policy | browser runtime policy와 migration option 근거 |
| quic-go/quiche docs | implementation positive control 근거 |
| AWS NLB QUIC support | CID-aware deployment path 근거 |
| multipath/media/security 관련 최신 연구 | future work와 operational risk framing |

### 12.3 현재 문헌이 강화하는 주장

| 주장 | 상태 |
| --- | --- |
| CM은 버려진 기능이 아니라 active research/deployment topic이다. | 강화됨 |
| HTTP/3 adoption과 CM adoption은 다르다. | 강화됨 |
| browser workload continuity는 transport CM만으로 설명할 수 없다. | 강화됨 |
| streaming은 QoE metric과 recovery mechanism을 분리해야 한다. | 강화됨 |

### 12.4 아직 보류해야 할 주장

| 주장 | 이유 |
| --- | --- |
| Chrome/Safari가 Wi-Fi/cellular handover에서 원래 HTTP/3 connection을 migration했다. | single-session CM evidence 부족 |
| CDN HTTP/3 support가 end-to-end CM support다. | edge termination 가능성 |
| application retry completion은 CM success다. | recovery mechanism이 다름 |
| local NAT rebinding 결과가 real mobile handover를 대표한다. | OS route/public path/change environment가 다름 |

### 12.5 챕터 결론

문헌과 실험을 합치면 논문 방향은 “CM 성공 증명”보다 “CM maturity/evidence-chain/workload recovery study”가 더 방어 가능하다.

근거 문서:

- `docs/results/literature-claim-positioning-20260629.md`
- `docs/results/literature-refresh-browser-cm-20260624.md`
- `docs/results/literature-refresh-latest-cm-boundary-20260624.md`

## Chapter 13. 현재 결론, 한계, 다음 의사결정

### 13.1 지금까지의 핵심 결론

현재까지의 연구 결과는 다음과 같이 정리된다.

1. QUIC Connection Migration은 표준과 구현체 수준에서 실재한다.
2. 주요 구현체 다수는 path validation, NAT rebinding, active/passive migration, qlog/event/test를 제공한다.
3. 그러나 실제 브라우저 HTTP/3 handover에서 CM 성공을 주장하려면 훨씬 강한 evidence chain이 필요하다.
4. Chrome desktop은 현재 가장 계측 가능한 browser target이지만, controlled public handover에서 single-session CM 성공은 아직 관찰되지 않았다.
5. full-response downlink와 retry 없는 Range download는 active handover에서 실패했다.
6. retry-enabled Range download는 3회 중 2회 완료되었지만, 이는 application-level recovery로 해석해야 한다.
7. upload active handover는 중요하지만 countable row가 부족하다.
8. streaming은 중요하지만 buffer/retry/session churn 때문에 QoE-aware extension으로 다뤄야 한다.

### 13.2 논문에서 쓸 수 있는 안전한 중심 주장

> QUIC CM은 구현체와 표준 수준에서 성숙한 primitive로 존재하지만, 브라우저 기반 웹 작업 연속성으로 관찰되기 위해서는 HTTP/3 discovery, 실제 client path change, qlog path validation, browser session continuity, deployment routing, workload-specific recovery가 함께 충족되어야 한다. 현재 Chrome controlled public handover 실험은 browser-level single-session CM 성공을 보여주지 못했지만, Range retry 등 application-level recovery가 user-visible completion을 바꿀 수 있음을 보여준다.

### 13.3 논문에서 피해야 할 주장

| 피해야 할 주장 | 이유 |
| --- | --- |
| HTTP/3 CM이 웹 작업 연속성을 보장한다. | 보장이라는 표현은 현재 증거보다 강하다. |
| Chrome이 Wi-Fi-to-cellular handover에서 원래 H3 connection을 migration했다. | qlog/session continuity evidence 부족 |
| Range retry 성공은 CM 성공이다. | application recovery다. |
| streaming completion은 CM 성공이다. | buffering/retry/multiple sessions 가능성 |
| Mac+iPhone USB failover가 모든 mobile handover를 대표한다. | external validity 한계 |
| CDN HTTP/3 support는 end-to-end CM support다. | edge termination 가능성 |

### 13.4 교수님께 받아야 할 결정

| 결정 항목 | 선택지 |
| --- | --- |
| 논문 방향 | CM success proof vs CM maturity/evidence-chain/workload recovery study |
| negative finding 사용 | Chrome single-session CM 미관찰 결과를 논문 중심 evidence로 쓸지 여부 |
| workload 중심 | upload/download/Range를 중심으로 둘지, streaming까지 중심으로 확장할지 |
| Safari/Android | 본 논문 실험 범위에 넣을지, feasibility/future work로 둘지 |
| application recovery | Range retry, upload retry, buffering을 CM 보완재로 다룰지 여부 |

### 13.5 다음 연구 우선순위

교수님이 현재 방향을 승인하면 다음 순서가 가장 안전하다.

| 우선순위 | 작업 | 이유 |
| ---: | --- | --- |
| 1 | controlled public upload active handover 반복 | upload는 사용자 작업 실패와 가장 직접 연결된다. |
| 2 | Range retry public handover 반복 수 증가 | 현재 2/3 성공을 더 안정적인 evidence로 만들어야 한다. |
| 3 | full-response vs Range vs upload 비교 table 완성 | workload taxonomy의 중심 결과가 된다. |
| 4 | media public handover QoE row | streaming은 completion, startup delay, rebuffer, retry, sessions를 함께 봐야 한다. |
| 5 | Safari feasibility row | Safari는 session evidence가 약하므로 supporting row로 처리한다. |
| 6 | Android Chrome/Cronet follow-up | 실제 mobile browser claim이 필요하면 별도 장비/logging 준비 후 진행한다. |

### 13.6 논문 목차 초안

1. Introduction
2. Background: QUIC Connection Migration and HTTP/3
3. Related Work: Wild CM Support, Browser Policy, Deployment Friction
4. Implementation Maturity Audit
5. Evidence Chain for Browser-Level CM
6. Testbed and Workloads
7. Controlled Implementation and Deployment Positive Controls
8. Chrome Controlled Public Handover Results
9. Application Recovery Across Workloads
10. Discussion: Why CM Is Hard to Observe in Web Applications
11. Threats to Validity
12. Conclusion and Future Work

## 부록 A. 챕터별 산출물 색인

| 챕터 | 주요 산출물 |
| --- | --- |
| Chapter 1 | `docs/results/local-implementation-test-results.md`, `docs/results/professor-decision-brief-20260629.md` |
| Chapter 2 | `docs/results/cm-operational-friction-matrix-20260624.md` |
| Chapter 3 | `docs/results/local-implementation-test-results.md`, `docs/results/quic-go-minimum-reproduction-results.md` |
| Chapter 4 | `docs/results/aws-nlb-http3-workload-results-20260624.md` |
| Chapter 5 | `docs/results/browser-cm-observability-matrix-20260624.md`, `docs/results/evidence-chain-and-gap-synthesis-20260624.md` |
| Chapter 6 | `docs/results/chrome-h3-rebinding-upload-summary-20260624.md`, `docs/results/chrome-h3-rebinding-range-download-control-20260629.md` |
| Chapter 7 | `docs/results/aws-ec2-refresh-origin-20260629.md` |
| Chapter 8 | `docs/results/controlled-public-full-downlink-iphone-usb-handover-20260629.md` |
| Chapter 9 | `docs/results/controlled-public-range-retry-iphone-usb-handover-20260629.md` |
| Chapter 10 | `docs/results/chrome-h3-rebinding-upload-summary-20260624.md`, `docs/results/professor-decision-brief-20260629.md` |
| Chapter 11 | `docs/results/streaming-workload-case-analysis-20260629.md` |
| Chapter 12 | `docs/results/literature-claim-positioning-20260629.md` |
| Chapter 13 | `docs/results/professor-decision-brief-20260629.md` |

## 부록 B. 최종 한 문장 요약

현재까지의 연구는 “QUIC CM이 없다”도, “브라우저 CM이 성공했다”도 아니다. 더 정확한 결론은 QUIC CM primitive는 구현체와 배포 positive control에서 확인되지만, 실제 브라우저 웹 작업 연속성으로 주장하려면 계층별 evidence chain이 필요하고, 현재 Chrome public handover에서는 single-session CM이 아니라 workload-dependent application recovery가 더 강하게 관찰되었다는 것이다.
