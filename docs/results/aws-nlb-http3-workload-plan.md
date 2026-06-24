# AWS NLB HTTP/3 Workload Plan

작성일: 2026-06-24  
상태: local gate PASS, AWS NLB gate PASS, mid-flight variant 대기

## 1. Purpose

지금까지 AWS NLB 실험은 custom QUIC stream payload로 active Connection Migration을 검증했다. 다음 단계는 같은 migration trigger를 유지하되 HTTP/3 request/response workload를 올려, transport continuity가 HTTP/3 task continuity로 이어지는지 확인하는 것이다.

## 2. Research Question

> AWS NLB `TCP_QUIC :443`에서 QUIC-LB plaintext CID 기반 active migration이 성공할 때, 같은 HTTP/3 connection 위의 upload/download request도 manual retry 없이 완료되는가?

## 3. Phase 1 Scope

이번 단계는 mid-flight upload/download가 아니라 post-migration HTTP/3 request continuity를 먼저 확인한다.

1. HTTP/3 POST `/upload` before task를 완료한다.
2. client가 second UDP socket을 만들고 `AddPath -> Probe -> Switch`를 수행한다.
3. 같은 QUIC connection 위의 HTTP/3 client connection으로 GET `/download` after task를 수행한다.
4. client result, server result, qlog에서 path validation과 request completion을 함께 확인한다.

이 실험이 통과하면 다음 단계에서 upload body 전송 중 migration, download body 수신 중 migration으로 확장한다.

## 4. Implementation Strategy

quic-go의 HTTP/3 API는 직접 생성한 `*quic.Conn` 위에 HTTP/3 client connection을 얹을 수 있다.

근거:

- `http3.Transport.NewClientConn(conn *quic.Conn)`
- `http3.Server.ServeListener(ln QUICListener)`
- `http3.ConfigureTLSConfig`가 ALPN을 `h3`로 설정

따라서 기존 transport harness의 장점인 deterministic migration trigger를 유지하면서 HTTP/3 workload를 추가할 수 있다.

## 5. Local Gate

새 로컬 gate:

```bash
cd /Users/manwook-han/Desktop/lab/quic-connection-migration-research/experiments/quic-go-min-repro
./scripts/run-local-h3-workload.sh
```

성공 조건:

| 기준 | 성공 조건 |
| --- | --- |
| before workload | HTTP/3 POST `/upload` status 200 |
| migration | `AddPath -> Probe -> Switch` 성공 |
| after workload | HTTP/3 GET `/download` status 200 |
| tuple change | client connection local addr가 socket B로 변경 |
| server evidence | server가 before/after HTTP/3 request 2개 관찰 |
| qlog | PATH_CHALLENGE/PATH_RESPONSE 확인 |

실행 결과:

> PASS. `experiments/quic-go-h3-local-workload-results-20260624.md`에 정리했다.

## 6. AWS Extension

local gate가 통과하면 기존 `run-aws-nlb-quic-data-plane.sh`의 packaging/provisioning/cleanup 흐름을 재사용하되 실행 binary를 `h3server`/`h3client`로 바꾸는 variant를 추가한다.

기준 AWS path:

- NLB protocol: `TCP_QUIC`
- listener port: `443`
- target group protocol: `TCP_QUIC`
- CID format: `0x00 + 8-byte Server ID + 7-byte nonce`

실행 결과:

> PASS. `experiments/aws-nlb-http3-workload-results-20260624.md`에 정리했다.

## 7. Paper Use

이 실험은 논문에서 다음 구분을 강화한다.

> transport stream continuity가 확인된 뒤에도 HTTP/3 request/task continuity를 별도로 검증해야 한다.

Phase 1은 “same connection after migration” evidence이고, Phase 2는 “mid-flight task survival” evidence가 된다.
