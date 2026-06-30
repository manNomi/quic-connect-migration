# Literature Claim Positioning Matrix

생성일: `2026-06-30`

## 목적

이 문서는 QUIC Connection Migration 관련 최신 문헌을 현재 실험 결과와 연결한다. 결론을 먼저 정하고 문헌을 끼워 맞추지 않기 위해, 각 source마다 `supports`, `does_not_support`, `experiment_gap`을 분리했다.

현재 논문 방향에서 가장 중요한 판단은 다음이다.

1. CM은 표준과 일부 구현체에서 실재하고, multipath/media/edge/security 연구로 계속 확장되는 active topic이다.
2. 하지만 그 사실만으로 Chrome/Safari HTTP/3 single-session handover 성공을 주장할 수는 없다.
3. CM이 덜 쓰이거나 덜 보이는 이유는 구현 부재 하나가 아니라 browser runtime policy, deployment routing, middlebox manageability, security concern, application recovery가 겹친 문제다.
4. 따라서 본 연구의 기여는 `CM이 된다/안 된다`가 아니라 `어느 계층의 어떤 증거가 있어야 browser web task continuity를 주장할 수 있는가`를 계측하는 쪽이 더 방어 가능하다.

## Positioning Matrix

| source | grade | claim axis | paper use | supports | does not support | experiment gap |
| --- | --- | --- | --- | --- | --- | --- |
| ccr2025-wild-cm | A | deployment reality / support unevenness | Primary related-work anchor and gap statement. | Internet-wide QUIC CM support is uneven, so a failure-layer study is justified. | It does not prove why each endpoint fails, nor does it prove browser workload continuity. | Need controlled decomposition into application H3, path change, path validation, session continuity, and task completion. |
| rfc9000-cm | A | standard primitive | Normative background for CID, path validation, NAT rebinding, and client migration. | QUIC has standardized primitives that allow a connection to survive address changes when endpoint and deployment conditions permit. | Path validation is necessary but not sufficient for HTTP/3 browser task continuity. | Need qlog path-validation evidence plus browser session and workload evidence in the same row. |
| rfc9114-h3-discovery | A | HTTP/3 endpoint discovery | Explains why application H3 baseline is a separate gate before CM testing. | A browser must first discover and choose an HTTP/3 endpoint before transport migration can matter for a web workload. | It does not imply that an HTTP/3-capable origin or Alt-Svc advertisement enables migration. | Need fresh public application-H3 baseline after origin recovery. |
| rfc9308-rfc9312-ops | A | operational manageability | Operational caution for UDP timeouts, NAT rebinding, CID choices, and manageability limits. | Deployment maturity is separate from transport feature existence. | It does not measure browser behavior or quantify CM adoption by itself. | Need deployment controls: direct origin, CID-aware load balancer, CDN/edge distinction, proxy negative controls. |
| chromium-cronet-policy | A | browser/runtime policy | Shows that client runtime policy exists and must be separated from transport capability. | Browser-family stacks expose migration-related policy knobs for network change, path degradation, idle migration, and non-default network use. | API/source hooks do not prove that Chrome or Safari actually migrated a live browser HTTP/3 session in our scenario. | Need NetLog migration trigger/success/failure evidence and controlled Android/Cronet feasibility rows. |
| quic-go-docs | A | implementation positive control | Positive-control implementation model for explicit path add/probe/switch behavior. | Some QUIC implementations expose concrete migration controls and path probing behavior. | A library positive control does not generalize to browser HTTP/3 handover behavior. | Need to contrast local quic-go positive controls with browser runtime and deployment evidence. |
| ietf-multipath | A | standards trajectory | Future-work and scoping source. | QUIC path work is moving toward richer multipath/path-management mechanisms rather than abandoning mobility. | Multipath support does not prove RFC 9000 single-path browser CM in today's Chrome/Safari. | Need to keep the paper scoped to single-path browser CM unless using a multipath-enabled stack. |
| swiftshift-2026 | B | interactive media / QoE sensitivity | Motivation for media QoE metrics and migration overhead discussion. | Even when QUIC migration exists, migration delay and recovery behavior can matter for low-latency media. | It does not prove vanilla browser HTTP/3 media continuity or our specific iPhone USB handover behavior. | Need media rows with startup delay, rebuffering, retry, session count, and path evidence. |
| encor-2026 | B | mobile handover / application continuity | Mobile-network adjacent evidence that application behavior can matter after handover. | Handover and application continuity can fail in edge cases when endpoint traffic and detection timing do not align. | It does not replace direct browser Wi-Fi/cellular HTTP/3 CM measurement. | Need silent-client downlink and heartbeat variants under active path change. |
| qasm-2026 | B | middlebox manageability | Explains operational reluctance and middlebox state tracking friction. | QUIC encryption and address migration complicate middlebox state, NAT, rate limiting, load balancing, and service tracking. | It does not measure our browser workloads or prove a specific public-origin failure cause. | Need to classify failures as browser policy, deployment routing, middlebox/proxy, or application recovery rather than one CM failure bucket. |
| quicstep-2026 | B | security / censorship circumvention | Shows that CM can be a valuable and sensitive primitive beyond mobility. | Connection migration has security/privacy use cases and can be used as a support-measurement signal. | It does not imply operators should always enable CM or that browsers expose it for web workloads. | Need a neutral maturity framing that includes value, abuse risk, and operational caution. |
| quic-exfil-2025 | B | security misuse / preferred address | Operational caution for preferred-address and server-side migration features. | Migration-related features can create monitoring and policy risks, explaining some deployment caution. | Preferred-address misuse is not the same mechanism as RFC 9000 client Wi-Fi/cellular migration. | Need to distinguish client migration, server preferred address, server-initiated migration, and multipath in terminology. |
| aws-nlb-quic | A | managed deployment / CID-aware routing | Deployment control for CID-aware routing and managed cloud feasibility. | Managed deployments may need QUIC-aware CID routing to preserve continuity across tuple changes. | A load balancer's CID-aware behavior is not the same as end-to-end browser-origin single-session migration. | Need to separate direct-origin, LB, CDN edge, and third-party public H3 cases. |

## 논문 주장에 주는 영향

### 강해진 주장

- QUIC CM은 버려진 기능이 아니다. RFC 9000의 primitive, IETF multipath draft, SwiftShift 같은 media migration 연구, cloud/LB 문서가 모두 active path-management 흐름을 보여준다.
- `왜 안 쓰이는가`는 구현 여부보다 deployment/runtime/observability 질문으로 바꿔야 한다. QASM, RFC 9308/9312, AWS NLB, QUIC-Exfil은 운영자가 CM을 조심스럽게 다룰 이유를 제공한다.
- streaming은 중요한 use case지만, completion만 보면 오해하기 쉽다. buffer, segment retry, startup delay, rebuffer, session churn을 같이 측정해야 한다.

### 약해졌거나 아직 보류해야 할 주장

- Chrome/Safari가 Wi-Fi에서 iPhone USB/cellular로 바뀌는 동안 원래 HTTP/3 connection을 single-session으로 migration했다는 주장은 아직 보류한다.
- third-party public H3 site 또는 CDN edge support는 controlled origin의 qlog/tuple/workload evidence를 대체하지 못한다.
- multipath, server preferred address, server-initiated migration은 RFC 9000 client active migration과 구분해야 한다.

## 다음 실험 우선순위

1. controlled public origin을 복구하고 no-change Chrome H3 baseline을 다시 얻는다.
2. Chrome downlink no-heartbeat 3회와 heartbeat 3회를 page-ready active path-change로 실행한다.
3. upload/download retry와 Range resume public rows를 추가해 application recovery와 CM을 분리한다.
4. streaming은 그 다음 단계에서 QoE row로 확장한다. 이때 startup delay, rebuffer event, retry count, Chrome target QUIC session count를 함께 보고한다.
5. Safari는 feasibility, Android/Cronet은 true mobile-platform follow-up으로 분리한다.

## Source Links

- `ccr2025-wild-cm`: [An Analysis of QUIC Connection Migration in the Wild](https://dl.acm.org/doi/10.1145/3727063.3727066)
- `rfc9000-cm`: [QUIC: A UDP-Based Multiplexed and Secure Transport](https://datatracker.ietf.org/doc/html/rfc9000)
- `rfc9114-h3-discovery`: [HTTP/3](https://datatracker.ietf.org/doc/html/rfc9114)
- `rfc9308-rfc9312-ops`: [RFC 9308 and RFC 9312](https://datatracker.ietf.org/doc/html/rfc9308)
- `chromium-cronet-policy`: [Chromium QUIC migration parameters and Android Cronet ConnectionMigrationOptions](https://developer.android.com/develop/connectivity/cronet/reference/org/chromium/net/ConnectionMigrationOptions)
- `quic-go-docs`: [quic-go Connection Migration documentation](https://quic-go.net/docs/quic/connection-migration/)
- `ietf-multipath`: [Managing multiple paths for a QUIC connection](https://datatracker.ietf.org/doc/draft-ietf-quic-multipath/)
- `swiftshift-2026`: [SwiftShift: Accelerating QUIC Migration for Ultra-Low-Latency Interactive Media](https://dl.acm.org/doi/10.1145/3798065.3798080)
- `encor-2026`: [EnCoR: An end-to-end architecture for simplifying cellular networks](https://arxiv.org/html/2605.22524v2)
- `qasm-2026`: [QASM: A Novel Framework for QUIC-Aware Stateful Middleboxes](https://arxiv.org/abs/2602.03354)
- `quicstep-2026`: [QUICstep: Evaluating connection migration based QUIC censorship circumvention](https://petsymposium.org/popets/2026/popets-2026-0014.php)
- `quic-exfil-2025`: [QUIC-Exfil: Exploiting QUIC's Server Preferred Address Feature to Perform Data Exfiltration Attacks](https://arxiv.org/abs/2505.05292)
- `aws-nlb-quic`: [AWS Network Load Balancer QUIC protocol support](https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-quic-protocol-support-for-network-load-balancer-accelerating-mobile-first-applications/)

## 재생성

`python3 tools/build_literature_claim_positioning.py`
