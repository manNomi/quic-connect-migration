# Evidence chain and gap synthesis

작성일: 2026-06-24

## 1. 목적

현재 연구 결과를 “된다/안 된다”로 먼저 정하지 않고, 논문에서 방어 가능한 claim 단위로 다시 정리한다.

핵심 질문:

> HTTP/3 Connection Migration이 실제 웹 작업 연속성으로 이어진다고 주장하려면 어떤 evidence chain이 필요한가?

관련 기준:

- [RFC 9000 QUIC](https://datatracker.ietf.org/doc/html/rfc9000): QUIC connection migration, peer address change, path validation, connection ID 사용의 기준점
- [RFC 9114 HTTP/3](https://datatracker.ietf.org/doc/html/rfc9114): HTTP semantics over QUIC와 HTTP/3 application request 판정의 기준점
- [Chromium NetLog event definitions](https://chromium.googlesource.com/chromium/src/+/HEAD/net/log/net_log_event_type_list.h): Chrome 내부 QUIC migration/session event 관찰 기준
- [HTTP/3 explained](https://http.dev/3): browser HTTP/3 discovery, fallback, deployment 해석 보조 기준

## 2. 현재까지 지지되는 claim

### 2.1 QUIC CM primitive는 구현체에 존재한다

현재 repo의 구현체 조사와 quic-go local/EC2/AWS 실험은 다음을 지지한다.

| claim | 근거 |
| --- | --- |
| quic-go direct-origin active migration 가능 | local transport, local HTTP/3, EC2 direct-origin에서 `AddPath -> Probe -> Switch` 성공 |
| path validation evidence 관찰 가능 | qlog에서 PATH_CHALLENGE/PATH_RESPONSE와 ALPN/H3 frame evidence 수집 |
| AWS NLB는 조건부로 continuity 가능 | `TCP_QUIC :443` + 올바른 QUIC-LB plaintext CID/Server ID에서 same-target continuity 관찰 |
| deployment routing은 실패 원인이 될 수 있음 | malformed CID, wrong Server ID negative control에서 application payload 실패 |

따라서 “CM이 안 쓰이는 이유는 구현이 전혀 없기 때문”이라고 쓰면 현재 증거와 맞지 않는다.

## 3. 현재까지 지지되지 않는 claim

다음은 아직 주장하면 안 된다.

| claim | 왜 아직 부족한가 |
| --- | --- |
| Chrome에서 실제 Wi-Fi/LTE handover 중 CM이 성공했다 | 현재 장비에는 active secondary path가 없고, Android device도 연결되어 있지 않다 |
| Safari에서 HTTP/3 CM이 성공했다 | Safari WebDriver readiness는 있지만 NetLog equivalent가 없고, controlled public origin baseline이 아직 없다 |
| tuple/source port 변화는 곧 CM이다 | Chrome CDP heartbeat no-change에서 network-change 없이도 server remote addr count 2, QUIC session count 2가 관찰됐다 |
| request-level tuple 변화가 없으면 rebinding/path validation도 없다 | Chrome streaming upload rebinding 3회에서 upload는 완료되고 qlog path validation은 있었지만 request-level remote tuple은 하나로 남았다 |
| inactive interface toggle은 handover 실험이다 | client path snapshot이 `no_client_path_change_observed`로 분류했다 |
| public third-party endpoint NetLog만으로 application H3를 확정할 수 있다 | Cloudflare/Google/YouTube public controls에서 discovery와 application H3를 분리해야 했다 |

## 4. 새로 얻은 중요한 negative evidence

### 4.1 Heartbeat는 no-change에서도 multiple QUIC sessions를 만들 수 있다

CDP real-time runner로 downlink streaming 중 heartbeat를 실행했다.

| condition | classification | server remote addr count | Chrome target QUIC sessions | qlog path validation |
| --- | --- | ---: | ---: | --- |
| no heartbeat, no network change | `no_path_change_baseline` | 1 | 1 | false |
| heartbeat, no network change | `multiple_quic_sessions_without_network_change` | 2 | 2 | false |
| heartbeat, inactive interface toggle | `multiple_quic_sessions_without_client_path_change` | 2 | 2 | false |

해석:

- heartbeat 자체는 application-level recovery 전략 후보지만, 관측 해석을 어렵게 만들 수 있다.
- server가 본 remote tuple이 늘어났다고 해서 곧바로 connection migration이라고 볼 수 없다.
- qlog path validation, Chrome session continuity, client active path change를 함께 요구해야 한다.
- NetLog migration 관련 event는 `QUIC_CONNECTION_MIGRATION_MODE` 같은 mode evidence와 실제 trigger/success/failure evidence를 분리해야 한다.

### 4.2 Inactive interface toggle은 path-change trigger가 아니다

inactive Thunderbolt Bridge toggle은 command exit 0이었다.

그러나 client path snapshot은 다음을 보였다.

| 항목 | before | after |
| --- | --- | --- |
| active interface | `en0` | `en0` |
| default interface | `en0` | `en0` |
| target route | `lo0` | `lo0` |
| classification | `no_client_path_change_observed` | `no_client_path_change_observed` |

따라서 이 실험은 handover가 아니라 no-op trigger 대조군이다.

### 4.3 Streaming upload rebinding은 request log 한계를 보여준다

Chrome forced-H3 page가 streaming `fetch()` upload를 수행하는 동안 local UDP rebinding proxy가 server-facing socket을 A에서 B로 전환했다.

| condition | runs | upload completion | request-level remote tuple count | Chrome target QUIC sessions | qlog path validation |
| --- | ---: | --- | ---: | ---: | --- |
| streaming upload, local UDP rebinding | 3 | 3/3 PASS, each `/upload-sink` received 262144 bytes | 1 in every run | 1 in every run | true in every run |

해석:

- client-sending workload에서도 Chrome forced-H3 request는 local NAT rebinding 중 완료될 수 있었다.
- 그러나 server request log의 `RemoteAddr`는 request handler 관점 값이라 packet-level rebinding을 항상 드러내지 않는다.
- 따라서 browser-level CM 또는 NAT rebinding claim에는 request log, qlog path validation, Chrome NetLog session attribution, proxy/client path evidence를 함께 사용해야 한다.
- 이 결과는 local NAT rebinding control이며, 실제 Wi-Fi/LTE active handover 성공을 의미하지 않는다.

## 5. 논문용 evidence chain

논문에서 browser-level HTTP/3 CM success를 주장하려면 최소 다음이 필요하다.

| 단계 | 필요한 evidence | 현재 상태 |
| --- | --- | --- |
| 1. Application H3 baseline | server request `HTTP/3.0`, TLS ALPN `h3`, qlog H3 frame, browser NetLog | local forced Chrome에서 관찰; controlled public origin은 pending |
| 2. 실제 client path 변화 | before/after route/interface/public IP 변화 | inactive toggle은 no-change; real active path pending |
| 3. 같은 logical QUIC connection 유지 | tuple change와 함께 qlog path validation, replacement session 아님 | quic-go controlled client에서 관찰; Chrome browser pending |
| 4. application task continuity | downlink/upload/polling task complete, manual refresh 없음 | local controls pass; public active path-change pending |
| 5. deployment continuity | LB/CDN/proxy가 changed tuple을 같은 logical backend로 유지 | AWS NLB TCP_QUIC positive/negative controls 있음; CDN pending |

machine-readable rubric은 [data/evidence-chain-rubric.csv](../../data/evidence-chain-rubric.csv)에 고정했다.

## 6. 연구 방향 결론

현재 연구는 “CM이 부족하니 개선하자”로 바로 가기보다, 다음 framing이 더 방어 가능하다.

> QUIC Connection Migration primitive는 구현체와 controlled deployment에서 작동하지만, browser/web application에서 CM success를 주장하려면 application H3 baseline, 실제 client path change, qlog path validation, browser session continuity, deployment routing continuity를 모두 확인해야 한다.

이 framing의 장점:

- 교수님 피드백의 “구현도 안 된 기술을 왜 안 쓰냐고 하면 안 된다”를 피한다.
- 구현체, browser policy, deployment routing, application workload를 계층별로 분리한다.
- 우리가 이미 만든 positive/negative control이 모두 논문에 쓰인다.

## 7. 다음 실험 우선순위

1. Controlled public WebPKI origin을 준비하고 Chrome application H3 baseline을 `PASS`로 만든다.
2. active secondary path를 준비한 뒤 CDP runner로 `WORKLOAD=downlink` no-heartbeat/heartbeat active path-change를 실행한다.
3. 같은 조건에서 polling interval을 바꿔 recovery detection delay를 비교한다.
4. Safari는 server qlog + packet capture + WebDriver result 중심으로 별도 evidence chain을 만든다.
5. Android Chrome/Cronet은 ADB device가 연결된 뒤 Wi-Fi/LTE handover로 확장한다.

현재 local 상태의 blockers:

| blocker | 현재 관찰 |
| --- | --- |
| secondary active path | `false`, active non-loopback IPv4는 `en0` 하나 |
| Android device | ADB device 없음 |
| AWS identity | caller identity unavailable |
| disk | 2.44 GiB free, 대형 packet capture는 보류 권장 |
