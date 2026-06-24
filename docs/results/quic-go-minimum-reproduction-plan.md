# quic-go 최소 Connection Migration 재현 실험 계획

작성일: 2026-06-22  
역할: 첫 controlled experiment인 quic-go direct client/server 실험을 구현 가능한 수준으로 설계한다.  
상태: 계획 문서. 아직 실험 코드는 작성하지 않았다.

## 1. 목적

이 실험의 목적은 HTTP/3, Android Chrome, AWS NLB, CDN을 모두 제외하고 QUIC transport 계층의 Connection Migration이 통제된 환경에서 재현되는지 먼저 확인하는 것이다.

검증할 핵심 질문:

> quic-go client가 연결 중 새 UDP socket/path를 추가하고, path validation 이후 같은 QUIC connection에서 stream 전송을 계속할 수 있는가?

첫 실험은 “웹 애플리케이션 작업 연속성”을 직접 검증하지 않는다. 그 전에 transport-level migration의 최소 성공 조건을 확정한다.

## 2. 근거 소스

검수한 quic-go commit:

- `9b0474c9b9971dd2ee8cdce0fba9ebf2574e193a`

주요 근거:

- [Path.Probe and Path.Switch](https://github.com/quic-go/quic-go/blob/9b0474c9b9971dd2ee8cdce0fba9ebf2574e193a/path_manager_outgoing.go#L26-L87)
- [Conn.AddPath](https://github.com/quic-go/quic-go/blob/9b0474c9b9971dd2ee8cdce0fba9ebf2574e193a/connection.go#L3083-L3108)
- [Connection migration integration test](https://github.com/quic-go/quic-go/blob/9b0474c9b9971dd2ee8cdce0fba9ebf2574e193a/integrationtests/self/connection_migration_test.go#L20-L144)
- [NAT rebinding integration test](https://github.com/quic-go/quic-go/blob/9b0474c9b9971dd2ee8cdce0fba9ebf2574e193a/integrationtests/self/nat_rebinding_test.go#L21-L115)
- [qlog QLOGDIR behavior](https://github.com/quic-go/quic-go/blob/9b0474c9b9971dd2ee8cdce0fba9ebf2574e193a/qlog/qlog_dir.go#L19-L61)
- [quic.Config.Tracer](https://github.com/quic-go/quic-go/blob/9b0474c9b9971dd2ee8cdce0fba9ebf2574e193a/interface.go#L95-L180)
- [echo example TLS/stream baseline](https://github.com/quic-go/quic-go/blob/9b0474c9b9971dd2ee8cdce0fba9ebf2574e193a/example/echo/echo.go#L31-L84)

## 3. 실험 범위

### 3.1 포함하는 것

- quic-go client/server
- QUIC stream 송수신
- client-side active migration
- two UDP sockets
- `Conn.AddPath`
- `Path.Probe`
- `Path.Switch`
- qlog
- tcpdump/Wireshark용 pcap
- local loopback 실험
- EC2 direct-origin 확장 계획

### 3.2 제외하는 것

- HTTP/3 request/response
- Android Chrome
- Wi-Fi/LTE 실제 전환
- CloudFront/Cloudflare
- AWS NLB
- Service Worker 또는 fetch retry
- 웹 UI 작업 연속성

제외 이유:

> 첫 실험에서는 transport migration 자체가 되는지부터 봐야 한다. HTTP/3와 브라우저를 넣으면 실패 원인이 transport, browser policy, application retry, CDN/LB 중 어디인지 분리하기 어렵다.

## 4. 실험 구조

### 4.1 Local direct-origin 구조

```text
client process
  UDP socket A: initial path
  UDP socket B: migration path
        |
        | QUIC packets
        v
server process
  UDP socket S
```

### 4.2 단계 흐름

```text
1. server starts on 127.0.0.1:4242
2. client creates UDP socket A
3. client dials server using socket A
4. client opens a stream and sends payload before migration
5. server receives payload on the same QUIC connection
6. client creates UDP socket B
7. client calls conn.AddPath(transport B)
8. client calls path.Probe()
9. quic-go sends PATH_CHALLENGE on socket B
10. server replies with PATH_RESPONSE
11. path.Probe() returns nil
12. client calls path.Switch()
13. client sends another stream payload
14. server receives post-migration payload on the same QUIC connection
15. logs/qlog/pcap are preserved
```

## 5. 구현 위치와 파일 구조

추천 위치:

```text
/Users/manwook-han/Desktop/lab/quic-connection-migration-research/experiments/quic-go-min-repro
```

추천 파일 구조:

```text
experiments/quic-go-min-repro/
  go.mod
  cmd/
    server/
      main.go
    client/
      main.go
  internal/
    common/
      tls.go
      logging.go
      payload.go
  artifacts/
    qlog/
    pcap/
    logs/
    results/
```

역할:

| 파일 | 역할 |
| --- | --- |
| `cmd/server/main.go` | QUIC listener, stream receive, peer address logging |
| `cmd/client/main.go` | socket A/B 생성, dial, `AddPath -> Probe -> Switch`, stream send |
| `internal/common/tls.go` | self-signed cert와 client TLS config |
| `internal/common/logging.go` | JSONL event log helper |
| `internal/common/payload.go` | payload 생성과 checksum |
| `artifacts/qlog` | qlog `.sqlog` 파일 |
| `artifacts/pcap` | tcpdump `.pcap` 파일 |
| `artifacts/logs` | client/server JSONL 로그 |
| `artifacts/results` | trial result CSV/JSON |

## 6. Go module 생성 계획

초기 명령:

```bash
cd /Users/manwook-han/Desktop/lab/quic-connection-migration-research
mkdir -p experiments/quic-go-min-repro
cd experiments/quic-go-min-repro
go mod init quic-cm/quic-go-min-repro
go get github.com/quic-go/quic-go@9b0474c9b9971dd2ee8cdce0fba9ebf2574e193a
```

주의:

- commit pinning이 안 되면 quic-go 최신 tag로 시작하되, `go list -m all` 결과를 기록한다.
- 논문 결과에는 반드시 `go version`, OS, quic-go module version 또는 pseudo-version을 남긴다.

## 7. TLS 설정

첫 실험은 public certificate가 필요 없다. self-signed certificate를 사용한다.

server TLS:

```text
Certificates: self-signed cert
NextProtos: ["quic-cm-repro"]
KeyLogWriter: optional artifacts/keylog/server.keys
```

client TLS:

```text
InsecureSkipVerify: true
NextProtos: ["quic-cm-repro"]
KeyLogWriter: optional artifacts/keylog/client.keys
```

왜 self-signed를 쓰는가:

- 실험 대상은 TLS trust chain이 아니라 QUIC path migration이다.
- EC2 direct-origin 전 단계에서는 public DNS/cert가 오히려 변수를 늘린다.

주의:

- Chrome/Android 실험으로 넘어갈 때는 public domain과 trusted certificate가 필요하다.
- Go `KeyLogWriter`는 Wireshark 복호화를 돕는 보조 산출물이다. qlog만으로도 migration frame 확인은 가능하다.

## 8. qlog 설정

quic-go는 `Config.Tracer`에 `qlog.DefaultConnectionTracer`를 넣고 `QLOGDIR` 환경변수를 설정하면 connection별 qlog를 생성한다.

client/server 공통 QUIC config:

```go
&quic.Config{
    Tracer: qlog.DefaultConnectionTracer,
}
```

실행 시:

```bash
export QLOGDIR=/Users/manwook-han/Desktop/lab/quic-connection-migration-research/experiments/quic-go-min-repro/artifacts/qlog
mkdir -p "$QLOGDIR"
```

기대 파일:

```text
<original-destination-connection-id>_client.sqlog
<original-destination-connection-id>_server.sqlog
```

qlog에서 확인할 항목:

| 항목 | 의미 |
| --- | --- |
| `path_challenge` | 새 path validation 시작 |
| `path_response` | 새 path validation 응답 |
| `new_connection_id` | spare CID 공급 |
| `retire_connection_id` | 이전 CID retirement |
| packet sent/received addresses | UDP 4-tuple 변화 |
| loss/recovery events | migration 중 packet loss 여부 |

## 9. 서버 구현 계획

### 9.1 서버 CLI

예상 명령:

```bash
go run ./cmd/server \
  --addr 127.0.0.1:4242 \
  --log artifacts/logs/server.jsonl \
  --result artifacts/results/server-result.json
```

### 9.2 서버 동작

서버는 다음만 수행한다.

1. `quic.ListenAddr` 또는 `quic.Transport.Listen`으로 listen
2. connection accept
3. connection ID와 initial remote address 기록
4. stream을 반복 accept
5. 각 stream payload를 읽고 checksum 기록
6. 필요하면 echo ack를 반환
7. connection close까지 로그 기록

서버 로그 이벤트:

```json
{"ts":"...","role":"server","event":"listen","addr":"127.0.0.1:4242"}
{"ts":"...","role":"server","event":"accept_connection","remote_addr":"127.0.0.1:xxxxx"}
{"ts":"...","role":"server","event":"stream_received","label":"before","bytes":1048576,"sha256":"..."}
{"ts":"...","role":"server","event":"stream_received","label":"after","bytes":1048576,"sha256":"..."}
{"ts":"...","role":"server","event":"connection_closed","error":null}
```

서버에서 직접 peer address change callback이 없을 수 있으므로, 1차 판정은 다음 조합으로 한다.

- client `conn.LocalAddr()` 변화
- qlog packet address 변화
- tcpdump 4-tuple 변화
- 같은 server connection에서 before/after stream을 모두 수신했는지

## 10. 클라이언트 구현 계획

### 10.1 클라이언트 CLI

예상 명령:

```bash
go run ./cmd/client \
  --server 127.0.0.1:4242 \
  --payload-bytes 1048576 \
  --probe-timeout 3s \
  --log artifacts/logs/client.jsonl \
  --result artifacts/results/client-result.json
```

### 10.2 클라이언트 동작

클라이언트는 반드시 `quic.Transport`를 직접 사용한다. 이유는 `Conn.AddPath`가 새 `Transport`를 받기 때문이다.

흐름:

```go
udpA := mustListenUDP("127.0.0.1:0")
trA := &quic.Transport{Conn: udpA}

conn, err := trA.Dial(ctx, serverAddr, tlsConf, quicConf)

sendStream(conn, "before", payloadBefore)

udpB := mustListenUDP("127.0.0.1:0")
trB := &quic.Transport{Conn: udpB}

path, err := conn.AddPath(trB)
err = path.Probe(ctx)
err = path.Switch()

sendStream(conn, "after", payloadAfter)
```

핵심 로그 이벤트:

```json
{"ts":"...","role":"client","event":"dial_start","local_addr_a":"127.0.0.1:xxxxx","server":"127.0.0.1:4242"}
{"ts":"...","role":"client","event":"dial_complete","conn_local_addr":"127.0.0.1:xxxxx"}
{"ts":"...","role":"client","event":"send_before","bytes":1048576,"sha256":"..."}
{"ts":"...","role":"client","event":"add_path_start","local_addr_b":"127.0.0.1:yyyyy"}
{"ts":"...","role":"client","event":"add_path_done"}
{"ts":"...","role":"client","event":"probe_start"}
{"ts":"...","role":"client","event":"probe_done","duration_ms":12}
{"ts":"...","role":"client","event":"switch_start"}
{"ts":"...","role":"client","event":"switch_done","old_local_addr":"127.0.0.1:xxxxx","new_local_addr":"127.0.0.1:yyyyy"}
{"ts":"...","role":"client","event":"send_after","bytes":1048576,"sha256":"..."}
```

### 10.3 client assertions

client는 실행 중 다음을 assert한다.

| assert | 실패 시 의미 |
| --- | --- |
| `conn.LocalAddr() == udpA.LocalAddr()` before switch | 초기 path가 socket A인지 확인 |
| `path.Switch()` before `Probe()` returns `ErrPathNotValidated` | validation 전 switch 차단 확인 |
| `path.Probe()` returns nil | PATH_CHALLENGE/RESPONSE 성공 |
| `path.Switch()` returns nil | active path 전환 성공 |
| `conn.LocalAddr() == udpB.LocalAddr()` after switch | 실제 송신 path가 socket B로 바뀜 |
| server receives both payloads | 같은 connection에서 stream 연속성 확인 |

## 11. tcpdump/pcap 수집

### 11.1 macOS local

```bash
mkdir -p artifacts/pcap
sudo tcpdump -i lo0 -w artifacts/pcap/quic-go-local.pcap 'udp and port 4242'
```

### 11.2 Linux local/EC2

```bash
mkdir -p artifacts/pcap
sudo tcpdump -i any -w artifacts/pcap/quic-go-direct.pcap 'udp port 4242'
```

### 11.3 pcap에서 확인할 것

| 확인 항목 | 기대값 |
| --- | --- |
| before path | client UDP source port A -> server UDP port |
| probe path | client UDP source port B -> server UDP port with PATH_CHALLENGE |
| response | server UDP port -> client UDP source port B with PATH_RESPONSE |
| after switch | application data packet이 source port B에서 나감 |

## 12. 실행 절차

### 12.1 local happy path

터미널 1:

```bash
cd /Users/manwook-han/Desktop/lab/quic-connection-migration-research/experiments/quic-go-min-repro
mkdir -p artifacts/{qlog,pcap,logs,results,keylog}
export QLOGDIR="$PWD/artifacts/qlog"
go run ./cmd/server --addr 127.0.0.1:4242 --log artifacts/logs/server.jsonl
```

터미널 2:

```bash
cd /Users/manwook-han/Desktop/lab/quic-connection-migration-research/experiments/quic-go-min-repro
export QLOGDIR="$PWD/artifacts/qlog"
go run ./cmd/client \
  --server 127.0.0.1:4242 \
  --payload-bytes 1048576 \
  --probe-timeout 3s \
  --log artifacts/logs/client.jsonl \
  --result artifacts/results/local-happy-path.json
```

터미널 3:

```bash
cd /Users/manwook-han/Desktop/lab/quic-connection-migration-research/experiments/quic-go-min-repro
sudo tcpdump -i lo0 -w artifacts/pcap/local-happy-path.pcap 'udp and port 4242'
```

### 12.2 validation-before-switch negative test

목적:

- `Probe()` 없이 `Switch()`하면 실패하는지 확인한다.

예상 명령:

```bash
go run ./cmd/client \
  --server 127.0.0.1:4242 \
  --mode switch-before-probe \
  --expect-switch-error path-not-validated
```

기대 결과:

- `path.Switch()`가 `ErrPathNotValidated`를 반환한다.
- connection은 닫히지 않는다.
- 이후 `Probe()`와 `Switch()`를 정상 수행할 수 있다.

### 12.3 failed path validation test

목적:

- 존재하지 않거나 응답하지 않는 path로 probe할 때 timeout을 분류한다.

방법:

- socket B를 만들되 server 응답이 오지 않도록 packet drop rule 또는 blackhole socket을 사용한다.
- 간단한 1차 구현에서는 이 negative test를 후순위로 둔다.

기대 결과:

- `path.Probe(ctx)`가 context deadline exceeded로 실패한다.
- 기존 path A에서는 connection이 유지된다.

## 13. EC2 direct-origin 확장

### 13.1 구성

```text
local laptop or EC2 client
        |
        | UDP 443 or UDP 4242
        v
EC2 public IPv4
  quic-go server
```

### 13.2 보안 그룹

inbound:

```text
UDP 4242 from client public IP
SSH 22 from researcher IP
```

나중에 HTTP/3로 확장할 때:

```text
UDP 443 from 0.0.0.0/0 or controlled source
TCP 443 for certificate/bootstrap if needed
```

### 13.3 EC2 실행 명령 예시

server:

```bash
mkdir -p ~/quic-cm/artifacts/{qlog,pcap,logs,results,keylog}
export QLOGDIR="$HOME/quic-cm/artifacts/qlog"
sudo tcpdump -i any -w ~/quic-cm/artifacts/pcap/ec2-direct-server.pcap 'udp port 4242' &
./quic-go-server --addr 0.0.0.0:4242 --log ~/quic-cm/artifacts/logs/server.jsonl
```

client:

```bash
export QLOGDIR="$PWD/artifacts/qlog"
go run ./cmd/client \
  --server <EC2_PUBLIC_IP>:4242 \
  --payload-bytes 1048576 \
  --probe-timeout 5s \
  --log artifacts/logs/client-ec2.jsonl \
  --result artifacts/results/ec2-direct.json
```

### 13.4 EC2에서 추가로 봐야 할 것

| 항목 | 이유 |
| --- | --- |
| security group UDP 허용 | path B source port도 같은 서버 port로 들어와야 함 |
| NAT behavior | laptop behind NAT에서는 source port 변화가 로컬 의도와 다르게 보일 수 있음 |
| public IP change는 재현 어려움 | source port migration부터 시작 |
| pcap server-side 4-tuple | 실제 서버가 본 client tuple 변화 확인 |

## 14. 결과 판정표

### 14.1 trial result JSON

```json
{
  "trial_id": "quic-go-local-001",
  "date": "2026-06-22",
  "implementation": "quic-go",
  "implementation_version": "9b0474c9b9971dd2ee8cdce0fba9ebf2574e193a",
  "deployment": "local-direct",
  "server_addr": "127.0.0.1:4242",
  "client_initial_local_addr": "127.0.0.1:xxxxx",
  "client_migrated_local_addr": "127.0.0.1:yyyyy",
  "handshake_success": true,
  "pre_migration_stream_success": true,
  "probe_success": true,
  "switch_success": true,
  "post_migration_stream_success": true,
  "same_quic_connection": true,
  "path_challenge_observed": true,
  "path_response_observed": true,
  "manual_intervention_required": false,
  "failure_layer": null,
  "notes": ""
}
```

### 14.2 success definition

성공:

```text
handshake_success
AND pre_migration_stream_success
AND probe_success
AND switch_success
AND post_migration_stream_success
AND same_quic_connection
AND path_challenge_observed
AND path_response_observed
```

부분 성공:

```text
stream은 유지되지만 qlog/pcap에서 PATH_CHALLENGE/PATH_RESPONSE를 확인하지 못함
또는 Probe/Switch는 성공했지만 server-side artifact가 부족함
```

실패:

```text
Probe 실패
Switch 실패
post-migration stream 실패
server가 새 connection으로 처리
connection close 발생
```

## 15. 실패 원인 taxonomy

| failure_layer | 예시 |
| --- | --- |
| `api_precondition` | server가 active migration disabled, server-side `AddPath` 호출 |
| `path_validation` | PATH_RESPONSE 미수신, probe timeout |
| `cid_lifecycle` | spare CID 부족, `OutOfIdentifiers` 유사 실패 |
| `routing` | packet이 server에 도달하지 않음 |
| `connection_state` | server가 같은 connection으로 매칭하지 못함 |
| `stream_continuity` | connection은 유지되나 stream read/write 실패 |
| `observability` | migration은 된 것 같지만 qlog/pcap 근거 부족 |

## 16. 논문에 들어갈 해석

이 실험이 성공하면 다음 주장을 할 수 있다.

> 통제된 direct-origin 환경에서 QUIC Connection Migration은 quic-go 구현체를 통해 application reconnect 없이 stream continuity를 유지할 수 있다.

하지만 다음 주장은 아직 할 수 없다.

> Android Chrome의 HTTP/3 fetch/upload도 Wi-Fi/LTE 전환 중 항상 유지된다.

> AWS NLB 뒤에서도 같은 결과가 나온다.

> CloudFront/Cloudflare edge continuity가 end-to-end QUIC Connection Migration이다.

즉, quic-go 최소 재현 실험은 논문의 첫 결과이지 최종 결론이 아니다. 이후 quiche, picoquic, s2n-quic, Chrome/AWS 실험으로 확장해야 한다.

## 17. 다음 구현 작업

다음 turn에서 실제 코드를 만든다면 작업 순서는 다음과 같다.

1. `experiments/quic-go-min-repro` 디렉터리 생성
2. `go.mod` 생성 및 quic-go commit pinning
3. `internal/common/tls.go` 작성
4. `internal/common/logging.go` 작성
5. `cmd/server/main.go` 작성
6. `cmd/client/main.go` 작성
7. local happy path 실행
8. qlog/pcap/log artifact 확인
9. result JSON 생성
10. 실험 결과를 새 문서로 정리

추천 다음 산출물:

```text
experiments/quic-go-min-repro/
experiments/quic-go-minimum-reproduction-results.md
```
