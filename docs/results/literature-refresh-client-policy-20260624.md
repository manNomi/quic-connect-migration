# Literature refresh: client policy and evidence interpretation

작성일: 2026-06-24

## 1. 목적

Chrome CDP downlink/heartbeat 대조군에서 network-change가 없어도 multiple QUIC sessions/source tuples가 관찰됐다.

따라서 이번 refresh는 다음 질문에 집중했다.

1. browser/app client에서 CM은 transport primitive만으로 켜지는가, 아니면 client policy가 필요한가?
2. multiple QUIC sessions와 connection migration evidence를 어떻게 분리해야 하는가?
3. CM의 연구 가치는 handover 외에 어디에 있는가?

## 2. 추가 확인한 자료

| source | 핵심 내용 | 우리 연구에 주는 의미 |
| --- | --- | --- |
| [Android Cronet ConnectionMigrationOptions](https://developer.android.com/develop/connectivity/cronet/reference/org/chromium/net/ConnectionMigrationOptions) | Cronet은 connection migration을 별도 option class로 노출한다. 설명상 QUIC connection과 server support가 필요하고, Wi-Fi/cellular 전환 같은 L4 connectivity 변화가 대상이다. | Android/Cronet 후속 실험은 단순 Chrome UI 테스트와 별도로 client policy 설정을 명시해야 한다. |
| [Chromium QuicParams](https://chromium.googlesource.com/chromium/src/+/master/net/quic/quic_context.h) | Chromium에는 network-change migration, path-degrading migration, idle migration, port migration, IP change 시 close/goaway 같은 정책 flag가 존재한다. | “브라우저가 QUIC을 쓴다”와 “브라우저가 CM을 시도한다”는 별개다. NetLog/session/config evidence가 필요하다. |
| [MIMIQ](https://www.usenix.org/conference/foci20/presentation/govil) | QUIC migration은 physical network handover뿐 아니라 IP masking/privacy에도 활용될 수 있음을 보인다. | CM의 가치는 “작업 연속성” 외에도 privacy/security use case가 있다. 논문 related work에서 CM의 broader motivation으로 쓸 수 있다. |
| [QUIC Applicability draft](https://quicwg.org/ops-drafts/draft-ietf-quic-applicability.html) | QUIC을 application protocol에 적용할 때 endpoint discovery, migration, connection ID exposure 등 caveat를 고려해야 한다. | 논문에서 application-level continuity와 deployment caveat를 다루는 방향을 뒷받침한다. 단, Internet-Draft라 normative 근거로 쓰지는 않는다. |

## 3. 현재 실험과 연결

Chrome CDP 대조군 결과:

| condition | result |
| --- | --- |
| downlink no heartbeat | single target QUIC session, single server remote tuple |
| downlink heartbeat | two target QUIC sessions, two server remote tuples, no qlog path validation |
| inactive interface toggle + heartbeat | command exit 0, client path unchanged, two target QUIC sessions, no qlog path validation |

해석:

- client/application behavior가 QUIC session 수를 바꿀 수 있다.
- 따라서 server tuple 변화는 필요한 단서일 수 있지만 충분조건은 아니다.
- browser CM claim은 client path change, qlog PATH_CHALLENGE/PATH_RESPONSE, browser session continuity를 함께 요구해야 한다.

## 4. 논문 방향 보정

기존 질문:

> 좋은 기술인데 왜 안 쓰이는가?

보정된 질문:

> QUIC CM primitive가 존재함에도 browser/web deployment에서 HTTP/3 작업 연속성 claim을 만들기 어려운 이유는 무엇인가?

현재 답:

1. 구현체 primitive와 browser/client policy는 다르다.
2. HTTP/3 discovery/application H3 baseline과 CM 시도는 다르다.
3. tuple 변화와 multiple sessions는 CM evidence가 아니다.
4. deployment routing과 CID affinity가 CM success를 좌우한다.
5. application workload가 client-silent인지 heartbeat/polling인지에 따라 관측과 recovery가 달라진다.

## 5. 다음 action

| action | 이유 |
| --- | --- |
| Android Cronet sample or test app 조사 | ConnectionMigrationOptions를 설정할 수 있어 browser Chrome보다 policy control이 명확할 수 있음 |
| Chromium NetLog event parser 보강 | `QUIC_CONNECTION_MIGRATION_SUCCESS`, trigger events, session source ids를 더 정확히 분리 |
| controlled public CDP downlink experiment | local forced-QUIC artifact를 public WebPKI/natural H3 조건으로 확장 |
| Safari packet/qlog plan | Safari는 NetLog equivalent가 없으므로 packet capture와 server qlog 중심으로 evidence chain 필요 |
