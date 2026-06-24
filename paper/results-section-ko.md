# 결과

## RQ1. QUIC Connection Migration primitive는 실제 구현체에 존재하는가?

본 연구의 구현체 조사와 local/EC2 positive control 결과는 QUIC Connection Migration이 단순한 명세상의 기능에 머물러 있지 않음을 보인다. quic-go는 `AddPath -> Probe -> Switch` 흐름으로 active migration을 수행할 수 있었고, local direct-origin 및 EC2 direct-origin 환경에서 migration 전후 payload checksum과 qlog path validation evidence가 일치했다. qlog에는 `PATH_CHALLENGE`/`PATH_RESPONSE`와 ALPN `h3` evidence가 관찰됐다.

따라서 본 연구의 출발점은 “CM은 구현되지 않았다”가 아니라, “구현체 primitive는 있으나 browser, deployment, application layer에서 같은 수준의 continuity claim을 만들 수 있는가”로 좁혀진다.

## RQ2. 배포 경로는 CM continuity를 유지하는가?

AWS NLB 실험은 deployment path가 CM 성숙도에 직접 영향을 준다는 점을 보였다. NLB `TCP_QUIC :443` 경로에서 QUIC-LB plaintext CID format과 target registration의 `QuicServerId`가 일치할 때, migration 이후에도 same-target continuity가 유지됐다. 반대로 malformed CID 또는 wrong Server ID 조건에서는 target health가 정상이어도 QUIC application payload가 실패했다.

이 결과는 CDN/LB 환경에서 HTTP/3 지원 여부만으로 end-to-end QUIC CM을 주장할 수 없음을 보여준다. connection ID routing, backend affinity, target protocol, qlog evidence를 함께 확인해야 한다.

## RQ3. HTTP/3 application task는 migration 후에도 완료되는가?

quic-go controlled client 환경에서는 HTTP/3 post-migration request continuity와 mid-flight upload/download continuity가 관찰됐다. local direct-origin과 AWS NLB `TCP_QUIC :443` 조건에서 1MiB upload/download workload가 manual retry 없이 완료됐고, qlog에는 H3 frame 및 path validation evidence가 남았다. 추가 local repetition에서는 mid-flight upload 3회와 download 3회가 모두 PASS였고, 각 case에서 client migration trigger, probe/switch success, socket B 전환, payload decode success가 확인됐다.

다만 이 결과는 custom controlled client 기준이다. browser policy, HTTP/3 discovery, certificate trust, application timer, page lifecycle이 개입하는 실제 웹 브라우저 환경으로 곧바로 일반화할 수 없다.

## RQ4. Chrome browser에서 HTTP/3 baseline과 workload evidence는 충분한가?

Chrome 149 headless forced-QUIC local origin에서는 단일 request, page+subresource sequence, polling, slow subresource, downlink-dominant streaming workload가 HTTP/3로 도달했다. server request log, Chrome NetLog, qlog가 application H3 evidence를 동시에 제공했다.

반면 natural Alt-Svc local control에서는 self-signed 또는 mkcert origin이 H3를 광고해도 실제 application request가 HTTP/3로 전환되지 않았다. 일부 경우 QUIC/H3 candidate evidence는 있었지만 certificate verification failure 또는 broken alternative service로 끝났다. public third-party endpoint에서는 H3 discovery 단서는 있었지만 application H3를 확정하기 어려웠다.

따라서 browser CM 실험은 반드시 controlled public WebPKI origin과 application H3 baseline gate를 먼저 통과해야 한다.

## RQ5. Browser-level CM evidence는 무엇을 요구하는가?

Chrome CDP downlink/heartbeat 대조군은 browser-level CM 판정에서 가장 중요한 해석상의 주의를 제공했다. no-change downlink without heartbeat에서는 server remote tuple과 Chrome target QUIC session이 각각 1개였다. 그러나 no-change downlink with heartbeat에서는 server remote tuple과 target QUIC session이 각각 2개가 됐다. inactive interface toggle 조건에서도 command exit은 0이었지만 client path snapshot은 `no_client_path_change_observed`였고 qlog path validation도 없었다.

추가로 local UDP rebinding proxy 실험에서는 Chrome forced-H3 traffic의 server-facing UDP socket을 A에서 B로 바꿨다. no-heartbeat 반복 3회는 모두 proxy packet log에서 A/B 양쪽 upstream으로 client packet이 전달됐고, server qlog와 Chrome target NetLog source 양쪽에서 PATH_CHALLENGE/PATH_RESPONSE 계열 evidence가 1/1로 관찰됐지만 request-level remote tuple은 하나로 남았다. heartbeat 반복 3회는 모두 packet rebinding, server remote tuple 2개, qlog/NetLog target path validation을 만들었지만 Chrome NetLog의 target QUIC session도 2개였다.

client-sending 방향의 streaming upload 대조군도 같은 경계를 보여준다. Chrome page가 streaming `fetch()`로 256KiB upload를 수행하는 동안 proxy rebinding을 3회 반복했고, 세 run 모두 proxy packet log에서 A/B upstream forwarding이 확인됐으며 upload는 완료됐다. Chrome target QUIC session은 1개로 유지됐고 server qlog 및 Chrome target NetLog source의 path validation frame evidence도 관찰됐다. 그러나 request-level server remote tuple은 여전히 하나로 남았다.

추가 timing-sensitivity 실험에서는 rebinding 시점을 early `500ms`와 late `5s`로 나누어 downlink 8회, upload 4회를 실행했다. 총 12회 모두 application task가 완료됐고, proxy packet rebinding, qlog path validation, Chrome target NetLog path-validation frame이 모두 관찰됐다. 다만 early 조건은 B upstream packet share가 downlink 평균 `0.618`, upload 평균 `0.800`으로 컸고, late 조건은 각각 `0.172`, `0.181`로 작았다. heartbeat downlink에서는 early 조건에서 remote tuple/session이 2개로 갈라졌지만, late 조건에서는 remote tuple은 1개인 채 Chrome target session만 2개로 관찰됐다. 이는 heartbeat/recovery 로직의 효과를 판단하려면 timing과 browser session attribution을 같이 봐야 함을 보여준다.

마지막으로 old-path-drop proxy control을 추가했다. proxy가 B upstream으로 전환된 뒤 A upstream의 server-to-client packet을 drop하도록 설정하고 downlink 1회, upload 1회를 실행했다. 두 run 모두 완료됐고 qlog 및 Chrome target NetLog path-validation frame이 관찰됐다. downlink에서는 switch 이후 drop할 A packet이 없었고, upload에서는 A-side server packet 21개를 drop했는데도 256KiB upload가 완료됐다. 그러나 upload run은 Chrome target QUIC session이 2개였으므로, old-path drop 조건에서 task가 완료됐다는 사실도 browser session continuity의 충분조건은 아니다.

즉, server가 본 source tuple 변화와 qlog path validation은 browser CM success의 충분조건이 아니며, 반대로 request-level tuple 변화가 없다고 해서 packet-level rebinding이나 path validation이 없었다고 단정할 수도 없다. packet forwarding log, qlog path validation, request-level tuple, Chrome NetLog session attribution은 서로 다른 계층의 증거다. heartbeat나 browser connection management만으로도 multiple QUIC sessions가 생길 수 있다. 본 연구의 classifier는 이를 `multiple_quic_sessions_without_network_change`, `multiple_quic_sessions_without_client_path_change`, `nat_rebinding_path_validation_without_observed_tuple_change`, `nat_rebinding_multiple_quic_sessions`처럼 분리한다.

후속 본 실험을 위해 Chrome, Safari, Android Chrome controlled public network-change harness를 각각 준비했다. 다만 browser observability matrix 기준으로 Chrome desktop만 NetLog 기반 session attribution을 제공한다. Safari와 Android Chrome은 현재 harness에서 browser-internal QUIC session log가 없으므로, 해당 결과는 server/qlog 중심의 `PASS_FEASIBILITY` 수준으로만 해석한다. 이 하네스 준비는 실제 handover 성공 결과가 아니다.

## 종합 결과

현재까지의 결과는 다음 결론을 지지한다.

1. QUIC CM primitive는 구현체와 controlled deployment에서 작동한다.
2. HTTP/3 application workload도 controlled client에서는 migration 후 완료될 수 있다.
3. LB/CDN/proxy 경로에서는 CID routing과 backend affinity가 success/failure를 좌우한다.
4. Browser 환경에서는 application H3 baseline, client active path change, qlog path validation, browser session continuity를 모두 확인해야 한다.
5. Tuple change나 NetLog mode event만으로는 CM success를 주장할 수 없다.

아직 지지하지 않는 결론은 다음이다.

1. Chrome 실제 Wi-Fi/LTE handover에서 HTTP/3 CM이 성공했다.
2. Safari에서 HTTP/3 CM이 성공했다.
3. Android Chrome 실제 Wi-Fi/LTE handover에서 HTTP/3 CM이 성공했다.
4. CDN managed edge 환경에서 end-to-end QUIC CM이 유지된다.
5. Service Worker나 application heartbeat가 실제 handover recovery를 개선한다.

이 다섯 가지는 controlled public origin, active secondary path, Android/Safari 관찰성, packet capture가 준비된 뒤 후속 실험으로 검증해야 한다.
