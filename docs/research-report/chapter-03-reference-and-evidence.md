# Chapter 3 Reference And Evidence

작성일: `2026-06-30`

이 문서는 Chapter 3 “구현체 Positive Control”의 실제 구현 코드, 실행 스크립트, 결과 문서, 외부 구현체 링크를 정리한다. 목적은 “controlled implementation에서는 CM이 된다”는 주장을 과장하지 않고, 어떤 근거가 현재 repo에 있고 어떤 근거는 요약 문서로만 남아 있는지 분리하는 것이다.

## 1. 현재 repo의 재현 코드

| 역할 | 링크 | 설명 |
| --- | --- | --- |
| quic-go client | [repro/quic-go-min-repro/cmd/client/main.go](../../repro/quic-go-min-repro/cmd/client/main.go) | UDP socket A로 dial, socket B 추가, `AddPath`, `Probe`, `Switch`, after payload 전송 |
| quic-go server | [repro/quic-go-min-repro/cmd/server/main.go](../../repro/quic-go-min-repro/cmd/server/main.go) | 같은 accepted QUIC connection에서 before/after stream payload 수신 |
| local run script | [repro/quic-go-min-repro/scripts/run-local-happy-path.sh](../../repro/quic-go-min-repro/scripts/run-local-happy-path.sh) | server/client 실행, qlog/keylog/result 생성 |
| harness wrapper | [harness/scripts/run-local-quic-go.sh](../../harness/scripts/run-local-quic-go.sh) | repo-level local quic-go run wrapper |
| artifact validator | [harness/scripts/validate-quic-go-artifacts.sh](../../harness/scripts/validate-quic-go-artifacts.sh) | client/server `ok=true`와 qlog path validation evidence 검사 |
| qlog scanner | [tools/scan_qlog_events.py](../../tools/scan_qlog_events.py) | `.sqlog`에서 `path_challenge`, `path_response`, packet event count 요약 |
| HTTP/3 client extension | [repro/quic-go-min-repro/cmd/h3client/main.go](../../repro/quic-go-min-repro/cmd/h3client/main.go) | HTTP/3 workload에서 active path switch를 수행하는 확장 client |
| HTTP/3 server extension | [repro/quic-go-min-repro/cmd/h3server/main.go](../../repro/quic-go-min-repro/cmd/h3server/main.go) | upload/download/browser workload를 제공하는 H3 server |

## 2. quic-go Fresh Rerun

이번 Chapter 3 정리 중 fresh rerun을 수행했다.

```bash
RUN_ID=chapter3-local-quic-go-rerun-20260630 \
PORT=4243 \
PAYLOAD_BYTES=1048576 \
harness/scripts/run-local-quic-go.sh
```

검증 결과:

| evidence | 결과 |
| --- | --- |
| run id | `chapter3-local-quic-go-rerun-20260630` |
| command exit | `0` |
| harness validation | `validation=ok` |
| client `ok` | `true` |
| server `ok` | `true` |
| before payload | 1 MiB, checksum matched |
| after payload | 1 MiB, checksum matched |
| validation-before-switch | `path not yet validated` |
| qlog client path frames | `path_challenge=2`, `path_response=2` |
| qlog server path frames | `path_challenge=2`, `path_response=2` |

Raw artifact는 `harness/results/chapter3-local-quic-go-rerun-20260630` 아래에 생성되었지만, `harness/results/`는 ignored artifact path라 commit하지 않는다.

## 3. qlog Validator Fix

fresh run 중 첫 validation은 실패했다.

```text
validation=fail
reason=missing qlog path validation evidence
```

실제 원인은 migration 실패가 아니었다. `.sqlog` 파일이 ignored artifact path 아래에 있어 `rg`가 기본 ignore rule로 qlog 파일을 스캔하지 않았다. `tools/scan_qlog_events.py`와 `grep -a`로 확인하면 path frames가 존재했다.

수정:

```text
rg --no-ignore --text -n "path_challenge|path_response" "$ARTIFACT_DIR/qlog"
```

수정한 파일:

- [harness/scripts/validate-quic-go-artifacts.sh](../../harness/scripts/validate-quic-go-artifacts.sh)
- [repro/quic-go-min-repro/scripts/run-local-happy-path.sh](../../repro/quic-go-min-repro/scripts/run-local-happy-path.sh)
- [repro/quic-go-min-repro/scripts/run-ec2-client.sh](../../repro/quic-go-min-repro/scripts/run-ec2-client.sh)
- [repro/quic-go-min-repro/scripts/run-h3-client.sh](../../repro/quic-go-min-repro/scripts/run-h3-client.sh)
- [repro/quic-go-min-repro/scripts/run-local-h3-midflight.sh](../../repro/quic-go-min-repro/scripts/run-local-h3-midflight.sh)

## 4. 외부 구현체 링크

| 구현체 | official/source link | Chapter 3에서의 역할 |
| --- | --- | --- |
| quic-go | [GitHub](https://github.com/quic-go/quic-go), [Connection Migration docs](https://quic-go.net/docs/quic/connection-migration/) | active migration positive control |
| Cloudflare quiche | [GitHub](https://github.com/cloudflare/quiche), [Connection API docs](https://docs.rs/quiche/latest/quiche/struct.Connection.html) | path event/qlog 교차검증 후보 |
| picoquic | [GitHub](https://github.com/private-octopus/picoquic) | NAT rebinding, migration failure, preferred address edge-case 기준선 |
| s2n-quic | [GitHub](https://github.com/aws/s2n-quic), [official docs](https://aws.github.io/s2n-quic/) | AWS/NLB 후보, migration tests |
| aioquic | [GitHub](https://github.com/aiortc/aioquic), [official docs](https://aioquic.readthedocs.io/) | Python readable passive/path-validation reference |
| ngtcp2 | [GitHub](https://github.com/ngtcp2/ngtcp2), [official site](https://nghttp2.org/ngtcp2/) | C library primitive comparison |
| Quinn | [GitHub](https://github.com/quinn-rs/quinn), [docs.rs](https://docs.rs/quinn/latest/quinn/) | Rust stack comparison |
| Neqo | [GitHub](https://github.com/mozilla/neqo) | Firefox-adjacent transport stack comparison |

구현체별 source trigger 위치는 Chapter 1 scanner table에 고정되어 있다.

- [tables/scanner-trigger-summary-20260630.md](tables/scanner-trigger-summary-20260630.md)

## 5. 기존 결과 문서와 현재 artifact 상태

| 항목 | 링크/상태 | 해석 |
| --- | --- | --- |
| local implementation summary | [docs/results/local-implementation-test-results.md](../results/local-implementation-test-results.md) | 8개 구현체 로컬 실행 요약 |
| quic-go minimum reproduction summary | [docs/results/quic-go-minimum-reproduction-results.md](../results/quic-go-minimum-reproduction-results.md) | quic-go active migration 최소 재현 요약 |
| quic-go fresh artifact | `harness/results/chapter3-local-quic-go-rerun-20260630` | 현재 로컬에 존재하지만 ignored path라 commit하지 않음 |
| quiche historical raw artifact | 현재 repo에 없음 | 제출 전 필요하면 재실행 필요 |
| picoquic historical raw artifact | 현재 repo에 없음 | 제출 전 필요하면 재실행 필요 |
| s2n-quic historical raw artifact | 현재 repo에 없음 | 제출 전 필요하면 재실행 필요 |
| aioquic/ngtcp2/Quinn/Neqo raw artifact | 현재 repo에 없음 | source/test summary evidence로만 사용 가능 |

## 6. 재현 명령 묶음

현재 repo에서 즉시 재현 가능한 최소 명령:

```bash
RUN_ID=chapter3-local-quic-go-rerun-$(date -u +%Y%m%dT%H%M%SZ) \
PORT=4243 \
PAYLOAD_BYTES=1048576 \
harness/scripts/run-local-quic-go.sh
```

qlog만 별도 요약:

```bash
python3 tools/scan_qlog_events.py harness/results/<RUN_ID>/qlog
```

artifact validation만 재실행:

```bash
harness/scripts/validate-quic-go-artifacts.sh harness/results/<RUN_ID>
```

## 7. 검수 체크리스트

| 항목 | 판정 | 근거 |
| --- | --- | --- |
| 현재 repo에서 최소 positive control이 재실행되는가? | PASS | `chapter3-local-quic-go-rerun-20260630` |
| qlog path validation false negative를 제거했는가? | PASS | validator와 qlog-producing scripts에 `--no-ignore --text` 적용 |
| 외부 구현체 링크가 있는가? | PASS | 8개 구현체 official/source/docs link 포함 |
| raw artifact 한계를 명시했는가? | PASS | quic-go 외 historical raw artifact가 현재 repo에 없음을 명시 |
| browser handover claim과 분리했는가? | PASS | 이 챕터는 implementation positive control로만 해석 |
