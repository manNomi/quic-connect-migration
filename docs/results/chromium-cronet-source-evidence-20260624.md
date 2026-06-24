# Chromium/Cronet Connection Migration source evidence

작성일: 2026-06-24
목적: Chrome/Cronet 계층에서 QUIC Connection Migration을 해석할 때, 구현 primitive와 runtime policy를 구분하기 위한 source-level 근거를 정리한다.

## 1. 확인한 primary source

| source | 관찰 |
| --- | --- |
| [QuicChromiumClientSession](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/net/quic/quic_chromium_client_session.h) | socket migration, network connected/disconnected/default callbacks, path-degrading migration hooks가 존재한다. |
| [NetLog event type list](https://chromium.googlesource.com/chromium/src/+/HEAD/net/log/net_log_event_type_list.h) | QUIC migration mode, trigger, success, failure, platform notification, probing 관련 event type이 정의되어 있다. |
| [Cronet URLRequestContextConfig](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/components/cronet/url_request_context_config.cc) | QUIC enabled 시 Cronet path에서 network-change migration을 명시적으로 disable한다. |

## 2. 핵심 관찰

### 2.1 Chromium client session에는 migration hook이 있다

`QuicChromiumClientSession` source에는 `MigrateToSocket(...)`가 있고, network-change callback도 있다. source comment 기준으로 새 network connected, disconnected network, new default network event가 session migration 판단에 연결된다.

또한 path degrading, write error, alternate network probing, migrate-back-to-default-network 같은 helper가 존재한다. 따라서 Chrome stack에 migration primitive가 없다고 말하면 안 된다.

### 2.2 NetLog에는 migration 관찰 event가 있다

Chromium NetLog event type에는 다음 계열이 있다.

- `QUIC_CONNECTION_MIGRATION_MODE`
- `QUIC_CONNECTION_MIGRATION_TRIGGERED`
- `QUIC_CONNECTION_MIGRATION_SUCCESS`
- `QUIC_CONNECTION_MIGRATION_FAILURE`
- `QUIC_CONNECTION_MIGRATION_ON_NETWORK_CONNECTED`
- `QUIC_CONNECTION_MIGRATION_ON_NETWORK_MADE_DEFAULT`
- `QUIC_CONNECTION_MIGRATION_ON_NETWORK_DISCONNECTED`
- `QUIC_CONNECTION_MIGRATION_FAILURE_AFTER_PROBING`
- `QUIC_CONNECTION_MIGRATION_SUCCESS_AFTER_PROBING`

따라서 Chrome 실험에서 `QUIC_CONNECTION_MIGRATION_MODE`만 보인 경우는 migration 가능 mode/configuration evidence로만 해석해야 한다. 실제 migration 발생을 주장하려면 trigger/success/probing event, server tuple change, qlog path validation이 함께 필요하다.

### 2.3 Cronet은 runtime policy가 다르다

Cronet `URLRequestContextConfig`는 QUIC enabled 경로에서 `goaway_sessions_on_ip_change=false`를 설정하면서도 `migrate_sessions_on_network_change_v2=false`를 설정한다. source comment도 network-change migration을 명시적으로 disable한다고 설명한다.

따라서 "Chromium 기반이면 Connection Migration이 된다"는 식의 일반화는 위험하다. Chrome browser, Android platform HTTP stack, Cronet app embedding은 policy와 default가 다를 수 있다.

## 3. 현재 실험과의 연결

우리 Chrome local/Wi-Fi-IP 실험에서는 다음이 관찰됐다.

- target `QUIC_SESSION`은 생성됐다.
- target `HTTP_STREAM_JOB`은 `using_quic=true`였다.
- `QUIC_CONNECTION_MIGRATION_MODE`는 관찰됐다.
- 하지만 server tuple change와 qlog `PATH_CHALLENGE`/`PATH_RESPONSE`는 없었다.

따라서 classifier가 `no_path_change_baseline`을 반환한 것은 source-level 기대와도 일치한다. mode event만으로 migration 발생을 판정하지 않는 것이 맞다.

## 4. 논문상 의미

Chrome/Cronet 계층은 다음처럼 정리할 수 있다.

> Browser/client stack에는 QUIC migration primitive와 observability hook이 존재한다. 그러나 runtime policy와 embedding default가 실제 migration 사용 여부를 결정한다. 따라서 browser-level CM 성숙도는 source support, NetLog observability, runtime trigger, application workload success를 분리해 검증해야 한다.

이 source evidence는 후속 Android/Cronet 실험의 필요성을 강화한다.
