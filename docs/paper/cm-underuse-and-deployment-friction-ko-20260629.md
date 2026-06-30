# 왜 QUIC Connection Migration은 덜 쓰이는가

생성일: `2026-06-29`

## 핵심 답변

현재 증거 기준으로 CM이 덜 쓰이는 이유는 기술이 아예 없어서가 아니다. 주요 QUIC 구현체에는 path validation, NAT rebinding 대응, active/passive migration primitive, qlog/trace, test가 상당히 존재한다. 문제는 이 primitive가 브라우저 runtime policy, HTTP/3 discovery, 실제 client path change, load balancer routing, proxy/CDN termination, middlebox 운영, application recovery와 동시에 맞아야 user-visible continuity로 나타난다는 점이다.

따라서 논문에서는 `CM 미사용 = 구현 부재`로 단순화하지 않는다. 더 정확한 framing은 다음과 같다.

> QUIC CM is implemented unevenly and deployed conservatively because transport support is only one layer. Browser policy, endpoint discovery, routing, observability, workload semantics, and operational risk decide whether CM becomes visible application continuity.

## 구현체 성숙도 요약

| metric | value |
| --- | --- |
| surveyed implementations | 18 |
| active migration API = yes | 8 |
| passive migration = yes | 14 |
| tests = yes | 14 |
| level distribution | L1_L2=1; L2_L3=1; L2_L4=1; L3_L4=4; L4=3; L4_AWS_L5_candidate=1; L4_L5=1; L4_L5_candidate=1; L4_L5_caveat=1; L4_client_policy_boundary_audit=1; L5_candidate=1; L5_deployment_candidate=1; L5_edge=1 |

## Layer별 friction

| layer | 논문용 주장 | 의미 | repo evidence rows | literature matches | paper use |
| --- | --- | --- | --- | --- | --- |
| 구현체/런타임 정책 | CM primitive는 존재하지만 구현체와 runtime policy에 따라 실제 사용 여부가 달라진다. | QUIC stack이 migration API를 제공해도 browser, application API, default policy가 runtime migration을 막을 수 있다. | 61 | 19 | source-backed explanation with repo evidence |
| 브라우저/HTTP/3 discovery | HTTP/3 application request가 실제로 성립해야 CM 실험이 가능하다. | Alt-Svc나 DNS hint만으로는 충분하지 않으며, target request가 HTTP/3로 갔는지 server log와 qlog로 확인해야 한다. | 17 | 3 | source-backed explanation with repo evidence |
| 클라이언트 path-change 증명 | network-change 명령이 실제 active client path를 바꾸지 않을 수 있다. | interface toggle은 성공해도 route/interface/public IP가 바뀌지 않으면 CM evidence가 아니다. | 3 | 7 | source-backed explanation with repo evidence |
| 브라우저/session attribution | tuple 변화는 CM이 아니라 replacement session일 수 있다. | 브라우저는 실제 path migration 없이도 새 QUIC session을 열 수 있으므로 session continuity가 필요하다. | 4 | 7 | source-backed explanation with repo evidence |
| 로드밸런서/CID routing | 로드밸런서는 tuple 변화 후에도 같은 logical backend로 라우팅해야 한다. | 5-tuple 기반 라우팅은 migration packet을 다른 backend로 보낼 수 있어 CID-aware routing이 필요하다. | 8 | 3 | source-backed explanation with repo evidence |
| 프록시/중간자 termination | HTTP/3 proxy 지원은 CM 지원을 의미하지 않는다. | proxy가 QUIC을 terminate하거나 path validation을 전달하지 못하면 end-to-end CM semantics가 깨진다. | 1 | 11 | source-backed explanation with repo evidence |
| CDN edge scope | CDN의 HTTP/3 CM은 origin end-to-end가 아니라 viewer-edge continuity일 수 있다. | managed CDN은 edge에서 QUIC을 terminate하므로 origin까지의 CM과 구분해야 한다. | 9 | 4 | source-backed explanation with repo evidence |
| 방화벽/NAT/운영 middlebox | CM은 middlebox와 운영 모니터링의 5-tuple 가정을 흔든다. | NAT, firewall, rate limiter, Kubernetes service tracking은 IP/port 변화와 encrypted control plane 때문에 어려워진다. | 26 | 8 | cautious explanatory support |
| 보안/운영 민감도 | CM과 preferred address는 보안/운영 정책상 민감할 수 있다. | IP masking, censorship circumvention, exfiltration, state-table abuse 가능성 때문에 operator가 보수적으로 설정할 수 있다. | 0 | 9 | related-work support only |
| 애플리케이션 workload | downlink-dominant workload는 migration recovery를 제때 유도하지 못할 수 있다. | path change 후 client가 보낼 데이터가 없으면 detection/validation이 늦어지고 heartbeat나 retry가 recovery mechanism을 바꾼다. | 27 | 8 | source-backed explanation with repo evidence |
| 관찰성/측정 방법 | browser CM evidence는 단일 artifact로 판정하기 어렵다. | NetLog, qlog, server tuple, route snapshot은 각각 빈틈이 있으므로 combined evidence chain이 필요하다. | 55 | 12 | source-backed explanation with repo evidence |
| 도입/측정 gap | HTTP/3 adoption은 CM adoption이 아니다. | 인터넷-wide scan에서 HTTP/3 capable server라도 CM support는 provider configuration과 deployment path에 따라 달라진다. | 13 | 8 | source-backed explanation with repo evidence |
| 성능/QoE 비용 | CM이 성공해도 stall, retransmission, QoE 비용이 남을 수 있다. | 특히 media나 interactive workload는 completion뿐 아니라 startup delay, rebuffer, recovery time을 봐야 한다. | 25 | 6 | cautious explanatory support |

## 논문에서 사용할 결론

1. CM은 표준과 구현체 수준에서 존재한다.
2. HTTP/3 지원은 CM 지원과 다르다.
3. 브라우저에서는 application H3 baseline, client path change, tuple change, qlog path validation, session continuity, task completion을 한 row에서 동시에 보여야 한다.
4. Load balancer/CDN/proxy는 CM을 end-to-end로 보존하지 않을 수 있다.
5. 많은 웹 workload는 retry, Range resume, buffering, reconnect로 사용자 경험을 복구하므로 transport CM 부재가 숨겨질 수 있다.
6. 반대로 upload/download 같은 long-lived task는 CM 부재가 직접 task failure로 드러난다.

## 현재 연구와의 연결

본 repo의 실험은 이 friction을 직접 반영한다. quic-go/quiche/AWS NLB positive control은 transport/deployment CM 가능성을 보여준다. HAProxy, browser Alt-Svc, inactive interface toggle, multiple-session, return-path outage, public iPhone USB rows는 HTTP/3 또는 tuple 변화만으로 browser CM을 주장할 수 없음을 보여준다. Upload/download/Range/media 결과는 application-level recovery와 workload semantics가 작업 연속성의 핵심 변수임을 보여준다.

## 아직 필요한 증거

- controlled public origin 복구 후 fresh Chrome H3 baseline
- Chrome no-heartbeat active path-change 3회
- Chrome heartbeat active path-change 3회
- Safari 또는 Android feasibility 1회
- public Range 및 buffered-media handover row
