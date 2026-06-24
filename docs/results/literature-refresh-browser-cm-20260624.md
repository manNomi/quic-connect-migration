# Literature refresh for browser CM experiments

작성일: 2026-06-24

## 1. 목적

Chrome/Safari controlled public origin 실험을 설계하기 전에, 최신 QUIC Connection Migration 문헌이 요구하는 실험 조건을 다시 확인했다.

이번 refresh의 초점은 다음이다.

1. Internet-wide CM deployment 결과가 우리 실험 질문과 어떻게 연결되는가
2. browser/public-origin 실험에서 어떤 precondition을 증명해야 하는가
3. mobile handover에서 application workload가 왜 중요해지는가
4. Chrome과 Safari의 observability 차이를 논문에서 어떻게 다룰 것인가

## 2. 핵심 문헌과 해석

| source | 핵심 내용 | 우리 연구에 주는 의미 |
| --- | --- | --- |
| [An Analysis of QUIC Connection Migration in the Wild](https://arxiv.org/html/2410.06066v1) | Internet-wide scan으로 QUIC CM 지원이 균일하지 않음을 보인다. SNI가 있는 IPv4 successful handshakes 중 migration success가 52%, IPv6 with SNI에서는 78%로 보고된다. 실패 이유는 implementation, load balancer routing, firewall, disabled migration 등으로 열거되지만 세부 원인 분류는 제한적이다. | “CM이 좋은데 왜 안 쓰나?”를 단순 구현 부재로 답하면 안 된다. deployment path와 failure layer를 나눠 실험해야 한다. 우리 HAProxy/NLB/controlled public gate가 이 gap에 대응한다. |
| [EnCoR: An end-to-end architecture for simplifying cellular networks](https://arxiv.org/html/2605.22524v2) | QUIC을 end-to-end mobility architecture로 보고, QUIC의 implicit mobility가 client가 이동 후 데이터를 보내지 않는 edge case에서 packet loss/failure를 만들 수 있음을 지적한다. 저자들은 application ping packet 같은 보완을 논의한다. | browser workload는 upload/download/polling만으로 부족하다. downlink-dominant long response, client-silent interval, post-change heartbeat를 분리해서 실험해야 한다. |
| [Connection Migration in QUIC draft](https://datatracker.ietf.org/doc/html/draft-tan-quic-connection-migration-00) | active/passive, vertical/horizontal, client/server, single/multipath migration taxonomy를 제시한다. expired draft지만 용어 분류에는 유용하다. | 논문 용어를 “Wi-Fi/LTE 전환” 하나로 뭉치지 말고 vertical client-side passive/active path-change처럼 명확히 써야 한다. |
| [HTTP/3 explained](https://http.dev/3) | browser는 Alt-Svc 또는 HTTPS DNS record로 HTTP/3 endpoint를 discover하고, QUIC/TCP handshake racing과 fallback을 수행한다. UDP 차단과 Alt-Svc cache/broken state도 고려해야 한다. | browser CM 실험 전 natural application H3 baseline을 증명해야 한다. discovery job만으로 application H3라고 주장하면 안 된다. |
| [HTTP/3 Practical Deployment Options](https://www.smashingmagazine.com/2021/09/http3-practical-deployment-options-part3/) | HTTP/3 support가 곧 모든 QUIC feature 사용을 뜻하지 않으며, high-level tooling만으로 HTTP/3 동작을 판단하기 어렵다. qlog/qvis/Wireshark 같은 low-level evidence 필요성을 강조한다. | Chrome NetLog, server qlog, server request log, client path snapshot을 함께 요구하는 현재 classifier 방향이 타당하다. Safari는 packet capture/server qlog 중심으로 따로 분류해야 한다. |
| [quic-go Connection Migration docs](https://quic-go.net/docs/quic/connection-migration/) | quic-go는 `AddPath -> Probe -> Switch` 흐름을 문서화하고, application에는 transparent하다고 설명한다. NAT rebinding은 server가 새 tuple packet을 보고 path validation을 수행한다. | local/direct-origin positive control은 표준 기능 확인에 적합하지만, browser/application continuity와 deployment maturity를 대체하지 않는다. |

## 3. 이번 refresh가 바꾸는 실험 설계

### 3.1 Downlink-dominant workload 추가 필요

현재 slow subresource와 mid-flight download는 useful하지만, EnCoR 관점에서는 “path change 직후 client가 얼마나 빨리 새 path에서 packet을 보내는가”가 중요하다.

추가해야 할 workload:

| workload | 목적 |
| --- | --- |
| long streaming response with silent client | server가 계속 보내는 동안 client source path가 바뀌었을 때 implicit detection이 늦어지는지 확인 |
| post-change heartbeat/ping variant | network-change 직후 application-level small fetch가 recovery를 돕는지 확인 |
| dashboard polling with long interval | polling interval이 길면 migration/recovery detection이 지연되는지 확인 |

### 3.2 Browser evidence level 분리

Chrome:

- NetLog로 QUIC session, HTTP stream job, migration-related event 후보를 볼 수 있다.
- 다만 NetLog mode/event만으로 migration을 단정하지 않고 server tuple/qlog와 결합한다.

Safari:

- WebDriver 실행 readiness는 있지만 Chrome NetLog equivalent가 없다.
- server qlog, request log, client path snapshot, packet capture를 evidence chain으로 둔다.

논문 표에는 다음 열이 필요하다.

```text
browser
application_h3_precondition
active_path_change_evidence
server_tuple_change
server_qlog_path_validation
browser_internal_quic_evidence
packet_capture_evidence
classification
```

### 3.3 Failure layer taxonomy 보강

문헌과 현재 실험을 합치면 failure layer는 최소 다음처럼 나눠야 한다.

| layer | 예 |
| --- | --- |
| discovery | Alt-Svc/HTTPS RR는 있으나 application H3 아님 |
| transport primitive | PATH_CHALLENGE/PATH_RESPONSE 또는 CID 부족 |
| client policy | browser/Cronet/Safari가 migration을 trigger하지 않음 |
| deployment routing | LB/CDN/proxy가 changed tuple을 같은 QUIC backend로 못 보냄 |
| middlebox/firewall | UDP 443 또는 non-handshake packet 차단 |
| application workload | client-silent downlink workload에서 recovery 지연 |
| observability | Chrome NetLog 가능, Safari는 packet/qlog 필요 |

## 4. 다음 구현 작업

1. controlled public origin이 준비되면 Chrome baseline을 먼저 `PASS`로 만든다.
2. Chrome network-change 실험에는 `client-path-change-summary.json`을 반드시 포함한다.
3. downlink-dominant silent-client workload와 post-change heartbeat variant는 local forced-QUIC baseline에서 `PASS`로 확인했다. CDP runner 결과 heartbeat는 no-change에서도 별도 QUIC session/source tuple을 만들 수 있으므로, 다음 controlled public active path-change 실험에서는 tuple change 단독이 아니라 client path snapshot, qlog path validation, browser session count를 함께 요구한다.
4. Safari는 baseline PASS 이후 packet capture plan을 붙여 별도 실험으로 실행한다.
5. 논문 본문에서는 “CM이 안 쓰인다”가 아니라 “CM support and observability are uneven across implementation, client policy, and deployment path”로 framing한다.
