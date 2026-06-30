# non-iPhone Professor Decision Packet

Generated: `2026-06-30`

이 문서는 교수님 논의용 public-safe decision packet이다. credential, 계정 ID, hostname, IP, qlog, keylog, pcap, NetLog 원문을 포함하지 않는다.

## 한 문장 결론

현재 연구는 구현체 성숙도와 deployment/browser gap을 보수적으로 주장할 수 있지만, public Chrome CM 성공과 live AWS+s2n 성공은 아직 외부 gate 때문에 주장하면 안 된다.

## 현재 판정

| 항목 | 값 |
| --- | --- |
| 허용 가능한 claim 수 | `5` |
| 아직 막아야 할 claim 수 | `3` |
| open gate | `[]` |
| all key gates blocked | `True` |
| controlled-public strong CM success | `0` |
| paper decision | The current corpus is ready for a conservative maturity/gap report, but not for Chrome public CM success or live AWS+s2n success claims. |

## 교수님께 받을 Decision

| decision | 권장도 | 이유 | 비용 | 리스크 |
| --- | --- | --- | --- | --- |
| `scope_gap_paper`<br>현재 근거로 논문 scope를 maturity/gap analysis로 확정할지 | `recommended` | 구현체 primitive, deployment boundary, local workload/QoE evidence는 충분하지만 public browser/AWS positive claim은 아직 닫혀 있다. | 추가 외부 실험 없이도 초안/보고서 방향을 확정할 수 있다. | positive public handover result가 없으므로 contribution wording을 보수적으로 유지해야 한다. |
| `open_positive_public_browser_path`<br>positive browser result를 얻기 위해 public H3 origin과 non-iPhone secondary path를 열지 | `conditional` | Chrome public-origin single-session CM 성공 claim을 열려면 현재 두 gate가 모두 필요하다. | WebPKI+Alt-Svc H3 origin, workload endpoint, Ethernet/USB LAN 같은 non-iPhone secondary desktop path가 필요하다. | 실행 후에도 strong CM success가 나오지 않을 수 있으며, 그 경우 negative/gap evidence가 된다. |
| `open_aws_s2n_path`<br>AWS NLB+s2n live forwarding을 우선 열지 | `conditional_high_value` | 교수님 decision 중 AWS 검증에 가장 직접적으로 대응한다. | 유효한 AWS credential이 필요하며, 첫 단계는 active migration이 아니라 live forwarding echo다. | s2n public active migration API 한계 때문에 forwarding 이후 별도 active path-change 설계가 필요하다. |
| `open_safari_feasibility`<br>Safari를 cross-browser feasibility appendix로만 추가할지 | `low_priority` | Safari는 NetLog 같은 browser-internal evidence가 약해서 Chrome보다 claim ceiling이 낮다. | Safari Allow remote automation 설정이 필요하다. | 성공해도 main contribution보다 feasibility appendix 성격이 강하다. |

## 현재 말해도 되는 Claim

- `implementation_maturity`
- `deployment_routing_boundary`
- `local_chrome_workload_controls`
- `streaming_qoe_claim`
- `paper_scope_decision`

## 아직 말하면 안 되는 Claim

- `chrome_public_cm_success`: blocked=`True`; reason=No controlled-public strong CM success row exists yet.; The user-provided public HTTPS origin is not H3 Alt-Svc ready.; The current desktop host lacks a non-iPhone active secondary path.
- `aws_s2n_live_success`: blocked=`True`; reason=AWS identity classifies as invalid_client_token on the current host.
- `safari_handover_success`: blocked=`True`; reason=Safari Allow remote automation is not enabled.

## 교수님께 물어볼 질문

- 현재 논문을 CM implementation/deployment/browser maturity gap 분석으로 scope를 확정해도 되는가?
- positive result가 꼭 필요하다면 AWS NLB+s2n과 Chrome controlled-public workload 중 어느 gate를 먼저 열 것인가?
- Streaming workload는 main claim으로 둘 것인가, QoE/session-churn appendix로 둘 것인가?
- Safari는 main browser comparison이 아니라 feasibility appendix로 제한해도 되는가?

## 말하면 안 되는 문장

- HTTP/3 Connection Migration이 웹 작업 연속성을 보장한다고 말하지 않는다.
- Chrome public-origin single-session Connection Migration 성공을 주장하지 않는다.
- AWS NLB+s2n live success 또는 active migration success를 주장하지 않는다.
- Streaming completion을 zero-impact continuity나 single-session CM으로 해석하지 않는다.
- CDN/edge HTTP/3 continuity를 end-to-end origin CM으로 해석하지 않는다.

## 권장 보고 방식

현재는 positive success paper라기보다 maturity/gap paper로 잡는 것이 방어 가능하다. 교수님이 positive deployment/browser result를 요구하면, 먼저 AWS credential 또는 public H3 origin plus non-iPhone secondary path 중 하나를 열어야 한다.
