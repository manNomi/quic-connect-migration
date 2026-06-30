# Chapter 3. 구현체 Positive Control

작성일: `2026-06-30`

## 1. 이 챕터의 목적

Chapter 2는 CM이 잘 보이지 않는 이유가 여러 계층에 흩어져 있음을 보여줬다. 그렇다면 복잡한 browser, CDN, LB, OS route change를 제거한 상태에서 먼저 확인해야 할 질문은 이것이다.

> controlled QUIC client/server에서는 Connection Migration이 실제로 동작하는가?

이 챕터의 역할은 browser-level claim을 만드는 것이 아니다. 구현체 positive control을 확보해서, 이후 browser/public handover 실패를 “CM 자체가 원래 없는 기술이라서”로 오해하지 않게 만드는 것이다.

## 2. 핵심 결론

현재까지의 결과는 다음과 같이 정리된다.

> quic-go, quiche, picoquic, s2n-quic 등 주요 구현체에서는 path validation, active/passive migration, NAT rebinding, migration failure, preferred address, disabled migration 같은 primitive와 test evidence가 확인되었다. 특히 quic-go는 현재 repo의 재현 코드로 `AddPath -> Probe -> Switch` 흐름을 다시 실행해 PASS를 확인했다.

2026-06-30 추가 재검수에서는 quiche, picoquic, s2n-quic, ngtcp2, aioquic도 현재 HEAD 기준으로 다시 실행해 PASS evidence를 확보했다. 다만 이 결론은 library/client-server positive control이다. Chrome/Safari/Android browser HTTP/3 handover 성공을 의미하지 않는다.

## 3. 현재 repo에서 재실행한 검수

### 3.1 왜 quic-go를 먼저 강하게 검수했는가

quic-go를 먼저 고른 것은 구현체 인기도만의 문제가 아니라 실험 통제 때문이다. quic-go는 active migration을 `AddPath -> Probe -> Switch` 순서로 직접 트리거할 수 있고, 같은 repo의 HTTP/3 harness, qlog, payload checksum 검증으로 쉽게 확장할 수 있었다. 즉 quic-go는 "CM이 구현되어 있고 controlled client/server에서는 실제로 동작한다"는 positive control을 만들기 위한 첫 기준점이었다.

하지만 quic-go 하나만 있으면 "다른 구현체는 실제로 검수하지 않았는가?"라는 약점이 남는다. 그래서 이 챕터의 최종 형태에서는 quic-go를 strong positive control로 두고, 다른 구현체를 cross-implementation maturity evidence로 보강한다.

### 3.2 quic-go fresh rerun

이번 정리 중 quic-go 최소 재현을 fresh run으로 다시 실행했다.

```bash
RUN_ID=chapter3-local-quic-go-rerun-20260630 \
PORT=4243 \
PAYLOAD_BYTES=1048576 \
harness/scripts/run-local-quic-go.sh
```

결과:

| 항목 | 결과 |
| --- | --- |
| `go test ./...` | PASS |
| client result | `ok=true` |
| server result | `ok=true` |
| validation before probe | `path not yet validated` 확인 |
| socket/path change | socket A에서 socket B로 전환 확인 |
| payload continuity | before/after 각 1 MiB payload checksum 일치 |
| qlog path validation | client/server qlog에서 `path_challenge`, `path_response` 확인 |
| harness validation | PASS |

중요한 검수 중 발견한 문제도 함께 기록한다.

| 문제 | 원인 | 조치 |
| --- | --- | --- |
| 첫 validation이 `missing qlog path validation evidence`로 실패 | `.sqlog`가 ignored artifact path 아래에 있어 `rg`가 기본 ignore rule로 파일을 스캔하지 않음 | qlog 검색 스크립트에 `rg --no-ignore --text` 적용 |

이 조치 후 같은 artifact validation과 fresh rerun이 모두 통과했다.

### 3.3 추가 구현체 fresh rerun

quic-go 편중을 줄이기 위해 2026-06-30에 다음 구현체를 현재 HEAD 기준으로 다시 실행했다.

| 구현체 | commit | 실행 범위 | 결과 | 해석 |
| --- | --- | --- | --- | --- |
| Cloudflare quiche | `c4c0b978461aa153399a90217d85bebd1800f84d` | library migration tests, sample client/server migration, qlog | PASS | quic-go 외 강한 implementation positive control |
| picoquic | `d3a80307200d28c53a6470d257bdd0801fad7971` | NAT rebinding, migration with loss, migration failure, preferred address, disabled migration | PASS | edge-case maturity evidence |
| s2n-quic | `0f5a4f8ae4163f1b84e72cd29ad110ad99d7efd1` | `connection_migration` test suite, PathChallenge/PathResponse events | PASS | AWS-relevant library evidence |
| ngtcp2 | `c24b12690c5bdf7ad2715ae427504e76bf5c6ffc` | client migration, path validation, disable active migration, frame encode | PASS | C library primitive evidence |
| aioquic | `6d36838d008c2202c337142fa07e8bf80e96bac8` | PATH_CHALLENGE/PATH_RESPONSE, preferred address, disable active migration tests | PASS | readable passive/path-validation reference |

상세 명령과 로그 위치는 [implementation-rerun-results-20260630.md](../results/implementation-rerun-results-20260630.md)에 분리했다. raw log는 `harness/results/impl-rerun-20260630T070249Z` 아래에 있으며, `harness/results/`가 ignored artifact path라 공개 repo에는 요약만 남긴다.

## 4. Positive Control의 증거 사슬

quic-go fresh run 기준으로 evidence chain은 다음과 같다.

| evidence | 확인 방식 | 의미 |
| --- | --- | --- |
| API-level trigger | `conn.AddPath`, `path.Probe`, `path.Switch` | 실험자가 active migration을 직접 트리거 |
| negative precondition | validation 전 `Switch()`가 `ErrPathNotValidated` 계열 error | probe 없이 path switch가 허용되지 않음 |
| path validation | qlog `path_challenge`, `path_response` | QUIC path validation primitive 실행 |
| payload continuity | before/after payload checksum | migration 전후 application payload 전달 |
| server-side path observation | server receive metadata | 같은 accepted connection에서 remote tuple 변화와 payload 수신 |
| reproducibility | `harness/scripts/run-local-quic-go.sh`, `validate-quic-go-artifacts.sh` | 현재 repo에서 반복 실행 가능 |

## 5. 구현체별 로컬 실행 요약

| 구현체 | 현재 evidence 상태 | 확인한 범위 | 해석 |
| --- | --- | --- | --- |
| quic-go | 현재 repo에서 fresh rerun PASS | active migration, `AddPath -> Probe -> Switch`, qlog, before/after payload | 가장 강한 positive control |
| Cloudflare quiche | 2026-06-30 fresh rerun PASS | migration tests, sample client/server, qlog | quic-go 교차검증 후보 |
| picoquic | 2026-06-30 fresh rerun PASS | NAT rebinding, migration failure, preferred address, disabled migration | edge-case maturity 기준선 |
| s2n-quic | 2026-06-30 fresh rerun PASS | IP/port rebinding, PathChallenge/PathResponse, active path update | AWS/NLB 후보 |
| aioquic | 2026-06-30 fresh rerun PASS | PATH_CHALLENGE/PATH_RESPONSE, preferred address, disable_active_migration parsing | readable passive reference |
| ngtcp2 | 2026-06-30 fresh rerun PASS | client migration test, path validation, disable active migration, frame encode | C library primitive 비교군 |
| Quinn | 결과 문서 기준 PASS, raw artifact는 현재 repo에 없음 | proto migration, rebind receive path | Rust stack 비교군 |
| Neqo | 결과 문서 기준 PASS, raw artifact는 현재 repo에 없음 | rebind, graceful/immediate migration, preferred address, disabled migration | Firefox-adjacent 비교군 |

주의:

> 2026-06-30 fresh rerun으로 quiche, picoquic, s2n-quic, ngtcp2, aioquic의 raw execution artifact는 로컬 ignored path에 존재한다. 다만 공개 repo에는 큰 raw log를 그대로 커밋하지 않았으므로, 논문 제출 전에는 sanitized evidence bundle을 만들거나 명령/commit/result 중심으로 인용해야 한다.

## 6. 논문에서 쓸 수 있는 주장

안전하게 쓸 수 있는 주장:

> Controlled implementation tests show that QUIC Connection Migration is an implemented and testable transport capability in multiple stacks. In quic-go, active migration can be explicitly triggered and verified through path validation frames, address change, and payload continuity.

피해야 할 주장:

| 피해야 할 주장 | 이유 |
| --- | --- |
| “quic-go에서 됐으니 Chrome에서도 된다.” | browser policy와 NetLog/session attribution 계층이 빠져 있다. |
| “test PASS가 production deployment readiness다.” | LB/CDN/proxy/middlebox 경로가 빠져 있다. |
| “PATH_CHALLENGE만 있으면 application continuity가 보장된다.” | application task success와 transport path validation은 다른 층이다. |
| “quiche/picoquic/s2n-quic raw log가 현재 repo에 있다.” | 현재 repo에는 요약 문서와 source links만 있다. |

## 7. 다음 챕터로 넘어간 이유

controlled implementation positive control이 확인되면, 다음 질문은 deployment path다.

> 같은 transport capability가 AWS NLB, proxy, CDN 같은 실제 배포 경로에서도 유지되는가?

그래서 Chapter 4에서는 CID-aware load balancing, proxy negative control, CDN edge termination을 다룬다.

## 8. 검수 결과

| 검수 항목 | 결과 |
| --- | --- |
| quic-go fresh rerun | PASS |
| quiche fresh rerun | PASS |
| picoquic fresh rerun | PASS |
| s2n-quic fresh rerun | PASS |
| ngtcp2 fresh rerun | PASS |
| aioquic fresh rerun | PASS |
| qlog validator false negative 수정 | PASS |
| 현재 repo 코드 링크 | `repro/quic-go-min-repro`, `harness/scripts/run-local-quic-go.sh` |
| 외부 구현체/source 링크 | `chapter-03-reference-and-evidence.md`에 정리 |
| raw artifact availability | fresh rerun artifact는 로컬 ignored path에 있음. 공개 repo에는 요약 문서와 재현 명령을 남김 |
| claim boundary | browser/public handover 성공 claim을 하지 않음 |
