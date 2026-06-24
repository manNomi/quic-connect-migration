# QUIC / HTTP/3 Connection Migration Research

이 저장소는 QUIC/HTTP/3 Connection Migration이 실제 웹 작업 연속성으로 이어지는 조건을 조사한 연구 기록이다.

핵심 질문은 단순히 "Connection Migration이 되는가?"가 아니다.

> QUIC Connection Migration은 구현체 수준에서는 어느 정도 존재하지만, 실제 HTTP/3 웹 작업 연속성으로 배포되려면 어떤 조건이 추가로 필요한가?

## 핵심 결론

현재까지의 실험 결과를 중립적으로 정리하면 다음과 같다.

1. QUIC Connection Migration은 여러 구현체에 실제 primitive와 test evidence가 있다.
2. quic-go direct-origin 환경에서는 controlled active migration이 성공했다.
3. HAProxy는 HTTP/3 baseline 요청은 처리했지만 active migration path validation은 실패했다.
4. AWS NLB는 QUIC-LB plaintext CID format과 registered `QuicServerId`가 맞을 때 migration 후 same-target continuity를 유지했다.
5. CID format이 틀리거나 Server ID가 mismatch되면 target health가 정상이어도 QUIC application payload가 실패했다.
6. controlled quic-go + AWS NLB `TCP_QUIC :443` 환경에서는 HTTP/3 post-migration request continuity와 1MiB mid-flight upload/download continuity가 관찰됐다.
7. Chrome 149 headless baseline에서 local quic-go H3 origin으로 단일 request, page+subresource sequence, polling workload가 HTTP/3로 도달하는 것을 확인했다.
8. Chrome slow subresource 중 inactive interface toggle은 workload를 깨지 않았지만 실제 QUIC path migration을 만들지는 않았다.
9. Chrome slow workload는 local Wi-Fi IP origin에서도 HTTP/3로 성립했지만, inactive interface toggle은 여전히 migration evidence를 만들지 못했다.
10. Chrome natural Alt-Svc control에서는 local self-signed 또는 mkcert origin이 h3를 광고해도 강제 QUIC 없이 실제 HTTP/3 application request가 관찰되지는 않았다. HTML diagnostic에서는 QUIC/H3 후보 연결이 열렸지만 인증서 검증 실패 또는 broken alternative service로 끝났다.
11. 초기 public WebPKI control에서 Cloudflare/Google/YouTube lightweight endpoint는 H3 discovery 또는 QUIC session 단서를 보였지만 application H3를 확정하지 못했다. 확장 실험에서는 `blog.cloudflare.com`, Bing, Facebook, Instagram에서 Chrome natural H3 application job이 관찰됐다.
12. public endpoint 확장 survey에서는 20개 중 12개가 H3 Alt-Svc를 광고했고 7개가 2xx workload 후보였다. 다만 제3자 endpoint는 server qlog, workload, active path-change, backend routing을 통제할 수 없으므로 browser CM target selection과 workload continuity는 controlled public origin에서 검증해야 한다.
13. controlled public WebPKI origin 실험을 위한 readiness checker와 server/browser wrapper를 추가했다. 이 단계는 아직 handover 결과가 아니라 다음 browser CM 실험의 통제 조건이다.
14. handover readiness scanner 기준 현재 장비는 Chrome/ADB는 준비됐지만 Android device, active secondary network, AWS identity가 부족하다.
15. local direct-origin HTTP/3 post-migration/mid-flight 반복실험을 새 `RUN_ID`로 재실행했고, request continuity와 1MiB upload/download continuity가 다시 PASS였다.
16. controlled public application H3 baseline gate와 network-change harness를 추가해, 실제 active path change 실험의 판정 기준을 server/qlog/NetLog 조합으로 고정했다.
17. Chrome forced-QUIC local H3에서 downlink-dominant streaming workload와 optional heartbeat variant가 HTTP/3로 정상 관찰되는 것을 확인했다.
18. Chrome CDP real-time runner 기준, heartbeat fetch는 network-change가 없어도 별도 QUIC session/source tuple을 만들 수 있었다. 따라서 tuple 변화 단독으로는 Connection Migration evidence가 아니다.
19. inactive interface toggle 대조군에서는 command exit은 0이었지만 client path snapshot은 `no_client_path_change_observed`였고 qlog path validation도 없었다.
20. Safari controlled public network-change harness를 추가하고, Chrome NetLog가 없는 Safari 결과는 `PASS_FEASIBILITY` 수준으로 별도 분류하도록 했다.
21. Android Chrome controlled public network-change harness를 추가하고, ADB 기반 navigation과 Android raw network snapshot 수집 경로를 준비했다.
22. 최종 browser handover protocol을 만족하기 위한 10개 실행 계획과 명령 template를 생성했다.
23. 최종 handover classifier summary를 `data/experiment-results.csv` row 초안으로 변환하는 도구와 regression test를 추가했다.
24. 단일 final handover artifact가 CSV 등록 가능하고 최종 protocol requirement에 실제로 카운트되는지 검증하는 validator를 추가했다.
25. 검증된 final handover row만 dry-run/apply 방식으로 `data/experiment-results.csv`에 추가하는 append 도구를 추가했다.
26. 현재 CSV 상태에서 다음에 실행해야 할 final handover trial과 등록 명령을 선택하는 next-trial selector를 추가했다.
27. 선택된 다음 trial 하나에 필요한 readiness gate를 별도로 점검하는 per-trial readiness checker를 추가했다.
28. controlled public origin config가 baseline/active/Android 단계별로 준비됐는지 public-safe하게 검사하는 config checker를 추가했다.
29. heavy browser handover capture 전 디스크 여유 공간을 계산하는 artifact cleanup dry-run planner를 추가했다.
30. 최종 handover trial을 시작하기 전 필요한 config, storage, next-trial, active path, Android action을 우선순위별 checklist로 생성한다.
31. next-trial readiness는 local client check와 public-origin-host TLS file check를 구분해 remote TLS path를 잘못 blocker로 보지 않게 했다.
32. controlled-public network-change classifier는 client active path change evidence가 없으면 server tuple/qlog 단서만으로 `possible_connection_migration`를 주지 않도록 보수화했다.
33. Android Chrome wrapper가 ADB route/address/connectivity snapshot을 `client-path-change-summary.json`으로 요약해 P1 feasibility도 client active path gate를 통과할 수 있게 했다.
34. 다음 final handover trial의 readiness, 실행 명령, expected artifacts, 등록 명령을 한 장으로 묶는 trial packet 생성기를 추가했다.
35. trial 실행 후 summary뿐 아니라 qlog/NetLog/path snapshot 등 expected raw artifact bundle이 모두 있는지 확인하는 gate를 추가했다.
36. final handover append 도구가 `--require-artifact-bundle` 옵션으로 summary-only 결과의 CSV 등록을 차단하게 했다.
37. 디스크 정리 전 raw artifact가 `data/experiment-results.csv`나 planned final trial에 연결되는지 확인하는 cleanup safety audit를 추가했다.
38. controlled-public private config를 공개 값 없이 채울 수 있도록 stage/owner/privacy/next action worksheet를 추가했다.
39. controlled-public wrapper들이 직접 실행되더라도 기본 5GiB disk guard를 통과해야 heavy NetLog/qlog artifact 생성을 시작하게 했다.
40. 최종 handover 본 실험을 재개하기 전 사용자가 제공해야 할 외부 입력을 public-safe handoff packet으로 생성하게 했다.
41. 아직 Chrome/Android 실제 Wi-Fi/LTE handover나 CloudFront origin end-to-end continuity를 검증한 것은 아니다.

따라서 현재 결론은 "항상 된다"도 "안 된다"도 아니다.

> 특정 조건에서는 된다. 하지만 실제 웹/모바일 배포에서 그 조건이 충족되는지는 deployment path, browser/client policy, application recovery를 추가로 검증해야 한다.

## 저장소 구조

```text
.
├── README.md
├── data/
│   ├── experiment-results.csv
│   ├── browser-cm-observability-20260624.json
│   ├── controlled-public-experiment-readiness-20260624.json
│   ├── cm-operational-friction-rubric.csv
│   ├── cm-operational-friction-matrix-20260624.csv
│   ├── evidence-chain-rubric.csv
│   ├── final-browser-handover-required-trials.csv
│   ├── implementation-survey.csv
│   ├── handover-readiness-20260624.json
│   ├── literature-review-tracker.csv
│   ├── public-alt-svc-survey-20260624.csv
│   ├── public-alt-svc-expanded-survey-20260624.csv
│   ├── public-origin-readiness-survey-20260624.csv
│   ├── public-origin-readiness-expanded-survey-20260624.csv
│   ├── final-protocol-readiness-matrix-20260624.csv
│   ├── final-trial-acceptance-scorecard-20260624.csv
│   ├── paper-evidence-gap-register-20260624.csv
│   ├── research-status-dashboard-20260624.json
│   ├── reproducibility-manifest-20260624.json
│   └── quiche-path-event-timeline.csv
├── docs/
│   ├── experiment-report-ko.md
│   ├── code-architecture-ko.md
│   └── results/
│       └── 개별 실험 결과 문서
├── harness/
│   ├── config/*.example
│   ├── manifests/experiment-matrix.csv
│   └── scripts/
├── paper/
│   ├── detailed-paper-plan-ko.md
│   └── detailed-paper-plan-en.md
├── tools/
│   ├── scan_implementation_evidence.py
│   ├── check_public_origin_readiness.py
│   ├── check_handover_readiness.py
│   ├── check_controlled_public_experiment_readiness.py
│   ├── check_controlled_public_config.py
│   ├── check_final_browser_handover_readiness.py
│   ├── check_next_final_handover_trial_readiness.py
│   ├── check_aws_identity_public_safe.py
│   ├── build_controlled_public_origin_deploy_packet.py
│   ├── build_final_protocol_readiness_matrix.py
│   ├── build_final_trial_acceptance_scorecard.py
│   ├── build_cm_operational_friction_matrix.py
│   ├── build_paper_evidence_gap_register.py
│   ├── build_research_status_dashboard.py
│   ├── build_reproducibility_manifest.py
│   ├── plan_final_browser_handover_runs.py
│   ├── check_browser_cm_observability.py
│   ├── classify_controlled_public_h3_baseline.py
│   ├── classify_controlled_public_h3_network_change.py
│   ├── capture_network_path_snapshot.py
│   ├── compare_network_path_snapshots.py
│   ├── compare_android_path_snapshots.py
│   ├── audit_final_browser_handover_trials.py
│   ├── draft_final_handover_result_row.py
│   ├── validate_final_handover_trial_artifact.py
│   ├── append_final_handover_result_row.py
│   ├── select_next_final_handover_trial.py
│   ├── build_final_handover_operator_checklist.py
│   ├── build_final_handover_external_inputs.py
│   ├── build_final_handover_trial_packet.py
│   ├── check_final_handover_trial_artifact_bundle.py
│   ├── audit_research_bundle.py
│   ├── audit_artifact_cleanup_safety.py
│   ├── build_controlled_public_config_worksheet.py
│   ├── build_paper_tables.py
│   ├── report_artifact_storage.py
│   ├── plan_artifact_cleanup.py
│   ├── run_chrome_cdp_navigation.js
│   ├── run_android_chrome_navigation.py
│   ├── run_safari_webdriver_navigation.py
│   ├── test_final_browser_handover_trial_audit.py
│   ├── test_draft_final_handover_result_row.py
│   ├── test_validate_final_handover_trial_artifact.py
│   ├── test_append_final_handover_result_row.py
│   ├── test_artifact_disk_guard.py
│   ├── test_audit_artifact_cleanup_safety.py
│   ├── test_select_next_final_handover_trial.py
│   ├── test_check_next_final_handover_trial_readiness.py
│   ├── test_build_final_handover_operator_checklist.py
│   ├── test_build_final_handover_external_inputs.py
│   ├── test_build_final_handover_trial_packet.py
│   ├── test_check_final_handover_trial_artifact_bundle.py
│   ├── test_build_controlled_public_config_worksheet.py
│   ├── test_classify_controlled_public_h3_network_change.py
│   ├── test_compare_android_path_snapshots.py
│   ├── test_check_controlled_public_config.py
│   ├── verify_research_bundle.py
│   ├── scan_public_alt_svc.py
│   ├── scan_public_origin_readiness.py
│   ├── scan_qlog_events.py
│   ├── summarize_experiment_results.py
│   └── validate_publication_bundle.py
└── repro/
    └── quic-go-min-repro/
```

## 주요 문서

- [실험 결과 상세 보고서](docs/experiment-report-ko.md)
- [코드/하네스 구조 설명](docs/code-architecture-ko.md)
- [재현 가이드](docs/reproducibility-guide-ko.md)
- [스캐너와 도구 설명](docs/scanners-and-tools-ko.md)
- [Controlled public application H3 evidence gate](docs/results/controlled-public-application-h3-gate-20260624.md)
- [Controlled public config check](docs/results/controlled-public-config-check-20260624.md)
- [Controlled public config worksheet](docs/results/controlled-public-config-worksheet-20260624.md)
- [Controlled public origin deploy packet](docs/results/controlled-public-origin-deploy-packet-20260624.md)
- [Controlled public Chrome H3 network-change harness](docs/results/controlled-public-network-change-harness-20260624.md)
- [Controlled public experiment readiness](docs/results/controlled-public-experiment-readiness-20260624.md)
- [Controlled public origin operations runbook](docs/results/controlled-public-origin-operations-runbook-20260624.md)
- [Browser CM observability readiness](docs/results/browser-cm-observability-readiness-20260624.md)
- [Safari controlled public H3 baseline harness](docs/results/safari-controlled-public-baseline-harness-20260624.md)
- [Safari controlled public H3 network-change harness](docs/results/safari-controlled-public-network-change-harness-20260624.md)
- [Android Chrome controlled public H3 network-change harness](docs/results/android-chrome-controlled-public-network-change-harness-20260624.md)
- [Final browser handover experiment protocol](docs/results/final-browser-handover-experiment-protocol-20260624.md)
- [Final browser handover readiness](docs/results/final-browser-handover-readiness-20260624.md)
- [Final browser handover run plan](docs/results/final-browser-handover-run-plan-20260624.md)
- [Final browser handover result registration guide](docs/results/final-browser-handover-result-registration-guide-20260624.md)
- [Final browser handover trial audit](docs/results/final-browser-handover-trial-audit-20260624.md)
- [Final handover trial artifact validator](docs/results/final-handover-trial-artifact-validator-20260624.md)
- [Final handover next trial](docs/results/final-handover-next-trial-20260624.md)
- [Final handover next trial readiness](docs/results/final-handover-next-trial-readiness-20260624.md)
- [Final handover operator checklist](docs/results/final-handover-operator-checklist-20260624.md)
- [Final handover external inputs handoff](docs/results/final-handover-external-inputs-20260624.md)
- [Final handover trial packet](docs/results/final-handover-trial-packet-20260624.md)
- [Final handover trial artifact bundle check](docs/results/final-handover-trial-artifact-bundle-check-20260624.md)
- [Final protocol readiness matrix](docs/results/final-protocol-readiness-matrix-20260624.md)
- [Final trial acceptance scorecard](docs/results/final-trial-acceptance-scorecard-20260624.md)
- [Research status dashboard](docs/results/research-status-dashboard-20260624.md)
- [CM operational friction matrix](docs/results/cm-operational-friction-matrix-20260624.md)
- [Active path-change operator cookbook](docs/results/active-path-change-operator-cookbook-20260624.md)
- [CI safe verification plan](docs/results/ci-safe-verification-plan-20260624.md)
- [CI safe verification result](docs/results/ci-safe-verification-result-20260624.md)
- [Paper evidence gap register](docs/results/paper-evidence-gap-register-20260624.md)
- [Reproducibility manifest](docs/results/reproducibility-manifest-20260624.md)
- [Browser CM literature refresh](docs/results/literature-refresh-browser-cm-20260624.md)
- [Client policy literature refresh](docs/results/literature-refresh-client-policy-20260624.md)
- [Public H3 and CM evidence boundary literature refresh](docs/results/literature-refresh-public-h3-and-cm-evidence-20260624.md)
- [Latest QUIC CM evidence boundary refresh](docs/results/literature-refresh-latest-cm-boundary-20260624.md)
- [Public H3 expanded browser candidate results](docs/results/public-h3-expanded-browser-candidate-results-20260624.md)
- [Chrome H3 downlink-dominant workload](docs/results/chrome-h3-downlink-dominant-workload-results-20260624.md)
- [Chrome H3 local UDP rebinding proxy results](docs/results/chrome-h3-rebinding-proxy-results-20260624.md)
- [quic-go local HTTP/3 migration replication results](docs/results/quic-go-local-h3-replication-results-20260624.md)
- [Evidence chain and gap synthesis](docs/results/evidence-chain-and-gap-synthesis-20260624.md)
- [Paper-ready generated tables](docs/results/paper-tables-20260624.md)
- [Research completion audit](docs/results/research-completion-audit-20260624.md)
- [Generated research bundle audit](docs/results/research-bundle-audit-20260624.md)
- [Research verification report](docs/results/research-verification-report-20260624.md)
- [AWS identity public-safe check](docs/results/aws-identity-public-safe-check-20260624.md)
- [Local artifact storage audit](docs/results/artifact-storage-report-20260624.md)
- [Local artifact cleanup plan](docs/results/artifact-cleanup-plan-20260624.md)
- [Local artifact cleanup safety audit](docs/results/artifact-cleanup-safety-audit-20260624.md)
- [Local artifact cleanup dry-run](docs/results/artifact-cleanup-dry-run-20260624.md)
- [논문 상세안 한국어](paper/detailed-paper-plan-ko.md)
- [논문 상세안 영어](paper/detailed-paper-plan-en.md)
- [논문 Results 섹션 한국어](paper/results-section-ko.md)
- [논문 Results 섹션 영어](paper/results-section-en.md)
- [실험 결과 CSV](data/experiment-results.csv)
- [최종 browser handover 필수 trial CSV](data/final-browser-handover-required-trials.csv)
- [구현체 조사 CSV](data/implementation-survey.csv)

## 재현 코드

핵심 재현 코드는 [repro/quic-go-min-repro](repro/quic-go-min-repro)에 있다.

주요 구성:

- `cmd/client`: QUIC transport stream migration client
- `cmd/server`: QUIC transport stream migration server
- `cmd/h3client`: HTTP/3 workload migration client
- `cmd/h3server`: HTTP/3 workload migration server
- `internal/common`: payload, TLS, logging, AWS NLB CID helper
- `scripts`: local/EC2/AWS 실행 wrapper

가장 빠른 로컬 검증:

```bash
python3 tools/validate_publication_bundle.py
python3 tools/verify_research_bundle.py --output docs/results/research-verification-report-20260624.md
python3 tools/summarize_experiment_results.py
cd repro/quic-go-min-repro
go test ./...
RUN_ID=local-h3-workload-check ./scripts/run-local-h3-workload.sh
RUN_ID=local-h3-midflight-check ./scripts/run-local-h3-midflight.sh
```

AWS까지 포함한 재현 절차는 [재현 가이드](docs/reproducibility-guide-ko.md)에 정리했다.

## 주의

이 저장소에는 공개 가능한 source, markdown, CSV만 포함한다.

제외한 항목:

- AWS credential
- local `harness/config/aws.env`
- keylog/qlog raw artifact
- pcap
- EC2 SSH key
- 대용량 실행 artifact

개별 실험의 자세한 artifact 위치와 결과 값은 [docs/experiment-report-ko.md](docs/experiment-report-ko.md)와 [data/experiment-results.csv](data/experiment-results.csv)에 정리되어 있다.
