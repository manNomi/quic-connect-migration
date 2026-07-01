# ngtcp2 Runtime Trial Packet

Generated: `2026-07-01`

This public-safe packet turns the ngtcp2 gap into a reproducible runtime gate. It does not claim a runtime PASS unless the fail-closed runner records `validation=ok`.

## Summary

| field | value |
| --- | --- |
| implementation | `ngtcp2` |
| source commit | `c24b12690c5bdf7ad2715ae427504e76bf5c6ffc` |
| local clone observed | `True` |
| local clone commit | `c24b12690c5bdf7ad2715ae427504e76bf5c6ffc` |
| local clone matches audit commit | `yes` |
| libev | `4.33` |
| libnghttp3 | `1.16.0` |
| openssl | `3.6.2` |
| focused migration tests | `6/6 expected seen` |
| example ossl binary pair present | `yes` |
| runner exists | `True` |
| runner result env exists | `True` |
| runtime trial status | `ready_or_passed` |
| runtime trial reason | `runner_validation_ok` |
| can claim runtime PASS | `yes` |
| public safety scan | `ok` |

## Runner

| field | value |
| --- | --- |
| path | `harness/scripts/run-ngtcp2-example-migration-demo.sh` |
| result env | `harness/results/ngtcp2-example-migration-demo-local-20260701/results/result.env` |
| validation | `ok` |
| blocked or failed reason | `none` |
| client exit | `0` |
| client local address changes | `1` |
| client qlog count | `1` |
| server qlog count | `1` |
| path challenge count | `34` |
| path response count | `24` |
| payload size bytes | `4194304` |

## Evidence Table

| id | source | topic | observation | implication |
| --- | --- | --- | --- | --- |
| `examples-require-libev-nghttp3` | [README.rst:45](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/README.rst#L45) | `Example dependency gate` | The ngtcp2 README states that sources under examples require libev and nghttp3. | A runtime example-client/server migration row must record libev and nghttp3 readiness before claiming execution. |
| `examples-are-http3-client-server` | [README.rst:201](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/README.rst#L201) | `Example runtime scope` | The README says the built client and server executables live under examples and speak HTTP/3. | The examples are a legitimate runtime bridge between transport migration APIs and an HTTP/3 workload. |
| `openssl-example-binaries` | [README.rst:312](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/README.rst#L312) | `OpenSSL example binaries` | The examples list includes osslclient and osslserver as OpenSSL-backed client/server binaries. | A public-safe local runner can target osslclient/osslserver without adding a new ngtcp2 application. |
| `cmake-finds-example-dependencies` | [CMakeLists.txt:152](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/CMakeLists.txt#L152) | `CMake dependency discovery` | When ENABLE_LIB_ONLY is off, CMake searches for Libev and Libnghttp3. | Missing libev is an example-runtime readiness blocker rather than evidence that migration primitives are absent. |
| `cmake-example-required-flags` | [CMakeLists.txt:252](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/CMakeLists.txt#L252) | `Example dependency flags` | CMake records HAVE_LIBEV and HAVE_LIBNGHTTP3 as example requirements. | The trial packet can classify current local state before attempting a runtime run. |
| `ossl-example-build-condition` | [examples/CMakeLists.txt:414](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/examples/CMakeLists.txt#L414) | `osslclient/osslserver build gate` | osslclient and osslserver are built only when Libev, OpenSSL helper support, and Libnghttp3 are found. | The runtime row cannot be promoted until these dependency gates are open. |
| `example-active-versus-nat-rebinding` | [examples/client.cc:1347](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/examples/client.cc#L1347) | `Example migration trigger` | The example client calls ngtcp2_conn_initiate_immediate_migration when changing local address without --nat-rebinding. | The example can exercise active client migration semantics, not just passive NAT rebinding simulation. |
| `example-change-local-addr-flag` | [examples/client.cc:2015](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/examples/client.cc#L2015) | `CLI trigger` | The --change-local-addr option changes the client local address after handshake completion. | The runner has a documented trigger for a controlled post-handshake migration attempt. |
| `example-qlog-options` | [examples/client.cc:2047](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/examples/client.cc#L2047) | `qlog capture` | The example client supports qlog-file and qlog-dir output. | A future runtime PASS can be tied to path-validation frame evidence rather than exit code only. |
| `server-htdocs-qlog-options` | [examples/server.cc:2500](https://github.com/ngtcp2/ngtcp2/blob/c24b12690c5bdf7ad2715ae427504e76bf5c6ffc/examples/server.cc#L2500) | `HTTP/3 app and qlog capture` | The example server supports --htdocs and --qlog-dir. | The runner can use a minimal static HTTP/3 object and collect server-side qlog-derived evidence. |
| `fresh-focused-test-log` | [docs/results/implementation-rerun-results-20260630.md:279](https://github.com/manNomi/quic-connect-migration/blob/docs/quinn-neqo-rerun-20260630/docs/results/implementation-rerun-results-20260630.md#L279) | `Fresh local migration tests` | The study records six focused ngtcp2 migration/path-validation tests passing at the audited commit. | The current missing runtime row is an example dependency/runtime gap, not an absence of migration tests. |

## Claim Boundary

- Safe claim: ngtcp2 has strong C-library migration/path-validation API and focused test evidence, and the official osslclient/osslserver HTTP/3 example completed a local migration runtime row with client exit 0, local-address-change evidence, and qlog-derived PATH_CHALLENGE/PATH_RESPONSE counters.
- Unsafe claim: ngtcp2 browser handover, CDN/LB deployment continuity, production app continuity, or equivalence to quic-go's custom AddPath/Probe/Switch control surface.
- Next gap: Use this as a second C-library runtime positive control; repeat on a clean host or Linux builder only if reviewers require independent replication, while browser/deployment rows remain separate gates.

## Interpretation

1. ngtcp2 should stay above source-only status because public migration APIs and focused local migration/path-validation tests are already present.
2. The official ngtcp2 HTTP/3 examples now add a local runtime positive row: the client changed local address, completed the payload request, and produced qlog-derived path-validation frame evidence.
3. This upgrades ngtcp2 to a second C-library runtime positive control, while browser, CDN/LB, and production application continuity still require separate rows.
