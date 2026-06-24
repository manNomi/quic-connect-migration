# Literature Refresh: Public H3 and CM Evidence Boundary

작성일: 2026-06-24

## 목적

public WebPKI endpoint에서 Chrome natural HTTP/3 application job이 일부 관찰된 뒤, 이것이 논문 claim에 어떤 의미를 갖는지 최신 문헌 기준으로 재정리했다.

핵심 질문:

> public page에서 HTTP/3 application job이 보이면 browser Connection Migration 실험을 대체할 수 있는가?

답은 아니다. public page evidence는 browser가 HTTP/3를 실제 사용할 수 있다는 precondition evidence로는 유용하지만, CM success evidence chain에는 server-side qlog, active path change, same logical connection/routing continuity, controlled workload가 추가로 필요하다.

## Sources

| grade | source | relevance |
| --- | --- | --- |
| A | [An Analysis of QUIC Connection Migration in the Wild](https://arxiv.org/html/2410.06066v1) | Internet-wide CM support is uneven; the paper explicitly leaves deeper reason analysis and preferred-address/server-side extensions as future work. |
| A | [quic-go Connection Migration docs](https://quic-go.net/docs/quic/connection-migration/) | Documents path probing and the `AddPath -> Probe -> Switch` implementation model; useful as controlled positive baseline. |
| B | [Connection Migration in QUIC draft](https://datatracker.ietf.org/doc/html/draft-tan-quic-connection-migration-00) | Expired/non-normative but useful taxonomy for active/passive, vertical/horizontal, client/server, and single/multipath migration. |
| Watch | [Enhancing QUIC Performance in Heterogeneous Networks: A Proactive Connection Migration Approach](https://onlinelibrary.wiley.com/doi/10.1002/nem.70022) | 2025 PCM-QUIC work frames CM as proactive path selection, not merely failure recovery; full-text review still needed. |
| C | [Performance Comparison of HTTP/3 and HTTP/2 with Proxy Integration](https://arxiv.org/html/2409.16267v3) | Adjacent proxy/performance study includes migration scenarios, but peer-review status and methodology need caution. |

## Interpretation for this study

### 1. Public H3 observation is a precondition, not the endpoint

Our expanded public browser observation found natural HTTP/3 application jobs on some third-party pages. This improves the browser precondition story: Chrome is not limited to forced local HTTP/3 in this environment.

However, the CM claim still needs a stronger evidence chain:

| needed evidence | public third-party page | controlled public origin |
| --- | --- | --- |
| application H3 baseline | partially possible through NetLog | yes, with server request log and qlog |
| active client path change | no | yes, with before/after path snapshot |
| same logical QUIC connection | ambiguous | yes, with server qlog and classifier |
| application workload completion | page-dependent and often non-quiescent | yes, workload duration/body size controlled |
| backend/routing continuity | unknown | yes, origin/LB/CDN path known |

### 2. The strongest current related-work gap remains failure-layer classification

The anchor measurement paper shows CM support is uneven at Internet scale. Our contribution should not simply restate that. Our stronger angle is:

> classify where CM continuity is lost across implementation primitive, browser policy, deployment routing, proxy/CDN termination, and application workload.

This is why the current positive and negative controls matter:

- quic-go local/EC2/AWS NLB positive controls establish the primitive and deployment-positive cases.
- HAProxy and malformed/wrong NLB CID tests establish deployment-negative cases.
- Chrome heartbeat/no-change controls show tuple changes can be false positives.
- public H3 observation shows natural browser H3 is possible but not enough for CM.

### 3. PCM-QUIC and multipath work suggest a future improvement direction

If final browser handover shows weak or inconsistent CM behavior, the improvement direction does not need to be "reimplement QUIC". More defensible directions are:

- application-level heartbeat after detected network change;
- explicit browser/client migration policy control, especially Cronet/Android;
- workload-aware path probing for long downlink tasks;
- controlled CID-aware routing in LB/origin deployments;
- eventual comparison with multipath QUIC or proactive migration.

## Updated experiment implication

The next decisive experiment remains unchanged:

1. Build a controlled public WebPKI origin.
2. Pass Chrome natural application H3 baseline using server log + qlog + NetLog.
3. Trigger real active path change.
4. Require client path snapshot, qlog PATH_CHALLENGE/PATH_RESPONSE, browser session continuity, and task completion.
5. Repeat no-heartbeat and heartbeat variants.

Until those are complete, the publishable conclusion should be framed as conditional:

> QUIC CM is mature enough to work in controlled implementation and selected deployment paths, but browser/web continuity requires additional evidence across discovery, client policy, routing, and application workload.
