# OpenLiteSpeed QUIC CM Source Feasibility

작성일: `2026-06-30`

## 1. 목적

이 문서는 LSQUIC example binary에서 확보한 preferred-address/NAT-rebinding positive control을 OpenLiteSpeed production-like server 실험으로 확장할 수 있는지 사전 검수한 결과다.

중요한 경계:

> 이 문서는 OpenLiteSpeed runtime Connection Migration 성공 결과가 아니다. 현재 단계의 결론은 “OpenLiteSpeed가 LSQUIC 기반 HTTP/3 server path를 갖고 있으므로 production-like follow-up target으로 타당하다”이다.

## 2. Local 상태

| 항목 | 결과 |
| --- | --- |
| 디스크 | `/System/Volumes/Data` 기준 20GiB free, 96% used |
| local binary | `openlitespeed`, `lshttpd` 미설치 |
| Homebrew | `openlitespeed` formula 미확인 |
| OpenLiteSpeed source | shallow clone only, `/private/tmp/quic-cm-scan-repos/openlitespeed` |
| OpenLiteSpeed clone size | 36MiB |
| OpenLiteSpeed commit | `f4a6f0f8ddbe93e846a2ddc442f87da07bf5c379` |
| OpenLiteSpeed source date | `2026-06-28T22:27:18-04:00` |
| OpenLiteSpeed subject | `Check in 1.9.1` |
| bundled LSQUIC commit pointer from `LSQUICCOMMIT` | `f8ebaf838d2f4db836bda1182ee35b05d5191cee` |
| local LSQUIC clone commit | `f8ebaf838d2f4db836bda1182ee35b05d5191cee` |

## 3. Source evidence

| evidence | source | 해석 |
| --- | --- | --- |
| LSQUIC server mode | [`CMakeLists.txt:11`](https://github.com/litespeedtech/openlitespeed/blob/f4a6f0f8ddbe93e846a2ddc442f87da07bf5c379/CMakeLists.txt#L11) | OpenLiteSpeed build가 LSQUIC server mode를 전제로 함 |
| LSQUIC include path | [`CMakeLists.txt:35`](https://github.com/litespeedtech/openlitespeed/blob/f4a6f0f8ddbe93e846a2ddc442f87da07bf5c379/CMakeLists.txt#L35) | `src/liblsquic`를 server build에 포함 |
| H3 ALPN definition | [`CMakeLists.txt:129-L130`](https://github.com/litespeedtech/openlitespeed/blob/f4a6f0f8ddbe93e846a2ddc442f87da07bf5c379/CMakeLists.txt#L129-L130) | `h3`, `h3-29` ALPN을 QUIC build에 정의 |
| default QUIC enabled | [`dist/conf/httpd_config.conf.in:76-L77`](https://github.com/litespeedtech/openlitespeed/blob/f4a6f0f8ddbe93e846a2ddc442f87da07bf5c379/dist/conf/httpd_config.conf.in#L76-L77) | 기본 설정 template에 `quicEnable 1`, `quicShmDir /dev/shm` 존재 |
| LSQUIC API use | [`src/quic/quicengine.cpp:41`](https://github.com/litespeedtech/openlitespeed/blob/f4a6f0f8ddbe93e846a2ddc442f87da07bf5c379/src/quic/quicengine.cpp#L41) | OpenLiteSpeed QUIC engine이 LSQUIC API를 직접 include |
| HTTP/3 server engine | [`src/quic/quicengine.cpp:732-L757`](https://github.com/litespeedtech/openlitespeed/blob/f4a6f0f8ddbe93e846a2ddc442f87da07bf5c379/src/quic/quicengine.cpp#L732-L757) | `lsquic_engine_new(LSENG_HTTP_SERVER, &api)`로 HTTP/3 server engine 생성 |
| SCID lifecycle callbacks | [`src/quic/quicengine.cpp:746-L748`](https://github.com/litespeedtech/openlitespeed/blob/f4a6f0f8ddbe93e846a2ddc442f87da07bf5c379/src/quic/quicengine.cpp#L746-L748) | new/live/old SCID callback을 등록해 CID lifecycle을 server가 추적 |
| UDP local/destination addr support | [`src/quic/udplistener.cpp:244-L259`](https://github.com/litespeedtech/openlitespeed/blob/f4a6f0f8ddbe93e846a2ddc442f87da07bf5c379/src/quic/udplistener.cpp#L244-L259) | UDP listener가 packet info를 받아 local address를 구분할 수 있음 |
| CID-to-listener routing | [`src/quic/udplistener.cpp:408-L454`](https://github.com/litespeedtech/openlitespeed/blob/f4a6f0f8ddbe93e846a2ddc442f87da07bf5c379/src/quic/udplistener.cpp#L408-L454) | SHM packet buffer에서 CID를 뽑아 listener/engine으로 전달 |
| source address control on send | [`src/quic/udplistener.cpp:646-L704`](https://github.com/litespeedtech/openlitespeed/blob/f4a6f0f8ddbe93e846a2ddc442f87da07bf5c379/src/quic/udplistener.cpp#L646-L704) | outgoing packet에서 local address/ECN control message를 설정 |
| QUIC SHM init | [`src/quic/quicshm.cpp:200-L207`](https://github.com/litespeedtech/openlitespeed/blob/f4a6f0f8ddbe93e846a2ddc442f87da07bf5c379/src/quic/quicshm.cpp#L200-L207) | shared hash/packet pool 초기화 경로 존재 |
| CID/PID map | [`src/quic/quicshm.cpp:355-L433`](https://github.com/litespeedtech/openlitespeed/blob/f4a6f0f8ddbe93e846a2ddc442f87da07bf5c379/src/quic/quicshm.cpp#L355-L433) | worker/process routing을 위한 CID/PID mapping 존재 |

## 4. 해석

OpenLiteSpeed는 단순히 “LSQUIC을 쓴다고 알려진 제품”이 아니라, 현재 source에서 다음 요건을 확인할 수 있다.

| 요건 | 확인 |
| --- | --- |
| HTTP/3 server engine | 있음 |
| LSQUIC server build mode | 있음 |
| QUIC default config surface | 있음 |
| CID lifecycle callback | 있음 |
| UDP packet local/peer address handling | 있음 |
| worker/process CID routing support | 있음 |

따라서 LSQUIC example positive control을 production-like server 경로로 확장하는 후속 실험 대상으로 타당하다.

다만 다음은 아직 증명하지 않았다.

| 아직 증명하지 않은 것 | 이유 |
| --- | --- |
| OpenLiteSpeed binary build success | 현재 디스크 여유가 20GiB이고 전체 build는 보류 |
| OpenLiteSpeed runtime H3 baseline | local `lshttpd` binary 없음 |
| active source-port migration success | quiche client against OpenLiteSpeed 미실행 |
| request continuity under migration | static 1MiB 또는 upload workload 미실행 |
| server-side path validation log | OpenLiteSpeed/LSQUIC runtime debug log 미수집 |

## 5. 다음 실험 설계

OpenLiteSpeed runtime 실험은 다음 순서로 진행한다.

| 단계 | 요구 evidence |
| --- | --- |
| build/install | `lshttpd -v`, build commit, LSQUIC commit, build log |
| minimal server root | temp `SERVER_ROOT`, TLS cert, `quicEnable 1`, HTTP/3 listener |
| H3 baseline | curl/quiche no-migration HTTP/3 request PASS |
| active migration attempt | quiche `--enable-active-migration --perform-migration` |
| transport evidence | LSQUIC/OpenLiteSpeed debug log, client qlog `PATH_CHALLENGE`/`PATH_RESPONSE`, final path state |
| application evidence | 1MiB static download or upload completion |
| negative-control guard | ordinary H3 success만으로 CM success로 판정하지 않음 |

권장 실행 환경:

| 환경 | 이유 |
| --- | --- |
| Linux VM or EC2 | OpenLiteSpeed default `quicShmDir /dev/shm`, Linux UDP packet info, `sendmmsg` path와 production deployment 조건이 더 잘 맞음 |
| macOS local | source audit와 light build feasibility까지는 가능하지만 production-like packet routing claim은 약함 |

## 6. 논문 claim boundary

쓸 수 있는 주장:

> OpenLiteSpeed is a valid production-like follow-up target for LSQUIC migration experiments because its current source tree builds an LSQUIC HTTP/3 server engine, exposes QUIC configuration, and contains CID/shared-memory routing hooks.

쓰면 안 되는 주장:

| 과장 주장 | 이유 |
| --- | --- |
| OpenLiteSpeed에서 CM이 성공했다 | 아직 runtime migration experiment를 실행하지 않음 |
| LSQUIC example demo가 곧 OpenLiteSpeed production behavior다 | example binary와 production server integration은 다름 |
| OpenLiteSpeed가 browser handover를 보장한다 | browser/runtime policy와 application continuity는 별도 evidence 필요 |

## 7. 현재 결론

OpenLiteSpeed는 다음 non-iPhone 연구 단계로 적합하다. 그러나 현재 디스크 여유가 낮고 local binary가 없으므로, 바로 전체 build를 진행하기보다 artifact cleanup 또는 Linux/EC2 환경 확보 후 runtime demo로 넘어가는 것이 안전하다.
