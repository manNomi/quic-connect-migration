# QUIC Connection Migration 연구 보고용 정리

작성일: `2026-06-30`

이 폴더는 연구 보고와 논문 초안 작성에 바로 사용할 수 있도록 기존 연구 산출물을 챕터별로 다시 정리하는 공간이다. `docs/results/`는 실험 결과와 중간 산출물이 많이 섞여 있으므로, 여기서는 보고서처럼 읽히는 순서와 표를 따로 만든다.

## 현재 정리 상태

| 챕터 | 상태 | 문서 |
| --- | --- | --- |
| 전체 부록. 참고자료 링크 카탈로그 | 작성 완료 | `reference-link-catalog-20260630.md` |
| 전체 부록. scanner/classifier/builder trigger 감사 인덱스 | 작성 완료 | `scanner-trigger-audit-index-20260630.md` |
| Chapter 1. QUIC Connection Migration 구현체 성숙도 조사 | 작성 완료 | `chapter-01-implementation-maturity.md` |
| Chapter 1 부록. 실제 참고 링크와 scanner trigger 근거 | 작성 완료 | `chapter-01-reference-and-scanner-evidence.md` |
| Chapter 1 표. 구현체별 조사 CSV 가독화 | 작성 완료 | `tables/implementation-survey-readable.md` |
| Chapter 1 표. scanner trigger 위치 | 작성 완료 | `tables/scanner-trigger-summary-20260630.md` |
| Chapter 1 표. 외부 링크 검수 결과 | 작성 완료 | `tables/chapter-01-external-link-check-20260630.md` |
| Chapter 2. CM 미사용/저가시성 원인 분석 | 작성 완료 | `chapter-02-underuse-friction.md` |
| Chapter 2 부록. 실제 참고 링크와 friction trigger 근거 | 작성 완료 | `chapter-02-reference-and-evidence.md` |
| Chapter 2 표. builder trigger 위치 | 작성 완료 | `tables/chapter-02-scanner-trigger-map-20260630.md` |
| Chapter 2 표. 외부 링크 검수 결과 | 작성 완료 | `tables/chapter-02-external-link-check-20260630.md` |
| Chapter 3. 구현체 Positive Control | 작성 완료 | `chapter-03-implementation-positive-control.md` |
| Chapter 3 부록. 실제 구현 코드와 reference 근거 | 작성 완료 | `chapter-03-reference-and-evidence.md` |
| Chapter 3 표. scanner trigger 위치 | 작성 완료 | `tables/chapter-03-scanner-trigger-map-20260630.md` |
| Chapter 3 표. 외부 링크 검수 결과 | 작성 완료 | `tables/chapter-03-external-link-check-20260630.md` |
| Chapter 4. 배포 경로 검수: AWS NLB, Proxy, CDN | 작성 완료 | `chapter-04-deployment-path.md` |
| Chapter 4 부록. 실제 배포 코드와 reference 근거 | 작성 완료 | `chapter-04-reference-and-evidence.md` |
| Chapter 4 표. deployment trigger 위치 | 작성 완료 | `tables/chapter-04-scanner-trigger-map-20260630.md` |
| Chapter 4 표. 외부 링크 검수 결과 | 작성 완료 | `tables/chapter-04-external-link-check-20260630.md` |
| Chapter 5. 브라우저 CM 관찰성 기준 | 작성 완료 | `chapter-05-browser-observability.md` |
| Chapter 5 부록. 실제 구현 코드와 reference 근거 | 작성 완료 | `chapter-05-reference-and-evidence.md` |
| Chapter 5 표. scanner trigger 위치 | 작성 완료 | `tables/chapter-05-scanner-trigger-map-20260630.md` |
| Chapter 5 표. 외부 링크 검수 결과 | 작성 완료 | `tables/chapter-05-external-link-check-20260630.md` |
| Chapter 6. Local Chrome NAT Rebinding Control | 작성 완료 | `chapter-06-local-chrome-nat-rebinding.md` |
| Chapter 6 부록. 실제 구현 코드와 reference 근거 | 작성 완료 | `chapter-06-reference-and-evidence.md` |
| Chapter 6 표. scanner trigger 위치 | 작성 완료 | `tables/chapter-06-scanner-trigger-map-20260630.md` |
| Chapter 6 표. 외부 링크 검수 결과 | 작성 완료 | `tables/chapter-06-external-link-check-20260630.md` |
| Chapter 7. Controlled Public Origin 구축 및 HTTP/3 Baseline | 작성 완료 | `chapter-07-controlled-public-origin-baseline.md` |
| Chapter 7 부록. 실제 구현 코드와 reference 근거 | 작성 완료 | `chapter-07-reference-and-evidence.md` |
| Chapter 7 표. scanner trigger 위치 | 작성 완료 | `tables/chapter-07-scanner-trigger-map-20260630.md` |
| Chapter 7 표. 외부 링크 검수 결과 | 작성 완료 | `tables/chapter-07-external-link-check-20260630.md` |
| Chapter 8. Full-Response Downlink Public Handover | 작성 완료 | `chapter-08-full-response-downlink-handover.md` |
| Chapter 8 부록. 실제 구현 코드와 reference 근거 | 작성 완료 | `chapter-08-reference-and-evidence.md` |
| Chapter 8 표. scanner trigger 위치 | 작성 완료 | `tables/chapter-08-scanner-trigger-map-20260630.md` |
| Chapter 8 표. 외부 링크 검수 결과 | 작성 완료 | `tables/chapter-08-external-link-check-20260630.md` |
| Chapter 9. Byte-Range Download And Retry Recovery | 작성 완료 | `chapter-09-byte-range-retry-recovery.md` |
| Chapter 9 부록. 실제 구현 코드와 reference 근거 | 작성 완료 | `chapter-09-reference-and-evidence.md` |
| Chapter 9 표. scanner trigger 위치 | 작성 완료 | `tables/chapter-09-scanner-trigger-map-20260630.md` |
| Chapter 9 표. 외부 링크 검수 결과 | 작성 완료 | `tables/chapter-09-external-link-check-20260630.md` |
| Chapter 10. Upload Workload Recovery | 작성 완료 | `chapter-10-upload-workload-recovery.md` |
| Chapter 10 부록. 실제 구현 코드와 reference 근거 | 작성 완료 | `chapter-10-reference-and-evidence.md` |
| Chapter 10 표. scanner trigger 위치 | 작성 완료 | `tables/chapter-10-scanner-trigger-map-20260630.md` |
| Chapter 10 표. 외부 링크 검수 결과 | 작성 완료 | `tables/chapter-10-external-link-check-20260630.md` |
| Chapter 11. Streaming And Media Workload | 작성 완료 | `chapter-11-streaming-media-workload.md` |
| Chapter 11 부록. 실제 구현 코드와 reference 근거 | 작성 완료 | `chapter-11-reference-and-evidence.md` |
| Chapter 11 표. scanner trigger 위치 | 작성 완료 | `tables/chapter-11-scanner-trigger-map-20260630.md` |
| Chapter 11 표. 외부 링크 검수 결과 | 작성 완료 | `tables/chapter-11-external-link-check-20260630.md` |
| Chapter 12. Literature-Based Claim Positioning | 작성 완료 | `chapter-12-literature-claim-positioning.md` |
| Chapter 12 부록. 실제 source link와 builder 근거 | 작성 완료 | `chapter-12-reference-and-evidence.md` |
| Chapter 12 표. builder trigger 위치 | 작성 완료 | `tables/chapter-12-scanner-trigger-map-20260630.md` |
| Chapter 12 표. 외부 링크 검수 결과 | 작성 완료 | `tables/chapter-12-external-link-check-20260630.md` |

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
| `docs/research-report/reference-link-catalog-20260630.md` | 전체 외부 참고자료 링크 카탈로그 |
| `docs/research-report/scanner-trigger-audit-index-20260630.md` | 전체 scanner/classifier/builder trigger 감사 인덱스 |
| `tools/scan_implementation_evidence.py` | 구현체 repo에서 CM 관련 evidence 후보를 찾는 scanner |
| `docs/research-report/chapter-01-reference-and-scanner-evidence.md` | 공식 참고 링크와 scanner trigger 검증 부록 |
| `docs/research-report/tables/scanner-trigger-summary-20260630.md` | 15개 공개 구현체 scanner trigger 위치 표 |
| `docs/research-report/tables/chapter-01-external-link-check-20260630.md` | Chapter 1 source/reference/clone URL 외부 링크 검수 결과 |
| `data/cm-operational-friction-rubric.csv` | Chapter 2 friction_id별 matching term |
| `data/cm-operational-friction-matrix-20260624.csv` | Chapter 2 friction matrix 원본 CSV |
| `tools/build_cm_operational_friction_matrix.py` | Chapter 2 friction matrix builder |
| `docs/research-report/tables/chapter-02-scanner-trigger-map-20260630.md` | Chapter 2 builder input/trigger/output 추적표 |
| `repro/quic-go-min-repro/` | Chapter 3 quic-go positive-control 재현 코드 |
| `harness/scripts/run-local-quic-go.sh` | Chapter 3 local quic-go 재현 wrapper |
| `harness/scripts/validate-quic-go-artifacts.sh` | Chapter 3 artifact validator |
| `harness/scripts/run-nginx-quic-active-migration-demo.sh` | Chapter 3 nginx QUIC active migration runtime demo |
| `harness/scripts/run-haproxy-http3-negative-control.sh` | Chapter 4 HAProxy HTTP/3 negative-control runner |
| `harness/scripts/openlitespeed-runtime-preflight.sh` | Chapter 4 OpenLiteSpeed production-like runtime readiness gate |
| `tools/report_artifact_storage.py` | Chapter 4 OpenLiteSpeed runtime 전 local artifact/disk usage report |
| `tools/audit_artifact_cleanup_safety.py` | Chapter 4 cleanup 후보가 기존 CSV 근거를 건드리는지 점검하는 safety audit |
| `tools/plan_artifact_cleanup.py` | Chapter 4 cleanup dry-run planner; 삭제 없이 회수 가능 용량만 계산 |
| `docs/results/openlitespeed-quic-cm-source-feasibility-20260630.md` | Chapter 4 OpenLiteSpeed production-like follow-up source feasibility |
| `docs/results/openlitespeed-runtime-preflight-20260630.md` | Chapter 4 OpenLiteSpeed runtime preflight result |
| `docs/results/artifact-storage-report-20260630-openlitespeed-preflight.md` | Chapter 4 OpenLiteSpeed runtime 전 local artifact storage report |
| `docs/results/artifact-cleanup-safety-audit-20260630-openlitespeed-preflight.md` | Chapter 4 cleanup safety audit; referenced/planned raw artifact 보호 |
| `docs/results/artifact-cleanup-dry-run-20260630-openlitespeed-preflight.md` | Chapter 4 cleanup dry-run; 안전 후보만으로는 30GiB 목표 미달 |
| `docs/research-report/tables/chapter-03-scanner-trigger-map-20260630.md` | Chapter 3 quic-go positive-control trigger 추적표 |
| `repro/quic-go-min-repro/internal/common/aws_nlb_cid.go` | Chapter 4 AWS NLB routable CID generator |
| `harness/scripts/run-aws-nlb-quic-data-plane.sh` | Chapter 4 AWS NLB positive/negative control harness |
| `docs/research-report/tables/chapter-04-scanner-trigger-map-20260630.md` | Chapter 4 AWS NLB/H3 deployment trigger 추적표 |
| `tools/check_browser_cm_observability.py` | Chapter 5 browser observability readiness scanner |
| `tools/classify_chrome_h3_artifacts.py` | Chapter 5 Chrome local H3/rebinding artifact classifier |
| `tools/classify_controlled_public_h3_network_change.py` | Chapter 5 controlled public-origin network-change classifier |
| `repro/quic-go-min-repro/cmd/udprebindproxy/main.go` | Chapter 6 local UDP NAT rebinding proxy |
| `repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh` | Chapter 6 local Chrome H3 rebinding harness |
| `tools/check_public_origin_readiness.py` | Chapter 7 public origin readiness scanner |
| `tools/classify_controlled_public_h3_baseline.py` | Chapter 7 controlled public application H3 baseline classifier |
| `repro/quic-go-min-repro/scripts/run-controlled-public-h3-network-change.sh` | Chapter 8 public-origin active network-change runner |
| `tools/capture_network_path_snapshot.py` | Chapter 8 client path snapshot collector |
| `tools/compare_network_path_snapshots.py` | Chapter 8 client path-change comparator |
| `tools/classify_controlled_public_h3_network_change.py` | Chapter 8 controlled public active network-change classifier |
| `tools/validate_final_handover_trial_artifact.py` | Chapter 8 final/negative-control claim-strength validator |
| `harness/scripts/run-aws-controlled-public-chrome-trial.sh` | Chapter 9 AWS controlled public Chrome trial wrapper |
| `tools/summarize_chrome_rebinding_range_matrix.py` | Chapter 9 local range control summarizer |
| `tools/summarize_chrome_rebinding_upload_matrix.py` | Chapter 10 local upload control summarizer |
| `tools/summarize_chrome_rebinding_media_matrix.py` | Chapter 11 local media segment summarizer |
| `tools/summarize_chrome_rebinding_buffered_media_matrix.py` | Chapter 11 local buffered media summarizer |
| `tools/build_literature_claim_positioning.py` | Chapter 12 literature-to-claim positioning builder |
| `docs/results/chapter1-implementation-maturity-methodology-20260630.md` | Chapter 1 상세 방법론 원본 |
| `docs/results/local-implementation-test-results.md` | 초기 8개 구현체 local test 결과 |
| `docs/results/implementation-rerun-results-20260630.md` | 2026-06-30 구현체 fresh rerun/demo/partial 결과 |
| `docs/results/s2n-quic-nlb-cid-provider-rerun-20260630.md` | s2n-quic AWS NLB CID provider proof 복원 및 rerun 결과 |
| `docs/results/lsquic-preferred-address-app-demo-20260630.md` | LSQUIC preferred-address HTTP/3 app demo 결과 |
| `docs/results/lsquic-nat-rebinding-app-demo-20260630.md` | LSQUIC local UDP proxy NAT rebinding HTTP/3 app demo 결과 |
| `docs/results/nginx-quic-active-migration-runtime-20260630.md` | nginx HTTP/3 server active-client-migration runtime demo 결과 |
| `docs/results/haproxy-http3-negative-control-rerun-20260630.md` | HAProxy HTTP/3 fresh negative-control rerun 결과 |
| `docs/results/nginx-haproxy-quic-cm-boundary-20260630.md` | nginx server passive migration source evidence와 HAProxy proxy negative-control boundary |
| `docs/results/mvfst-cm-source-audit-20260630.md` | mvfst path manager/client/server migration source-test audit |
| `docs/results/chaptered-research-synthesis-20260629.md` | 전체 챕터 흐름 |
| `docs/results/controlled-public-full-downlink-iphone-usb-handover-20260629.md` | Chapter 8 full-response downlink public handover result |
| `docs/results/controlled-public-range-retry-iphone-usb-handover-20260629.md` | Chapter 9 byte-range retry public handover result |
| `docs/results/iphone-usb-upload-retry-pilot-20260626.md` | Chapter 10 upload retry public handover result |
| `docs/results/streaming-workload-case-analysis-20260629.md` | Chapter 11 streaming workload synthesis |
| `docs/results/chrome-h3-rebinding-buffered-media-control-20260629.md` | Chapter 11 buffered media local control |
| `docs/results/literature-claim-positioning-20260629.md` | Chapter 12 literature claim positioning |
| `docs/results/non-iphone-research-gap-plan-20260630.md` | iPhone 없이 이어갈 후속 연구 공백 보강 계획 |
