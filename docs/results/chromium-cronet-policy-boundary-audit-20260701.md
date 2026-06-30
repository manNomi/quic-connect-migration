# Chromium/Cronet Policy Boundary Audit

Generated: `2026-06-30`

This public-safe audit tightens the browser/client part of the implementation survey. Chromium/Cronet is high-impact because Chrome and Android clients matter, but the source evidence must be separated from live browser handover evidence.

## Summary

| field | value |
| --- | --- |
| implementation | `Chromium Chrome Cronet` |
| source repository | [https://chromium.googlesource.com/chromium/src](https://chromium.googlesource.com/chromium/src) |
| source commit | `fd49b92dc0dc7d4353e2e79ad155e43ca7947ab7` |
| evidence items | `13` |
| socket migration hook present | `yes` |
| network-change policy knobs present | `yes` |
| NetLog migration observability present | `yes` |
| Cronet network-change migration default | `disabled_when_quic_enabled` |
| Android Cronet policy API present | `yes` |
| browser runtime handover proven here | `no` |
| interpretation | Chromium/Cronet weakens an implementation-absence explanation because source hooks, policy knobs, and NetLog events exist; it strengthens the runtime-policy explanation because Cronet explicitly disables network-change migration by default in the inspected path. |

## Conclusion

| claim axis | result |
| --- | --- |
| transport implementation | `client_stack_has_internal_migration_primitives` |
| runtime policy | `policy_dependent_and_embedding_specific` |
| observability | `NetLog_can_expose_mode_trigger_success_failure_and_probing_events` |
| Cronet boundary | `network_change_migration_disabled_by_default_in_url_request_context_config` |
| paper use | Use Chromium/Cronet as a high-usage client policy-boundary audit, not as proof that Chrome or Cronet migrated a live HTTP/3 browser workload. |

## Evidence Table

| id | source | topic | observation | implication |
| --- | --- | --- | --- | --- |
| `quicparams-default-network-migration-policy` | [net/quic/quic_context.h:176-184](https://chromium.googlesource.com/chromium/src/+/fd49b92dc0dc7d4353e2e79ad155e43ca7947ab7/net/quic/quic_context.h#176) | `QuicParams network-change migration flags` | QuicParams includes migrate_sessions_on_network_change_v2 and migrate_sessions_early_v2 fields for network-change and poor-path migration policy. | Chromium has browser-stack policy knobs for migration; support is not a missing primitive. |
| `quicparams-idle-and-port-migration-policy` | [net/quic/quic_context.h:186-194](https://chromium.googlesource.com/chromium/src/+/fd49b92dc0dc7d4353e2e79ad155e43ca7947ab7/net/quic/quic_context.h#186) | `Idle and port migration flags` | QuicParams includes migrate_idle_sessions and allow_port_migration fields that control idle-session and port-change behavior. | Migration behavior is intentionally configurable rather than universally enabled. |
| `client-session-migrate-to-socket` | [net/quic/quic_chromium_client_session.h:930-936](https://chromium.googlesource.com/chromium/src/+/fd49b92dc0dc7d4353e2e79ad155e43ca7947ab7/net/quic/quic_chromium_client_session.h#930) | `QuicChromiumClientSession::MigrateToSocket` | QuicChromiumClientSession declares MigrateToSocket with new socket reader/writer ownership. | The Chrome client stack has an internal socket migration primitive. |
| `client-session-network-connected-callback` | [net/quic/quic_chromium_client_session.h:938-941](https://chromium.googlesource.com/chromium/src/+/fd49b92dc0dc7d4353e2e79ad155e43ca7947ab7/net/quic/quic_chromium_client_session.h#938) | `Network connected callback` | OnNetworkConnected can migrate a session to a newly connected network when pending migration exists. | Network-change notifications can drive migration decisions inside the browser stack. |
| `client-session-disconnected-default-callbacks` | [net/quic/quic_chromium_client_session.h:943-949](https://chromium.googlesource.com/chromium/src/+/fd49b92dc0dc7d4353e2e79ad155e43ca7947ab7/net/quic/quic_chromium_client_session.h#943) | `Disconnected and default-network callbacks` | The session class has callbacks for disconnected networks and new default networks, including a comment that migration occurs if appropriate. | A browser handover claim must prove that the runtime policy actually chose these paths. |
| `client-session-path-degrading-callback` | [net/quic/quic_chromium_client_session.h:797-805](https://chromium.googlesource.com/chromium/src/+/fd49b92dc0dc7d4353e2e79ad155e43ca7947ab7/net/quic/quic_chromium_client_session.h#797) | `Path degrading callback` | QuicChromiumClientSession overrides OnPathDegrading and related forward-progress callbacks. | Chromium can react to path-quality degradation, not only hard interface loss. |
| `netlog-migration-mode-trigger` | [net/log/net_log_event_type_list.h:3168-3177](https://chromium.googlesource.com/chromium/src/+/fd49b92dc0dc7d4353e2e79ad155e43ca7947ab7/net/log/net_log_event_type_list.h#3168) | `NetLog migration mode and trigger events` | NetLog defines QUIC_CONNECTION_MIGRATION_MODE and QUIC_CONNECTION_MIGRATION_TRIGGERED events. | Mode evidence is useful but must be paired with trigger/session evidence before claiming migration. |
| `netlog-migration-success-failure` | [net/log/net_log_event_type_list.h:3179-3192](https://chromium.googlesource.com/chromium/src/+/fd49b92dc0dc7d4353e2e79ad155e43ca7947ab7/net/log/net_log_event_type_list.h#3179) | `NetLog migration failure and success events` | NetLog defines QUIC_CONNECTION_MIGRATION_FAILURE and QUIC_CONNECTION_MIGRATION_SUCCESS. | A strong browser artifact should contain success/failure evidence for the target session. |
| `netlog-network-change-events` | [net/log/net_log_event_type_list.h:3194-3228](https://chromium.googlesource.com/chromium/src/+/fd49b92dc0dc7d4353e2e79ad155e43ca7947ab7/net/log/net_log_event_type_list.h#3194) | `NetLog network-change migration events` | NetLog defines events for connected network, new default network, disconnected network, write error, waiting for a network, and path degrading. | Classifier logic should require event-chain evidence rather than tuple-change-only inference. |
| `netlog-probing-events` | [net/log/net_log_event_type_list.h:3237-3247](https://chromium.googlesource.com/chromium/src/+/fd49b92dc0dc7d4353e2e79ad155e43ca7947ab7/net/log/net_log_event_type_list.h#3237) | `NetLog probing success/failure events` | NetLog defines post-probing migration success, failure, and waiting-for-network timeout events. | Browser CM maturity includes observability for failed attempts, not just completed migrations. |
| `cronet-explicitly-disables-network-change-migration` | [components/cronet/url_request_context_config.cc:918-924](https://chromium.googlesource.com/chromium/src/+/fd49b92dc0dc7d4353e2e79ad155e43ca7947ab7/components/cronet/url_request_context_config.cc#918) | `Cronet default network-change migration policy` | When QUIC is enabled, Cronet sets goaway_sessions_on_ip_change=false but explicitly sets migrate_sessions_on_network_change_v2=false. | Chromium-derived clients can suppress network-change migration by default, so Chrome, Cronet embedding, and Android platform behavior must be tested separately. |
| `android-cronet-connection-migration-options` | [ConnectionMigrationOptions](https://developer.android.com/develop/connectivity/cronet/reference/org/chromium/net/ConnectionMigrationOptions) | `Cronet migration policy API` | The Android Cronet API exposes ConnectionMigrationOptions so applications can configure migration-related behavior. | Cronet migration is an embedding policy question, not a guaranteed browser-runtime outcome. |
| `android-platform-connection-migration-options-builder` | [android.net.http.ConnectionMigrationOptions.Builder](https://developer.android.com/reference/android/net/http/ConnectionMigrationOptions.Builder) | `Platform HTTP stack migration policy API` | The Android platform API exposes a builder for connection migration options. | Android browser/app experiments must record client policy, platform stack, and defaults. |

## Reporting Boundary

- Safe claim: Chromium/Cronet has migration hooks, policy knobs, and NetLog observability; Cronet's inspected default path disables network-change migration when QUIC is enabled.
- Unsafe claim: Chrome browser, Android platform HTTP, or a Cronet-embedded app successfully performs single-session HTTP/3 Connection Migration in a live handover based on source hooks alone.
- Next non-iPhone gate: When a non-iPhone secondary path or Android/Cronet device path is available, run a Chrome/Cronet active network-change trial and require target-session NetLog trigger/success, client path change, server tuple/qlog evidence, and workload completion.

## Paper Interpretation

1. Chromium/Cronet is too important to omit from the implementation survey because Chrome/Android client usage dominates the real deployment question.
2. The source evidence shows migration capability and observability, so a pure `not implemented` explanation is too weak.
3. Cronet's default policy boundary explains why a good transport mechanism can remain invisible to applications: a client runtime may deliberately suppress migration.
4. The next defensible browser claim requires runtime artifacts, especially target-session NetLog trigger/success/failure evidence paired with server/qlog and workload completion evidence.
