# Chapter 7 Scanner Trigger Map

작성일: `2026-06-30`

이 표는 Chapter 7 controlled public origin baseline에서 어떤 scanner/classifier가 어떤 evidence를 읽는지 line-level로 정리한다.

## 1. Public Origin Readiness

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [check_public_origin_readiness.py#L43-L59](../../../tools/check_public_origin_readiness.py#L43-L59) | HTTPS URL parsing, DNS lookup | hostname/port, DNS address count | public reachability precondition |
| [check_public_origin_readiness.py#L70-L88](../../../tools/check_public_origin_readiness.py#L70-L88) | Python TLS probe | TLS version/cipher/subject/issuer or error | WebPKI/TLS evidence |
| [check_public_origin_readiness.py#L91-L112](../../../tools/check_public_origin_readiness.py#L91-L112) | `curl -sSIL` headers | final status, Alt-Svc headers | browser discovery candidate |
| [check_public_origin_readiness.py#L115-L144](../../../tools/check_public_origin_readiness.py#L115-L144) | DNS/TLS/curl results | `tcp_tls_ok`, `curl_https_ok`, `has_h3_alt_svc` | readiness summary |
| [check_public_origin_readiness.py#L147-L183](../../../tools/check_public_origin_readiness.py#L147-L183) | redaction tokens | URL, host, addresses, TLS subject/issuer redacted | public-safe output |

## 2. Config Readiness

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [check_controlled_public_config.py#L21-L42](../../../tools/check_controlled_public_config.py#L21-L42) | baseline/active/Android required keys | key groups | readiness layer 분리 |
| [check_controlled_public_config.py#L130-L163](../../../tools/check_controlled_public_config.py#L130-L163) | key value validation | present/placeholder/valid/detail | host/url/port/listener/Alt-Svc/Chrome path validation |
| [check_controlled_public_config.py#L166-L207](../../../tools/check_controlled_public_config.py#L166-L207) | parsed ignored env | baseline ready, active ready, android ready, blockers | active network-change blocker 분리 |
| [check_controlled_public_config.py#L210-L246](../../../tools/check_controlled_public_config.py#L210-L246) | report object | public-safe markdown without real values | 민감정보 출력 방지 |

## 3. Baseline Classifier

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [classify_controlled_public_h3_baseline.py#L25-L60](../../../tools/classify_controlled_public_h3_baseline.py#L25-L60) | server request list | request count, paths, workloads, ALPN, remote addr count | server-side application request evidence |
| [classify_controlled_public_h3_baseline.py#L63-L91](../../../tools/classify_controlled_public_h3_baseline.py#L63-L91) | Chrome public H3 summary | application using_quic jobs, discovery jobs, QUIC sessions | discovery와 application H3 구분 |
| [classify_controlled_public_h3_baseline.py#L94-L139](../../../tools/classify_controlled_public_h3_baseline.py#L94-L139) | CDP body dataset | workload completion/success/error keys | DOM application outcome |
| [classify_controlled_public_h3_baseline.py#L142-L158](../../../tools/classify_controlled_public_h3_baseline.py#L142-L158) | server ok, expected count, qlog H3, browser H3 | PASS/PASS_NEGATIVE_CONTROL/PASS_FEASIBILITY/FAIL classification | H3 discovery-only overclaim 방지 |
| [classify_controlled_public_h3_baseline.py#L175-L215](../../../tools/classify_controlled_public_h3_baseline.py#L175-L215) | server.json, metadata, readiness, Chrome summary, qlog | combined summary object | baseline artifact 통합 |

## 4. Unlock Gate And Wrappers

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [check_controlled_public_baseline_unlock.py#L21-L24](../../../tools/check_controlled_public_baseline_unlock.py#L21-L24) | allowed unlock classifications | allowed set | final-countable baseline class 제한 |
| [check_controlled_public_baseline_unlock.py#L27-L83](../../../tools/check_controlled_public_baseline_unlock.py#L27-L83) | validation, artifact bundle completeness | `unlocks_active_trials` | baseline PASS와 artifact completeness 동시 요구 |
| [run-controlled-public-h3-server.sh#L8-L22](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-server.sh#L8-L22) | host/cert/key/port/listener/Alt-Svc env | server preconditions | WebPKI controlled origin |
| [run-controlled-public-h3-server.sh#L35-L60](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-server.sh#L35-L60) | run metadata | server-public-origin-metadata.json | traceability, but raw value는 commit 금지 |
| [run-controlled-public-h3-browser-baseline.sh#L24-L36](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-browser-baseline.sh#L24-L36) | public origin readiness, Chrome public H3 runner | readiness JSON, Chrome NetLog summary | baseline browser artifact 생성 |
| [run-controlled-public-h3-browser-baseline.sh#L38-L60](../../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-browser-baseline.sh#L38-L60) | server artifact present, require application H3 flag | controlled public baseline summary | gate enforcement |

## 5. Preflight Redaction

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [controlled-public-preflight.sh#L54-L64](../../../harness/scripts/controlled-public-preflight.sh#L54-L64) | public URL, baseline summary, network-change command, Chrome path, redaction flag | preflight variables | active path-change readiness input |
| [controlled-public-preflight.sh#L65-L82](../../../harness/scripts/controlled-public-preflight.sh#L65-L82) | `REDACT_SENSITIVE=1` | `<configured>` / redacted placeholders | public-safe console/report |
| [controlled-public-preflight.sh#L117-L127](../../../harness/scripts/controlled-public-preflight.sh#L117-L127) | experiment readiness checker | JSON/Markdown readiness artifacts | preflight gate |
| [controlled-public-preflight.sh#L140-L168](../../../harness/scripts/controlled-public-preflight.sh#L140-L168) | generated next commands | redacted server/baseline/network-change commands | 실험 재현성 + secret leak 방지 |
| [init-controlled-public-config.sh#L34-L57](../../../harness/scripts/init-controlled-public-config.sh#L34-L57) | ignored config template and checker | config init/worksheet/check | local-only env 관리 |

## 6. False-Positive Guards

| guard | 코드 근거 | 방지하는 오해 |
| --- | --- | --- |
| discovery-only demotion | [classify_controlled_public_h3_baseline.py#L149-L152](../../../tools/classify_controlled_public_h3_baseline.py#L149-L152) | `dns_alpn_h3`만 보고 application H3라고 주장하는 것 |
| application H3 PASS 제한 | [classify_controlled_public_h3_baseline.py#L153-L157](../../../tools/classify_controlled_public_h3_baseline.py#L153-L157) | server qlog/browser evidence 없는 baseline을 PASS로 처리하는 것 |
| active config blocker | [check_controlled_public_config.py#L183-L195](../../../tools/check_controlled_public_config.py#L183-L195) | baseline ready를 active network-change ready로 혼동하는 것 |
| final-countable unlock gate | [check_controlled_public_baseline_unlock.py#L48-L63](../../../tools/check_controlled_public_baseline_unlock.py#L48-L63) | record-only smoke를 final-countable baseline으로 쓰는 것 |
