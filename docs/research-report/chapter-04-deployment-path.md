# Chapter 4. 배포 경로 검수: AWS NLB, Proxy, CDN

작성일: `2026-06-30`

## 1. 이 챕터의 목적

Chapter 3는 controlled QUIC client/server에서 CM이 실제로 동작함을 보여줬다. 하지만 실제 서비스는 대개 load balancer, proxy, CDN, edge termination을 거친다. 따라서 Chapter 4의 질문은 다음이다.

> Connection Migration이 transport library에서는 되더라도, 실제 배포 경로의 LB/CDN/proxy는 이를 보존하는가?

이 챕터는 “AWS NLB에서는 된다”, “HAProxy에서는 안 된다” 같은 단순 결론이 아니다. 더 정확히는 배포 경로마다 CM의 의미가 달라진다는 것을 보인다.

## 2. 핵심 결론

현재 증거 기준에서 안전한 결론은 다음이다.

> CID-aware load balancing은 Connection Migration을 보존할 수 있지만, HTTP/3 support 또는 target health만으로 CM support를 추론할 수는 없다. AWS NLB QUIC/TCP_QUIC positive control은 routable CID가 맞을 때 같은 target continuity를 보였고, HAProxy 및 AWS malformed CID negative control은 HTTP/3/proxy/LB 존재만으로는 충분하지 않음을 보여줬다.

## 3. AWS NLB Positive Control

AWS NLB 경로에서 확인한 positive control은 두 단계다.

| 실험 | 결과 | 의미 |
| --- | --- | --- |
| NLB `QUIC` data-plane | PASS | custom QUIC stream payload가 active source-port migration 후 같은 target에 도달 |
| NLB `TCP_QUIC :443` HTTP/3 workload | PASS | HTTP/3 POST before request 이후 active migration, GET after request 성공 |

핵심 조건:

| 조건 | 값 |
| --- | --- |
| backend | `quic-go` custom server/client |
| CID format | `0x00 + 8-byte Server ID + 7-byte nonce` |
| migration trigger | `AddPath -> Probe -> Switch` |
| evidence | qlog `PATH_CHALLENGE`/`PATH_RESPONSE`, before/after payload 또는 request continuity |
| cleanup | temporary NLB, target group, instances, security group, key pair deleted |

중요한 해석:

> AWS NLB positive control은 “CID-aware deployment path에서는 migration continuity가 가능하다”는 근거다. Chrome browser handover 성공이나 CDN end-to-end CM 성공을 의미하지 않는다.

## 4. AWS NLB Negative Control

positive control의 반대쪽 근거도 확보했다.

| negative control | 조건 | 결과 | 의미 |
| --- | --- | --- | --- |
| malformed CID layout | `8-byte Server ID + 8-byte nonce` | payload delivery 실패 | NLB가 기대하는 QUIC-LB plaintext layout과 맞아야 함 |
| Server ID mismatch | target registration Server ID와 backend-generated CID Server ID 불일치 | handshake/response 실패 | target health와 routable CID correctness는 별개 |

논문에서 쓸 수 있는 문장:

> CID-aware load balancing is a deployability contract. The load balancer may support QUIC, and targets may be healthy, but migrated packets are only routable when backend-generated CIDs follow the load balancer's expected Server ID layout.

## 5. HAProxy Negative Control

HAProxy local HTTP/3 negative control은 다음을 보여줬다.

| 항목 | 결과 |
| --- | --- |
| ordinary HTTP/3 request | PASS |
| quiche no-migration request | PASS |
| quiche `--perform-migration` | failed as expected |
| qlog | `PATH_CHALLENGE` observed, `PATH_RESPONSE` absent |

해석:

> HTTP/3 endpoint availability is not evidence of active Connection Migration support.

이 결과는 proxy 계층에서 특히 중요하다. Proxy가 QUIC을 terminate하면, viewer/proxy 구간의 continuity와 proxy/origin 구간의 continuity가 분리된다.

## 6. CDN/Edge 해석

CDN은 별도로 해석해야 한다.

| 배포 유형 | CM 해석 |
| --- | --- |
| direct origin | browser-origin 사이의 QUIC path evidence를 직접 볼 수 있음 |
| CID-aware NLB | tuple change 후 같은 backend로 routing되는지 확인 필요 |
| reverse proxy | proxy가 QUIC을 terminate하면 end-to-end CM이 끊길 수 있음 |
| managed CDN edge | viewer-edge continuity일 수 있으며 origin end-to-end CM과 다름 |

따라서 CloudFront/Cloudflare 같은 managed edge에서 HTTP/3가 켜져 있더라도, 논문에서는 다음처럼 표현해야 한다.

> managed edge-level HTTP/3 continuity, not necessarily end-to-end origin QUIC Connection Migration.

## 7. 논문에 쓸 수 있는 주장

안전한 주장:

> Deployment support is an independent maturity axis. A QUIC implementation may support migration, but a production path must also preserve routable connection IDs or terminate the semantics at a clearly identified edge.

피해야 할 주장:

| 피해야 할 주장 | 이유 |
| --- | --- |
| “AWS NLB HTTP/3 성공은 모든 AWS/CDN CM 성공을 뜻한다.” | NLB CID-aware passthrough와 CDN edge termination은 다르다. |
| “HTTP/3 proxy가 있으면 CM도 된다.” | HAProxy negative control과 충돌한다. |
| “target health가 정상이면 migration도 라우팅된다.” | Server ID/CID mismatch negative control과 충돌한다. |
| “CloudFront/Cloudflare H3 support는 origin end-to-end CM이다.” | viewer-edge termination 가능성이 있다. |

## 8. 다음 챕터로 넘어간 이유

구현체와 deployment positive/negative control을 확보했더라도, 논문의 중심은 browser web application continuity다. 따라서 다음 질문은 브라우저에서 어떤 증거가 있어야 CM이라고 말할 수 있는지다.

> Chrome/Safari/Android에서 browser-level CM을 어떤 evidence chain으로 검증할 수 있는가?

이 질문이 Chapter 5의 출발점이다.

## 9. 검수 결과

| 검수 항목 | 결과 |
| --- | --- |
| AWS NLB positive/negative control 분리 | PASS |
| proxy/CDN edge 해석 분리 | PASS |
| 공식 AWS/HAProxy/Cloudflare 문서 링크 | `chapter-04-reference-and-evidence.md`에 정리 |
| 구현 코드 링크 | `aws_nlb_cid.go`, NLB harness script로 연결 |
| 민감정보 처리 | 새 보고용 문서에는 공인 IP, hostname, instance ID, account ID, SSH target을 쓰지 않음 |
| claim boundary | browser handover 또는 CDN origin-end-to-end CM claim을 하지 않음 |
