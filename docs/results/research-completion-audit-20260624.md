# Research completion audit

작성일: 2026-06-24

## 1. 목적

활성 연구 목표는 다음이다.

> QUIC/HTTP/3 Connection Migration 논문을 위한 재현 가능한 실험 하네스, readiness gate, controlled public/browser network-change 실험 결과와 문서화까지 완성한다.

이 문서는 현재 저장소가 그 목표를 어디까지 만족하는지 요구사항별로 점검한다. 아직 부족한 부분을 숨기지 않고, 논문에서 claim 가능한 범위를 명확히 제한한다.

## 2. 요구사항별 상태

| 요구사항 | 현재 상태 | 근거 | 판정 |
| --- | --- | --- | --- |
| 재현 가능한 local QUIC/HTTP/3 migration harness | 구현됨 | `repro/quic-go-min-repro`, local transport/H3/mid-flight scripts, `go test ./...` 통과 | 충족 |
| 구현체 성숙도 조사 | 구현/문서화됨 | `data/implementation-survey.csv`, `tools/scan_implementation_evidence.py`, 관련 docs | 충족 |
| AWS/NLB deployment-path 검증 | 수행됨 | AWS NLB positive/negative control rows in `data/experiment-results.csv`, NLB result docs | 충족 |
| Browser HTTP/3 baseline | local forced-QUIC 기준 수행됨 | Chrome local baseline, sequence, polling, slow, downlink, upload rebinding rows | 부분 충족 |
| Browser natural/public H3 baseline | third-party public endpoint는 negative/control 수준 | public discovery controls show application H3 not confirmed | 부분 충족 |
| Controlled public origin readiness gate | 구현됨 | `check_controlled_public_experiment_readiness.py`, `controlled-public-preflight.sh`, runbooks | 충족 |
| Controlled public active network-change result | 아직 없음 | public controlled origin, baseline PASS summary, active secondary path 필요 | 미충족 |
| Browser active path-change result | 아직 없음 | 현재 active non-loopback IPv4 path가 `en0` 하나뿐 | 미충족 |
| Safari baseline/handover result | baseline/network-change harness는 있음; 본 실험 결과는 없음 | Safari WebDriver wrappers exist; controlled public Safari baseline/handover not run | 부분 충족 |
| Android Chrome handover result | ADB network-change harness는 있음; 본 실험 결과는 없음 | Android Chrome wrapper exists; no ADB device connected | 부분 충족 |
| Evidence interpretation rubric | 구현/문서화됨 | `data/evidence-chain-rubric.csv`, evidence synthesis doc | 충족 |
| 논문용 결과표 | 생성됨 | `tools/build_paper_tables.py`, `docs/results/paper-tables-20260624.md` | 충족 |
| 논문 Results 초안 | 작성됨 | `paper/results-section-ko.md`, `paper/results-section-en.md` | 충족 |

## 3. 현재 readiness snapshot

최근 `check_handover_readiness.py --format markdown` 결과:

| check | value |
| --- | --- |
| Chrome found | `true` |
| ADB found | `true` |
| Android devices | `-` |
| active IPv4 interfaces | `en0(192.168.0.212)` |
| secondary path ready | `false` |
| AWS identity OK | `false` |
| disk available GiB | `47.76` |
| desktop handover ready | `false` |
| Android handover ready | `false` |

blockers:

1. Desktop active path-change 실험에는 최소 2개의 active non-loopback IPv4 interface가 필요하다.
2. Android handover 실험에는 ADB로 연결된 Android device가 필요하다.
3. controlled public origin 자동 구축에는 AWS identity가 필요하다.

## 4. 논문에서 현재 claim 가능한 범위

현재 claim 가능:

1. QUIC CM primitive는 quic-go/quiche 등 구현체와 controlled 환경에서 관찰된다.
2. quic-go controlled client에서는 HTTP/3 post-migration 및 mid-flight workload continuity가 관찰됐다.
3. AWS NLB에서는 QUIC-LB plaintext CID와 `QuicServerId`가 맞아야 continuity가 유지된다.
4. Chrome forced-QUIC local origin은 HTTP/3 browser workload baseline을 만들 수 있다.
5. Chrome heartbeat/downlink 대조군은 tuple change 단독 주장이 위험함을 보여준다.
6. Chrome streaming upload rebinding 대조군은 request-level tuple 변화 부재가 packet-level rebinding/path validation 부재를 의미하지 않음을 보여준다.

현재 claim 불가:

1. Chrome 실제 Wi-Fi/LTE handover에서 HTTP/3 CM이 성공했다.
2. Safari 실제 handover에서 HTTP/3 CM이 성공했다.
3. Android Chrome 실제 Wi-Fi/LTE handover에서 HTTP/3 CM이 성공했다.
4. CloudFront/Cloudflare 같은 managed CDN edge에서 end-to-end QUIC CM이 성공했다.
5. application heartbeat나 Service Worker가 실제 active path-change recovery를 개선했다.

## 5. 완료까지 남은 필수 실험

| priority | 실험 | 필요한 준비물 | 성공/실패 판정 |
| --- | --- | --- | --- |
| P0 | controlled public Chrome H3 baseline | public WebPKI origin, UDP/TCP 443, baseline server artifact | server request HTTP/3, qlog H3, browser NetLog application H3 |
| P0 | controlled public Chrome active path-change downlink no-heartbeat | P0 baseline + active secondary path + `NETWORK_CHANGE_CMD` | client active path change, task completion, qlog/session evidence |
| P0 | controlled public Chrome active path-change downlink heartbeat | same as above | heartbeat가 recovery/session behavior를 바꾸는지 비교 |
| P1 | Safari controlled public baseline/network-change | Safari WebDriver + server qlog + packet capture plan | server/qlog H3 evidence, no NetLog dependency |
| P1 | Android Chrome/Cronet handover | ADB device + Wi-Fi/LTE or tethering path + raw Android snapshot/capture | browser/app policy와 handover behavior 관찰 |
| P2 | Service Worker/application recovery variant | public origin + controlled active path-change | application-level recovery time/manual retry 여부 |

## 6. 현재 목표 달성 여부

현재 상태는 “논문을 위한 재현 가능한 하네스와 상당한 positive/negative control evidence는 갖췄지만, controlled public/browser active network-change 본 실험은 아직 완료되지 않음”이다.

따라서 활성 goal은 아직 complete가 아니다. 다만 다음 작업을 실행할 준비는 되어 있다.

1. public controlled origin 준비
2. secondary active path 확보
3. Chrome CDP downlink no-heartbeat/heartbeat active path-change 실행
4. Safari/Android follow-up
5. `docs/results/final-browser-handover-experiment-protocol-20260624.md` 기준으로 trial 반복과 claim strength 분류
