# QUIC / HTTP/3 Connection Migration 실험 결과 상세 보고서

작성일: 2026-06-24  
대상: QUIC Connection Migration 구현체 성숙도, 배포 경로 성숙도, HTTP/3 작업 연속성  
원칙: 결과를 미리 정해놓고 해석하지 않고, 관찰된 증거를 기준으로 계층별로 정리한다.

## 1. 연구 질문

본 연구는 다음 질문에서 출발했다.

> HTTP/3 Connection Migration은 실제 웹 애플리케이션 작업 연속성을 보존할 수 있는가?

하지만 조사와 실험을 진행하면서 질문을 더 엄밀하게 나누었다.

1. QUIC Connection Migration은 실제 구현체에 구현되어 있는가?
2. 구현되어 있다면 연구자가 의도적으로 migration을 trigger하고 관찰할 수 있는가?
3. direct-origin, reverse proxy, CDN, load balancer 같은 배포 경로에서 migration이 유지되는가?
4. transport connection이 유지될 때 HTTP/3 request와 body transfer도 완료되는가?
5. controlled client 결과를 실제 browser/mobile handover로 일반화할 수 있는가?

현재까지의 실험은 1-4번을 상당 부분 검증했고, 5번은 후속 연구로 남아 있다.

## 2. 전체 결과 요약

현재까지의 증거 체인은 다음과 같다.

```text
구현체 primitive 존재 확인
  -> local active migration 재현
  -> EC2 direct-origin positive control
  -> HAProxy HTTP/3 negative control
  -> AWS NLB CID-aware routing positive/negative controls
  -> HTTP/3 post-migration request continuity
  -> HTTP/3 mid-flight upload/download continuity
  -> Chrome browser H3 baseline, downlink/heartbeat workload, multiple-session negative control
```

중립적 결론:

> QUIC Connection Migration은 여러 구현체에서 실제로 존재하고, controlled 환경에서는 HTTP/3 작업까지 이어질 수 있다. 그러나 실제 웹/모바일 배포로 일반화하려면 CDN/proxy/LB/browser/application 계층을 별도로 검증해야 한다.

특히 Chrome CDP downlink/heartbeat 대조군은 server remote tuple 변화만으로 CM을 주장하면 안 됨을 보였다. heartbeat request는 network-change가 없어도 별도 QUIC session/source tuple을 만들 수 있었고, inactive interface toggle에서는 client path snapshot이 `no_client_path_change_observed`였다.

## 3. 실험 환경

### 3.1 Local 개발 환경

| 항목 | 내용 |
| --- | --- |
| OS | macOS local machine |
| 주요 언어 | Go, Bash, Python helper |
| 주요 구현체 | quic-go, Cloudflare quiche, picoquic, s2n-quic, ngtcp2, Quinn, Neqo, aioquic |
| 주요 관찰 수단 | JSONL log, result JSON, qlog, implementation test log |
| 로컬 재현 코드 | `repro/quic-go-min-repro/` |

### 3.2 AWS 환경

| 항목 | 내용 |
| --- | --- |
| Region | `ap-northeast-2` |
| Direct-origin | EC2 public IP에 QUIC server 배치 |
| Load balancer | AWS Network Load Balancer |
| Target group protocols | `QUIC`, `TCP_QUIC` |
| 주요 port | `4242`, `443` |
| Target count | 2개 EC2 target |
| Health check | TCP sidecar |
| Cleanup | 각 실험 후 listener, NLB, target group, EC2, SG, key pair 삭제 확인 |

AWS 실험에서 중요한 조건:

```text
AWS NLB QUIC-LB plaintext CID format:
0x00 + 8-byte Server ID + 7-byte nonce
```

이 format과 target registration의 `QuicServerId`가 맞아야 migration 이후에도 같은 backend target으로 routing된다.

## 4. 코드 구성 요약

자세한 코드 설명은 [code-architecture-ko.md](code-architecture-ko.md)에 정리했다.

핵심 코드는 [repro/quic-go-min-repro](../repro/quic-go-min-repro)에 있다.

### 4.1 QUIC transport stream 실험 코드

| 파일 | 역할 |
| --- | --- |
| `cmd/server/main.go` | QUIC stream server |
| `cmd/client/main.go` | active migration을 수행하는 QUIC stream client |
| `internal/common/payload.go` | deterministic payload 생성과 checksum 검증 |
| `internal/common/logging.go` | JSONL/result JSON 기록 |
| `internal/common/tls.go` | self-signed TLS config |
| `internal/common/aws_nlb_cid.go` | AWS NLB용 QUIC-LB plaintext CID 생성 |

### 4.2 HTTP/3 workload 실험 코드

| 파일 | 역할 |
| --- | --- |
| `cmd/h3server/main.go` | HTTP/3 upload/download server |
| `cmd/h3client/main.go` | HTTP/3 workload client 및 migration trigger |
| `scripts/run-local-h3-workload.sh` | local post-migration HTTP/3 request gate |
| `scripts/run-local-h3-midflight.sh` | local mid-flight upload/download gate |
| `scripts/run-h3-client.sh` | local/AWS 공통 HTTP/3 client wrapper |
| `scripts/run-h3-server.sh` | local/AWS 공통 HTTP/3 server wrapper |

HTTP/3 client mode:

| mode | 의미 |
| --- | --- |
| `upload-download` | POST `/upload` 완료 후 migration, GET `/download` 수행 |
| `midflight-upload` | POST body reader가 threshold 도달 시 migration trigger |
| `midflight-download` | streaming GET response reader가 threshold 도달 시 migration trigger |

### 4.3 AWS 하네스

| 파일 | 역할 |
| --- | --- |
| `harness/scripts/run-aws-nlb-quic-data-plane.sh` | EC2 target A/B, NLB, target group, client 실행, artifact 수집, cleanup |
| `harness/scripts/aws-preflight.sh` | AWS CLI/auth/region 확인 |
| `harness/scripts/package-quic-go-ec2.sh` | EC2 업로드용 quic-go repro package 생성 |
| `harness/manifests/experiment-matrix.csv` | 실험 큐와 상태 |

## 5. 구현체 조사 결과

### 5.1 목적

교수님 피드백의 핵심은 다음이었다.

> 구현도 안 된 기술을 왜 안 쓰냐고 말하면 안 된다. 먼저 구현체별로 Connection Migration 성숙도를 조사해야 한다.

따라서 먼저 주요 QUIC 구현체의 Connection Migration 관련 source, API, test, observability를 조사했다.

### 5.2 조사 대상

| 분류 | 구현체/환경 |
| --- | --- |
| 직접 local test 실행 | quic-go, quiche, picoquic, s2n-quic, aioquic, ngtcp2, Quinn, Neqo |
| source/docs 조사 | mvfst, MsQuic, lsquic, nginx QUIC, quicly, XQUIC, Chromium/Cronet, HAProxy |
| 배포 환경 | AWS NLB, CloudFront, Cloudflare HTTP/3, reverse proxy |

### 5.3 결과

핵심 결과:

> Connection Migration은 구현체에 아예 없는 기능이 아니었다.

구현체별 역할:

| 구현체 | 관찰 결과 | 연구상 의미 |
| --- | --- | --- |
| quic-go | `AddPath -> Probe -> Switch` 기반 active migration 가능 | controlled baseline |
| quiche | PathEvent, qlog, active migration sample | migration lifecycle 관찰 |
| picoquic | NAT rebinding, false migration, preferred address 등 edge-case test 풍부 | edge-case maturity |
| s2n-quic | rebinding/migration policy test, CID provider 가능성 | AWS/NLB 연계 후보 |
| ngtcp2 | RFC guardrail test | 표준 동작 기준선 |
| Quinn/Neqo/aioquic | migration 관련 test evidence | 추가 구현체 근거 |
| HAProxy | HTTP/3는 지원하지만 QUIC CM은 제한/미지원 | negative control |
| Chromium/Cronet | migration policy hook 존재 | 후속 browser/client 실험 대상 |

해석:

> 현재까지는 "CM이 안 쓰이는 이유가 구현 부재 때문"이라고 단정하기 어렵다. 구현체 primitive는 존재하지만, API 노출, 관찰성, 배포 적합성은 구현체마다 다르다.

## 6. Local active migration 실험

### 6.1 목적

AWS나 proxy를 보기 전에, local direct-origin에서 active migration이 재현 가능한지 확인한다.

### 6.2 환경

```text
local client socket A
  -> QUIC connection
  -> local server

client adds socket B
  -> AddPath
  -> Probe
  -> Switch
  -> same connection continues
```

### 6.3 코드

주요 코드:

- `repro/quic-go-min-repro/cmd/client/main.go`
- `repro/quic-go-min-repro/cmd/server/main.go`

client 동작:

1. UDP socket A로 QUIC connection 생성.
2. before payload stream 전송.
3. UDP socket B 생성.
4. `conn.AddPath(trB)` 호출.
5. `path.Switch()`를 probe 전 호출해 `ErrPathNotValidated` 확인.
6. `path.Probe(ctx)`로 PATH_CHALLENGE/PATH_RESPONSE 수행.
7. `path.Switch()`로 active path 전환.
8. after payload stream 전송.
9. result JSON과 qlog 저장.

### 6.4 결과

결과: PASS

의미:

> controlled local direct-origin 환경에서 quic-go active migration을 재현할 수 있었다.

## 7. EC2 direct-origin positive control

### 7.1 목적

local이 아니라 public cloud direct path에서도 active migration이 성공하는지 확인한다.

### 7.2 환경

```text
local client
  -> public Internet
  -> EC2 QUIC server
```

중간에 NLB, CDN, proxy를 두지 않았다. 이 실험은 이후 복잡한 배포 경로 실험의 positive control이다.

### 7.3 결과

| 항목 | 값 |
| --- | --- |
| status | PASS |
| implementation | quic-go |
| deployment | EC2 direct origin |
| source tuple change | `211.60.158.133:64273 -> 211.60.158.133:58085` |
| workload | before/after 1MiB QUIC stream payload |
| evidence | qlog PATH_CHALLENGE/PATH_RESPONSE, pcap, client/server JSON |
| cleanup | EC2, SG, key pair 삭제 |

### 7.4 해석

> public cloud direct-origin에서도 active migration은 성공했다.

따라서 이후 HAProxy, NLB, CDN에서 실패가 나오더라도 이를 곧바로 "QUIC CM 자체가 안 된다"로 해석하면 안 된다.

## 8. quiche path-event timeline

### 8.1 목적

quic-go 외 구현체에서도 migration lifecycle을 관찰할 수 있는지 확인한다.

### 8.2 결과

quiche sample/client-server 기반으로 다음 lifecycle을 확인했다.

```text
new path observed
  -> PATH_CHALLENGE
  -> PATH_RESPONSE
  -> path validated
  -> connection migrated
```

### 8.3 해석

quiche는 `PathEvent`와 qlog 관찰성이 좋아서 논문에서 migration lifecycle 그림을 만들기 좋다.

## 9. HAProxy HTTP/3 negative control

### 9.1 목적

HTTP/3 endpoint availability와 Connection Migration support가 같은 것인지 확인한다.

### 9.2 환경

```text
quiche client
  -> HTTP/3
  -> HAProxy HTTP/3 frontend
  -> backend origin
```

### 9.3 결과

| 항목 | 값 |
| --- | --- |
| status | PASS_NEGATIVE_CONTROL |
| HAProxy | 3.4.0, QUIC enabled |
| baseline HTTP/3 request | 성공 |
| active migration attempt | 실패 |
| PATH_CHALLENGE | 3회 |
| PATH_RESPONSE | 0회 |
| final state | migrated path `validation_state=Failed` |

### 9.4 해석

> HTTP/3 지원은 Connection Migration 지원을 의미하지 않는다.

이 결과는 본 연구에서 매우 중요한 반례다. 실제 운영 환경에서 `h3`가 보인다고 해서 네트워크 전환 시 connection이 유지된다고 말할 수 없다.

## 10. AWS NLB QUIC feasibility와 CID provider

### 10.1 목적

AWS NLB가 QUIC/TCP_QUIC target group과 `QuicServerId` 기반 routing을 실제로 지원하는지 확인한다.

### 10.2 결과

| 항목 | 결과 |
| --- | --- |
| `QUIC` target group create/delete | PASS |
| `TCP_QUIC` target group create/delete | PASS |
| `QuicServerId` target registration | 지원 확인 |
| local CID provider proof | PASS |

AWS NLB에 맞춘 CID format:

```text
0x00 + 8-byte Server ID + 7-byte nonce
```

### 10.3 해석

AWS NLB 뒤에서 Connection Migration을 유지하려면 client source tuple 변화 자체보다 backend-generated CID의 Server ID encoding이 중요하다.

## 11. AWS NLB QUIC data-plane positive control

### 11.1 목적

실제 AWS NLB `QUIC` listener와 EC2 target A/B를 두고, migration 후에도 같은 target에 packet이 도달하는지 확인한다.

### 11.2 환경

```text
local quic-go client
  -> AWS NLB QUIC :4242
  -> EC2 target A / target B
```

target A/B는 각각 다른 8-byte Server ID를 갖는다.

### 11.3 결과

| 항목 | 값 |
| --- | --- |
| status | PASS |
| NLB protocol | `QUIC` |
| port | `4242` |
| target count | 2 |
| successful target | target-b |
| source tuple change | `211.60.158.133:55957 -> 211.60.158.133:59355` |
| workload | before/after 64KiB QUIC stream payload |
| qlog | PATH_CHALLENGE/PATH_RESPONSE |

### 11.4 해석

> AWS NLB는 backend CID가 registered `QuicServerId`를 올바르게 encode하면 migration 후에도 same-target continuity를 유지할 수 있다.

## 12. AWS NLB negative controls

### 12.1 목적

AWS NLB positive result가 우연이 아니라 CID 조건에 의존한다는 점을 확인한다.

### 12.2 결과

| negative control | 결과 | 의미 |
| --- | --- | --- |
| malformed CID layout | PASS_NEGATIVE_CONTROL | raw `8-byte Server ID + 8-byte nonce`는 payload continuity 실패 |
| CloudWatch evidence | observed | `QUIC_Unknown_Server_ID_Packet_Drop_Count` 관찰 |
| explicit Server ID mismatch | PASS_NEGATIVE_CONTROL | target health 2/2 healthy여도 handshake/application payload 실패 |

### 12.3 해석

> NLB QUIC migration은 단순히 QUIC/HTTP3를 켜면 되는 기능이 아니다. CID layout과 registered Server ID mapping이 정확히 맞아야 한다.

## 13. AWS NLB `TCP_QUIC :443` repeat

### 13.1 목적

custom high port가 아니라 실제 HTTP/3 배포에 가까운 `443` port와 `TCP_QUIC` protocol에서도 결과가 반복되는지 확인한다.

### 13.2 결과

| 항목 | 값 |
| --- | --- |
| status | PASS |
| NLB protocol | `TCP_QUIC` |
| port | `443` |
| source tuple change | `211.60.158.133:57897 -> 211.60.158.133:56632` |
| successful target | target-b |
| workload | before/after 64KiB QUIC stream payload |

### 13.3 해석

> AWS NLB CID-aware continuity는 `QUIC :4242`에만 묶이지 않고 `TCP_QUIC :443`에서도 재현되었다.

## 14. HTTP/3 post-migration request continuity

### 14.1 목적

custom QUIC stream이 아니라 HTTP/3 request에서도 migration 이후 작업이 계속되는지 확인한다.

### 14.2 Local HTTP/3 gate

실험 순서:

```text
POST /upload before
  -> AddPath -> Probe -> Switch
  -> GET /download after
```

결과:

| 항목 | 값 |
| --- | --- |
| status | PASS |
| protocol | HTTP/3 over QUIC |
| before task | POST `/upload`, 64KiB |
| after task | GET `/download`, 64KiB |
| source tuple change | `127.0.0.1:63819 -> 127.0.0.1:63361` |
| qlog | ALPN `h3`, HTTP/3 HEADERS/DATA, PATH_CHALLENGE/PATH_RESPONSE |

### 14.3 AWS NLB HTTP/3 gate

환경:

```text
local h3client
  -> AWS NLB TCP_QUIC :443
  -> h3server target A/B
```

결과:

| 항목 | 값 |
| --- | --- |
| status | PASS |
| protocol | `TCP_QUIC :443` |
| successful target | target-a |
| source tuple change | `211.60.158.133:54110 -> 211.60.158.133:50930` |
| workload | before POST `/upload`, after GET `/download` |
| cleanup | EC2, SG, key pair, NLB, TG 삭제 확인 |

### 14.4 해석

> controlled 조건에서는 transport continuity를 HTTP/3 request continuity로 확장할 수 있었다.

## 15. HTTP/3 mid-flight upload/download continuity

### 15.1 목적

request 사이가 아니라 HTTP/3 body 전송 중 migration이 발생해도 작업이 완료되는지 확인한다.

이 실험은 지금까지 수행한 HTTP/3 workload 중 작업 연속성에 가장 가깝다.

### 15.2 코드 방식

`cmd/h3client/main.go`에 두 mode를 추가했다.

| mode | 방식 |
| --- | --- |
| `midflight-upload` | request body reader가 threshold 이상 전송되면 migration trigger |
| `midflight-download` | streaming response reader가 threshold 이상 수신하면 migration trigger |

server는 `GET /download?stream=true` 요청에서 response body를 chunk 단위로 천천히 쓴다.

### 15.3 Local 결과

| workload | status | socket A | socket B | final addr | migration threshold | evidence |
| --- | --- | --- | --- | --- | ---: | --- |
| mid-flight upload | PASS | `[::]:53663` | `[::]:63569` | `[::]:63569` | 532480 bytes | server decoded 1MiB upload |
| mid-flight download | PASS | `[::]:49959` | `[::]:52767` | `[::]:52767` | 524288 bytes | client decoded 1MiB response |

### 15.4 AWS NLB 결과

| workload | status | target | socket A | socket B | evidence |
| --- | --- | --- | --- | --- | --- |
| mid-flight upload | PASS | target-a | `[::]:56276` | `[::]:52824` | target decoded 1MiB upload |
| mid-flight download | PASS | target-b | `[::]:61456` | `[::]:63381` | client decoded 1MiB streaming response |

download 첫 실행은 client dial 단계에서 `timeout: no recent network activity`로 실패했다. socket B 생성 전 실패였으므로 mid-flight migration failure가 아니라 NLB readiness timing 또는 transient handshake failure로 분류했다. target health 2/2 이후 client start delay를 둔 재시도는 PASS였다.

### 15.5 중요한 관찰

mid-flight case에서는 `path.Switch()` 직후 `conn.LocalAddr()`가 socket A로 남아 있을 수 있었다. 그러나 후속 packet 송수신 이후 workload 완료 시 final address는 socket B였다.

따라서 mid-flight migration 성공 기준은 다음 세 가지를 함께 봐야 한다.

1. final connection address가 socket B인지
2. qlog에 path validation evidence가 있는지
3. payload checksum/integrity가 맞는지

### 15.6 Local HTTP/3 반복실험

2026-06-24에 같은 local direct-origin 하네스를 새 `RUN_ID`로 재실행했다.

| workload | status | migration point | application result | qlog evidence |
| --- | --- | --- | --- | --- |
| post-migration upload/download | PASS | POST 완료 후 `AddPath -> Probe -> Switch` | 64KiB upload와 64KiB download 모두 `HTTP/3.0`, ALPN `h3` | client/server 모두 PATH_CHALLENGE/PATH_RESPONSE 2회 |
| mid-flight upload | PASS | 532480 bytes | server가 1MiB request body 전체 decode | client/server 모두 PATH_CHALLENGE/PATH_RESPONSE 2회 |
| mid-flight download | PASS | 524288 bytes | client가 1MiB streaming response 전체 decode | client/server 모두 PATH_CHALLENGE/PATH_RESPONSE 2회 |

상세 결과는 [quic-go local HTTP/3 migration replication results](results/quic-go-local-h3-replication-results-20260624.md)에 정리했다.

이 반복실험은 controlled local direct-origin에서 HTTP/3 작업 연속성 결과가 재현됨을 보강한다. 다만 browser Wi-Fi/LTE handover나 CDN/proxy/LB 경로의 성공을 직접 의미하지는 않는다.

## 16. 현재까지 말할 수 있는 결론

현재까지의 실험으로 말할 수 있는 것은 다음이다.

1. QUIC Connection Migration은 여러 구현체에서 실제로 구현되고 테스트된다.
2. quic-go는 active migration을 deterministic하게 재현할 수 있다.
3. EC2 direct-origin에서는 active migration이 성공한다.
4. HAProxy처럼 HTTP/3를 지원해도 active migration을 지원하지 않는 proxy가 있다.
5. AWS NLB는 CID-aware routing 조건을 맞추면 active migration 후 same-target continuity를 유지할 수 있다.
6. AWS NLB의 성공 조건은 CID format과 registered `QuicServerId` mapping에 민감하다.
7. `TCP_QUIC :443`에서도 QUIC stream continuity와 HTTP/3 request continuity가 관찰됐다.
8. controlled quic-go client 조건에서는 HTTP/3 upload/download body 전송 중 migration도 local과 AWS NLB에서 통과했고, local direct-origin 반복실험에서도 같은 방향으로 재현됐다.
9. Chrome 149 headless browser는 local quic-go H3 origin으로 단일 HTTP/3 request, page+subresource sequence request, sequential polling workload, slow streaming subresource workload를 보낼 수 있었다.
10. inactive interface service toggle은 Chrome slow workload를 깨지 않았지만 실제 QUIC path migration evidence를 만들지는 못했다.
11. Chrome slow workload는 local Wi-Fi IP origin에서도 HTTP/3로 성립했지만, inactive service toggle은 여전히 path migration evidence를 만들지 못했다.
12. Chrome natural Alt-Svc control에서는 local self-signed 또는 mkcert origin이 h3를 광고했지만, forced QUIC 없이 실제 HTTP/3 application request가 관찰되지는 않았다. HTML diagnostic에서는 QUIC/H3 후보 연결이 열렸지만 `certificate unknown / CERTIFICATE_VERIFY_FAILED` 또는 broken alternative service로 끝났다.
13. 초기 public WebPKI control에서는 Google, YouTube, Cloudflare trace endpoint가 H3 discovery 또는 QUIC session 단서를 만들었지만 application/main request H3를 확정하지 못했다.
14. 확장 public browser 후보 실험에서는 `blog.cloudflare.com`, `www.bing.com`, `www.facebook.com`, `www.instagram.com`에서 Chrome natural H3 application job이 관찰됐다. 그러나 제3자 페이지는 server-side qlog, workload, active path-change, backend routing을 통제할 수 없으므로 CM 성공 증거가 아니라 browser public H3 capability evidence로만 해석한다.
15. public Alt-Svc survey에서는 20개 endpoint 중 12개가 H3 Alt-Svc를 광고했고, 그중 7개가 2xx workload 후보였다. GitHub/Naver/Kakao/Apple/Wikipedia/Microsoft/Netflix/TikTok은 이번 관찰에서 H3 workload 후보가 아니었다.

요약하면:

> Connection Migration은 controlled 조건에서는 동작하고 HTTP/3 작업까지 이어질 수 있다.

그리고 browser 계층에서는 다음이 추가로 분리됐다.

> Chrome은 forced local baseline뿐 아니라 일부 public WebPKI page에서도 HTTP/3 application job을 만들 수 있다. 다만 local self-signed/mkcert Alt-Svc 실험과 third-party public page evidence는 controlled public application H3 baseline과 active CM 실험을 대체하지 못한다.

## 17. 아직 말하면 안 되는 결론

아직 다음은 말하면 안 된다.

1. HTTP/3 Connection Migration이 웹 작업 연속성을 보장한다.
2. Chrome/Android에서 Wi-Fi/LTE 전환 시 동일하게 Connection Migration이 동작한다.
3. CloudFront/CDN 환경에서 origin end-to-end CM이 유지된다.
4. 모든 upload/download/dashboard 작업이 migration 중 성공한다.
5. 모든 QUIC 구현체가 deployable maturity를 갖췄다.
6. Alt-Svc를 광고하기만 하면 browser가 항상 HTTP/3를 선택한다.
7. public WebPKI H3 discovery 또는 `QUIC_SESSION` evidence만으로 application request가 HTTP/3로 처리됐다고 말한다.
8. public WebPKI discovery control이 관찰됐으므로 Chrome browser network change에서도 곧바로 Connection Migration이 성공한다고 말한다.

현재 연구의 정직한 결론은 다음이다.

> 특정 조건에서는 된다. 하지만 그 조건이 실제 웹/모바일 배포에서 얼마나 자주 충족되는지는 추가 검증이 필요하다.

## 18. 다음 연구 방향

### 18.1 CloudFront viewer-edge limited control

목표:

- CloudFront HTTP/3 Connection Migration이 viewer-edge continuity인지 origin end-to-end continuity인지 분리한다.

검증할 것:

- client가 CloudFront edge와 HTTP/3를 사용하는지
- origin이 client QUIC connection을 직접 관찰할 수 없는지
- network change 중 request/download continuity가 viewer-edge 수준에서 유지되는지

### 18.2 Cronet/Android workload

목표:

- controlled quic-go 결과가 실제 client policy에서도 재현되는지 확인한다.

workload:

- large upload
- streaming download
- dashboard polling 또는 SSE-like update

측정:

- task success/failure
- retry count
- stall time
- recovery time
- Android network callback
- Cronet NetLog
- server qlog

### 18.3 Chrome browser network-change workload

목표:

- Chrome browser baseline을 network-change 실험으로 확장한다.

검증할 것:

- Chrome NetLog에서 기존 HTTP/3 session이 network change 후 유지되는지
- server qlog에서 path validation 또는 새 connection 생성 중 무엇이 관찰되는지
- upload/download/dashboard 작업이 reload 없이 완료되는지
- 실패 시 Chrome policy, TLS, server compatibility, application layer 중 어느 계층에서 실패하는지

현재 확보한 baseline:

- `GET /download` 단일 request baseline
- `GET /browser-sequence` HTML page + two `GET /pixel` subresource sequence baseline
- sequence baseline에서 target QUIC session 1개, `using_quic=true` stream job 3개, server request 3개가 관찰됨
- `GET /browser-poll` HTML page + five sequential `GET /poll` fetch baseline
- polling no-change baseline에서 classifier는 `no_path_change_baseline`을 반환함
- `GET /browser-slow` HTML page + streaming `GET /slow-js` subresource limited control
- inactive `Thunderbolt Bridge` off/on hook은 `exit=0`이었지만, server tuple change와 qlog path validation은 없었음
- `LISTEN_ADDR=0.0.0.0:4443`, `ORIGIN_ADDR=<Wi-Fi IP>:4443` non-loopback local origin baseline
- Wi-Fi IP origin에서도 inactive service toggle은 active path migration을 만들지 못함

- `run-chrome-h3-alt-svc.sh` natural Alt-Svc control에서 `127.0.0.1`과 `localhost` binary response는 server request가 `HTTP/1.1`로만 기록됐고 qlog `http3_frame=0`이었음
- HTML page/subresource diagnostic에서는 QUIC/H3 후보 연결과 qlog `http3_frame=1`이 생겼지만, connection close reason이 `certificate unknown / CERTIFICATE_VERIFY_FAILED`였고 application request 4개는 모두 `HTTP/1.1`이었음
- mkcert localhost diagnostic에서는 certificate failure가 사라졌지만 target QUIC alternative service가 `broken_alternative_services`로 기록됐고 application request는 모두 `HTTP/1.1`이었음
- mkcert `127.0.0.1` diagnostic에서는 QUIC/H3 후보 연결이 다시 certificate verification failure로 닫혔고 application request는 모두 `HTTP/1.1`이었음
- public WebPKI Cloudflare QUIC trace endpoint에서는 forced QUIC 없이 target `QUIC_SESSION=1`과 `dns_alpn_h3` discovery job이 관찰됐지만, application/main job은 non-QUIC였음
- public WebPKI Google `generate_204` endpoint에서는 bootstrap/second NetLog 모두 JSON으로 파싱됐고 target `QUIC_SESSION`과 `dns_alpn_h3` discovery job이 관찰됐지만, application/main job은 non-QUIC였음
- public WebPKI YouTube `generate_204` endpoint에서는 H3 Alt-Svc와 `dns_alpn_h3` discovery job이 관찰됐지만 target `QUIC_SESSION=0`, application/main job non-QUIC로 분류됐음
- public Alt-Svc survey에서 `github.com`, `naver.com`, `kakao.com`은 이번 관찰 시점의 browser H3 target 후보가 아니었음
- `amazon.com`은 H3 Alt-Svc를 광고했지만 status가 `HTTP/2 503`이라 안정적인 workload target으로 쓰기 어려움
- readiness 점검에서 ADB는 설치돼 있었지만 연결된 Android device가 없었고, active 일반 네트워크 interface는 Wi-Fi `en0`만 확인됐음
- controlled public WebPKI origin gate를 위해 DNS/TLS/Alt-Svc readiness checker, public H3 server wrapper, Chrome public browser baseline wrapper를 추가했음
- controlled public browser baseline wrapper는 Google `generate_204` smoke test에서 실행 흐름은 검증됐지만, 새 classifier 기준으로는 `public_h3_discovery_without_application_h3` negative control로 재분류됨
- public origin readiness survey에서는 Google/YouTube `generate_204`만 H3 discovery와 2xx lightweight workload 후보로 남았음
- controlled public application H3 gate를 위해 server request log, server qlog, Chrome public NetLog summary, readiness JSON을 합치는 `classify_controlled_public_h3_baseline.py`를 추가했음
- local regression에서 forced H3 artifact는 `PASS_FEASIBILITY`, H1-only Alt-Svc artifact는 `PASS_NEGATIVE_CONTROL`로 분리되어 gate가 application H3와 discovery-only/H1-only를 구분함을 확인했음
- controlled public network-change 하네스와 `classify_controlled_public_h3_network_change.py`를 추가해 baseline PASS 이후 tuple change, qlog path validation, Chrome QUIC session evidence를 함께 분류할 수 있게 했음
- Safari와 Android Chrome용 controlled public network-change wrapper를 추가했지만, 두 경로는 browser-internal QUIC session log가 없으므로 `PASS_FEASIBILITY` 수준으로만 해석해야 함
- 최종 browser handover experiment protocol을 추가해 Chrome/Safari/Android trial 반복 수, evidence gate, claim strength를 고정했음
- controlled public experiment readiness checker를 추가했고, 현재 환경은 Chrome과 harness는 준비됐지만 public origin URL, application H3 baseline PASS summary, active secondary path, `NETWORK_CHANGE_CMD`가 없어 real network-change 실행 조건을 만족하지 못함

이 baseline은 network path change를 포함하지 않는다. 따라서 다음 단계에서는 controlled public WebPKI origin에서 application HTTP/3 no-change baseline을 먼저 통과시킨 뒤, 같은 browser workload를 유지한 채 network-change trigger만 추가해야 한다.

network-change 판정 기준:

| classification | 해석 |
| --- | --- |
| `possible_connection_migration` | remote tuple change + qlog path validation + target QUIC session 1개 |
| `reconnect_or_multiple_sessions` | remote tuple change가 있으나 target QUIC session이 여러 개 |
| `tuple_changed_without_path_validation` | server tuple은 바뀌었지만 qlog path validation이 없음 |
| `browser_h3_request_failed` | workload 자체가 완료되지 않음 |
| `no_path_change_baseline` | network change가 관찰되지 않음 |

### 18.4 실제 Wi-Fi/LTE handover

목표:

- source-port migration이 아니라 실제 interface/network change에서 어떤 일이 발생하는지 확인한다.

핵심 질문:

- Chrome/Cronet이 migration을 trigger하는가?
- migration timing은 path validation delay와 어떻게 연결되는가?
- application workload는 transport migration과 별개로 실패하는가?

현재 local Chrome control에서 확인한 점:

- inactive service toggle은 active Wi-Fi path를 바꾸지 않는다.
- loopback origin에서는 server remote tuple이 바뀌지 않는다.
- local Wi-Fi IP origin은 loopback보다는 나은 browser baseline이지만, 같은 머신의 active route가 바뀌지 않으면 migration evidence가 나오지 않는다.
- 따라서 실제 browser CM 검증에는 public/non-loopback origin과 active interface 전환이 필요하다.
- 또한 browser가 target origin을 application HTTP/3로 처리했다는 evidence를 먼저 확보해야 한다. local self-signed/mkcert Alt-Svc control과 third-party public endpoint NetLog만으로는 충분하지 않았다.
- public WebPKI origin에서는 H3 discovery control이 확보됐지만, 이는 migration evidence도 application HTTP/3 evidence도 아니다.
- 현재 장비 상태에서는 active secondary network와 Android device가 확인되지 않았으므로 실제 handover 실험은 준비 후 실행해야 한다.
- third-party public H3 endpoint는 discovery control에는 유용하지만 upload/download/dashboard workload continuity 실험에는 controlled public origin이 필요하다.
- Chromium/Cronet source evidence상 browser stack에는 migration hook과 NetLog event가 있지만, runtime policy와 embedding default가 실제 migration 여부를 좌우한다.

## 19. 참고 데이터

정량/상태 요약:

- [실험 결과 CSV](../data/experiment-results.csv)
- [구현체 조사 CSV](../data/implementation-survey.csv)
- [handover readiness JSON](../data/handover-readiness-20260624.json)
- [문헌 조사 CSV](../data/literature-review-tracker.csv)
- [public Alt-Svc endpoint survey CSV](../data/public-alt-svc-survey-20260624.csv)
- [public origin readiness survey CSV](../data/public-origin-readiness-survey-20260624.csv)
- [quiche path-event timeline](../data/quiche-path-event-timeline.csv)

개별 결과 문서:

- [EC2 direct-origin 결과](results/aws-direct-origin-results-20260623.md)
- [HAProxy negative control 결과](results/haproxy-http3-negative-control-results-20260623.md)
- [AWS NLB QUIC data-plane 결과](results/aws-nlb-quic-data-plane-results-20260624.md)
- [AWS NLB negative control 결과](results/aws-nlb-quic-negative-control-results-20260624.md)
- [AWS NLB TCP_QUIC 443 결과](results/aws-nlb-tcp-quic-443-results-20260624.md)
- [HTTP/3 local workload 결과](results/quic-go-h3-local-workload-results-20260624.md)
- [AWS NLB HTTP/3 workload 결과](results/aws-nlb-http3-workload-results-20260624.md)
- [HTTP/3 mid-flight 결과](results/aws-nlb-http3-midflight-results-20260624.md)
- [Chrome local HTTP/3 baseline 결과](results/chrome-h3-local-baseline-results-20260624.md)
- [Chrome local HTTP/3 sequence baseline 결과](results/chrome-h3-local-sequence-results-20260624.md)
- [Chrome local HTTP/3 polling no-change baseline 결과](results/chrome-h3-poll-nochange-results-20260624.md)
- [Chrome slow HTTP/3 inactive interface toggle 결과](results/chrome-h3-slow-inactive-if-toggle-results-20260624.md)
- [Chrome Wi-Fi IP HTTP/3 limited control 결과](results/chrome-h3-wifi-ip-limited-control-results-20260624.md)
- [Chromium/Cronet source evidence](results/chromium-cronet-source-evidence-20260624.md)
- [Chrome natural Alt-Svc HTTP/3 control 결과](results/chrome-h3-alt-svc-natural-results-20260624.md)
- [Chrome public H3 discovery baseline 결과](results/chrome-public-natural-h3-results-20260624.md)
- [Public HTTP/3 Alt-Svc endpoint survey](results/public-alt-svc-endpoint-survey-20260624.md)
- [Public origin readiness survey](results/public-origin-readiness-survey-20260624.md)
- [Browser handover readiness and next experiment plan](results/browser-handover-readiness-plan-20260624.md)
- [Controlled public WebPKI H3 origin plan](results/controlled-public-origin-h3-plan-20260624.md)
- [Controlled public application H3 evidence gate](results/controlled-public-application-h3-gate-20260624.md)
- [Controlled public Chrome H3 network-change harness](results/controlled-public-network-change-harness-20260624.md)
- [Safari controlled public H3 network-change harness](results/safari-controlled-public-network-change-harness-20260624.md)
- [Android Chrome controlled public H3 network-change harness](results/android-chrome-controlled-public-network-change-harness-20260624.md)
- [Final browser handover experiment protocol](results/final-browser-handover-experiment-protocol-20260624.md)
- [Controlled public experiment readiness](results/controlled-public-experiment-readiness-20260624.md)
