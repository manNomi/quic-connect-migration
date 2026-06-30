# Chapter 3 Implementation Positive-Control Trigger Map

작성일: `2026-06-30`

이 표는 Chapter 3 “구현체 Positive Control”에서 quic-go active migration을 어떻게 만들고 검증했는지 코드 라인 단위로 추적한다. 목적은 “CM이 transport primitive로 구현 가능한가”와 “브라우저 handover에서 검증됐는가”를 분리하는 것이다.

## 1. Transport Client Migration

| 코드 위치 | trigger/input | 출력 필드 | 해석 |
| --- | --- | --- | --- |
| [client/main.go#L51-L65](../../../repro/quic-go-min-repro/cmd/client/main.go#L51-L65) | server, bind, payload, qlog, timeout flags | client result config | 재현 run의 client 조건 |
| [client/main.go#L98-L109](../../../repro/quic-go-min-repro/cmd/client/main.go#L98-L109) | `QLOGDIR` setup | qlog files | path validation evidence 수집 |
| [client/main.go#L128-L160](../../../repro/quic-go-min-repro/cmd/client/main.go#L128-L160) | UDP socket A and `trA.Dial` | `connection_local_addr_after_dial` | initial path |
| [client/main.go#L166-L178](../../../repro/quic-go-min-repro/cmd/client/main.go#L166-L178) | before payload stream | sent checksum/stream id | migration 전 application payload |
| [client/main.go#L180-L191](../../../repro/quic-go-min-repro/cmd/client/main.go#L180-L191) | UDP socket B | `socket_b_local_addr` | migration 후보 path |
| [client/main.go#L193-L213](../../../repro/quic-go-min-repro/cmd/client/main.go#L193-L213) | `AddPath`, `Switch` before probe, `ErrPathNotValidated` check | `switch_before_probe_matched` | path validation 없는 switch를 성공으로 보지 않음 |
| [client/main.go#L215-L229](../../../repro/quic-go-min-repro/cmd/client/main.go#L215-L229) | `path.Probe` | `probe_duration_millis`, `connection_local_addr_after_probe` | PATH_CHALLENGE/PATH_RESPONSE 유도 |
| [client/main.go#L231-L240](../../../repro/quic-go-min-repro/cmd/client/main.go#L231-L240) | `path.Switch` after probe | `connection_local_addr_after_switch` | validated path로 active switch |
| [client/main.go#L242-L260](../../../repro/quic-go-min-repro/cmd/client/main.go#L242-L260) | after payload stream and address check logging | sent checksum, post-migration addr | migration 뒤 같은 connection에서 payload 전송 |
| [client/main.go#L262-L267](../../../repro/quic-go-min-repro/cmd/client/main.go#L262-L267) | `LocalAddrChangedToSocketB` assertion | error on mismatch | socket switch 없는 성공 overclaim 방지 |

## 2. Transport Server Verification

| 코드 위치 | trigger/input | 출력 필드 | 해석 |
| --- | --- | --- | --- |
| [server/main.go#L71-L81](../../../repro/quic-go-min-repro/cmd/server/main.go#L71-L81) | optional AWS Server ID | `connection_id_mode`, `aws_server_id` | Chapter 4 NLB mode와 transport server 연결 |
| [server/main.go#L91-L118](../../../repro/quic-go-min-repro/cmd/server/main.go#L91-L118) | qlog setup and quic config | qlog files | server-side path evidence |
| [server/main.go#L133-L139](../../../repro/quic-go-min-repro/cmd/server/main.go#L133-L139) | `quic.Transport` and optional CID generator | listener config | same server can run local and AWS CID-aware mode |
| [server/main.go#L159-L172](../../../repro/quic-go-min-repro/cmd/server/main.go#L159-L172) | `listener.Accept` | accepted connection local/remote addr | one QUIC connection accepted |
| [server/main.go#L174-L213](../../../repro/quic-go-min-repro/cmd/server/main.go#L174-L213) | receive two unidirectional streams | `received` rows with checksum and addr | before/after payload가 같은 accepted connection으로 도착 |
| [server/main.go#L215-L227](../../../repro/quic-go-min-repro/cmd/server/main.go#L215-L227) | before/after labels and `OK=true` | server success | payload label 누락 시 실패 |

## 3. Runner And Artifact Validator

| 코드 위치 | trigger/input | 생성/검증 artifact | 해석 |
| --- | --- | --- | --- |
| [run-local-happy-path.sh#L17-L20](../../../repro/quic-go-min-repro/scripts/run-local-happy-path.sh#L17-L20) | artifact dirs and `go test ./...` | local test gate | unit/build failure를 실험 성공으로 남기지 않음 |
| [run-local-happy-path.sh#L21-L29](../../../repro/quic-go-min-repro/scripts/run-local-happy-path.sh#L21-L29) | server launch with qlog/keylog/result paths | server artifacts | run artifact 생성 |
| [run-local-happy-path.sh#L41-L52](../../../repro/quic-go-min-repro/scripts/run-local-happy-path.sh#L41-L52) | client launch with payload/probe/qlog paths | client artifacts | positive control 실행 |
| [run-local-happy-path.sh#L57-L61](../../../repro/quic-go-min-repro/scripts/run-local-happy-path.sh#L57-L61) | `rg --no-ignore --text` for path frames | `qlog-path-validation.txt` | ignored artifact path의 qlog도 검출 |
| [run-local-quic-go.sh#L24-L46](../../../harness/scripts/run-local-quic-go.sh#L24-L46) | repo-level wrapper | manifest and validation summary | 교수님 보고용 한 명령 wrapper |
| [validate-quic-go-artifacts.sh#L19-L21](../../../harness/scripts/validate-quic-go-artifacts.sh#L19-L21) | client/server/qlog existence | required artifact gate | 결과 파일 누락 방지 |
| [validate-quic-go-artifacts.sh#L23-L29](../../../harness/scripts/validate-quic-go-artifacts.sh#L23-L29) | client/server `ok=true` | success gate | qlog만 있고 application 실패한 run 배제 |
| [validate-quic-go-artifacts.sh#L31-L37](../../../harness/scripts/validate-quic-go-artifacts.sh#L31-L37) | `path_challenge|path_response` scan | non-empty qlog evidence | migration primitive 검증 |
| [validate-quic-go-artifacts.sh#L39-L45](../../../harness/scripts/validate-quic-go-artifacts.sh#L39-L45) | valid artifact paths | `harness-validation.txt` | 재검산 위치 기록 |

## 4. qlog Scanner

| 코드 위치 | trigger/input | 출력 필드 | 해석 |
| --- | --- | --- | --- |
| [scan_qlog_events.py#L13-L24](../../../tools/scan_qlog_events.py#L13-L24) | `path_challenge`, `path_response`, `connection_started`, `http3:frame`, `chosen_alpn`, `migration`, `path` strings | event counters | qlog evidence를 정량 요약 |
| [scan_qlog_events.py#L27-L33](../../../tools/scan_qlog_events.py#L27-L33) | `.sqlog`, `.qlog`, `.json`, `.jsonl`, `.txt` files | qlog file set | quic-go/qlog output 포맷 변동 대응 |
| [scan_qlog_events.py#L36-L45](../../../tools/scan_qlog_events.py#L36-L45) | lowercased file text | per-pattern counts | schema parser가 아니라 evidence counter임을 명시 |
| [scan_qlog_events.py#L56-L85](../../../tools/scan_qlog_events.py#L56-L85) | qlog path CLI args | markdown/json summary | artifact 재검산 가능 |

## 5. False-Positive Guards

| guard | 코드 근거 | 방지하는 오해 |
| --- | --- | --- |
| switch-before-probe failure expected | [client/main.go#L199-L213](../../../repro/quic-go-min-repro/cmd/client/main.go#L199-L213) | path validation 없이 switch됐다고 착각하는 것 |
| client/server `ok=true` 동시 요구 | [validate-quic-go-artifacts.sh#L23-L29](../../../harness/scripts/validate-quic-go-artifacts.sh#L23-L29) | transport qlog만 보고 application payload 성공으로 쓰는 것 |
| qlog path evidence required | [validate-quic-go-artifacts.sh#L31-L37](../../../harness/scripts/validate-quic-go-artifacts.sh#L31-L37) | payload before/after만 보고 CM으로 단정하는 것 |
| post-migration local addr assertion | [client/main.go#L255-L267](../../../repro/quic-go-min-repro/cmd/client/main.go#L255-L267) | socket B로 실제 switch되지 않은 run을 성공 처리하는 것 |
