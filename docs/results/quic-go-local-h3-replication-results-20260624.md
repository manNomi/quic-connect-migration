# quic-go Local HTTP/3 Migration Replication Results

작성일: 2026-06-24

## 목적

기존 local direct-origin HTTP/3 migration 결과가 일회성 산출물이 아닌지 확인하기 위해 같은 하네스를 새 `RUN_ID`로 재실행했다.

검증 대상은 두 가지다.

- post-migration request continuity: POST `/upload` 완료 후 QUIC path를 전환하고 GET `/download`가 같은 connection에서 성공하는지 확인
- mid-flight task continuity: POST body 또는 streaming GET response 전송 중 path migration을 trigger해도 HTTP/3 task가 끝까지 완료되는지 확인

## 실행 환경

| 항목 | 값 |
| --- | --- |
| 실행일 | 2026-06-24 |
| 구현체 | quic-go + HTTP/3 |
| 배포 경로 | local direct origin |
| server address | `127.0.0.1` |
| 증거 | client/server JSON, JSONL logs, qlog `.sqlog` |
| artifact size | `local-h3-workload-rerun`: 172 KiB, `local-h3-midflight-rerun`: 1.7 MiB |

## 실행 명령

```bash
cd repro/quic-go-min-repro
RUN_ID=local-h3-workload-rerun-20260624 ./scripts/run-local-h3-workload.sh
RUN_ID=local-h3-midflight-rerun-20260624 ./scripts/run-local-h3-midflight.sh
```

## 결과 요약

| trial | status | trigger | application task | result |
| --- | --- | --- | --- | --- |
| `quic-go-local-h3-workload-rerun-20260624-001` | `PASS` | POST 완료 후 `AddPath -> Probe -> Switch` | 64 KiB upload 후 64 KiB download | before/after request 모두 `HTTP/3.0`, ALPN `h3`, checksum 성공 |
| `quic-go-local-h3-midflight-upload-rerun-20260624-001` | `PASS` | 1 MiB POST body 전송 중 532,480 bytes 지점에서 migration | mid-flight upload | server가 전체 1 MiB body를 decode했고 checksum 성공 |
| `quic-go-local-h3-midflight-download-rerun-20260624-001` | `PASS` | 1 MiB streaming GET response 수신 중 524,288 bytes 지점에서 migration | mid-flight download | client가 전체 1 MiB response를 decode했고 checksum 성공 |

## 세부 관찰

### Post-migration request continuity

| 관찰 항목 | 값 |
| --- | --- |
| artifact | `repro/quic-go-min-repro/artifacts/local-h3-workload-rerun-20260624` |
| client socket A | `[::]:54306` |
| client socket B | `[::]:53492` |
| connection local addr after request | `[::]:53492` |
| server before remote | `127.0.0.1:54306` |
| server after remote | `127.0.0.1:53492` |
| before task | POST `/upload`, 65,536 bytes, `HTTP/3.0`, ALPN `h3` |
| after task | GET `/download`, 65,536 bytes, `HTTP/3.0`, ALPN `h3` |

### Mid-flight upload continuity

| 관찰 항목 | 값 |
| --- | --- |
| artifact | `repro/quic-go-min-repro/artifacts/local-h3-midflight-rerun-20260624/midflight-upload` |
| client socket A | `[::]:64901` |
| client socket B | `[::]:56587` |
| migration trigger point | 532,480 bytes |
| request body | 1,048,576 bytes |
| server workload | `upload` |
| server decode | successful |

### Mid-flight download continuity

| 관찰 항목 | 값 |
| --- | --- |
| artifact | `repro/quic-go-min-repro/artifacts/local-h3-midflight-rerun-20260624/midflight-download` |
| client socket A | `[::]:64702` |
| client socket B | `[::]:52667` |
| migration trigger point | 524,288 bytes |
| response body | 1,048,576 bytes |
| server workload | `download` |
| client decode | successful |

## qlog evidence

| case | side | PATH_CHALLENGE | PATH_RESPONSE | chosen_alpn | HTTP/3 frame |
| --- | --- | ---: | ---: | ---: | ---: |
| post-migration workload | client | 2 | 2 | 1 | 17 |
| post-migration workload | server | 2 | 2 | 1 | 17 |
| mid-flight upload | client | 2 | 2 | 1 | 134 |
| mid-flight upload | server | 2 | 2 | 1 | 134 |
| mid-flight download | client | 2 | 2 | 1 | 69 |
| mid-flight download | server | 2 | 2 | 1 | 69 |

## 해석

이 반복 실행은 기존 local direct-origin 결과와 같은 방향을 보였다. controlled quic-go 환경에서는 QUIC path validation 후 HTTP/3 request continuity뿐 아니라 mid-flight upload/download continuity도 재현됐다.

다만 이 결과는 browser Wi-Fi/LTE handover나 CDN/proxy/LB 경로를 일반화하지 않는다. 논문에서는 이 결과를 "transport/application positive control"로 사용하고, browser-level claim은 controlled public WebPKI origin과 실제 active path-change 실험 이후에만 주장해야 한다.
