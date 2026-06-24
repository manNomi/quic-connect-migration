# quic-go 최소 재현 구현 전 리뷰 계획

작성일: 2026-06-22  
상태: 구현 전 reviewed plan. 이 문서는 코드 구현 전에 범위, 위험, 검증 기준을 고정하기 위한 계획이다.  
대상 구현: `experiments/quic-go-min-repro/`

## 1. Goal

통제된 local direct-origin 환경에서 quic-go client/server를 구현하여 다음 흐름을 재현한다.

```text
QUIC connection on UDP socket A
  -> stream payload before migration
  -> client adds UDP socket B as a new path
  -> path.Probe()
  -> path.Switch()
  -> stream payload after migration on the same QUIC connection
```

최종 사용자 산출물:

- 실행 가능한 quic-go client/server 실험 코드
- local happy path 실행 결과
- client/server JSONL 로그
- qlog `.sqlog` artifact
- result JSON
- 실험 결과 요약 문서

## 2. Current Facts

작업 폴더:

- `/Users/manwook-han/Desktop/lab/quic-connection-migration-research`

현재 상태:

- 이 폴더는 git repository가 아니다. `git status --short`는 `fatal: not a git repository`를 반환했다.
- `experiments/quic-go-min-repro/` 디렉터리는 아직 존재하지 않는다.
- `go` 명령은 현재 PATH에서 발견되지 않는다.
- Homebrew는 `/opt/homebrew/bin/brew`에 존재한다.
- 계획 근거 문서는 이미 작성되어 있다.

관련 문서:

- `experiments/quic-go-minimum-reproduction-plan.md`
- `docs/13-experiment-target-selection.md`
- `docs/04-next-actions.md`

소스 근거:

- quic-go `Conn.AddPath`는 client-side migration path를 추가한다.
- quic-go `Path.Probe`는 path validation을 수행한다.
- quic-go `Path.Switch`는 validated path로 active path를 전환한다.
- quic-go qlog는 `QLOGDIR`와 `qlog.DefaultConnectionTracer`로 생성 가능하다.

## 3. Scope

이번 구현 범위:

1. Go toolchain precheck 또는 설치 안내/처리
2. `experiments/quic-go-min-repro/` Go module 생성
3. self-signed TLS helper 작성
4. JSONL logger helper 작성
5. payload/checksum helper 작성
6. QUIC server CLI 작성
7. QUIC client CLI 작성
8. local happy path 실행
9. qlog/log/result artifact 확인
10. 결과 문서 작성

## 4. Non-goals

이번 구현에서 하지 않는 것:

- HTTP/3 server/client 구현
- Android Chrome 실험
- AWS EC2 배포
- AWS NLB 설정
- CloudFront/Cloudflare 실험
- 실제 Wi-Fi/LTE 전환
- Service Worker/fetch/upload 웹 앱 구현
- picoquic/quiche/s2n-quic 실험 구현
- pcap 자동 분석기 작성

## 5. Ownership Boundaries

수정 예정 위치:

```text
quic-connection-migration-research/
  experiments/
    quic-go-min-repro/
      go.mod
      go.sum
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
        .gitkeep or runtime-generated files
    quic-go-minimum-reproduction-results.md
  docs/
    04-next-actions.md
  archive/
    2026-06-22-conversation-and-findings.md
  README.md
```

수정하지 않을 위치:

- 기존 구현체 감사 문서 `docs/05`-`docs/13`
- 기존 `experiments/aws-testbed-plan.md`
- `/tmp/quic-cm-audit-repos/*` 클론

## 6. Implementation Order

### Step 0. Toolchain precheck

확인:

```bash
go version
```

현재 결과:

```text
zsh:1: command not found: go
```

다음 구현 턴에서 처리할 선택지:

1. Homebrew로 Go 설치: `brew install go`
2. 사용자가 이미 설치한 Go 경로가 있다면 PATH만 수정
3. 설치를 원하지 않으면 코드 작성까지만 하고 실행 검증은 보류

권장:

- 실험을 실제로 돌려야 하므로 `brew install go`로 toolchain을 먼저 준비한다.

### Step 1. Directory and module

생성:

```bash
mkdir -p experiments/quic-go-min-repro/{cmd/server,cmd/client,internal/common,artifacts/{qlog,pcap,logs,results,keylog}}
cd experiments/quic-go-min-repro
go mod init quic-cm/quic-go-min-repro
go get github.com/quic-go/quic-go@9b0474c9b9971dd2ee8cdce0fba9ebf2574e193a
```

주의:

- commit pinning이 실패하면 최신 tag 또는 pseudo-version을 기록한다.
- `go env`, `go version`, `go list -m all` 결과를 results 문서에 남긴다.

### Step 2. Common helpers

`internal/common/tls.go`:

- server self-signed TLS config 생성
- client TLS config 생성
- `NextProtos: []string{"quic-cm-repro"}`
- optional keylog writer path 지원

`internal/common/logging.go`:

- JSONL logger
- `ts`, `role`, `event`, dynamic fields 기록
- file open/close 처리

`internal/common/payload.go`:

- deterministic payload 생성
- SHA-256 checksum
- label별 payload 생성: `before`, `after`

### Step 3. Server CLI

`cmd/server/main.go` responsibilities:

- flags:
  - `--addr`
  - `--log`
  - `--result`
  - `--keylog`
- artifact directories 생성
- qlog tracer config
- `quic.ListenAddr`
- single connection accept
- stream receive loop
- stream payload checksum 기록
- `before`와 `after` 두 payload를 모두 받으면 success result 작성

서버 결과 판단:

- 같은 accepted connection에서 두 stream을 모두 받아야 한다.
- payload checksum이 client result와 일치해야 한다.

### Step 4. Client CLI

`cmd/client/main.go` responsibilities:

- flags:
  - `--server`
  - `--payload-bytes`
  - `--probe-timeout`
  - `--log`
  - `--result`
  - `--keylog`
  - `--mode`
- UDP socket A 생성
- `quic.Transport{Conn: udpA}`로 dial
- before payload stream 전송
- UDP socket B 생성
- `conn.AddPath(trB)`
- negative check: `path.Switch()` before probe should return `quic.ErrPathNotValidated`
- `path.Probe(ctx)`
- `path.Switch()`
- `conn.LocalAddr()`가 socket B로 바뀌었는지 확인
- after payload stream 전송
- result JSON 작성

기본 모드:

- `--mode happy-path`

후순위 모드:

- `--mode switch-before-probe`
- `--mode probe-timeout`

첫 구현에서는 `happy-path`와 validation-before-switch check만 포함한다.

### Step 5. Local verification

터미널 1:

```bash
cd /Users/manwook-han/Desktop/lab/quic-connection-migration-research/experiments/quic-go-min-repro
export QLOGDIR="$PWD/artifacts/qlog"
go run ./cmd/server --addr 127.0.0.1:4242 --log artifacts/logs/server.jsonl --result artifacts/results/server.json
```

터미널 2:

```bash
cd /Users/manwook-han/Desktop/lab/quic-connection-migration-research/experiments/quic-go-min-repro
export QLOGDIR="$PWD/artifacts/qlog"
go run ./cmd/client --server 127.0.0.1:4242 --payload-bytes 1048576 --probe-timeout 3s --log artifacts/logs/client.jsonl --result artifacts/results/client.json
```

선택 pcap:

```bash
sudo tcpdump -i lo0 -w artifacts/pcap/local-happy-path.pcap 'udp and port 4242'
```

주의:

- pcap은 sudo가 필요하므로 자동 검증 필수 조건으로 두지 않는다.
- qlog와 JSONL/result가 1차 필수 artifact다.

### Step 6. Result document

작성:

```text
experiments/quic-go-minimum-reproduction-results.md
```

포함:

- 실행 환경
- quic-go version
- Go version
- 실행 명령
- result JSON 요약
- qlog 파일 목록
- client/server 로그 요약
- 성공/실패 판정
- 다음 실험으로 넘어갈 조건

## 7. Success Criteria

구현 완료 조건:

- `go run ./cmd/server`가 실행된다.
- `go run ./cmd/client`가 실행된다.
- client가 before payload를 보낸다.
- server가 before payload를 같은 connection에서 받는다.
- client가 `AddPath`에 성공한다.
- `Switch()` before `Probe()`가 `ErrPathNotValidated`로 실패한다.
- `Probe()`가 성공한다.
- `Switch()`가 성공한다.
- client `conn.LocalAddr()`가 socket B address로 바뀐다.
- client가 after payload를 보낸다.
- server가 after payload를 같은 connection에서 받는다.
- qlog `.sqlog`가 client/server 중 하나 이상 생성된다.
- result JSON이 success를 기록한다.
- results markdown이 작성된다.

## 8. Verification Commands

필수:

```bash
go version
go test ./...
go run ./cmd/server --addr 127.0.0.1:4242 --log artifacts/logs/server.jsonl --result artifacts/results/server.json
go run ./cmd/client --server 127.0.0.1:4242 --payload-bytes 1048576 --probe-timeout 3s --log artifacts/logs/client.jsonl --result artifacts/results/client.json
ls -la artifacts/qlog artifacts/logs artifacts/results
```

선택:

```bash
sudo tcpdump -i lo0 -w artifacts/pcap/local-happy-path.pcap 'udp and port 4242'
```

문서 검증:

```bash
rg -n "quic-go-min-repro|happy-path|Probe|Switch" experiments docs README.md archive
```

## 9. Risks

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Go toolchain missing | 구현/검증 불가 | `brew install go` 또는 PATH 수정 선행 |
| quic-go commit pinning 실패 | 재현성 저하 | 실제 module version을 결과에 기록 |
| server exits before client finishes | flaky test | server는 두 stream 수신 또는 context timeout까지 유지 |
| qlog 생성 안 됨 | frame 근거 부족 | `QLOGDIR` export 확인, config tracer 확인 |
| pcap requires sudo | 자동화 중단 | pcap은 선택 artifact로 둠 |
| `conn.LocalAddr()` 변화만으로 부족 | migration 증거 약함 | qlog와 server same-connection stream 수신을 함께 요구 |
| loopback에서 OS behavior가 실제 네트워크와 다름 | 외삽 위험 | 결과 해석을 local direct-origin으로 제한 |
| artifact 파일이 너무 커짐 | 저장소 관리 부담 | qlog/pcap은 runtime artifact, 필요 시 `.gitignore` 고려 |

## 10. Codex Self-review

### Finding 1: Go toolchain is currently missing

Severity: blocking for implementation verification  
Status: accepted

계획 반영:

- Step 0을 toolchain precheck로 승격했다.
- 다음 구현 턴의 첫 작업을 `go version` 확인과 `brew install go` 또는 PATH 수정으로 둔다.

### Finding 2: pcap을 필수 성공 조건으로 두면 sudo 때문에 막힐 수 있음

Severity: important  
Status: accepted

계획 반영:

- qlog/JSONL/result를 필수 artifact로 두고, pcap은 선택 artifact로 낮췄다.

### Finding 3: server-side peer address change callback이 불명확함

Severity: important  
Status: accepted

계획 반영:

- server success는 같은 accepted connection에서 before/after stream을 모두 받는 것으로 판정한다.
- migration 자체의 path 증거는 client `conn.LocalAddr()`, qlog, optional pcap 조합으로 판정한다.

### Finding 4: negative tests를 첫 구현에 모두 넣으면 범위가 커짐

Severity: important  
Status: accepted

계획 반영:

- 첫 구현은 happy path와 `Switch()` before `Probe()` assertion만 포함한다.
- `probe-timeout` blackhole test는 후순위로 둔다.

### Finding 5: runtime artifacts를 문서/소스와 분리해야 함

Severity: important  
Status: accepted

계획 반영:

- `artifacts/` 하위에 qlog/log/result/pcap/keylog를 모은다.
- 구현 시 `.gitignore` 또는 `.gitkeep` 정책을 정한다.

## 11. Independent Review

독립 sub-agent 리뷰는 이번 턴에서 실행하지 않았다.

이유:

- 사용자는 “계획 세우고 리뷰”를 요청했지만, “서브에이전트/클로드에게 맡겨”라고 명시하지 않았다.
- 현재 multi-agent 도구 지침은 명시적 위임 요청 없이 sub-agent spawn을 금지한다.

대신 Codex self-review를 수행했고, blocking/important finding을 모두 계획에 반영했다.

독립 리뷰를 추가하려면 다음 요청으로 진행하면 된다.

```text
이 계획을 서브에이전트/클로드에게 독립 리뷰시켜줘
```

## 12. Final Reviewed Plan

GREEN for implementation, with one precondition:

> Go toolchain must be installed or made available in PATH before code can be verified.

다음 구현 턴의 순서:

1. Go toolchain 확인 및 설치/PATH 처리
2. `experiments/quic-go-min-repro/` scaffold 생성
3. Go module 생성 및 quic-go dependency pin
4. common helper 작성
5. server 작성
6. client 작성
7. `go test ./...`
8. local happy path 실행
9. qlog/log/result 확인
10. results markdown 작성

Stop condition:

- local happy path가 성공하고 result JSON 및 qlog/log artifact가 생성되면 구현 완료로 본다.
- Go toolchain 설치가 불가능하면 code scaffold까지만 만들고 verification blocked로 명시한다.
