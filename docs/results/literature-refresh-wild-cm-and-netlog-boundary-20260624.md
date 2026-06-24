# Literature Refresh: Wild CM Support and NetLog Evidence Boundary

작성일: 2026-06-24

## 목적

현재 로컬 Chrome forced-H3 NAT rebinding 실험은 packet-level rebinding, qlog path validation, Chrome target NetLog PATH_CHALLENGE/PATH_RESPONSE를 함께 관찰했다.

이 문서는 그 결과를 최신 문헌과 표준 기준에 다시 맞춰 보고, 논문에서 어디까지 주장할 수 있는지 고정한다.

핵심 질문:

> Chrome NetLog target source에서 path validation frame이 보이면 browser-level Connection Migration 성공이라고 말할 수 있는가?

답은 아직 아니다. 이는 강한 local NAT rebinding evidence지만, 실제 Wi-Fi/LTE 또는 active secondary path handover success claim에는 client path-change proof와 controlled public WebPKI baseline이 추가로 필요하다.

## Sources

| grade | source | checked fact | impact on this study |
| --- | --- | --- | --- |
| A | [An Analysis of QUIC Connection Migration in the Wild](https://arxiv.org/html/2410.06066v1) | Internet-wide scan shows CM support is not uniformly present across large QUIC providers, and the paper notes deeper reason analysis and preferred-address behavior as future work. | Our study should not ask only whether CM exists; it should classify failure layers across implementation, browser policy, deployment routing, and application workload. |
| A | [RFC 9000 QUIC](https://datatracker.ietf.org/doc/html/rfc9000) | Path validation verifies reachability after address change and uses PATH_CHALLENGE/PATH_RESPONSE, but it is not a complete NAT traversal mechanism or application-continuity guarantee. | qlog/NetLog path frames are necessary transport evidence, not sufficient browser handover evidence. |
| A | [quic-go Connection Migration docs](https://quic-go.net/docs/quic/connection-migration/) | quic-go documents a direct `AddPath -> Probe -> Switch` model and explains probing with fresh CIDs. | quic-go remains our controlled positive baseline; browser experiments need stricter runtime-policy evidence. |
| B | [MIMIQ: Masking IPs with Migration in QUIC](https://www.usenix.org/system/files/foci20-paper-govil.pdf) | MIMIQ uses QUIC migration to change client IPs within ongoing connections for privacy, showing CM has real value outside simple mobility. | The “why is CM not broadly used?” section should include privacy/security value and operational sensitivity, not dismiss CM as useless. |
| B | [Connection Migration in QUIC draft](https://datatracker.ietf.org/doc/html/draft-tan-quic-connection-migration-00) | Expired non-normative draft classifies active/passive, vertical/horizontal, client/server, and single/multipath migration. | Use as terminology support only; do not treat as a standard. |
| Watch | [Managing multiple paths for a QUIC connection](https://quicwg.org/multipath/draft-ietf-quic-multipath.html) | Multipath QUIC enables simultaneous use of multiple paths but does not define address discovery or application scheduling. | Keep this paper scoped to RFC 9000 single-path migration and browser/web continuity evidence. |

## Interpretation Update

### 1. Path validation frame evidence is strong but scoped

The latest Chrome local rebinding summaries show:

| workload | repetitions | proxy packet rebinding | qlog path validation | Chrome target NetLog path validation |
| --- | ---: | --- | --- | --- |
| downlink forced-H3 rebinding | 6 | 6/6 observed | 6/6 observed | 6/6 observed |
| streaming upload forced-H3 rebinding | 3 | 3/3 observed | 3/3 observed | 3/3 observed |

This is stronger than earlier tuple-only evidence because it ties three independent views together:

- UDP proxy packet logs show client packets forwarded through both local upstream sockets.
- Server qlog records path validation behavior.
- Chrome NetLog target source records PATH_CHALLENGE received and PATH_RESPONSE sent on the same target QUIC session.

However, this remains a local NAT rebinding control. It does not prove that Chrome successfully migrated across Wi-Fi/LTE or another active network interface.

### 2. Browser CM success needs one more layer than transport CM success

RFC 9000 path validation answers a transport reachability question:

> Can packets sent on the changed path reach the peer and be validated?

The paper question is a web continuity question:

> Did a browser HTTP/3 workload keep the same useful task alive across a real client path change?

Therefore the browser success classifier must require all of the following:

| layer | required evidence | current status |
| --- | --- | --- |
| HTTP/3 application baseline | controlled public WebPKI origin, server request protocol, ALPN/qlog, browser NetLog | local forced-H3 yes; controlled public pending |
| actual client path change | before/after route, interface, or public IP evidence | active secondary path pending |
| transport path validation | qlog and/or NetLog PATH_CHALLENGE/PATH_RESPONSE on target session | local rebinding yes |
| browser session continuity | no replacement target QUIC session for the workload | local rebinding yes; active handover pending |
| task continuity | download/upload/polling task completes without manual refresh | local controls yes; active handover pending |

### 3. The paper contribution is becoming an evidence-boundary methodology

The ACM CCR 2025 wild-scan paper is the correct anchor for “CM support is uneven on the public Internet.”

Our contribution should be framed differently:

> We turn QUIC CM from a binary support question into a reproducible evidence chain for browser/web task continuity.

This is stronger than merely re-running public scans because it explains why an implementation can support CM while a browser application experiment still cannot claim success:

- HTTP/3 discovery may fail before CM is relevant.
- Browser runtime policy may choose not to migrate an active session.
- Deployment routing may break changed 5-tuple traffic unless CID-aware routing is configured.
- Application workloads may finish, restart, or recover in ways that look like CM unless session evidence is checked.
- NetLog/qlog path frames prove transport behavior but must be tied to a real client path change.

## Paper Claim Boundary

Safe wording now:

> In controlled local Chrome forced-H3 NAT rebinding experiments, HTTP/3 workloads completed while packet forwarding switched between local upstream sockets, and both qlog and Chrome NetLog recorded path-validation frames on the target QUIC session.

Unsafe wording for now:

> Chrome successfully performed Wi-Fi/LTE HTTP/3 Connection Migration.

That claim stays blocked until the final browser handover protocol has controlled-public baseline rows and active path-change rows.

## Experiment Implication

The next decisive experiment should not be another tuple-only repetition. It should create countable final-protocol rows:

1. Controlled public WebPKI Chrome application H3 baseline.
2. Chrome downlink active path-change without heartbeat.
3. Chrome downlink active path-change with heartbeat.
4. Chrome no-change baselines for both workload variants.
5. Safari or Android feasibility run with a weaker but explicit evidence rubric.

If active path-change hardware/network inputs remain unavailable, the strongest publishable interim result is:

> CM primitives and controlled deployment paths are operationally real, but browser/web CM claims require a stricter multi-layer evidence chain than current public or local-only artifacts usually provide.
