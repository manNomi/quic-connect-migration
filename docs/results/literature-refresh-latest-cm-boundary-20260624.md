# Latest QUIC CM Evidence Boundary Refresh

작성일: 2026-06-24

## 목적

현재 실험 결론이 “QUIC Connection Migration은 안 된다” 또는 “브라우저에서 이미 완성됐다”처럼 과하게 흐르지 않도록, 2026년 기준 최신 표준/구현/연구 신호를 다시 확인했다.

## 확인한 최신 신호

| source | 확인 내용 | 연구 반영 |
| --- | --- | --- |
| [IETF QUIC multipath draft-21](https://datatracker.ietf.org/doc/draft-ietf-quic-multipath/) | Multipath QUIC은 single-path RFC 9000 CM 위에 path identifier와 동시 다중 path 사용을 추가한다. Wi-Fi/mobile failover는 중요한 use-case지만, stream scheduling과 성능 영향은 별도 고려 대상이다. | 본 연구는 multipath가 아니라 RFC 9000 style single-path migration/browser handover evidence를 대상으로 한정한다. |
| [Chromium `quic_context.h`](https://chromium.googlesource.com/chromium/src/+/master/net/quic/quic_context.h) | Chrome/Chromium에는 default-network change, poor connectivity, idle session, port migration, server migration 관련 policy knob가 존재한다. | “브라우저에 primitive가 없다”가 아니라 “policy가 켜졌는지, runtime에서 실제 migration event가 발생했는지”를 실험으로 분리한다. |
| [QUIC applicability guidance](https://quicwg.org/ops-drafts/draft-ietf-quic-applicability.html#connection-migration) | QUIC v1은 client active migration을 지원하지만, path validation에는 최소 RTT가 필요하고 congestion control reset 등 성능 영향이 있다. active migration 지원 시 non-zero server CID가 권장된다. | migration success 여부와 application continuity/QoE를 분리해서 본다. qlog path validation을 필수 evidence로 둔다. |
| [Server-initiated migration draft](https://datatracker.ietf.org/doc/draft-kozuka-quic-server-migration/) | 2026년 server-initiated CM proposal이 존재하지만 work-in-progress이며, RFC 9000 client-side active migration과는 다른 문제다. | future work로만 둔다. 본 실험의 primary success claim에는 포함하지 않는다. |
| [s2n-quic zero-length CID issue](https://github.com/aws/s2n-quic/issues/2378) | zero-length CID와 active migration 해석은 구현체 간 이견과 수정 이력이 있다. Chrome/Cronet의 zero-length CID 사용도 논의된다. | 구현체 성숙도 평가는 API 유무만 보지 않고 CID policy, peer migration support, qlog/path validation까지 본다. |
| [SwiftShift / NOSSDAV 2026](https://dl.acm.org/doi/10.1145/3798065.3798080) | 최신 연구는 QUIC migration의 blocking path validation과 timeout-driven recovery가 ultra-low-latency media에서 stall을 만든다는 방향으로 개선을 제안한다. | 본 연구의 downlink-dominant workload와 heartbeat variant는 “CM이 되더라도 app continuity가 자동 보장되지 않는다”는 질문과 맞닿아 있다. |
| [ACM CCR 2025 CM in the Wild](https://dl.acm.org/doi/10.1145/3727063.3727066) | Internet-wide CM support가 불균일하다는 anchor paper다. | 본 연구의 novelty는 public support 유무 재측정이 아니라, 실패 계층을 browser/runtime/deployment/application evidence chain으로 분해하는 데 둔다. |

## 해석 업데이트

1. CM은 “좋은 기술인데 왜 안 쓰나?”라는 질문보다 “어느 계층에서 끊기는가?”가 더 논문답다.
2. 최신 표준 흐름은 CM을 버리는 쪽이 아니라 multipath/path management/server migration으로 확장하는 쪽이다.
3. 다만 그 확장 흐름은 본 실험의 browser HTTP/3 handover success claim을 대신 증명하지 않는다.
4. Chrome/Chromium에는 migration 관련 구현/정책 지점이 있으므로, browser experiment에서는 NetLog mode evidence만으로는 부족하고 trigger/success/failure/session continuity evidence를 함께 요구해야 한다.
5. 구현체별 maturity는 `supports CM API`보다 다음 축으로 나누는 것이 더 정확하다.

| maturity axis | 필요한 확인 |
| --- | --- |
| transport primitive | AddPath/Probe/Switch, migrate/probe_path, path validation |
| CID/routing policy | non-zero CID, QUIC-LB/CID-aware routing, zero-length CID corner case |
| browser/runtime policy | network-change notifier, migration flags, active session migration trigger |
| observability | qlog path events, NetLog migration events, server tuple/session evidence |
| application continuity | downlink/upload/polling task success, refresh/retry 필요 여부 |
| deployment maturity | direct-origin, LB, CDN edge termination, proxy negative control |

## 논문에 반영할 문장 방향

현재까지의 안전한 표현:

> QUIC CM primitive and CID-aware deployment paths are available in several stacks, but browser-visible HTTP/3 task continuity requires a stricter evidence chain: application H3 baseline, actual client path change, path validation, session continuity, and workload completion.

아직 쓰면 안 되는 표현:

> Chrome/Safari mobile handover에서 HTTP/3 Connection Migration이 성공했다.

이 표현은 final browser handover protocol `0/6`이 해소되기 전까지 보류한다.
