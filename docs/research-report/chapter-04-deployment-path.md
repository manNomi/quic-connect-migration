# Chapter 4. 배포 경로 검수: AWS NLB, Proxy, CDN

작성일: `2026-06-30`

## 1. 이 챕터의 목적

Chapter 3는 controlled QUIC client/server에서 CM이 실제로 동작함을 보여줬다. 하지만 실제 서비스는 대개 load balancer, proxy, CDN, edge termination을 거친다. 따라서 Chapter 4의 질문은 다음이다.

> Connection Migration이 transport library에서는 되더라도, 실제 배포 경로의 LB/CDN/proxy는 이를 보존하는가?

이 챕터는 “AWS NLB에서는 된다”, “HAProxy에서는 안 된다” 같은 단순 결론이 아니다. 더 정확히는 배포 경로마다 CM의 의미가 달라진다는 것을 보인다.

## 2. 핵심 결론

현재 증거 기준에서 안전한 결론은 다음이다.

> CID-aware load balancing은 Connection Migration을 보존할 수 있지만, HTTP/3 support 또는 target health만으로 CM support를 추론할 수는 없다. AWS NLB QUIC/TCP_QUIC positive control은 routable CID가 맞을 때 같은 target continuity를 보였고, HAProxy 및 AWS malformed CID negative control은 HTTP/3/proxy/LB 존재만으로는 충분하지 않음을 보여줬다.

## 3. AWS NLB와 HAProxy를 고른 이유

두 대상을 고른 이유는 둘 다 실제 웹 배포에서 흔히 등장하는 중간 경로지만, QUIC Connection Migration을 깨뜨리거나 보존하는 방식이 서로 다르기 때문이다.

| 대상 | 왜 골랐는가 | 연구에서의 역할 |
| --- | --- | --- |
| AWS NLB | QUIC/TCP_QUIC listener와 target group을 제공하고, QUIC Connection ID의 Server ID를 이용해 tuple 변화 후에도 같은 backend target으로 보낼 수 있는 CID-aware load balancing 경로이기 때문 | "배포 경로가 CM을 보존할 수 있다"는 positive control |
| HAProxy | HTTP/3 proxy로 실제 서비스 앞단에 둘 수 있고, QUIC을 client-facing endpoint로 terminate할 수 있는 대표적인 proxy 계층이기 때문 | "HTTP/3 proxy support가 CM support는 아니다"를 보이는 negative control |

즉 AWS NLB는 "QUIC connection을 backend까지 살려서 보낼 수 있는가"를 보는 대상이고, HAProxy는 "proxy가 HTTP/3를 처리할 수 있어도 client-facing active migration을 유지할 수 있는가"를 보는 대상이다.

이 둘을 같이 보면 배포 경로의 차이를 분리할 수 있다.

```text
NLB passthrough:
client <==== QUIC connection ====> backend server
              NLB는 CID 기반 routing

Proxy termination:
client <==== QUIC connection ====> HAProxy <==== 별도 연결 ====> origin
```

따라서 NLB와 HAProxy는 "중간 장비"라는 점은 같지만, CM에서 검증하는 실패 지점이 다르다. NLB는 같은 backend로 라우팅되는지가 핵심이고, HAProxy는 proxy 자신이 client-facing QUIC migration을 처리하는지가 핵심이다.

## 4. AWS NLB와 HAProxy의 차이

| 구분 | AWS NLB | HAProxy |
| --- | --- | --- |
| 계층/역할 | L4 load balancer에 가까움 | reverse proxy / HTTP proxy |
| QUIC endpoint 여부 | QUIC을 종단하지 않고 backend로 보존하는 경로로 사용 | client-facing QUIC/HTTP3 endpoint가 될 수 있음 |
| 핵심 기능 | Connection ID를 보고 같은 backend target으로 routing | client request를 받아 처리하고 origin으로 별도 forwarding |
| CM에서 중요한 조건 | CID-aware routing, Server ID layout, target registration | proxy의 path validation, migration handling, buffering/timeout 정책 |
| 성공하면 의미하는 것 | client-backend QUIC connection continuity가 배포 경로를 통과함 | client-proxy 구간 continuity 또는 HTTP/3 proxying 가능성 |
| 실패하면 의미하는 것 | CID routing contract가 깨졌거나 같은 backend continuity가 실패 | HTTP/3 proxy 가능성과 active CM support가 분리됨 |

NLB에서 CM이 성공했다는 말은 client의 tuple이 바뀐 뒤에도 NLB가 Connection ID를 보고 같은 backend로 packet을 보냈고, backend QUIC server가 path validation과 payload/request continuity를 유지했다는 뜻이다.

HAProxy에서 HTTP/3 request가 성공했다는 말은 client가 HAProxy와 HTTP/3 통신을 할 수 있었다는 뜻이다. 그러나 active migration이 실패했다면, client의 네트워크 path 변화 후에도 같은 client-facing QUIC connection이 유지됐다고 말할 수 없다.

그래서 두 실험의 결론은 서로 다르다.

```text
AWS NLB:
CID-aware passthrough path에서는 CM continuity가 가능할 수 있다.

HAProxy:
HTTP/3 proxy support만으로 active CM support를 주장할 수 없다.
```

## 5. AWS NLB Positive Control

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

## 6. AWS NLB Negative Control

positive control의 반대쪽 근거도 확보했다.

| negative control | 조건 | 결과 | 의미 |
| --- | --- | --- | --- |
| malformed CID layout | `8-byte Server ID + 8-byte nonce` | payload delivery 실패 | NLB가 기대하는 QUIC-LB plaintext layout과 맞아야 함 |
| Server ID mismatch | target registration Server ID와 backend-generated CID Server ID 불일치 | handshake/response 실패 | target health와 routable CID correctness는 별개 |

논문에서 쓸 수 있는 문장:

> CID-aware load balancing is a deployability contract. The load balancer may support QUIC, and targets may be healthy, but migrated packets are only routable when backend-generated CIDs follow the load balancer's expected Server ID layout.

## 6.1 s2n-quic AWS NLB Follow-up Readiness

s2n-quic은 AWS NLB와의 연결성이 높은 구현체지만, quic-go 기반 NLB success를 곧바로 s2n success로 일반화하면 안 된다. 그래서 dedicated s2n live experiment 전제 조건을 별도 readiness gate로 분리했다.

| 항목 | 최신 결과 | 의미 |
| --- | --- | --- |
| runner | `harness/scripts/check-s2n-nlb-live-readiness.sh` | live AWS resource 생성 전 public-safe gate |
| AWS identity | `aws_identity_ok=no`, `aws_identity_classification=invalid_client_token` | 현재 live AWS resource 생성 금지 |
| local s2n CID proof | `local_proof_status=PASS`, `local_proof_echo_matches=yes` | custom CID provider와 local s2n echo 전제 조건은 통과 |
| existing NLB runner | `existing_quic_go_nlb_runner_ready=yes` | 기존 live runner는 quic-go 경로를 커버 |
| dedicated s2n live runner | `s2n_live_nlb_runner_ready=yes` | s2n target A/B용 live runner는 준비됨 |
| fail-closed live run | `validation=blocked`, `blocked_reason=aws_identity_invalid_client_token` | runner가 AWS resource 생성 전에 안전하게 중단됨 |
| active migration API audit | `public_active_trigger_api_found=False`, focused test `10 passed` | s2n은 migration/rebinding machinery는 있으나 public app API에서 quic-go식 active trigger는 확인되지 않음 |

따라서 현재 s2n NLB claim은 "local provider prerequisite ready", "dedicated live runner ready", "migration/rebinding tests present but public app trigger not exposed"까지다. AWS NLB 뒤에서 s2n target이 packet을 받는지는 현재 credential 때문에 아직 검증하지 않았다. 또한 지금 live runner의 1단계 목표는 forwarding echo이며, active migration/path-change variant는 public API 변화 또는 lower-level IO/proxy 설계가 필요한 그 다음 단계다.

## 7. HAProxy Negative Control

HAProxy local HTTP/3 negative control은 다음을 보여줬다.

| 항목 | 결과 |
| --- | --- |
| ordinary HTTP/3 request | PASS |
| quiche no-migration request | PASS |
| quiche `--perform-migration` | failed as expected |
| qlog | `path_challenge=3`, `path_response=0` |
| fresh runner | `harness/scripts/run-haproxy-http3-negative-control.sh`, `validation=ok_negative_control` |

해석:

> HTTP/3 endpoint availability is not evidence of active Connection Migration support.

이 결과는 proxy 계층에서 특히 중요하다. Proxy가 QUIC을 terminate하면, viewer/proxy 구간의 continuity와 proxy/origin 구간의 continuity가 분리된다.

## 7.1 nginx Server Runtime Contrast

HAProxy negative-control과 반대로, nginx QUIC은 origin/web-server 계층에서 server-side runtime positive evidence를 확보했다.

| 항목 | 결과 |
| --- | --- |
| runner | `harness/scripts/run-nginx-quic-active-migration-demo.sh` |
| latest run | `nginx-quic-active-migration-20260630T104724Z` |
| workload | quiche client `--perform-migration`, nginx `GET /file-1M` |
| application result | `client_response_bytes=1048576`, access log `HTTP/3.0 200` |
| path evidence | server `quic path seq:1 created`, `PATH_CHALLENGE`/`PATH_RESPONSE`, `successfully validated` |

해석:

> nginx runtime demo는 "서버 구현체가 active client migration을 처리할 수 있다"는 근거다. 그러나 이는 proxy/CDN/LB 경로가 같은 semantics를 보존한다는 뜻은 아니며, browser handover claim도 아니다.

Linux `quic_bpf` production-routing claim은 별도다. `harness/scripts/check-nginx-quic-bpf-readiness.sh` 최신 local run은 source, migration file, runtime demo script, HTTP/3 module build는 `yes`였지만 현재 host가 Darwin이라 `can_run_linux_quic_bpf_now=no`, `blocked_reason=linux_required`로 닫혔다. 추가로 `harness/scripts/run-nginx-quic-bpf-linux-demo.sh`를 준비해 Linux/root/`/sys/fs/bpf` gate가 열릴 때 기존 active migration workload를 `quic_bpf on;`과 `listen ... reuseport`로 실행할 수 있게 했다. 현재 local run은 `validation=blocked`, `blocked_reason=linux_required`다. 따라서 nginx에 대해서는 local server runtime positive control과 Linux runner readiness까지만 말하고, Linux/eBPF packet-routing deployment success는 후속으로 남긴다.

## 7.2 OpenLiteSpeed Follow-up Packet

LSQUIC example demo는 이미 preferred-address와 NAT rebinding app-level positive control을 제공하지만, production-like server integration은 별도 검증이 필요하다. 이를 위해 OpenLiteSpeed follow-up을 세 단계로 분리했다.

| 단계 | 상태 | 의미 |
| --- | --- | --- |
| source feasibility | 완료 | OpenLiteSpeed source에서 LSQUIC HTTP/3 server engine, `quicEnable`, SCID callback, CID/SHM routing hook 확인 |
| runtime preflight | 완료 | 현재 macOS local은 `runtime_ready=no`; binary, Linux `/dev/shm`, disk gate가 닫힘 |
| runtime runner | 완료 | `harness/scripts/run-openlitespeed-active-migration-demo.sh`가 Linux/EC2에서 config test, 1MiB H3 response, active migration path evidence를 검증하도록 준비됨 |

현재 로컬 실행은 `validation=blocked`, `blocked_reason=missing-openlitespeed-binary`다. 따라서 OpenLiteSpeed에 대해 아직 success/failure를 말하지 않고, Linux/EC2에서 runner를 실행한 뒤 `result.env`의 validation과 `migration-grep.log`를 근거로 claim을 갱신한다.

## 8. CDN/Edge 해석

CDN은 별도로 해석해야 한다.

| 배포 유형 | CM 해석 |
| --- | --- |
| direct origin | browser-origin 사이의 QUIC path evidence를 직접 볼 수 있음 |
| CID-aware NLB | tuple change 후 같은 backend로 routing되는지 확인 필요 |
| reverse proxy | proxy가 QUIC을 terminate하면 end-to-end CM이 끊길 수 있음 |
| managed CDN edge | viewer-edge continuity일 수 있으며 origin end-to-end CM과 다름 |

따라서 CloudFront/Cloudflare 같은 managed edge에서 HTTP/3가 켜져 있더라도, 논문에서는 다음처럼 표현해야 한다.

> managed edge-level HTTP/3 continuity, not necessarily end-to-end origin QUIC Connection Migration.

## 9. 논문에 쓸 수 있는 주장

안전한 주장:

> Deployment support is an independent maturity axis. A QUIC implementation may support migration, but a production path must also preserve routable connection IDs or terminate the semantics at a clearly identified edge.

피해야 할 주장:

| 피해야 할 주장 | 이유 |
| --- | --- |
| “AWS NLB HTTP/3 성공은 모든 AWS/CDN CM 성공을 뜻한다.” | NLB CID-aware passthrough와 CDN edge termination은 다르다. |
| “HTTP/3 proxy가 있으면 CM도 된다.” | HAProxy negative control과 충돌한다. |
| “target health가 정상이면 migration도 라우팅된다.” | Server ID/CID mismatch negative control과 충돌한다. |
| “CloudFront/Cloudflare H3 support는 origin end-to-end CM이다.” | viewer-edge termination 가능성이 있다. |

## 10. 다음 챕터로 넘어간 이유

구현체와 deployment positive/negative control을 확보했더라도, 논문의 중심은 browser web application continuity다. 따라서 다음 질문은 브라우저에서 어떤 증거가 있어야 CM이라고 말할 수 있는지다.

> Chrome/Safari/Android에서 browser-level CM을 어떤 evidence chain으로 검증할 수 있는가?

이 질문이 Chapter 5의 출발점이다.

## 11. 검수 결과

| 검수 항목 | 결과 |
| --- | --- |
| AWS NLB positive/negative control 분리 | PASS |
| proxy/CDN edge 해석 분리 | PASS |
| nginx server runtime contrast | PASS |
| HAProxy fresh negative-control runner | PASS |
| 공식 AWS/HAProxy/Cloudflare 문서 링크 | `chapter-04-reference-and-evidence.md`에 정리 |
| 구현 코드 링크 | `aws_nlb_cid.go`, NLB harness script로 연결 |
| 민감정보 처리 | 새 보고용 문서에는 공인 IP, hostname, instance ID, account ID, SSH target을 쓰지 않음 |
| claim boundary | browser handover 또는 CDN origin-end-to-end CM claim을 하지 않음 |
