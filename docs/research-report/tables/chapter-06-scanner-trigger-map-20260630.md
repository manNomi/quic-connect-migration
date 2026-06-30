# Chapter 6 Scanner Trigger Map

작성일: `2026-06-30`

이 표는 Chapter 6 local Chrome NAT rebinding control에서 어떤 코드가 어떤 evidence를 만드는지 line-level로 정리한다.

## 1. UDP Rebinding Proxy

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [udprebindproxy/main.go#L18-L46](../../../repro/quic-go-min-repro/cmd/udprebindproxy/main.go#L18-L46) | proxy result schema | upstream A/B, switch/drop counters, byte counters | proxy artifact field 정의 |
| [udprebindproxy/main.go#L94-L105](../../../repro/quic-go-min-repro/cmd/udprebindproxy/main.go#L94-L105) | `--switch-after`, `--drop-a-server-after-switch`, `--drop-b-server-after-switch`, bounded drop windows | proxy control options | rebinding과 return-path drop 조건 |
| [udprebindproxy/main.go#L156-L171](../../../repro/quic-go-min-repro/cmd/udprebindproxy/main.go#L156-L171) | two upstream UDP sockets | `upstream_a_addr`, `upstream_b_addr` | A/B upstream 분리 |
| [udprebindproxy/main.go#L221-L247](../../../repro/quic-go-min-repro/cmd/udprebindproxy/main.go#L221-L247) | A/B server-to-client drop active 여부 | `dropped_server_packets_a/b`, JSONL drop events | return-path loss control |
| [udprebindproxy/main.go#L283-L306](../../../repro/quic-go-min-repro/cmd/udprebindproxy/main.go#L283-L306) | first client packet 이후 `switchAfter` 경과 | client-to-server upstream A -> B 전환, `client_to_server` JSONL | packet-level rebinding trigger |

## 2. Runner

| 코드 위치 | trigger/input | 생성 artifact | 해석 |
| --- | --- | --- | --- |
| [run-chrome-h3-rebinding-proxy.sh#L27-L109](../../../repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh#L27-L109) | workload switch: downlink/poll/media/buffered-media/range/upload | request path, expected request count | workload별 DOM/application condition |
| [run-chrome-h3-rebinding-proxy.sh#L138-L149](../../../repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh#L138-L149) | H3 server start, proxy build | server/qlog/proxy binary | local H3 origin 준비 |
| [run-chrome-h3-rebinding-proxy.sh#L150-L172](../../../repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh#L150-L172) | proxy args and drop options | proxy JSON/JSONL artifact | rebinding/drop control 실행 |
| [run-chrome-h3-rebinding-proxy.sh#L189-L199](../../../repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh#L189-L199) | Chrome CDP runner with forced QUIC and NetLog | Chrome NetLog, DOM dump | browser artifact 생성 |
| [run-chrome-h3-rebinding-proxy.sh#L212-L219](../../../repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh#L212-L219) | classifier invocation | `results/chrome-summary.json` | 판정은 classifier에 위임 |
| [run-chrome-h3-rebinding-proxy.sh#L221-L249](../../../repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy.sh#L221-L249) | proxy result merged into summary | `rebinding_proxy` field | classifier summary에 proxy counters 결합 |

## 3. Matrix Runners

| 코드 위치 | trigger/input | 생성 결과 | 해석 |
| --- | --- | --- | --- |
| [run-chrome-h3-rebinding-proxy-matrix.sh#L28-L61](../../../repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy-matrix.sh#L28-L61) | heartbeat false/true x repeat count | repetition matrix runs | heartbeat가 session attribution에 미치는 영향 |
| [run-chrome-h3-rebinding-proxy-matrix.sh#L63-L65](../../../repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-proxy-matrix.sh#L63-L65) | matrix artifact dirs | markdown/CSV summary | repetition summary 생성 |
| [run-chrome-h3-rebinding-transient-return-path-sweep.sh#L79-L101](../../../repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-transient-return-path-sweep.sh#L79-L101) | A+B drop enabled with bounded windows | transient outage run | return-path outage duration control |
| [run-chrome-h3-rebinding-transient-return-path-sweep.sh#L106-L123](../../../repro/quic-go-min-repro/scripts/run-chrome-h3-rebinding-transient-return-path-sweep.sh#L106-L123) | 250/1500/3000/4000/5000/6000/9000ms windows | broad boundary summary | initial transition zone |

## 4. H3 Server And Browser Workload

| 코드 위치 | trigger/input | artifact | 해석 |
| --- | --- | --- | --- |
| [h3server/main.go#L122-L169](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L122-L169) | qlog dir, TLS config, quic config with tracer | qlog, keylog, request result | transport/application evidence |
| [h3server/main.go#L187-L220](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L187-L220) | request handler | `remote_addr`, `proto`, `tls_alpn`, workload, byte counts | server-side request evidence |
| [h3server/main.go#L672-L740](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L672-L740) | `/browser-downlink`, `/browser-upload` | DOM workload page | browser task condition |
| [h3server/main.go#L1000-L1004](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L1000-L1004) | downlink DOM data attributes | `data-downlink-complete`, elapsed/error fields | classifier DOM completion source |
| [h3server/main.go#L1010-L1027](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L1010-L1027) | upload streaming fetch and DOM data attributes | `data-upload-complete`, response bytes, elapsed/error fields | upload task completion source |

## 5. Classifier And Summarizer

| 코드 위치 | trigger/input | 출력 | 해석 |
| --- | --- | --- | --- |
| [classify_chrome_h3_artifacts.py#L247-L290](../../../tools/classify_chrome_h3_artifacts.py#L247-L290) | request/server tuple/qlog/NetLog/proxy/DOM | classification labels | browser task failure, multiple sessions, path validation 분리 |
| [summarize_chrome_rebinding_timing_sensitivity.py#L79-L119](../../../tools/summarize_chrome_rebinding_timing_sensitivity.py#L79-L119) | early/late run specs and artifact dirs | row fields for timing summary | B packet share, qlog/NetLog path evidence |
| [summarize_chrome_rebinding_timing_sensitivity.py#L146-L219](../../../tools/summarize_chrome_rebinding_timing_sensitivity.py#L146-L219) | summary rows | markdown aggregate/run table | timing-sensitive interpretation boundary |
| [summarize_chrome_rebinding_transient_return_path_sweep.py#L124-L178](../../../tools/summarize_chrome_rebinding_transient_return_path_sweep.py#L124-L178) | transient artifact dirs | status, DOM, qlog, proxy drop, upload bytes | transient outage row extraction |
| [summarize_chrome_rebinding_transient_return_path_sweep.py#L200-L210](../../../tools/summarize_chrome_rebinding_transient_return_path_sweep.py#L200-L210) | PASS/FAIL windows | local boundary summary | monotonic threshold 과장 방지 |

## 6. False-Positive Guards

| guard | 코드 근거 | 방지하는 오해 |
| --- | --- | --- |
| proxy switched 별도 기록 | [udprebindproxy/main.go#L296-L300](../../../repro/quic-go-min-repro/cmd/udprebindproxy/main.go#L296-L300) | qlog path validation만 보고 rebinding이 있었다고 말하는 것 |
| DOM task failure 우선 | [classify_chrome_h3_artifacts.py#L262-L265](../../../tools/classify_chrome_h3_artifacts.py#L262-L265) | transport evidence가 있어도 application failure를 PASS로 처리하는 것 |
| multiple session 분리 | [classify_chrome_h3_artifacts.py#L266-L283](../../../tools/classify_chrome_h3_artifacts.py#L266-L283) | heartbeat/retry로 새 session이 생긴 row를 single-session CM으로 과장하는 것 |
| local boundary non-monotonic 처리 | [summarize_chrome_rebinding_transient_return_path_sweep.py#L200-L210](../../../tools/summarize_chrome_rebinding_transient_return_path_sweep.py#L200-L210) | 5초 같은 단일 universal threshold 주장 |
