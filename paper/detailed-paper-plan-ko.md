# 논문 상세안: HTTP/3 Connection Migration의 배포 성숙도와 웹 작업 연속성 평가

작성일: 2026-06-24  
문서 성격: 결과 기반 논문 상세안  
대상: 교수님 논의, 논문 구조 확정, 후속 실험 설계

## 1. 논문 핵심 방향

### 1.1 가제

**HTTP/3 Connection Migration의 배포 성숙도와 웹 작업 연속성 평가**

영문 가제:

**Assessing the Deployment Maturity of HTTP/3 Connection Migration for Web Task Continuity**

### 1.2 핵심 문제의식

QUIC Connection Migration은 Connection ID와 path validation을 통해 client IP 또는 port가 바뀌어도 같은 connection을 유지할 수 있게 하는 기능이다. 이 기능은 Wi-Fi/LTE 전환, 모바일 현장 업무, 대용량 파일 업로드, 실시간 대시보드 확인 같은 웹 작업에서 유용해 보인다.

하지만 지금까지의 조사와 실험 결과를 보면, 문제는 “기술이 좋은데 왜 안 쓰이는가?”가 아니라 다음 질문에 가깝다.

> QUIC Connection Migration은 구현체 수준에서는 어느 정도 존재하지만, 실제 HTTP/3 웹 작업 연속성으로 배포되려면 어떤 조건이 추가로 필요한가?

즉, 본 논문은 Connection Migration을 단순 성능 기능이 아니라 **구현체 성숙도, 배포 경로 성숙도, 애플리케이션 작업 연속성**의 세 계층으로 평가한다.

### 1.3 최종 주장

본 연구의 핵심 주장은 다음과 같다.

> QUIC Connection Migration은 여러 주요 구현체에서 이미 testable transport primitive로 존재한다. 그러나 HTTP/3 웹 작업 연속성으로 배포 가능하려면 CID-aware routing, proxy/CDN 동작, client/browser migration policy, observability, application workload semantics까지 함께 성숙해야 한다.

조금 더 실험 결과 중심으로 쓰면 다음과 같다.

> controlled quic-go client와 AWS NLB `TCP_QUIC :443` passthrough 환경에서 backend-generated CID가 AWS NLB가 요구하는 QUIC-LB plaintext Server ID format을 만족할 경우, active client-side migration 이후 HTTP/3 request continuity뿐 아니라 1MiB upload/download body 전송 중 mid-flight continuity도 유지될 수 있다. 그러나 HAProxy negative control과 CID mismatch negative control은 HTTP/3 지원 자체가 Connection Migration 지원을 의미하지 않음을 보여준다.

## 2. 연구 질문

### RQ1. 구현체 성숙도

**주요 QUIC 구현체들은 Connection Migration primitive를 어느 정도 구현하고 있는가?**

세부 질문:

- active migration API가 존재하는가?
- passive NAT rebinding 또는 peer address change를 처리하는가?
- path validation state machine이 있는가?
- qlog, PathEvent, NetLog 같은 관찰성이 있는가?
- 실패 경로, disabled migration, zero-length CID, preferred address를 테스트하는가?

현재 답변:

- quic-go, quiche, picoquic, s2n-quic, ngtcp2, Quinn, Neqo, aioquic 등은 migration 관련 primitive 또는 test evidence를 제공한다.
- 따라서 “Connection Migration은 구현도 안 된 기술”이라고 말하기 어렵다.
- 하지만 구현체별 API, observability, deployment readiness는 크게 다르다.

### RQ2. 배포 경로 성숙도

**HTTP/3 endpoint가 존재할 때, 어떤 배포 경로가 Connection Migration을 유지하거나 깨뜨리는가?**

세부 질문:

- direct-origin에서는 active migration이 성공하는가?
- HTTP/3 reverse proxy는 active migration을 지원하는가?
- load balancer 뒤에서는 5-tuple 변화 이후에도 같은 backend로 routing되는가?
- CID-aware load balancing이 migration continuity에 필요한가?

현재 답변:

- EC2 direct-origin positive control은 PASS.
- HAProxy HTTP/3 negative control은 baseline HTTP/3 request는 처리하지만 active migration path validation은 FAIL.
- AWS NLB는 CID format과 registered `QuicServerId`가 맞으면 PASS.
- malformed CID 또는 mismatched Server ID에서는 FAIL.

### RQ3. HTTP/3 작업 연속성

**Transport-level migration이 실제 HTTP/3 application task completion으로 이어지는가?**

세부 질문:

- migration 전후 같은 HTTP/3 connection에서 request를 계속 보낼 수 있는가?
- upload body 전송 중 migration이 발생해도 server가 전체 body를 받는가?
- streaming download response 수신 중 migration이 발생해도 client가 전체 body를 받는가?

현재 답변:

- local HTTP/3 post-migration request continuity: PASS.
- AWS NLB `TCP_QUIC :443` HTTP/3 post-migration request continuity: PASS.
- local HTTP/3 mid-flight upload/download: PASS.
- AWS NLB `TCP_QUIC :443` mid-flight upload/download: PASS.

### RQ4. 남은 질문

**controlled quic-go 결과를 실제 브라우저/모바일 handover로 일반화할 수 있는가?**

현재 답변:

- 아직 일반화하면 안 된다.
- Chrome/Android/Cronet policy, 실제 Wi-Fi/LTE handover, CloudFront viewer-edge continuity는 후속 실험으로 남는다.

## 3. 논문 기여점

### Contribution 1. 구현체 성숙도 분류

주요 QUIC 구현체를 source evidence, test evidence, control API, observability, deployment implication 기준으로 분류한다.

논문에 넣을 문장:

> We provide a source-backed maturity taxonomy of QUIC Connection Migration implementations, distinguishing transport mechanisms, public control APIs, observability, test coverage, and deployment readiness.

한국어 설명:

> Connection Migration이 구현체에 아예 없는 기능인지부터 검증하고, 구현체별로 연구자가 실험 가능한지, 배포 환경과 연결될 수 있는지 분리해 평가한다.

### Contribution 2. HTTP/3 지원과 Connection Migration 지원의 분리

HAProxy negative control을 통해 HTTP/3 endpoint availability와 active Connection Migration support가 동일하지 않음을 실험적으로 보인다.

논문에 넣을 문장:

> We experimentally show that HTTP/3 endpoint availability does not imply end-to-end QUIC Connection Migration support.

핵심 근거:

- HAProxy 3.4.0 HTTP/3 baseline request 성공.
- quiche `--perform-migration` active migration attempt 실패.
- PATH_CHALLENGE 3회, PATH_RESPONSE 0회.
- migrated path `validation_state=Failed`.

### Contribution 3. CID-aware load balancing 조건 검증

AWS NLB QUIC/TCP_QUIC 실험으로 load-balanced deployment에서 migration continuity가 CID format과 registered Server ID에 민감하다는 점을 보인다.

논문에 넣을 문장:

> We demonstrate that deployable migration behind AWS NLB requires CID-aware routing compatibility: the backend-generated QUIC CID must encode the registered Server ID in the expected QUIC-LB plaintext format.

핵심 근거:

- AWS NLB `QUIC :4242`: PASS.
- AWS NLB `TCP_QUIC :443`: PASS.
- malformed CID: FAIL, CloudWatch unknown Server ID packet drops.
- explicit Server ID mismatch: FAIL, target health 2/2 healthy였지만 handshake/application payload 실패.

### Contribution 4. HTTP/3 workload continuity 검증

Transport stream 실험을 넘어 HTTP/3 request 및 mid-flight body transfer 실험까지 수행한다.

논문에 넣을 문장:

> We extend transport-level migration validation to HTTP/3 task continuity by testing post-migration requests and mid-flight 1MiB upload/download body transfers.

핵심 근거:

- local HTTP/3 post-migration request continuity: PASS.
- AWS NLB HTTP/3 post-migration request continuity: PASS.
- local mid-flight upload/download: PASS.
- AWS NLB mid-flight upload/download: PASS.

## 4. 논문 구조 상세안

## 4.1 Introduction

### 목적

왜 이 연구가 필요한지 설명한다.

핵심 논리:

1. QUIC은 Connection ID를 통해 IP/port 변화에도 connection을 유지할 수 있다.
2. 이 기능은 HTTP/3 웹 애플리케이션의 작업 연속성에 유용해 보인다.
3. 그러나 HTTP/3 지원, QUIC 구현, CDN/LB 배포, browser policy, application recovery는 서로 다른 계층이다.
4. 따라서 “HTTP/3 Connection Migration이 된다/안 된다”가 아니라 “어떤 조건에서 웹 작업 연속성으로 이어지는가”를 평가해야 한다.

넣을 결과 예고:

- 여러 구현체는 migration primitive를 제공한다.
- HAProxy는 HTTP/3를 지원하지만 active migration은 실패한다.
- AWS NLB는 CID 조건이 맞으면 migration continuity를 유지한다.
- controlled quic-go 환경에서는 HTTP/3 mid-flight upload/download도 통과한다.

### Introduction 마지막 문단 후보

> 본 연구는 Connection Migration의 실용적 장벽이 구현 부재 하나로 설명되지 않음을 보인다. 여러 구현체는 testable migration primitive를 제공하지만, HTTP/3 웹 작업 연속성으로 이어지기 위해서는 CID-aware routing, proxy/CDN termination, browser migration policy, observability, application workload semantics가 함께 맞아야 한다.

## 4.2 Background

### 들어갈 내용

1. QUIC Connection ID
2. Path validation
3. Active migration vs passive NAT rebinding
4. Preferred address, multipath, server-side migration과의 구분
5. HTTP/3 deployment path
6. Web task continuity 정의

### 중요한 용어 정리

| 용어 | 본 논문에서의 의미 |
| --- | --- |
| Connection Migration | RFC 9000 single-path client-side active migration 및 NAT rebinding 중심 |
| Passive rebinding | NAT 또는 network path 변화에 의해 peer address가 바뀌는 상황 |
| Active migration | client가 새 path를 의도적으로 추가하고 검증한 뒤 사용 |
| Path validation | `PATH_CHALLENGE`/`PATH_RESPONSE`로 peer reachability를 검증하는 과정 |
| HTTP/3 task continuity | application reconnect/manual retry/checksum failure 없이 HTTP/3 작업이 완료되는 것 |
| Deployment maturity | LB/CDN/proxy/client policy까지 포함해 migration이 실제 배포 경로에서 유지되는 수준 |

### 피해야 할 표현

- “보장한다”
- “모바일 네트워크 전체에서 동작한다”
- “Chrome에서 동작한다”

대신:

- “controlled condition에서 보존되었다”
- “AWS NLB `TCP_QUIC :443` passthrough 조건에서 관찰되었다”
- “browser/Cronet policy는 후속 검증으로 남는다”

## 4.3 Related Work

### 문헌 분류

| 분류 | 문헌/자료 | 논문에서 쓰는 역할 |
| --- | --- | --- |
| Standard baseline | RFC 9000, RFC 9308, RFC 9312 | CID, path validation, manageability caveat |
| Internet-wide measurement | An Analysis of QUIC Connection Migration in the Wild | CM 지원이 균일하지 않다는 anchor |
| Mobile handover | mQUIC, EnCoR | 모바일 handover와 application continuity 맥락 |
| Middlebox/proxy | When QUIC CM Meets Middleboxes, HAProxy docs | 배포 계층이 CM을 깨뜨릴 수 있음 |
| Load balancing | QUIC-LB draft, AWS NLB docs/blog | CID-aware routing 필요성 |
| Observability | qlog/qvis, qlog schema | qlog evidence 필요성 |
| Browser/client policy | Android Cronet, Chromium source | 실제 client policy가 별도 계층임 |
| Security/manageability | QUIC-Exfil, QUICstep, MIMIQ | 운영자가 CM을 조심스럽게 다루는 이유 |

### Related Work gap 문장

> 기존 연구는 QUIC Connection Migration의 표준 동작, Internet-wide 지원률, 모바일 handover 효과, middlebox 문제, multipath 확장을 각각 다루었다. 그러나 구현체 primitive, CID-aware load balancing, CDN/proxy termination, browser policy, application workload continuity를 하나의 검증 체계로 연결한 연구는 부족하다.

## 4.4 Implementation Maturity Survey

### 목적

Connection Migration이 실제 구현체에 있는지 확인하고, 구현되어 있다면 어떤 수준인지 분류한다.

### 평가 축

| 축 | 평가 질문 |
| --- | --- |
| Mechanism | active migration, passive rebinding, preferred address 지원 여부 |
| Control API | 연구자가 migration을 trigger할 수 있는 public API 여부 |
| Observability | qlog, PathEvent, NetLog, callback 여부 |
| Test coverage | success/failure/edge-case test 여부 |
| Deployment readiness | CID length/generator/LB compatibility 여부 |
| HTTP/3 usability | HTTP/3 workload로 확장 가능한지 |

### 구현체별 논문 내 역할

| 구현체/환경 | 논문 내 역할 | 현재 판단 |
| --- | --- | --- |
| quic-go | active migration baseline | L4 testable maturity |
| quiche | PathEvent/qlog lifecycle evidence | L4 observability evidence |
| picoquic | edge-case maturity baseline | L4 edge-case evidence |
| s2n-quic | AWS/CID provider 후보 | L4, AWS L5 candidate |
| ngtcp2 | RFC guardrail baseline | L4 |
| Quinn/Neqo/aioquic | 추가 implementation evidence | L3-L4 |
| MsQuic/mvfst | production/deployment maturity evidence | source evidence |
| HAProxy | HTTP/3 != CM negative control | L1-L2 |
| Chromium/Cronet | future browser/client policy target | client-runtime evidence |

### 이 장의 결론

> Connection Migration은 여러 구현체에서 이미 구현 및 테스트되고 있다. 그러나 구현체마다 API, observability, preferred address, deployment readiness가 다르고, testable transport maturity가 deployable HTTP/3 continuity를 의미하지 않는다.

## 4.5 Experimental Design

### 전체 실험 체인

```text
Implementation survey
  -> local implementation tests
  -> EC2 direct-origin positive control
  -> HAProxy HTTP/3 negative control
  -> AWS NLB CID-aware deployment control
  -> HTTP/3 post-migration request workload
  -> HTTP/3 mid-flight upload/download workload
```

### 실험별 목적

| 실험 | 목적 | 왜 필요한가 |
| --- | --- | --- |
| quic-go local direct-origin | active migration 최소 재현 | 실험 제어 가능성 확인 |
| quiche path-event timeline | migration lifecycle 관찰 | qlog/Event 기반 설명 가능 |
| EC2 direct-origin | public cloud direct path positive control | transport 자체가 cloud에서 되는지 확인 |
| HAProxy HTTP/3 | negative control | HTTP/3 support와 CM support 분리 |
| AWS NLB QUIC | CID-aware routing 검증 | LB 뒤 migration 가능성 확인 |
| AWS NLB negative controls | 실패 조건 확인 | CID format/Server ID 민감도 검증 |
| AWS NLB `TCP_QUIC :443` | 현실적인 port/protocol repeat | custom high port 한계 제거 |
| HTTP/3 workload | application task로 확장 | transport continuity와 HTTP/3 task 연결 |
| Mid-flight workload | body 전송 중 migration 검증 | 작업 연속성에 가장 가까운 controlled evidence |

## 4.6 Results

### Result 1. 구현체 수준에서 CM primitive는 존재한다

근거:

- quic-go local direct-origin PASS.
- quiche path-event timeline PASS.
- picoquic migration edge-case tests PASS.
- s2n-quic migration tests PASS.
- aioquic/ngtcp2/Quinn/Neqo 관련 tests PASS.

논문 문장:

> The implementation survey and local tests show that Connection Migration is not merely specified but absent from implementations. Several stacks expose testable transport primitives and observability hooks.

### Result 2. Direct-origin에서는 active migration이 성공한다

EC2 direct-origin 결과:

| 항목 | 값 |
| --- | --- |
| status | PASS |
| implementation | quic-go |
| source tuple change | `211.60.158.133:64273 -> 211.60.158.133:58085` |
| workload | before/after 1MiB stream payload |
| evidence | qlog PATH_CHALLENGE/PATH_RESPONSE, pcap, JSON |

해석:

> 이후 proxy/LB/CDN 실패를 transport primitive 자체 부재로 해석하면 안 된다.

### Result 3. HTTP/3 support는 CM support가 아니다

HAProxy 결과:

| 항목 | 값 |
| --- | --- |
| status | PASS_NEGATIVE_CONTROL |
| baseline HTTP/3 | 성공 |
| active migration | 실패 |
| PATH_CHALLENGE | 3회 |
| PATH_RESPONSE | 0회 |
| final state | `validation_state=Failed` |

해석:

> HTTP/3 endpoint availability does not imply Connection Migration support.

### Result 4. AWS NLB는 CID-aware 조건에서 migration continuity를 유지한다

AWS NLB QUIC data-plane:

| 항목 | 값 |
| --- | --- |
| status | PASS |
| protocol | `QUIC` |
| port | `4242` |
| successful target | target-b |
| source tuple | `211.60.158.133:55957 -> 211.60.158.133:59355` |
| workload | before/after 64KiB stream |

AWS NLB `TCP_QUIC :443` repeat:

| 항목 | 값 |
| --- | --- |
| status | PASS |
| protocol | `TCP_QUIC` |
| port | `443` |
| successful target | target-b |
| source tuple | `211.60.158.133:57897 -> 211.60.158.133:56632` |
| workload | before/after 64KiB stream |

필수 CID format:

```text
0x00 + 8-byte Server ID + 7-byte nonce
```

해석:

> load-balanced QUIC migration은 가능하지만, CID format과 registered `QuicServerId`가 정확히 맞아야 한다.

### Result 5. CID 조건이 틀리면 실패한다

Negative controls:

| 조건 | 결과 | 의미 |
| --- | --- | --- |
| malformed CID layout | FAIL as expected | CloudWatch unknown Server ID drop |
| explicit Server ID mismatch | FAIL as expected | target health 2/2여도 handshake/application failure |

논문에서의 역할:

- positive result의 조건성을 강화한다.
- “NLB에서 QUIC만 켜면 된다”는 해석을 차단한다.

### Result 6. HTTP/3 post-migration request continuity가 유지된다

Local:

| 항목 | 값 |
| --- | --- |
| status | PASS |
| workload | POST `/upload` before -> migration -> GET `/download` after |
| source tuple | `127.0.0.1:63819 -> 127.0.0.1:63361` |

AWS NLB:

| 항목 | 값 |
| --- | --- |
| status | PASS |
| protocol | `TCP_QUIC :443` |
| successful target | target-a |
| source tuple | `211.60.158.133:54110 -> 211.60.158.133:50930` |
| workload | before POST `/upload`, after GET `/download` |

해석:

> controlled 조건에서는 transport continuity가 HTTP/3 request continuity로 확장될 수 있다.

### Result 7. HTTP/3 mid-flight body transfer도 controlled 조건에서 유지된다

Local mid-flight:

| workload | status | socket A | socket B | final addr | evidence |
| --- | --- | --- | --- | --- | --- |
| upload | PASS | `[::]:53663` | `[::]:63569` | `[::]:63569` | server decoded 1MiB upload |
| download | PASS | `[::]:49959` | `[::]:52767` | `[::]:52767` | client decoded 1MiB response |

AWS NLB mid-flight:

| workload | status | target | socket A | socket B | evidence |
| --- | --- | --- | --- | --- | --- |
| upload | PASS | target-a | `[::]:56276` | `[::]:52824` | target decoded 1MiB upload |
| download | PASS | target-b | `[::]:61456` | `[::]:63381` | client decoded 1MiB streaming response |

중요 관찰:

> mid-flight case에서는 `path.Switch()` 직후 `conn.LocalAddr()`가 socket A로 남아 있을 수 있었고, 후속 packet 송수신 이후 final address가 socket B로 바뀌었다. 따라서 성공 기준은 final address, qlog path validation, payload integrity를 함께 봐야 한다.

## 5. 표와 그림 구성안

### Figure 1. 연구 계층 모델

```text
QUIC implementation primitive
  -> testable active migration
  -> direct-origin transport continuity
  -> CID-aware deployment continuity
  -> HTTP/3 request continuity
  -> HTTP/3 mid-flight task continuity
  -> browser/mobile real-world continuity
```

용도:

- 논문 초반에 전체 framing을 보여준다.

### Figure 2. 실험 아키텍처

```text
client socket A/B
      |
      | QUIC / HTTP/3
      v
Direct origin / HAProxy / AWS NLB
      |
      v
target A/B or origin
```

용도:

- direct-origin, proxy, NLB 경로 차이를 보여준다.

### Figure 3. Migration lifecycle

quiche path-event timeline 또는 qlog 기반:

```text
new path observed
  -> PATH_CHALLENGE
  -> PATH_RESPONSE
  -> path validated
  -> active path switched
```

용도:

- migration이 단순 port switch가 아니라 validation lifecycle임을 설명한다.

### Table 1. 구현체 성숙도 표

컬럼:

- implementation
- active migration API
- passive rebinding
- observability
- test coverage
- deployment implication
- role in this study

### Table 2. 전체 실험 결과 요약

컬럼:

- experiment
- environment
- protocol
- migration trigger
- result
- key evidence
- interpretation

### Table 3. AWS NLB positive/negative controls

컬럼:

- CID condition
- registered Server ID
- result
- target health
- application payload
- interpretation

### Table 4. HTTP/3 workload continuity

컬럼:

- workload
- local result
- AWS NLB result
- payload size
- final socket change
- integrity check

## 6. Discussion 상세안

### 6.1 왜 Connection Migration은 잘 쓰이지 않는가?

결론적으로 “구현이 안 돼서”만은 아니다.

계층별 이유:

| 계층 | 왜 어려운가 |
| --- | --- |
| Implementation | API, preferred address, observability, tests가 구현체마다 다름 |
| Client/browser | OS network event, default network, cellular cost, battery policy가 migration trigger에 영향 |
| CDN/proxy | HTTP/3가 edge/proxy에서 종료되어 origin end-to-end CM과 분리됨 |
| Load balancer | 5-tuple 변화 후 backend affinity를 잃을 수 있음 |
| CID routing | CID format, Server ID, routing table이 맞아야 함 |
| Observability | QUIC 암호화로 외부 pcap만으로 원인 분리 어려움 |
| Application | upload/download/dashboard는 transport 유지와 별개로 실패할 수 있음 |
| Security/manageability | migration/preferred address는 exfiltration, censorship, tracking, middlebox policy와 연결 |

### 6.2 AWS NLB 결과가 말하는 것

말할 수 있는 것:

- CID-aware load balancer 뒤에서도 Connection Migration continuity는 가능하다.
- AWS NLB `TCP_QUIC :443`에서 HTTP/3 request와 mid-flight workload가 통과했다.
- CID format과 registered `QuicServerId`가 핵심 조건이다.

말하면 안 되는 것:

- 모든 NLB/QUIC server에서 자동으로 된다.
- CloudFront/CDN origin end-to-end에서도 된다.
- Chrome/Android에서 실제 handover 시에도 된다.

### 6.3 Web task continuity의 현재 범위

현재 증명한 체인:

```text
custom transport stream continuity
  -> AWS NLB CID-aware transport continuity
  -> HTTP/3 post-migration request continuity
  -> controlled HTTP/3 mid-flight body continuity
```

아직 남은 체인:

```text
browser/Cronet policy
  -> real Wi-Fi/LTE handover
  -> real web application fetch/upload/download/dashboard behavior
  -> user-visible continuity
```

## 7. 한계

### 7.1 Controlled migration과 실제 handover의 차이

현재 실험은 client source port 변경 또는 secondary UDP socket을 이용한 controlled migration이다. 실제 Wi-Fi/LTE handover는 interface change, routing table change, carrier NAT, radio delay, OS default network selection이 포함된다.

### 7.2 quic-go 중심 실험

quic-go는 active migration API가 명확해 실험에 적합하지만, 다른 구현체의 deployment behavior를 대표하지 않는다.

### 7.3 AWS NLB 특정성

AWS NLB `TCP_QUIC :443` 결과는 CID-aware AWS NLB 환경의 결과다. 다른 cloud LB, CDN, reverse proxy에 일반화할 수 없다.

### 7.4 Browser policy 미검증

Chrome/Android/Cronet은 아직 실제 workload 실험이 완료되지 않았다. 따라서 실제 사용자의 모바일 브라우저 경험을 주장하면 안 된다.

### 7.5 Application workload 제한

현재 workload는 deterministic upload/download 중심이다. Dashboard polling, SSE/WebSocket/WebTransport, service worker, UI recovery는 후속 연구가 필요하다.

## 8. 후속 실험 상세안

### 8.1 CloudFront viewer-edge limited control

목표:

- CloudFront HTTP/3 Connection Migration이 viewer-edge continuity인지 origin end-to-end continuity인지 분리한다.

실험:

```text
client
  -> HTTP/3
  -> CloudFront edge
  -> origin
```

측정:

- client가 CloudFront와 HTTP/3 사용 여부.
- origin에서 client QUIC connection을 직접 관찰할 수 없는지.
- network change 중 request/download continuity.

예상 논문 역할:

> CDN 환경에서는 Connection Migration을 end-to-end origin claim으로 쓰면 안 되고, viewer-edge continuity로 해석해야 한다.

### 8.2 Cronet/Android workload

목표:

- 실제 client policy가 controlled quic-go 결과와 어떻게 다른지 확인한다.

Workload:

- large upload
- streaming download
- dashboard polling 또는 SSE-like update

조건:

- HTTP/2 baseline
- HTTP/3 direct-origin
- HTTP/3 AWS NLB
- HTTP/3 CloudFront

측정:

- task success/failure
- retry count
- stall time
- recovery time
- Android network callback
- Cronet NetLog
- server qlog

## 9. 최종 결론 상세안

논문 결론은 다음처럼 정리한다.

1. Connection Migration은 구현체에 없는 기능이 아니다.
2. 여러 QUIC stack은 이미 testable transport maturity를 갖고 있다.
3. 그러나 HTTP/3 endpoint support는 Connection Migration support가 아니다.
4. 배포 환경에서는 CID-aware routing이 핵심 조건이다.
5. AWS NLB `TCP_QUIC :443`에서는 올바른 CID format 조건에서 HTTP/3 request 및 mid-flight body continuity가 관찰되었다.
6. 하지만 실제 브라우저/모바일 handover에서 웹 작업 연속성을 주장하려면 Cronet/Chrome policy와 real handover 실험이 추가로 필요하다.

최종 한 문장:

> QUIC Connection Migration은 작동할 수 있지만, HTTP/3 웹 작업 연속성은 transport 구현만으로 결정되지 않으며 implementation, deployment, client policy, application semantics가 함께 맞을 때에만 보존된다.
