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
41. controlled public Chrome H3 baseline이 active network-change trial을 열 수 있는지, PASS summary와 raw artifact bundle complete를 함께 확인하는 unlock gate를 추가했다.
42. Chrome local UDP rebinding proxy에서 streaming browser upload를 3회 반복했고, upload는 성공했지만 request-level remote tuple은 그대로여서 qlog/NetLog 없이 request log만으로 path change를 판단하면 안 된다는 근거를 추가했다.
43. Chrome forced-H3 local old-path-drop stress matrix에서 1MiB/4MiB downlink/upload 5회가 모두 완료됐고, A-side server packet 105개가 drop된 상태에서도 qlog/Chrome NetLog path validation이 관찰됐다.
44. return-path drop control에서 B-only server packet drop은 2/2 PASS였지만 A+B return path loss는 2/2 FAIL이어서, transport evidence와 application completion을 분리해야 함을 확인했다.
45. transient return-path outage sweep에서는 A+B return path를 250ms/1500ms/3000ms/4000ms 막은 1MiB downlink/upload가 8/8 PASS였지만, 5000ms/6000ms/9000ms는 6/6 FAIL이었다. 이 local workload의 outage-tolerance boundary는 4초와 5초 사이로 좁혀졌다.
46. transient boundary repetition에서는 4000ms와 4500ms가 각각 6/6 PASS였고, 5000ms는 downlink 3/3 PASS와 upload 0/3 PASS로 갈려 outage tolerance가 workload-sensitive transition zone임을 확인했다.
47. downlink-only fine boundary에서는 5000ms와 5500ms가 각각 2/3 PASS로 혼재했고, 6000ms는 0/3 PASS였다. downlink 역시 단조 threshold가 아니라 packet/timer alignment에 민감한 transition zone을 보였다.
48. upload-only fine boundary에서는 4600ms upload가 3/3 PASS, 4750ms가 1/3 PASS, 4900ms와 5000ms가 6/6 FAIL이어서 upload 안정 완료 구간과 실패 구간을 더 좁혔다.
49. 같은 4900ms/5000ms upload 실패 구간에서 application-level upload retry를 1회 허용하면 6/6 PASS로 작업 완료가 회복됐다. 다만 모든 row가 Chrome target QUIC session 2개로 분류되어, 이는 single-session CM 성공이 아니라 retry/reconnect 기반 작업 회복 control로 해석해야 한다.
50. 더 긴 6000ms/9000ms upload outage에서도 1회 retry는 6/6 PASS로 작업 완료를 회복했다. 그러나 Chrome target QUIC session count가 2-3개로 관찰되어, outage가 길수록 retry recovery와 browser session continuity의 차이를 더 명확히 분리해야 한다.
51. 12000ms/15000ms retry stress boundary에서는 12000ms가 3/3 PASS, 15000ms가 0/3 PASS였다. 즉 application-level retry도 무제한 보장이 아니며, 이 local upload workload의 1회 retry recovery boundary는 12초와 15초 사이로 관찰됐다.
52. 같은 15000ms outage에서 retry를 2회로 늘리면 3/3 PASS로 회복됐지만 DOM complete timing은 약 24.5초였고 Chrome target QUIC session count는 4개였다. 이는 사용자 작업 완료 회복의 근거이지 single-session browser CM 성공 근거가 아니다.
53. 18000ms/21000ms retry2 stress boundary에서는 18000ms가 3/3 PASS, 21000ms가 3/3 FAIL이었다. 2회 retry도 local recovery boundary가 18초와 21초 사이에서 다시 깨지며, 실패 row에도 qlog path evidence와 Chrome session evidence가 남았다.
54. Application recovery tradeoff synthesis는 no-retry 안정 구간 4600ms, 1회 retry 안정 구간 12000ms, 2회 retry 안정 구간 18000ms로 boundary가 오른쪽으로 이동하지만 completion latency와 Chrome QUIC session churn도 함께 증가함을 보여준다.
55. Workload transition-zone synthesis는 downlink가 5.0-5.5초 혼재 후 6초 반복 실패, upload가 4.75초 혼재 후 4.9초 반복 실패로 갈려 workload direction 자체가 continuity boundary를 바꾼다는 점을 요약한다.
56. Downlink 1회 retry recovery control에서는 6000ms/9000ms outage가 6/6 PASS였지만, 3개 row는 retry 없이 단일 session retransmission으로, 3개 row는 retry 후 multiple session으로 완료되어 recovery mechanism을 분리해 보고해야 함을 확인했다.
57. 같은 6000ms/9000ms에서 retry 없는 wait-only control은 6/6 FAIL이었으므로, downlink recovery PASS는 단순히 긴 hold/grace 때문이라고 볼 수 없고 application-level recovery/timer behavior를 독립 축으로 측정해야 한다.
58. Polling/dashboard형 반복 fetch workload는 250ms/1500ms/3000ms outage에서 9/9 PASS였지만 모든 row가 Chrome target QUIC session 2개, qlog PATH_CHALLENGE/PATH_RESPONSE 0/0으로 관찰되어, 작업 완료와 single-session browser CM을 분리해야 함을 추가로 확인했다.
59. Polling/dashboard long-boundary에서는 4000ms가 1/3 PASS로 혼재했고 6000ms/9000ms는 0/6 PASS여서, 이 local polling workload의 transition zone은 3초 all-pass 이후 4초부터 시작되고 6초부터 반복 실패하는 것으로 관찰됐다.
60. 아직 Chrome/Android 실제 Wi-Fi/LTE handover나 CloudFront origin end-to-end continuity를 검증한 것은 아니다.
61. Paper claim support matrix는 현재 결과로 쓸 수 있는 논문 문장과 쓰면 안 되는 과장 문장을 claim별로 분리한다. 결론적으로 controlled implementation/deployment claim은 가능하지만, browser/mobile active handover 성공 claim은 아직 pending이다.
62. Replication sufficiency audit는 local 반복 실험의 Wilson 95% 구간을 계산해, n=3/6/9 결과를 reliability probability나 guarantee처럼 쓰면 안 되고 transition-zone 또는 directional local evidence로 써야 함을 정리한다.
63. Replication run plan은 추가 local 반복 실험을 전부 무작정 늘리는 대신 final public/browser handover를 P0로 두고, local transition-zone row와 boundary anchor row를 L1/L2로 나눠 실행 우선순위를 정한다.
64. P0 unblock status는 final protocol readiness matrix에서 현재 P0를 막는 gate를 압축해, next trial을 열기 위한 `needed-now` gate와 baseline 이후 gate를 분리한다.
65. P0 baseline execution packet은 private config 작성, preflight, origin server, Chrome client, artifact validation, CSV append 순서를 stage별 stop condition과 함께 고정한다.
66. P0 baseline preflight check는 `--require-go` guard로, server/client capture를 시작해도 되는 상태인지 판정하고 현재처럼 config gate가 남아 있으면 실패하도록 한다.
67. P0 baseline preflight control report는 synthetic fixture 3개로 guard가 missing config/stale needed-now에서는 닫히고, modeled-ready baseline에서만 열리는지 검증한다.
68. P0 baseline execution packet의 stage 1 preflight 명령은 `harness/scripts/final-p0-baseline-preflight.sh` wrapper를 사용해 ignored artifact dir에 readiness output을 쓰고, 내부 `--require-go` guard 통과 전 stage 2 capture를 열지 않는다.
69. Final capture storage budget은 현재 여유공간으로 next planned execution은 가능하지만, 2GiB reserve 기준 remaining final queue 전체에는 추가 cleanup/provisioning이 필요함을 분리한다.
70. Final handover registration wrapper는 artifact bundle check, validation, append dry-run/apply, audit를 묶고, missing artifact 상태에서는 CSV append 없이 fail-closed한다.
71. Polling/dashboard 4000ms local replication 3회를 추가 실행했고 모두 FAIL이었다. 기존 1/3 PASS와 합산하면 4000ms는 1/6 PASS, 5/6 FAIL인 failure-heavy transition zone으로 정리된다.
72. Upload 4750ms local replication 3회를 추가 실행했고 2/3 PASS였다. 기존 1/3 PASS와 합산하면 4750ms upload는 3/6 PASS, 3/6 FAIL인 중심 transition zone으로 유지된다.
73. Downlink 5000/5500ms local replication 6회를 추가 실행했고 5000ms는 3/3 PASS, 5500ms는 2/3 PASS였다. 기존 결과와 합산하면 5000ms는 5/6 PASS, 5500ms는 4/6 PASS로 성공 편향 transition zone이다.
74. AWS NLB + s2n-quic 전용 live runner를 추가했다. 새 s2n live server/client는 local echo smoke를 통과했고, 현재 AWS credential은 `invalid_client_token`이라 runner는 resource 생성 전에 `validation=blocked`로 닫힌다.
75. s2n-quic active migration API audit를 추가했다. focused `connection_migration` test는 `10 passed`였지만, 현재 public app API에서 quic-go식 `AddPath -> Probe -> Switch` trigger는 확인되지 않아 AWS NLB+s2n active path-change는 forwarding echo 이후 별도 phase로 남긴다.
76. mvfst migration test readiness runner를 추가했다. latest remote HEAD 기준 focused migration/path test case 106개와 BUCK target 3개를 확인했지만, 현재 로컬은 disk 부족, `buck2` 없음, CMake direct target 미노출로 build/test 실행은 `validation=blocked`로 남긴다.
77. nginx `quic_bpf` Linux runner를 추가했다. Linux/root/`/sys/fs/bpf` 조건이 열리면 `quic_bpf on;`과 `listen ... reuseport`로 기존 active migration workload를 실행하고, 현재 macOS 로컬에서는 `validation=blocked`, `blocked_reason=linux_required`로 닫힌다.
78. Chrome desktop non-iPhone media local refresh를 추가했다. fresh local forced-H3 media run은 `PASS`, `nat_rebinding_possible_session_continuity`, Chrome target QUIC session `1`, server remote tuple `2`, qlog/NetLog PATH_CHALLENGE/PATH_RESPONSE `1/1`로 관찰됐지만, public Wi-Fi/LTE handover claim은 아니다.
79. Chrome desktop non-iPhone range local refresh를 추가했다. 1MiB byte-range workload 2회가 retry 없이 2/2 PASS였고, 두 row 모두 Chrome target QUIC session `1`, server remote tuple `2`, qlog PATH_CHALLENGE/PATH_RESPONSE `1/1`로 관찰됐다. 이 역시 local UDP rebinding control이지 public handover claim은 아니다.
80. Chrome desktop non-iPhone upload local refresh를 추가했다. 128KiB upload workload는 retry 없이 PASS였고 Chrome target QUIC session `1`, qlog/NetLog PATH_CHALLENGE/PATH_RESPONSE `1/1`, proxy packet A/B `29/110`이 관찰됐다. 다만 server request-level remote tuple은 `1`개라서 upload에서는 request log만으로 path change를 판단하면 안 된다.
81. Safari WebDriver readiness를 binary readiness와 session readiness로 분리했다. 현재 장비는 Safari `26.2`, `safaridriver exit=0`, packet capture tooling ready이지만 실제 WebDriver session creation은 Safari Settings의 `Allow remote automation` 미활성화로 실패하므로 Safari controlled-public trial은 아직 실행할 수 없다.
82. user-provided public origin readiness를 redacted로 확인했다. HTTPS reachability는 있지만 현재 `HTTP/2 200`이고 `h3 Alt-Svc=false`라서, 그대로는 controlled-public Chrome H3/CM 실험 타깃이 아니다.
83. non-iPhone next research decision brief를 추가했다. 현재 구현체 성숙도 조사를 더 늘리기보다 deployment/browser bridge를 열어야 하며, 1순위는 AWS credential refresh 후 AWS NLB+s2n live forwarding echo, 2순위는 controlled public Chrome media/range/upload trial, Safari는 `PASS_FEASIBILITY` 보강으로 정리된다.
84. 2026-07-01 non-iPhone gate rerun을 추가했다. AWS는 여전히 `invalid_client_token`, Safari WebDriver session은 `Allow remote automation` 미활성화, user-provided public origin은 `h3 Alt-Svc=false`라서 다음 실험 시작 전 외부 gate가 필요하다.
85. Chrome desktop non-iPhone music-like local refresh를 추가했다. 6000ms local outage에서 retry0은 0/1 FAIL, retry1은 1/1 PASS였지만 retry1도 Chrome target QUIC session `3`개로 관찰되어, 음악형 streaming completion은 single-session CM이 아니라 application retry/reconnect 회복으로 해석해야 한다.
86. tracked controlled-public Chrome validation 18개를 bridge synthesis로 묶었다. no-change H3 baseline은 6/6 확인됐지만 active network-change 12개 중 single-session CM 성공으로 볼 수 있는 row는 0개라서, 현재 public-browser evidence는 성공 결론이 아니라 deployment/browser bridge gap과 negative-control 근거로 해석해야 한다.
87. Chrome desktop non-iPhone buffered-media local refresh를 추가했다. 6000ms local outage에서 low/high buffer row 모두 playback complete였지만 low buffer는 rebuffer `6`, high buffer는 rebuffer `1`, 두 row 모두 Chrome target QUIC session `3`개로 관찰되어 동영상형 completion은 QoE 비용과 session churn을 함께 봐야 함을 보강했다.
88. non-iPhone workload continuity/QoE synthesis를 추가했다. 기존 local Chrome/quic-go CSV 8개에서 32개 row를 정규화했고, range/download와 upload는 single-session local path-validation evidence가 상대적으로 강한 반면 buffered video와 music-like segment는 completion을 QoE 비용, retry/reconnect, Chrome session churn과 분리해야 함을 확인했다.
89. non-iPhone public workload trial packet을 추가했다. public H3 origin과 desktop active path-change command가 준비되면 baseline, range no-change, range active 3회, upload no-change, upload active 3회, buffered low/high active, music-like retry0/retry1 active 순서로 실행하며 strong CM acceptance는 task completion, client path change, target tuple change, qlog PATH_CHALLENGE/PATH_RESPONSE, Chrome target QUIC session `1`개를 모두 요구하도록 고정했다.
90. controlled public origin workload deploy packet을 추가했다. WebPKI TLS, TCP/UDP 443, Alt-Svc `h3`, quic-go H3 server baseline, non-iPhone public workload packet 실행 순서를 하나로 연결해 public origin gate가 열리면 range/upload/media trial로 바로 넘어갈 수 있게 했다.
91. non-iPhone desktop path-change readiness를 추가했다. 현재 호스트는 active IPv4 interface가 `en0` 하나뿐이라 iPhone을 제외한 desktop active secondary path가 없고, iPhone latent failover와 Android 후보는 desktop public workload gate에서 제외했다. 따라서 public workload active row를 세기 전 Ethernet/USB LAN/Thunderbolt Ethernet 같은 non-iPhone secondary path를 먼저 열어야 한다.

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
│   ├── p0-unblock-status-20260624.csv
│   ├── p0-baseline-execution-packet-20260624.csv
│   ├── p0-baseline-preflight-check-20260624.csv
│   ├── p0-baseline-preflight-control-report-20260624.csv
│   ├── final-capture-storage-budget-20260624.csv
│   ├── paper-evidence-gap-register-20260624.csv
│   ├── paper-claim-support-matrix-20260624.csv
│   ├── replication-sufficiency-audit-20260624.csv
│   ├── replication-run-plan-20260624.csv
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
│   ├── build_p0_unblock_status.py
│   ├── build_p0_baseline_execution_packet.py
│   ├── check_p0_baseline_preflight.py
│   ├── build_p0_preflight_control_report.py
│   ├── build_final_capture_storage_budget.py
│   ├── build_cm_operational_friction_matrix.py
│   ├── build_paper_evidence_gap_register.py
│   ├── build_paper_claim_support_matrix.py
│   ├── build_replication_sufficiency_audit.py
│   ├── build_replication_run_plan.py
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
- [Controlled public baseline unlock check](docs/results/controlled-public-baseline-unlock-check-20260624.md)
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
- [P0 unblock status](docs/results/p0-unblock-status-20260624.md)
- [P0 baseline execution packet](docs/results/p0-baseline-execution-packet-20260624.md)
- [P0 baseline preflight check](docs/results/p0-baseline-preflight-check-20260624.md)
- [P0 baseline preflight control report](docs/results/p0-baseline-preflight-control-report-20260624.md)
- [Final capture storage budget](docs/results/final-capture-storage-budget-20260624.md)
- [Research status dashboard](docs/results/research-status-dashboard-20260624.md)
- [CM operational friction matrix](docs/results/cm-operational-friction-matrix-20260624.md)
- [Browser CM observability matrix](docs/results/browser-cm-observability-matrix-20260624.md)
- [Active path-change operator cookbook](docs/results/active-path-change-operator-cookbook-20260624.md)
- [CI safe verification plan](docs/results/ci-safe-verification-plan-20260624.md)
- [CI safe verification result](docs/results/ci-safe-verification-result-20260624.md)
- [Paper evidence gap register](docs/results/paper-evidence-gap-register-20260624.md)
- [Paper claim support matrix](docs/results/paper-claim-support-matrix-20260624.md)
- [Replication sufficiency audit](docs/results/replication-sufficiency-audit-20260624.md)
- [Replication run plan](docs/results/replication-run-plan-20260624.md)
- [Reproducibility manifest](docs/results/reproducibility-manifest-20260624.md)
- [Browser CM literature refresh](docs/results/literature-refresh-browser-cm-20260624.md)
- [Client policy literature refresh](docs/results/literature-refresh-client-policy-20260624.md)
- [Public H3 and CM evidence boundary literature refresh](docs/results/literature-refresh-public-h3-and-cm-evidence-20260624.md)
- [Latest QUIC CM evidence boundary refresh](docs/results/literature-refresh-latest-cm-boundary-20260624.md)
- [Public H3 expanded browser candidate results](docs/results/public-h3-expanded-browser-candidate-results-20260624.md)
- [Chrome H3 downlink-dominant workload](docs/results/chrome-h3-downlink-dominant-workload-results-20260624.md)
- [Chrome H3 local UDP rebinding proxy results](docs/results/chrome-h3-rebinding-proxy-results-20260624.md)
- [Chrome H3 local UDP rebinding repetition summary](docs/results/chrome-h3-rebinding-repetition-summary-20260624.md)
- [Chrome H3 local UDP rebinding upload summary](docs/results/chrome-h3-rebinding-upload-summary-20260624.md)
- [Chrome desktop non-iPhone upload local refresh](docs/results/chrome-desktop-noniphone-upload-local-refresh-20260630.md)
- [Chrome desktop non-iPhone music-like local refresh](docs/results/chrome-desktop-noniphone-musiclike-local-refresh-20260701.md)
- [Chrome desktop non-iPhone buffered media local refresh](docs/results/chrome-desktop-noniphone-buffered-media-local-refresh-20260701.md)
- [Non-iPhone workload continuity and QoE synthesis](docs/results/noniphone-workload-qoe-continuity-synthesis-20260701.md)
- [Non-iPhone public workload trial packet](docs/results/noniphone-public-workload-trial-packet-20260701.md)
- [Non-iPhone claim readiness dashboard](docs/results/noniphone-claim-readiness-dashboard-20260701.md)
- [Non-iPhone professor decision packet](docs/results/noniphone-professor-decision-packet-20260701.md)
- [Non-iPhone reviewer risk audit](docs/results/noniphone-reviewer-risk-audit-20260701.md)
- [Controlled public origin workload deploy packet](docs/results/controlled-public-origin-workload-deploy-packet-20260701.md)
- [Non-iPhone desktop path-change readiness](docs/results/noniphone-desktop-path-change-readiness-20260701.md)
- [Controlled public Chrome bridge synthesis](docs/results/controlled-public-chrome-bridge-synthesis-20260701.md)
- [Safari WebDriver session readiness](docs/results/safari-webdriver-session-readiness-20260630.md)
- [User-provided public origin readiness](docs/results/user-provided-public-origin-readiness-20260630.md)
- [Non-iPhone next research decision brief](docs/results/non-iphone-next-research-decision-20260630.md)
- [Non-iPhone gate rerun report](docs/results/non-iphone-gate-rerun-20260701.md)
- [Chrome H3 local transient return-path sweep](docs/results/chrome-h3-rebinding-transient-return-path-sweep-20260624.md)
- [Chrome H3 local transient boundary repetition](docs/results/chrome-h3-rebinding-transient-boundary-repetition-20260624.md)
- [Chrome H3 local transient downlink fine boundary](docs/results/chrome-h3-rebinding-transient-downlink-fine-boundary-20260624.md)
- [Chrome H3 local transient upload fine boundary](docs/results/chrome-h3-rebinding-transient-upload-fine-boundary-20260624.md)
- [Workload transition-zone synthesis](docs/results/workload-transition-zone-synthesis-20260624.md)
- [Chrome H3 local transient downlink retry boundary](docs/results/chrome-h3-rebinding-transient-downlink-retry-boundary-20260624.md)
- [Chrome H3 local transient downlink wait-only boundary](docs/results/chrome-h3-rebinding-transient-downlink-wait-boundary-20260624.md)
- [Downlink recovery comparison](docs/results/downlink-recovery-comparison-20260624.md)
- [Chrome H3 local transient polling/dashboard boundary](docs/results/chrome-h3-rebinding-transient-poll-boundary-20260624.md)
- [Chrome H3 local transient polling/dashboard long boundary](docs/results/chrome-h3-rebinding-transient-poll-long-boundary-20260624.md)
- [Polling transition-zone synthesis](docs/results/polling-transition-zone-synthesis-20260624.md)
- [Chrome H3 local transient upload retry boundary](docs/results/chrome-h3-rebinding-transient-upload-retry-boundary-20260624.md)
- [Chrome H3 local transient upload retry long outage](docs/results/chrome-h3-rebinding-transient-upload-retry-long-outage-20260624.md)
- [Chrome H3 local transient upload retry stress boundary](docs/results/chrome-h3-rebinding-transient-upload-retry-stress-boundary-20260624.md)
- [Chrome H3 local transient upload retry2 15000ms recovery](docs/results/chrome-h3-rebinding-transient-upload-retry2-15000ms-20260624.md)
- [Chrome H3 local transient upload retry2 stress boundary](docs/results/chrome-h3-rebinding-transient-upload-retry2-stress-boundary-20260624.md)
- [Application recovery tradeoff synthesis](docs/results/application-recovery-tradeoff-20260624.md)
- [quic-go local HTTP/3 migration replication results](docs/results/quic-go-local-h3-replication-results-20260624.md)
- [quic-go local HTTP/3 mid-flight repetition summary](docs/results/quic-go-h3-midflight-repetition-summary-20260624.md)
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
MATRIX_ID=quic-go-h3-midflight-repetition-20260624 REPEAT_COUNT=3 ./scripts/run-local-h3-midflight-matrix.sh
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
