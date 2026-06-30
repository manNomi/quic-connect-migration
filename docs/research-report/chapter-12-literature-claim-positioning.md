# Chapter 12. Literature-Based Claim Positioning

작성일: `2026-06-30`

## 1. 이 챕터의 목적

지금까지 실험은 구현체, 배포 경로, browser observability, public handover workload를 순서대로 검수했다. Chapter 12는 이 결과를 문헌과 연결한다.

중요한 원칙은 다음이다.

> 문헌은 연구 방향과 claim boundary를 정하는 데 쓰고, 우리 실험이 보여주지 않은 browser single-session CM 성공을 대신 증명하는 데 쓰지 않는다.

따라서 각 source를 `supports`, `does_not_support`, `experiment_gap`으로 나눈다.

## 2. 가장 중요한 문헌 포지션

| source group | 핵심 의미 | 우리 연구에 주는 영향 |
| --- | --- | --- |
| Internet-wide CM measurement | QUIC CM support는 uneven하고 failure reason 분석이 남아 있음 | failure-layer decomposition이 연구 gap이 된다 |
| RFC 9000 / RFC 9114 | QUIC path validation과 HTTP/3 discovery는 표준 primitive | path validation과 app H3 baseline은 필요조건이지 task continuity 충분조건이 아니다 |
| RFC 9308 / RFC 9312 / middlebox work | UDP timeout, NAT rebinding, CID, manageability friction 존재 | CM 미사용 이유를 "구현 부재" 하나로 축소하면 안 된다 |
| Chromium/Cronet policy docs | client runtime policy knobs 존재 | browser behavior는 transport capability와 분리해서 실험해야 한다 |
| quic-go docs | controlled implementation positive control 가능 | library positive control을 browser success로 일반화하면 안 된다 |
| multipath drafts | path management 연구는 계속 진행 중 | 본 논문은 RFC 9000 single-path/browser evidence로 scope 제한 |
| media/QoE papers | migration overhead and recovery matter for low-latency media | streaming은 completion뿐 아니라 startup/rebuffer/session churn 측정 필요 |
| security/privacy work | migration is valuable but operationally sensitive | operators may be cautious for security/manageability reasons |
| AWS NLB QUIC support | CID-aware routing is now a cloud deployment axis | direct-origin, LB, CDN edge를 분리해서 평가해야 한다 |

## 3. 문헌이 강화하는 주장

### CM은 죽은 기술이 아니다

RFC 9000은 QUIC connection migration의 normative primitive를 제공하고, multipath draft와 media migration work는 path management가 계속 active research topic임을 보여준다. 따라서 논문에서 "왜 안 쓰이는가"를 물을 때, "쓸모없는 기술이라서"가 아니라 "어느 계층에서 막히는가"로 질문해야 한다.

### 구현 여부와 실제 browser web task continuity는 다르다

quic-go처럼 path add/probe/switch control을 제공하는 구현체가 있고, local positive control에서도 qlog path validation을 확인했다. 그러나 Chrome public handover rows에서는 qlog path validation과 single-session continuity를 아직 증명하지 못했다. 따라서 implementation maturity와 browser runtime maturity는 별도 축이다.

### deployment와 manageability가 핵심 friction이다

RFC 9308/9312, QASM, AWS NLB, CloudFront/Cloudflare/HAProxy 같은 배포 문서는 QUIC migration이 단순 endpoint feature가 아니라 routing, CID, middlebox, edge termination, observability 문제와 얽혀 있음을 보여준다.

### workload continuity는 application recovery와 섞인다

upload retry, byte-range retry, media buffering 결과는 모두 같은 방향을 가리킨다. 사용자 task completion은 transport CM만으로 결정되지 않는다. retry/resume/buffer/session churn을 함께 봐야 한다.

## 4. 문헌만으로는 말할 수 없는 것

| 보류해야 할 주장 | 이유 |
| --- | --- |
| Chrome/Safari가 Wi-Fi to iPhone USB 중 original HTTP/3 connection을 single-session으로 migration했다 | 문헌은 가능성/정책/표준을 말할 뿐, 우리 scenario의 runtime artifact가 아니다 |
| public H3 site가 있으면 CM도 된다 | HTTP/3 discovery와 migration은 별도 evidence다 |
| CDN edge HTTP/3 continuity는 origin까지 end-to-end CM이다 | managed CDN은 edge에서 termination될 수 있다 |
| media playback complete는 CM success다 | segment retry, buffering, replacement sessions가 completion을 만들 수 있다 |
| tuple change만 있으면 migration이다 | qlog path validation, session count, target workload attribution이 필요하다 |

## 5. 현재 실험 결과와 문헌의 접점

| 우리 결과 | 관련 문헌 축 | 해석 |
| --- | --- | --- |
| quic-go local positive control | RFC 9000, quic-go docs, qlog | implementation-level CM은 재현 가능 |
| HAProxy/CDN/LB deployment review | RFC 9308/9312, AWS NLB, Cloudflare/CloudFront/HAProxy docs | deployment tier에 따라 continuity 의미가 달라짐 |
| Chrome local NAT rebinding control | RFC 9000, qlog/NetLog | artifact interpretation rule 검증 |
| public full-response downlink failure | EnCoR, browser policy, workload continuity | path change가 task failure로 나타날 수 있음 |
| public byte-range retry completion | HTTP/3/Fetch, application recovery | task completion can recover without CM proof |
| public upload retry completion | application recovery, session attribution | upload retry restores task but costs replacement/multiple sessions |
| local media/buffer controls | SwiftShift/media QoE, Fetch/Streams | streaming requires QoE/session metrics |

## 6. 논문 기여로 바꿀 수 있는 문장

안전한 contribution wording:

> We propose an evidence-chain framework for evaluating HTTP/3 browser task continuity under path change, separating application HTTP/3 establishment, client path-change evidence, QUIC path validation, browser session attribution, deployment routing, and workload-level completion.

한국어로 쓰면:

> 본 연구는 HTTP/3 브라우저 작업 연속성을 단순 connection 유지 여부가 아니라 application H3 baseline, client path change, QUIC path validation, browser session attribution, deployment routing, workload completion으로 분해해 평가하는 evidence-chain framework를 제안한다.

## 7. 다음 논문 작업에 주는 결정

다음 연구 의사결정을 정리할 때는 다음처럼 가져가는 것이 좋다.

1. "CM이 왜 안 쓰이는가"를 단정하지 않는다.
2. 대신 "CM이 실제 웹 workload에서 보이려면 어떤 evidence chain이 필요한가"로 framing한다.
3. 지금까지 결과는 CM 개선 논문보다는 maturity/evidence/workload taxonomy 논문에 더 가깝다.
4. 만약 다음 실험에서 browser single-session CM이 끝까지 안 나오면, application recovery와 deployment friction을 중심 contribution으로 잡는다.
5. 만약 Android/Cronet 또는 특정 stack에서 CM success가 나오면, Chrome/Safari와의 runtime maturity 차이를 논문 contribution으로 잡는다.

## 8. 검수 결과

| 검수 항목 | 결과 |
| --- | --- |
| source마다 supports/does_not_support/gap을 분리했는가? | PASS |
| 문헌으로 browser CM success를 대신 주장하지 않았는가? | PASS |
| external link status를 별도 표로 남겼는가? | PASS |
| 404 reference를 수정했는가? | PASS, RFC 9308 link를 datatracker로 교체 |
| builder trigger를 line-level로 문서화했는가? | PASS, `chapter-12-reference-and-evidence.md`와 trigger map 참조 |
