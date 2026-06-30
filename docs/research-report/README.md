# QUIC Connection Migration 연구 보고용 정리

작성일: `2026-06-30`

이 폴더는 교수님 보고와 논문 초안 작성에 바로 사용할 수 있도록 기존 연구 산출물을 챕터별로 다시 정리하는 공간이다. `docs/results/`는 실험 결과와 중간 산출물이 많이 섞여 있으므로, 여기서는 보고서처럼 읽히는 순서와 표를 따로 만든다.

## 현재 정리 상태

| 챕터 | 상태 | 문서 |
| --- | --- | --- |
| Chapter 1. QUIC Connection Migration 구현체 성숙도 조사 | 작성 완료 | `chapter-01-implementation-maturity.md` |
| Chapter 1 부록. 실제 참고 링크와 scanner trigger 근거 | 작성 완료 | `chapter-01-reference-and-scanner-evidence.md` |
| Chapter 1 표. 구현체별 조사 CSV 가독화 | 작성 완료 | `tables/implementation-survey-readable.md` |
| Chapter 1 표. scanner trigger 위치 | 작성 완료 | `tables/scanner-trigger-summary-20260630.md` |
| Chapter 2. CM 미사용/저가시성 원인 분석 | 작성 완료 | `chapter-02-underuse-friction.md` |
| Chapter 2 부록. 실제 참고 링크와 friction trigger 근거 | 작성 완료 | `chapter-02-reference-and-evidence.md` |
| Chapter 2 표. 외부 링크 검수 결과 | 작성 완료 | `tables/chapter-02-external-link-check-20260630.md` |
| Chapter 3. 구현체 Positive Control | 작성 완료 | `chapter-03-implementation-positive-control.md` |
| Chapter 3 부록. 실제 구현 코드와 reference 근거 | 작성 완료 | `chapter-03-reference-and-evidence.md` |
| Chapter 3 표. 외부 링크 검수 결과 | 작성 완료 | `tables/chapter-03-external-link-check-20260630.md` |
| Chapter 4. 배포 경로 검수: AWS NLB, Proxy, CDN | 작성 완료 | `chapter-04-deployment-path.md` |
| Chapter 4 부록. 실제 배포 코드와 reference 근거 | 작성 완료 | `chapter-04-reference-and-evidence.md` |
| Chapter 4 표. 외부 링크 검수 결과 | 작성 완료 | `tables/chapter-04-external-link-check-20260630.md` |
| Chapter 5. 브라우저 CM 관찰성 기준 | 작성 완료 | `chapter-05-browser-observability.md` |
| Chapter 5 부록. 실제 구현 코드와 reference 근거 | 작성 완료 | `chapter-05-reference-and-evidence.md` |
| Chapter 5 표. scanner trigger 위치 | 작성 완료 | `tables/chapter-05-scanner-trigger-map-20260630.md` |
| Chapter 5 표. 외부 링크 검수 결과 | 작성 완료 | `tables/chapter-05-external-link-check-20260630.md` |

## 폴더 운영 방식

앞으로 챕터를 추가할 때는 다음 규칙을 따른다.

1. 챕터 본문은 `chapter-XX-*.md`에 둔다.
2. 원본 CSV나 실험 matrix를 보고용으로 바꾼 표는 `tables/` 아래에 둔다.
3. 원본 데이터는 수정하지 않고, 보고용 문서는 원본 데이터와 결과 문서를 참조한다.
4. 공개 저장소에 올라갈 수 있도록 credential, 공인 IP, hostname, SSH target, local network address는 쓰지 않는다.
5. “성공했다”, “보장한다” 같은 강한 표현은 evidence chain이 충분할 때만 쓴다.

## 주요 원본 산출물

| 원본 | 역할 |
| --- | --- |
| `data/implementation-survey.csv` | Chapter 1 구현체별 원본 조사표 |
| `tools/scan_implementation_evidence.py` | 구현체 repo에서 CM 관련 evidence 후보를 찾는 scanner |
| `docs/research-report/chapter-01-reference-and-scanner-evidence.md` | 공식 참고 링크와 scanner trigger 검증 부록 |
| `docs/research-report/tables/scanner-trigger-summary-20260630.md` | 15개 공개 구현체 scanner trigger 위치 표 |
| `data/cm-operational-friction-rubric.csv` | Chapter 2 friction_id별 matching term |
| `data/cm-operational-friction-matrix-20260624.csv` | Chapter 2 friction matrix 원본 CSV |
| `tools/build_cm_operational_friction_matrix.py` | Chapter 2 friction matrix builder |
| `repro/quic-go-min-repro/` | Chapter 3 quic-go positive-control 재현 코드 |
| `harness/scripts/run-local-quic-go.sh` | Chapter 3 local quic-go 재현 wrapper |
| `harness/scripts/validate-quic-go-artifacts.sh` | Chapter 3 artifact validator |
| `repro/quic-go-min-repro/internal/common/aws_nlb_cid.go` | Chapter 4 AWS NLB routable CID generator |
| `harness/scripts/run-aws-nlb-quic-data-plane.sh` | Chapter 4 AWS NLB positive/negative control harness |
| `tools/check_browser_cm_observability.py` | Chapter 5 browser observability readiness scanner |
| `tools/classify_chrome_h3_artifacts.py` | Chapter 5 Chrome local H3/rebinding artifact classifier |
| `tools/classify_controlled_public_h3_network_change.py` | Chapter 5 controlled public-origin network-change classifier |
| `docs/results/chapter1-implementation-maturity-methodology-20260630.md` | Chapter 1 상세 방법론 원본 |
| `docs/results/local-implementation-test-results.md` | 8개 구현체 local test 결과 |
| `docs/results/chaptered-research-synthesis-20260629.md` | 전체 챕터 흐름 |
