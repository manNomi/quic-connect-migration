# Chapter 2. CM 미사용/저가시성 원인 분석

작성일: `2026-06-30`

## 1. 이 챕터의 목적

Chapter 1의 결론은 “QUIC Connection Migration은 구현체에 아예 없는 기술이 아니다”였다. 그러면 다음 질문은 자연스럽게 바뀐다.

> 구현체와 표준에는 CM primitive가 있는데, 왜 실제 웹 브라우저와 서비스에서는 CM이 잘 보이지 않는가?

이 챕터는 CM의 낮은 가시성을 단일 원인으로 설명하지 않는다. 대신 구현체 정책, HTTP/3 discovery, 실제 client path change, session attribution, CID-aware load balancing, proxy/CDN termination, middlebox manageability, security concern, workload recovery, observability gap을 나누어 본다.

## 2. 결론 요약

현재 evidence 기준에서 가장 근거가 충분한 답은 다음이다.

> CM이 덜 쓰이거나 잘 보이지 않는 이유는 “기술이 없어서”가 아니라, transport support가 user-visible web continuity로 관찰되기까지 여러 계층의 조건을 동시에 만족해야 하기 때문이다.

즉, QUIC stack이 path validation과 CID를 제공해도 브라우저 runtime policy가 migration을 하지 않을 수 있고, application request가 HTTP/3로 가지 않았을 수 있으며, network-change trigger가 실제 active path를 바꾸지 않았을 수 있다. 또한 tuple이 바뀌어도 그것이 원래 connection의 migration인지 새 QUIC session인지 분리해야 한다.

## 3. 분석 방법

분석은 다음 세 입력을 묶어서 수행했다.

| 입력 | 파일 | 역할 |
| --- | --- | --- |
| friction rubric | `data/cm-operational-friction-rubric.csv` | layer별 friction 정의와 matching term |
| experiment corpus | `data/experiment-results.csv` | 지금까지의 local/AWS/browser 실험 row |
| literature tracker | `data/literature-review-tracker.csv` | RFC, 논문, 공식 문서 링크와 relevance |

이 입력은 `tools/build_cm_operational_friction_matrix.py`로 집계했다. 결과물은 다음이다.

- `docs/results/cm-operational-friction-matrix-20260624.md`
- `data/cm-operational-friction-matrix-20260624.csv`

## 4. Friction Matrix 요약

| layer | 핵심 friction | 논문에서의 의미 |
| --- | --- | --- |
| implementation | CM primitive는 있지만 구현체와 runtime policy가 다르다. | 구현 여부를 yes/no로만 보면 안 된다. |
| browser | HTTP/3 application request 자체를 먼저 증명해야 한다. | Alt-Svc나 H3 capability만으로 CM 실험이 아니다. |
| network | network-change trigger가 active path를 실제로 바꾸지 않을 수 있다. | interface toggle 성공은 CM 증거가 아니다. |
| browser/session | tuple change는 replacement session일 수 있다. | server remote tuple만으로 CM이라고 말하면 위험하다. |
| load-balancer | LB는 CID-aware routing을 해야 한다. | 5-tuple routing은 migrated packet을 다른 backend로 보낼 수 있다. |
| proxy | HTTP/3 proxy support는 end-to-end CM support가 아니다. | HAProxy 같은 proxy는 negative control로 중요하다. |
| cdn | CDN HTTP/3 continuity는 edge-level일 수 있다. | viewer-edge continuity와 origin end-to-end CM을 구분해야 한다. |
| middlebox | middlebox는 5-tuple semantics에 의존한다. | NAT/firewall/rate-limit 운영이 보수적으로 될 수 있다. |
| security | migration/preferred address는 악용 가능성을 만든다. | 운영자가 CM을 조심스럽게 설정할 이유가 있다. |
| application | workload recovery가 transport failure를 숨길 수 있다. | retry/Range/buffering은 CM success와 다르다. |
| methods | 단일 artifact는 모호하다. | qlog, NetLog, route snapshot, server log를 한 row에 묶어야 한다. |
| adoption | HTTP/3 adoption과 CM adoption은 다르다. | H3가 널리 보인다고 CM도 널리 동작한다고 말할 수 없다. |
| performance | CM이 성공해도 stall/QoE cost가 남을 수 있다. | completion뿐 아니라 delay, rebuffer, retry count가 필요하다. |

## 5. 논문에 쓸 수 있는 문장

안전하게 쓸 수 있는 주장:

> QUIC CM is implemented as a transport capability in multiple stacks, but its deployment and visibility in web applications are gated by browser policy, HTTP/3 endpoint discovery, active path-change evidence, session attribution, CID-aware routing, intermediary termination, observability, and workload-specific recovery.

피해야 할 주장:

| 피해야 할 표현 | 이유 |
| --- | --- |
| “CM은 구현되지 않아서 안 쓰인다.” | Chapter 1 evidence와 충돌한다. |
| “HTTP/3를 지원하면 CM도 지원한다.” | HTTP/3 support와 CM support는 별개다. |
| “tuple이 바뀌었으니 CM이다.” | 새 QUIC session일 수 있다. |
| “CDN HTTP/3 continuity는 origin end-to-end CM이다.” | edge termination 가능성이 있다. |
| “Range retry 성공은 CM 성공이다.” | application recovery이지 transport migration evidence가 아니다. |

## 6. 다음 챕터로 넘어간 이유

이 챕터는 CM이 잘 안 보이는 이유가 여러 계층에 흩어져 있음을 보여준다. 따라서 다음 단계는 복잡한 browser/deployment path를 제거한 positive control이다.

> 통제된 QUIC client/server에서는 CM이 실제로 동작하는가?

이 질문이 Chapter 3의 출발점이다.

## 7. 검수 결과

| 검수 항목 | 결과 |
| --- | --- |
| Chapter 1과 충돌 여부 | 충돌 없음. “구현 부재”가 아니라 “계층별 friction”으로 정리했다. |
| source link 존재 여부 | `chapter-02-reference-and-evidence.md`에 RFC, 논문, 공식 문서 링크를 분리했다. |
| 로컬 구현/실험 근거 | `data/experiment-results.csv`, `data/cm-operational-friction-matrix-20260624.csv`로 연결했다. |
| generator 맥락 | `tools/build_cm_operational_friction_matrix.py`의 matching logic과 term을 부록에 적었다. |
| claim boundary | Chrome/Safari/Android browser handover CM 성공 claim은 하지 않았다. |
