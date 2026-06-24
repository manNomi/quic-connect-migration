# quic-go Minimum Connection Migration Reproduction Results

작성일: 2026-06-22  
상태: local direct-origin happy path 성공  
대상 코드: `experiments/quic-go-min-repro/`

## 1. Summary

quic-go의 public active migration API를 사용해 local direct-origin 환경에서 Connection Migration 최소 재현을 성공했다.

검증한 흐름:

```text
client UDP socket A로 QUIC 연결
  -> before payload 전송
  -> UDP socket B 생성
  -> conn.AddPath(transport B)
  -> path.Switch() before Probe 실패 확인
  -> path.Probe() 성공
  -> path.Switch() 성공
  -> after payload 전송
  -> server가 같은 accepted QUIC connection에서 before/after payload 모두 수신
```

핵심 결과:

- client result: `ok: true`
- server result: `ok: true`
- `Switch()` before `Probe()`는 `path not yet validated`를 반환했다.
- qlog에서 `path_challenge`와 `path_response`가 client/server 양쪽에 기록됐다.
- migration 후 `after` payload는 socket B local address로 전환된 뒤 송신된 것으로 관측됐다.

## 2. Environment

```text
OS: macOS darwin/arm64
Go: go1.26.4
quic-go: v0.60.1-0.20260622040909-9b0474c9b997
quic-go commit: 9b0474c9b997
```

quic-go module metadata:

```text
Path: github.com/quic-go/quic-go
Version: v0.60.1-0.20260622040909-9b0474c9b997
Time: 2026-06-22T04:09:09Z
GoVersion: 1.25.0
```

## 3. Implemented Files

```text
experiments/quic-go-min-repro/
  go.mod
  go.sum
  cmd/
    server/main.go
    client/main.go
  internal/
    common/
      logging.go
      payload.go
      payload_test.go
      tls.go
  artifacts/
    .gitignore
    logs/client.jsonl
    logs/server.jsonl
    qlog/febb9189667fb7f1dcd8456c9bede306_client.sqlog
    qlog/febb9189667fb7f1dcd8456c9bede306_server.sqlog
    results/client.json
    results/server.json
```

주의:

- qlog file name은 connection ID에 따라 매 실행마다 달라질 수 있다.
- runtime artifact는 `artifacts/` 아래에 생성된다.

## 4. Run Commands

서버:

```bash
cd /Users/manwook-han/Desktop/lab/quic-connection-migration-research/experiments/quic-go-min-repro
go run ./cmd/server \
  --addr 127.0.0.1:4242 \
  --log artifacts/logs/server.jsonl \
  --result artifacts/results/server.json \
  --qlog-dir artifacts/qlog \
  --timeout 30s
```

클라이언트:

```bash
cd /Users/manwook-han/Desktop/lab/quic-connection-migration-research/experiments/quic-go-min-repro
go run ./cmd/client \
  --server 127.0.0.1:4242 \
  --payload-bytes 1048576 \
  --probe-timeout 3s \
  --log artifacts/logs/client.jsonl \
  --result artifacts/results/client.json \
  --qlog-dir artifacts/qlog \
  --timeout 30s
```

검증:

```bash
go test ./...
rg -n "path_challenge|path_response" artifacts/qlog artifacts/logs
```

## 5. Client Result

핵심 필드:

```json
{
  "ok": true,
  "socket_a_local_addr": "127.0.0.1:60232",
  "socket_b_local_addr": "127.0.0.1:58360",
  "connection_local_addr_after_dial": "127.0.0.1:60232",
  "connection_local_addr_after_probe": "127.0.0.1:60232",
  "connection_local_addr_after_switch": "127.0.0.1:60232",
  "connection_local_addr_after_after_payload": "127.0.0.1:58360",
  "switch_before_probe_error": "path not yet validated",
  "switch_before_probe_matched": true,
  "probe_duration_millis": 0,
  "local_addr_changed_to_socket_b": true
}
```

관찰:

- `path.Switch()` 호출 자체는 성공했지만, `conn.LocalAddr()` 관측값은 switch 직후 즉시 socket B로 바뀌지 않았다.
- post-migration payload를 송신한 뒤 `conn.LocalAddr()`가 socket B로 바뀌었다.
- 이 동작은 quic-go integration test가 `Switch()` 이후 추가 송신을 수행한 뒤 주소를 확인하는 패턴과 일치한다.
- loopback 환경이므로 `probe_duration_millis`는 0ms로 기록됐다.

전송 payload:

```text
before: stream_id=2, bytes=1048576, sha256=e59b10ce8e18ca1db44526202f0287fcc77eb0cebe041bb686d8b16a91bc9482
after:  stream_id=6, bytes=1048576, sha256=c1d467c8adf86f5b3ebafc910c09b1240b3f249888d7cefa30958243243a3aec
```

## 6. Server Result

핵심 필드:

```json
{
  "ok": true,
  "listen_addr": "127.0.0.1:4242",
  "connection_local_addr": "127.0.0.1:4242",
  "connection_remote_addr": "127.0.0.1:60232"
}
```

server는 같은 accepted QUIC connection에서 다음 payload를 모두 수신했다.

```text
before: stream_id=2, bytes=1048576, sha256=e59b10ce8e18ca1db44526202f0287fcc77eb0cebe041bb686d8b16a91bc9482
after:  stream_id=6, bytes=1048576, sha256=c1d467c8adf86f5b3ebafc910c09b1240b3f249888d7cefa30958243243a3aec
```

이 결과는 최소 transport-level 작업 연속성 관점에서, path migration 전후 stream 전송이 같은 QUIC connection 위에서 이어졌다는 근거로 사용할 수 있다.

## 7. qlog Evidence

생성된 qlog:

```text
artifacts/qlog/febb9189667fb7f1dcd8456c9bede306_client.sqlog
artifacts/qlog/febb9189667fb7f1dcd8456c9bede306_server.sqlog
```

`path_challenge|path_response` occurrence:

```text
server.sqlog: 3
client.sqlog: 3
```

대표 관측:

```text
client packet_sent: frame_type=path_challenge
server packet_received: frame_type=path_challenge
server packet_sent: frame_type=path_challenge + path_response
client packet_received: frame_type=path_challenge + path_response
client packet_sent: frame_type=path_response
server packet_received: frame_type=path_response
```

해석:

- `Probe()`가 실제 QUIC path validation 절차를 트리거했다.
- migration은 단순히 client local socket만 바꾼 것이 아니라 QUIC path validation을 거쳐 활성화됐다.

## 8. Maturity Interpretation

이번 local reproduction 기준에서 quic-go의 Connection Migration 성숙도는 높게 평가할 수 있다.

근거:

- public API로 active migration을 직접 트리거할 수 있다.
- `AddPath`, `Probe`, `Switch`가 분리되어 있어 실험 통제가 쉽다.
- validation 전 switch 실패가 명시적 error로 드러난다.
- qlog artifact로 path validation을 확인할 수 있다.
- migration 전후 stream continuity를 application-level payload checksum으로 확인할 수 있다.

단, 이 결과가 곧바로 HTTP/3 웹 애플리케이션 작업 연속성을 의미하지는 않는다.

아직 검증하지 않은 것:

- HTTP/3 request/response, upload, stream reset behavior
- browser stack behavior
- Android Wi-Fi/LTE transition
- EC2 direct-origin path
- AWS NLB/CloudFront/Cloudflare 같은 managed edge/LB 환경
- NAT rebinding과 active migration의 차이
- real mobile network delay/loss/reordering

## 9. Next Step

권장 다음 단계:

1. 같은 코드로 EC2 direct-origin 실험을 수행한다.
2. client는 로컬 또는 EC2 client에서 실행하고 server는 공인 IP EC2에서 실행한다.
3. qlog와 optional tcpdump로 source port/IP 변화와 path validation을 확인한다.
4. 이후 quiche path event reproduction으로 구현체 간 관측 가능성 차이를 비교한다.

논문 관점의 현재 결론:

> quic-go는 Connection Migration을 "구현은 되어 있는가" 수준을 넘어, public API와 qlog 기반 검증이 가능한 성숙한 실험 대상이다. 다만 local direct-origin 성공은 managed cloud/LB 또는 browser HTTP/3에서의 성공을 보장하지 않으므로, 다음 실험은 EC2 direct-origin과 AWS LB/CDN 경계로 확장해야 한다.
