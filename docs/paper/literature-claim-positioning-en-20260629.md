# Literature Claim Positioning Matrix

Generated: `2026-06-29`

## Purpose

This document connects the current QUIC Connection Migration literature to the experiment corpus without deciding the conclusion in advance. Each source is separated into what it supports, what it does not support, and what experimental gap remains.

The current paper direction should be:

1. CM is a real standard feature and an active research topic, extending into multipath, media, edge, and security work.
2. That does not prove Chrome/Safari HTTP/3 single-session handover in the web workload setting.
3. Underuse or low visibility is a layered deployment/runtime/observability problem, not simply a missing-implementation problem.
4. The defensible contribution is an evidence-chain and workload-continuity study for browser-visible CM claims.

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

## Implications For The Paper

### Strengthened Claims

- QUIC CM is not abandoned. RFC 9000, the multipath draft, media-migration work, and cloud/LB documentation all point to active path-management work.
- The underuse question should be framed around deployment, runtime policy, and observability rather than implementation existence alone.
- Streaming is a meaningful workload, but it needs QoE and mechanism metrics, not only completion.

### Claims To Keep On Hold

- Do not claim that Chrome/Safari migrated the original HTTP/3 connection across Wi-Fi-to-cellular/iPhone-USB until the full evidence chain is present.
- Do not treat third-party H3 sites or CDN edge support as substitutes for controlled-origin qlog, tuple, workload, and session evidence.
- Do not conflate multipath, server preferred address, server-initiated migration, and RFC 9000 client active migration.

## Next Experimental Priority

1. Recover the controlled public origin and rerun a no-change Chrome H3 baseline.
2. Run three Chrome downlink no-heartbeat rows and three heartbeat rows with page-ready active path change.
3. Add upload/download retry and Range-resume public rows to separate application recovery from CM.
4. Expand streaming after that as a QoE workload with startup delay, rebuffer events, retries, and Chrome target QUIC-session count.
5. Treat Safari as feasibility and Android/Cronet as the true mobile-platform follow-up.

## Source Links

- `ccr2025-wild-cm`: [An Analysis of QUIC Connection Migration in the Wild](https://dl.acm.org/doi/10.1145/3727063.3727066)
- `rfc9000-cm`: [QUIC: A UDP-Based Multiplexed and Secure Transport](https://datatracker.ietf.org/doc/html/rfc9000)
- `rfc9114-h3-discovery`: [HTTP/3](https://datatracker.ietf.org/doc/html/rfc9114)
- `rfc9308-rfc9312-ops`: [RFC 9308 and RFC 9312](https://www.rfc-editor.org/rfc/rfc9308.html)
- `chromium-cronet-policy`: [Chromium QUIC migration parameters and Android Cronet ConnectionMigrationOptions](https://developer.android.com/develop/connectivity/cronet/reference/org/chromium/net/ConnectionMigrationOptions)
- `quic-go-docs`: [quic-go Connection Migration documentation](https://quic-go.net/docs/quic/connection-migration/)
- `ietf-multipath`: [Managing multiple paths for a QUIC connection](https://datatracker.ietf.org/doc/draft-ietf-quic-multipath/)
- `swiftshift-2026`: [SwiftShift: Accelerating QUIC Migration for Ultra-Low-Latency Interactive Media](https://dl.acm.org/doi/10.1145/3798065.3798080)
- `encor-2026`: [EnCoR: An end-to-end architecture for simplifying cellular networks](https://arxiv.org/html/2605.22524v2)
- `qasm-2026`: [QASM: A Novel Framework for QUIC-Aware Stateful Middleboxes](https://arxiv.org/abs/2602.03354)
- `quicstep-2026`: [QUICstep: Evaluating connection migration based QUIC censorship circumvention](https://petsymposium.org/popets/2026/popets-2026-0014.php)
- `quic-exfil-2025`: [QUIC-Exfil: Exploiting QUIC's Server Preferred Address Feature to Perform Data Exfiltration Attacks](https://arxiv.org/abs/2505.05292)
- `aws-nlb-quic`: [AWS Network Load Balancer QUIC protocol support](https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-quic-protocol-support-for-network-load-balancer-accelerating-mobile-first-applications/)

## Regenerate

`python3 tools/build_literature_claim_positioning.py`
