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

마지막으로 old-path-drop proxy control을 반복했다. proxy가 B upstream으로 전환된 뒤 A upstream의 server-to-client packet을 drop하도록 설정하고 downlink 7회, upload 4회를 실행했다. 총 11회 모두 완료됐고 qlog 및 Chrome target NetLog path-validation frame이 관찰됐다. downlink에서는 switch 이후 drop할 A packet이 없었지만, upload 4회에서는 A-side server packet 총 60개를 drop했는데도 매번 256KiB upload가 완료됐다. 특히 반복 upload 3회는 Chrome target QUIC session도 1개로 유지됐다. 반면 heartbeat downlink 3회는 여전히 multiple session으로 갈라져, old-path drop 조건에서도 heartbeat 기반 회복/관측은 session attribution과 함께 해석해야 한다.

old-path-drop stress matrix에서는 같은 조건을 1MiB/4MiB workload로 확장했다. downlink 3회와 upload 2회, 총 5회 모두 완료됐고 qlog 및 Chrome target NetLog path validation이 5/5로 관찰됐다. Upload는 1MiB와 4MiB가 모두 server의 `/upload-sink`에 도달해 총 5MiB가 수신됐고, 전체 stress row에서 A-side server packet 105개, 74279 bytes가 drop됐다. no-heartbeat downlink와 upload는 Chrome target QUIC session 1개로 유지됐지만, 1MiB heartbeat downlink는 여전히 target session 2개로 갈라졌다. 따라서 stress 조건에서도 핵심 결론은 같다. 로컬 NAT rebinding과 old-path-unavailable 상황에서 작업 완료는 가능하지만, 실제 browser handover claim은 active client path change와 browser session continuity까지 확인해야 한다.

마지막으로 return-path drop control을 추가했다. B-side server-to-client packet만 drop한 1MiB downlink/upload 2회는 모두 완료됐다. 이때 server B packet 18개가 drop됐지만 server A packet이 계속 전달되어 old return path가 작업을 살렸다. 반대로 A와 B의 server-to-client packet을 모두 drop한 1MiB downlink/upload 2회는 모두 `browser_application_task_failed`로 실패했다. 두 실패 row 모두 server request, qlog H3/path frame, Chrome QUIC session evidence가 있었지만 DOM application completion은 false였다. 따라서 transport-level evidence가 있어도 return path availability가 없으면 웹 작업 연속성은 깨질 수 있으며, 이 때문에 본 연구의 final protocol은 application completion을 독립 기준으로 둔다.

이를 duration sweep으로 확장한 transient return-path outage 실험에서는 A+B server-to-client packet drop을 250ms, 1500ms, 3000ms, 4000ms, 5000ms, 6000ms, 9000ms window로 제한했다. 1MiB downlink/upload workload 기준 250ms/1500ms/3000ms/4000ms는 8/8 PASS였고, 5000ms/6000ms/9000ms는 6/6 FAIL이었다. PASS row의 DOM 완료 시간은 약 7.5초에서 11.3초 사이였고, FAIL row는 약 6.9초에서 11.1초 사이에 DOM error timing을 남겼다. 모든 row에서 proxy switch와 qlog H3/path evidence는 남았으므로, local browser workload continuity는 단순히 path frame 존재 여부가 아니라 outage duration, retransmission 가능성, browser task timer의 조합으로 결정된다고 해석해야 한다. 이 local 1MiB Chrome forced-H3 workload의 관찰 경계는 4초와 5초 사이였다.

그러나 boundary repetition은 이 경계가 단일한 절단점이 아님을 보여줬다. 4000ms, 4500ms, 5000ms window를 downlink/upload 각각 3회 반복한 18개 row에서 4000ms와 4500ms는 각각 6/6 PASS였고, 5000ms는 downlink 3/3 PASS와 upload 0/3 PASS로 갈렸다. 완료 row의 DOM complete timing은 10.2초에서 13.9초 사이였고, 실패 row의 DOM error timing은 6.921초에서 6.922초로 매우 좁았다. 따라서 5초 근처에서는 "CM이 된다/안 된다"가 아니라 workload direction, browser task timer, retransmission timing이 맞물린 transition zone으로 논문 결과를 표현해야 한다.

Downlink-only fine boundary는 이 transition zone이 단조 threshold가 아님을 더 명확히 보여줬다. 5000ms와 5500ms window는 각각 2/3 PASS로 혼재했고, 6000ms는 3/3 FAIL이었다. PASS row는 12.276-14.114초에 완료됐고, FAIL row는 6.922-6.927초에 실패했다. 모든 row에 qlog H3/path evidence가 남았으므로, downlink에서도 transport-level path evidence와 DOM-level task completion을 분리해야 한다.

Upload workload의 transition을 더 좁히기 위해 4600ms, 4750ms, 4900ms, 5000ms window를 각각 3회 반복했다. 4600ms upload는 3/3 PASS였고, 4750ms는 1/3 PASS로 갈렸으며, 4900ms와 5000ms는 6/6 FAIL이었다. 이 결과는 local 1MiB upload workload에서 안정 완료 구간이 4600ms까지, 불안정 transition이 4750ms부터, 반복 실패 구간이 4900ms부터 나타난다는 것을 보여준다. 모든 실패 row가 qlog H3/path evidence를 남겼으므로, 이 fine boundary도 transport-level path evidence가 application-level upload continuity를 보장하지 않는다는 결론을 강화한다.

두 fine-boundary control을 종합한 workload transition-zone table은 downlink가 5000ms/5500ms에서 혼재 후 6000ms에서 반복 실패하고, upload가 4750ms부터 혼재 후 4900ms에서 반복 실패한다는 차이를 보여준다. 따라서 본 연구의 continuity metric은 단일 outage-duration threshold가 아니라 workload direction별 transition zone으로 보고되어야 한다.

Downlink에도 같은 application-level recovery 관점을 적용하기 위해 6000ms/9000ms outage에서 1회 stream retry control을 실행했다. 두 window 모두 3/3 PASS였고 DOM complete timing은 15.487-21.713초였다. 그러나 6개 row 중 3개는 `retries_used=0`, Chrome target QUIC session 1개로 첫 stream이 늦게 완료됐고, 나머지 3개는 `retries_used=1`, Chrome target QUIC session 2개로 retry 후 완료됐다. 따라서 downlink recovery 결과는 단순히 "retry가 성공했다"가 아니라, retransmission-only completion과 retry/multiple-session recovery가 같은 조건 안에서 혼재한다는 근거로 해석해야 한다.

마지막으로 같은 4900ms/5000ms upload 실패 구간에서 application-level retry control을 실행했다. 브라우저 upload page가 첫 `fetch()` 실패 후 1000ms 뒤 새 스트림으로 한 번 재시도하도록 설정하자 6개 row가 모두 PASS였고, 각 row에서 `/upload-sink` request가 2개씩 기록됐으며 최종 1MiB body가 수신됐다. 그러나 6개 row 모두 Chrome target QUIC session count가 2였고 classification은 `nat_rebinding_multiple_quic_sessions`였다. 따라서 이 결과는 "CM이 성공했다"가 아니라, "application-level retry가 사용자 작업 완료를 회복할 수 있지만 transport/browser session continuity와는 별도로 보고해야 한다"는 근거다.

Retry control을 더 긴 6000ms/9000ms outage로 확장했을 때도 6개 row가 모두 PASS였다. 6000ms row의 DOM complete timing은 약 15.5초였고, 9000ms row는 약 19.7초였다. 다만 Chrome target QUIC session count는 2-3개로 관찰됐다. 이는 retry가 더 긴 outage에서도 task completion을 회복할 수 있지만, 그 대가는 증가한 completion latency와 replacement/multiple-session behavior라는 점을 보여준다. 따라서 application-level recovery는 CM 성숙도 평가의 보조 축이지, browser CM success의 대체 지표가 아니다.

마지막 stress boundary에서는 12000ms/15000ms outage를 반복했다. 12000ms retry upload는 3/3 PASS였고 DOM complete timing은 약 20.0초였다. 반면 15000ms retry upload는 3/3 FAIL이었고 DOM error timing은 약 15.94초였으며, 두 번째 `/upload-sink` request가 서버에 도달하지 못해 upload bytes도 0이었다. 실패 row에도 qlog H3/path evidence와 Chrome target QUIC session evidence는 남았다. 따라서 1회 retry도 무제한 보장이 아니며, 이 local 1MiB upload workload의 one-retry recovery boundary는 12초와 15초 사이로 관찰됐다.

그 실패 구간을 재검수하기 위해 동일한 15000ms outage에서 application-level retry를 2회로 늘렸다. 세 번의 반복 모두 PASS였고 최종 1MiB body가 수신됐지만, DOM complete timing은 24.484-24.503초로 늘었으며 Chrome target QUIC session count는 모두 4였다. 따라서 retry 횟수를 늘리면 더 긴 outage에서도 사용자 작업 완료를 회복할 수 있지만, 이 회복은 replacement/multiple-session behavior와 큰 지연을 동반한다. 이 결과는 "CM이 충분히 성숙하다"는 근거가 아니라, browser CM이 애플리케이션 작업 연속성으로 전달되지 않는 구간에서 application-level recovery가 별도 설계 축이 되어야 한다는 근거다.

2회 retry의 failure side를 찾기 위해 18000ms/21000ms outage를 추가로 반복했다. 18000ms row는 3/3 PASS였고 DOM complete timing은 28.196-28.199초였다. 반면 21000ms row는 3/3 FAIL이었고 DOM error timing은 20.950-20.955초로 모였다. 실패 row에도 qlog H3/path evidence와 Chrome target QUIC session count 4가 남았지만 `/upload-sink`는 한 번만 서버에 도달했고 upload bytes는 0이었다. 따라서 retry budget 증가는 failure boundary를 15초에서 18초까지 밀었지만, 21초에서는 다시 application task continuity가 깨졌다.

이 upload boundary control들을 종합하면 no-retry의 안정 완료 구간은 4600ms까지, 1회 retry의 안정 완료 구간은 12000ms까지, 2회 retry의 안정 완료 구간은 18000ms까지 확장됐다. 그러나 최신 all-pass window의 DOM completion timing도 약 10.2초, 20.0초, 28.2초로 증가했고 Chrome target QUIC session count는 1개, 3개, 4개로 증가했다. 즉 application-level recovery는 작업 완료율을 개선하지만, 그 자체가 browser CM 성숙도를 증명하지는 않으며 recovery latency와 session churn을 함께 보고해야 한다.

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
5. Service Worker, application heartbeat, 또는 upload retry가 실제 handover recovery를 개선한다.

이 다섯 가지는 controlled public origin, active secondary path, Android/Safari 관찰성, packet capture가 준비된 뒤 후속 실험으로 검증해야 한다.
