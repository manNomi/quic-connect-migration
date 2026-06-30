# Chapter 2 Reference And Evidence

작성일: `2026-06-30`

이 문서는 Chapter 2 “CM 미사용/저가시성 원인 분석”의 근거 링크와 로컬 집계 맥락을 정리한다. Chapter 2는 source scanner가 아니라 friction matrix builder를 사용한다. 따라서 검증 단위는 `friction_id`, matching term, experiment corpus count, literature/source link다.

## 1. 재현 가능한 로컬 근거

| 구분 | 경로 | 의미 |
| --- | --- | --- |
| builder | [tools/build_cm_operational_friction_matrix.py](../../tools/build_cm_operational_friction_matrix.py) | friction rubric, experiment corpus, literature tracker를 읽어 matrix를 생성 |
| rubric | [data/cm-operational-friction-rubric.csv](../../data/cm-operational-friction-rubric.csv) | friction_id별 layer, 설명, experiment/literature matching term |
| experiment corpus | [data/experiment-results.csv](../../data/experiment-results.csv) | local implementation, AWS NLB, browser, controlled public handover 실험 row |
| literature tracker | [data/literature-review-tracker.csv](../../data/literature-review-tracker.csv) | RFC, 논문, 공식 문서, draft, issue 링크와 relevance |
| generated report | [docs/results/cm-operational-friction-matrix-20260624.md](../results/cm-operational-friction-matrix-20260624.md) | paper-facing friction matrix |
| generated csv | [data/cm-operational-friction-matrix-20260624.csv](../../data/cm-operational-friction-matrix-20260624.csv) | friction row별 experiment/literature match count |
| paper draft section | [docs/paper/cm-underuse-and-deployment-friction-ko-20260629.md](../paper/cm-underuse-and-deployment-friction-ko-20260629.md) | 한국어 논문 섹션 초안 |

## 2. Builder가 하는 일

`tools/build_cm_operational_friction_matrix.py`는 다음 방식으로 row를 만든다.

1. `data/cm-operational-friction-rubric.csv`에서 `friction_id`와 matching term을 읽는다.
2. `experiment_terms_any`를 `data/experiment-results.csv`의 `trial_id`, `status`, `implementation`, `deployment_tier`, `migration_trigger`, `failure_layer`, `notes`에 대해 부분 문자열로 match한다.
3. `literature_terms_any`를 `data/literature-review-tracker.csv`의 `grade`, `type`, `title`, `venue_or_status`, `relevance`, `next_action`에 대해 부분 문자열로 match한다.
4. experiment status count와 literature grade count를 세어 `data/cm-operational-friction-matrix-20260624.csv`를 만든다.
5. confidence와 evidence count를 기준으로 `paper_use`를 분류한다.

중요한 한계:

- 이 builder는 semantic classifier가 아니라 term-based evidence aggregator다.
- match count가 많다고 해당 friction이 더 중요하다는 뜻은 아니다.
- term false positive 가능성이 있으므로 `friction_id`별 원본 row와 source link를 사람이 확인해야 한다.

## 3. Friction별 Trigger Term과 근거

| friction_id | trigger term | 주요 source/evidence link | 해석 |
| --- | --- | --- | --- |
| `implementation-policy` | `quic-go`; `quiche`; `chromium`; `cronet` | [quic-go CM docs](https://quic-go.net/docs/quic/connection-migration/), [quiche Connection docs](https://docs.rs/quiche/latest/quiche/struct.Connection.html), [Chromium QUIC context](https://chromium.googlesource.com/chromium/src/+/master/net/quic/quic_context.h), [Android Cronet ConnectionMigrationOptions](https://developer.android.com/develop/connectivity/cronet/reference/org/chromium/net/ConnectionMigrationOptions), [Chapter 1 scanner summary](tables/scanner-trigger-summary-20260630.md) | 구현체 primitive와 browser/runtime policy를 구분해야 한다. |
| `application-h3-discovery` | `alt-svc`; `public-h3`; `chrome-h3-local` | [RFC 9114](https://datatracker.ietf.org/doc/html/rfc9114), [HTTP/3 explained](https://http.dev/3), [quic-go HTTP/3 server docs](https://quic-go.net/docs/http3/server/), `data/experiment-results.csv`의 Chrome Alt-Svc rows | application request가 실제 H3로 갔는지 먼저 증명해야 한다. |
| `active-path-proof` | `inactive-if-toggle`; `client-path-change`; `no_client_path_change` | [An Analysis of QUIC Connection Migration in the Wild](https://arxiv.org/abs/2410.06066), [QUICstep](https://petsymposium.org/popets/2026/popets-2026-0014.php), `tools/capture_network_path_snapshot.py`, `tools/compare_network_path_snapshots.py` | network-change 명령 성공과 실제 active path 변화는 다르다. |
| `session-attribution` | `multiple_quic_sessions`; `heartbeat-cdp` | [Chromium NetLog event type list](https://chromium.googlesource.com/chromium/src/+/HEAD/net/log/net_log_event_type_list.h), [qlog main schema](https://quicwg.org/qlog/draft-ietf-quic-qlog-main-schema.html), `tools/classify_chrome_h3_artifacts.py`, `tools/classify_controlled_public_h3_network_change.py` | tuple change만으로 같은 QUIC session migration이라고 말할 수 없다. |
| `cid-load-balancing` | `aws-nlb`; `malformed-cid`; `wrong-server-id` | [AWS NLB QUIC announcement](https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-quic-protocol-support-for-network-load-balancer-accelerating-mobile-first-applications/), [AWS NLB docs](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html), [QUIC-LB draft](https://datatracker.ietf.org/doc/html/draft-ietf-quic-load-balancers), `docs/results/aws-nlb-quic-data-plane-results-20260624.md` | LB는 CID-aware routing을 해야 tuple 변화 뒤에도 같은 logical backend로 보낼 수 있다. |
| `proxy-termination` | `haproxy`; `proxy-path-validation` | [HAProxy docs](https://docs.haproxy.org/3.2/configuration.html), [HAProxy GitHub](https://github.com/haproxy/haproxy), `docs/results/haproxy-http3-negative-control-results-20260623.md` | HTTP/3 proxy support가 end-to-end CM support를 의미하지 않는다. |
| `cdn-edge-scope` | `cloudflare`; `cloudfront`; `public-h3` | [AWS CloudFront HTTP/3 announcement](https://aws.amazon.com/blogs/aws/new-http-3-support-for-amazon-cloudfront/), [CloudFront distribution HTTP version docs](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-values-specify.html#DownloadDistValuesSupportedHTTPVersions), [CloudFront UpdateDistribution API](https://docs.aws.amazon.com/cloudfront/latest/APIReference/API_UpdateDistribution.html), [Cloudflare HTTP/3 docs](https://developers.cloudflare.com/speed/optimization/protocol/http3/) | CDN은 viewer-edge continuity일 수 있어 origin end-to-end CM과 분리해야 한다. |
| `middlebox-manageability` | `haproxy`; `aws-nlb`; `path_challenge` | [RFC 9308](https://datatracker.ietf.org/doc/html/rfc9308), [RFC 9312](https://datatracker.ietf.org/doc/html/rfc9312), [QASM](https://arxiv.org/abs/2602.03354), [Secure Middlebox-Assisted QUIC](https://arxiv.org/abs/2307.08543) | QUIC encryption과 address migration은 middlebox state tracking을 어렵게 만든다. |
| `security-risk` | `quicstep`; `mimiq`; `preferred-address` | [QUICstep](https://petsymposium.org/popets/2026/popets-2026-0014.php), [MIMIQ](https://www.usenix.org/conference/foci20/presentation/govil), [QUIC-Exfil](https://arxiv.org/abs/2505.05292), [alternative server address draft](https://datatracker.ietf.org/doc/html/draft-munizaga-quic-alternative-server-address-00) | migration/preferred address는 privacy/security 가치와 misuse risk를 모두 가진다. |
| `silent-client-downlink` | `downlink`; `heartbeat`; `midflight-download`; `retry`; `application-level-retry-recovery` | [EnCoR](https://arxiv.org/html/2605.22524v2), [SwiftShift](https://dl.acm.org/doi/10.1145/3798065.3798080), `docs/results/chrome-h3-rebinding-transient-downlink-retry-boundary-20260624.md`, `docs/results/controlled-public-full-downlink-iphone-usb-handover-20260629.md` | downlink-dominant workload는 client가 보낼 데이터가 적어 recovery timing이 달라질 수 있다. |
| `observability-gap` | `netlog`; `qlog`; `path-validation`; `browser-public-h3` | [qlog/qvis paper](https://doi.org/10.1145/3404868.3406663), [qlog main schema](https://quicwg.org/qlog/draft-ietf-quic-qlog-main-schema.html), [Chromium NetLog event types](https://chromium.googlesource.com/chromium/src/+/HEAD/net/log/net_log_event_type_list.h), [CM in the Wild](https://arxiv.org/abs/2410.06066) | 단일 artifact가 아니라 combined evidence chain이 필요하다. |
| `measurement-gap` | `public-h3`; `scan`; `controlled-public` | [CM in the Wild](https://arxiv.org/abs/2410.06066), [QUIC Hunter](https://zirngibl.github.io/publication/2024-03-11-QUIC-Hunter-Finding-QUIC-Deployments-and-Identifying-Server-Libraries-Across-the-Internet), [Measuring HTTP/3](https://arxiv.org/abs/2102.12358) | HTTP/3 adoption은 CM adoption을 보장하지 않는다. |
| `performance-risk` | `midflight`; `downlink` | [SwiftShift](https://dl.acm.org/doi/10.1145/3798065.3798080), [PCM-QUIC](https://onlinelibrary.wiley.com/doi/10.1002/nem.70022), [Video Streaming over QUIC](https://arxiv.org/abs/2505.21769) | migration success와 user-visible QoE는 별개다. |

## 4. 연구 자료 링크 묶음

| source_id | 링크 | Chapter 2에서의 역할 |
| --- | --- | --- |
| `ccr2025-wild-cm` | [An Analysis of QUIC Connection Migration in the Wild](https://arxiv.org/abs/2410.06066), [ACM DOI](https://dl.acm.org/doi/10.1145/3727063.3727066) | Internet-wide CM support가 균등하지 않다는 anchor |
| `rfc9000` | [RFC 9000](https://datatracker.ietf.org/doc/html/rfc9000) | CM primitive의 normative 기준 |
| `rfc9114` | [RFC 9114](https://datatracker.ietf.org/doc/html/rfc9114) | HTTP/3 endpoint discovery와 application H3 baseline 기준 |
| `rfc9308` | [RFC 9308](https://datatracker.ietf.org/doc/html/rfc9308) | QUIC applicability와 deployment caveat |
| `rfc9312` | [RFC 9312](https://datatracker.ietf.org/doc/html/rfc9312) | QUIC manageability, middlebox/monitoring caveat |
| `quic-lb` | [QUIC-LB draft](https://datatracker.ietf.org/doc/html/draft-ietf-quic-load-balancers) | CID-aware load balancing 이론 기준 |
| `qlog` | [qlog main schema](https://quicwg.org/qlog/draft-ietf-quic-qlog-main-schema.html), [qlog/qvis ANRW paper](https://doi.org/10.1145/3404868.3406663) | qlog/path evidence 필요성 |
| `chromium-policy` | [Chromium QUIC context](https://chromium.googlesource.com/chromium/src/+/master/net/quic/quic_context.h), [Chromium client session](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/net/quic/quic_chromium_client_session.h), [NetLog event list](https://chromium.googlesource.com/chromium/src/+/HEAD/net/log/net_log_event_type_list.h) | browser runtime policy와 observability 근거 |
| `cronet-policy` | [Android Cronet ConnectionMigrationOptions](https://developer.android.com/develop/connectivity/cronet/reference/org/chromium/net/ConnectionMigrationOptions), [Android platform builder](https://developer.android.com/reference/android/net/http/ConnectionMigrationOptions.Builder) | Android/Cronet client migration policy 근거 |
| `aws-nlb-quic` | [AWS NLB QUIC announcement](https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-quic-protocol-support-for-network-load-balancer-accelerating-mobile-first-applications/), [AWS NLB docs](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html) | CID-aware cloud deployment 근거 |
| `cdn-edge` | [CloudFront HTTP/3 announcement](https://aws.amazon.com/blogs/aws/new-http-3-support-for-amazon-cloudfront/), [CloudFront supported HTTP versions](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-values-specify.html#DownloadDistValuesSupportedHTTPVersions), [Cloudflare HTTP/3 docs](https://developers.cloudflare.com/speed/optimization/protocol/http3/) | edge continuity와 origin end-to-end CM 구분 |
| `proxy-negative` | [HAProxy docs](https://docs.haproxy.org/3.2/configuration.html), [HAProxy source](https://github.com/haproxy/haproxy) | HTTP/3 proxy support와 CM support 분리 |
| `implementation-docs` | [quic-go CM docs](https://quic-go.net/docs/quic/connection-migration/), [quiche Connection docs](https://docs.rs/quiche/latest/quiche/struct.Connection.html), [MsQuic deployment docs](https://microsoft.github.io/msquic/msquicdocs/docs/Deployment.html) | implementation support가 stack별로 다름을 설명 |
| `security-work` | [QUICstep](https://petsymposium.org/popets/2026/popets-2026-0014.php), [MIMIQ](https://www.usenix.org/conference/foci20/presentation/govil), [QUIC-Exfil](https://arxiv.org/abs/2505.05292) | CM의 가치와 operational sensitivity를 동시에 설명 |
| `media-qoe` | [SwiftShift](https://dl.acm.org/doi/10.1145/3798065.3798080), [Video Streaming over QUIC](https://arxiv.org/abs/2505.21769) | completion과 QoE를 분리해야 하는 이유 |

## 5. 로컬 실험 근거 연결

Chapter 2의 friction은 local/AWS/browser 실험 corpus에서 나온 count와 함께 해석한다.

| friction | 관련 로컬 결과 파일 |
| --- | --- |
| implementation/runtime policy | [docs/results/local-implementation-test-results.md](../results/local-implementation-test-results.md), [Chapter 1 scanner summary](tables/scanner-trigger-summary-20260630.md) |
| HTTP/3 discovery | [docs/results/chrome-h3-alt-svc-natural-results-20260624.md](../results/chrome-h3-alt-svc-natural-results-20260624.md), [docs/results/controlled-public-application-h3-gate-20260624.md](../results/controlled-public-application-h3-gate-20260624.md) |
| active path proof | [docs/results/active-path-change-candidates-20260629.md](../results/active-path-change-candidates-20260629.md), [docs/results/iphone-usb-current-detection-20260629.md](../results/iphone-usb-current-detection-20260629.md) |
| session attribution / observability | [docs/results/browser-cm-observability-matrix-20260624.md](../results/browser-cm-observability-matrix-20260624.md), [docs/results/evidence-chain-and-gap-synthesis-20260624.md](../results/evidence-chain-and-gap-synthesis-20260624.md) |
| CID-aware LB | [docs/results/aws-nlb-quic-data-plane-results-20260624.md](../results/aws-nlb-quic-data-plane-results-20260624.md), [docs/results/aws-nlb-http3-workload-results-20260624.md](../results/aws-nlb-http3-workload-results-20260624.md) |
| proxy negative control | [docs/results/haproxy-http3-negative-control-results-20260623.md](../results/haproxy-http3-negative-control-results-20260623.md) |
| application recovery | [docs/results/chrome-h3-rebinding-range-download-control-20260629.md](../results/chrome-h3-rebinding-range-download-control-20260629.md), [docs/results/controlled-public-range-retry-iphone-usb-handover-20260629.md](../results/controlled-public-range-retry-iphone-usb-handover-20260629.md) |
| performance/QoE | [docs/results/streaming-workload-case-analysis-20260629.md](../results/streaming-workload-case-analysis-20260629.md), [docs/results/chrome-h3-rebinding-buffered-media-control-20260629.md](../results/chrome-h3-rebinding-buffered-media-control-20260629.md) |

## 6. 검수 체크리스트

| 항목 | 판정 | 근거 |
| --- | --- | --- |
| “구현이 없어서 안 쓰인다”로 단순화하지 않았는가? | PASS | Chapter 1 scanner/evidence와 충돌하지 않도록 layer friction으로 정리 |
| 실제 source link가 있는가? | PASS | RFC, IETF draft, Chromium source, Android docs, AWS docs, Cloudflare docs, HAProxy docs 링크 포함 |
| 로컬 실험 근거와 연결되는가? | PASS | `data/experiment-results.csv`와 결과 문서 링크 포함 |
| builder trigger가 설명되는가? | PASS | `experiment_terms_any`, `literature_terms_any`, matching target columns 설명 |
| false positive 가능성을 명시했는가? | PASS | term-based aggregator 한계 명시 |
| claim boundary가 안전한가? | PASS | browser single-session CM 성공 claim을 하지 않음 |
