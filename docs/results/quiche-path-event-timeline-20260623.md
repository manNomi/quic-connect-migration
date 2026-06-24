# quiche Path-Event Timeline

작성일: 2026-06-23  
상태: PASS  
범위: Cloudflare quiche sample client/server local active migration artifact를 논문용 timeline으로 재구성한다.

## 1. 결론

Cloudflare `quiche` sample client/server의 local active migration artifact에서 Connection Migration lifecycle을 재구성했다.

핵심 결과:

| 항목 | 결과 |
| --- | --- |
| initial client path | `0.0.0.0:53238 -> 127.0.0.1:4443` |
| migrated client path | `0.0.0.0:61867 -> 127.0.0.1:4443` |
| server detection | `Seen new path` |
| path validation | client/server 모두 new path validated |
| migration decision | server log에 `Connection migrated to ...:61867` |
| qlog evidence | `PATH_CHALLENGE` / `PATH_RESPONSE` 확인 |
| HTTP/3 task | migration event 이후 `GET /` request/response 성공 |

논문용 한 문장:

> In the quiche sample stack, active migration produced an observable path lifecycle: the server observed a new peer path, the endpoints exchanged PATH_CHALLENGE/PATH_RESPONSE frames, both endpoints marked the new path as validated, and the HTTP/3 request completed on the migrated connection.

## 2. Artifact

원본 artifact:

- `experiments/quiche-local/artifacts/logs/client.log`
- `experiments/quiche-local/artifacts/logs/server.log`
- `experiments/quiche-local/artifacts/qlog/client-2ca737275c5fb4cfb23368c64e90ddfcbcc384f1.sqlog`
- `experiments/quiche-local/artifacts/qlog/server-1415b10aefffd5e99d53dd2a1315898f4f52a604.sqlog`

새로 정리한 timeline:

- `data/quiche-path-event-timeline.csv`

## 3. Timeline

Wall-clock log 기준 timeline은 client connect timestamp인 `2026-06-22T11:43:39.140335000Z`를 0 ms로 두고 계산했다. qlog timestamp는 vantage별 상대 시간이므로 client qlog와 server qlog를 서로 직접 비교하지 않고 frame sequence 근거로만 사용한다.

| 순서 | 시각 | 이벤트 | 근거 | 해석 |
| ---: | ---: | --- | --- | --- |
| 1 | 0.000 ms | client connect start | `client.log:1` | initial path는 `53238` |
| 2 | 6.299 ms | server sees new path | `server.log:3` | server가 `61867` peer path를 감지 |
| 3 | client qlog 6.293 ms | PATH_CHALLENGE sent | `client qlog:21` | client가 새 path probe |
| 4 | server qlog 4.792 ms | PATH_CHALLENGE received | `server qlog:39` | server가 새 path probe 수신 |
| 5 | server qlog 4.955 ms | PATH_RESPONSE + PATH_CHALLENGE sent | `server qlog:45` | server가 응답하고 reverse path 검증 시작 |
| 6 | client qlog 6.736 ms | PATH_RESPONSE + PATH_CHALLENGE received | `client qlog:26` | client가 server 응답과 challenge 수신 |
| 7 | client qlog 7.015 ms | PATH_RESPONSE sent | `client qlog:29` | client가 reverse path challenge 응답 |
| 8 | server qlog 5.438 ms | PATH_RESPONSE received | `server qlog:49` | server가 reverse path validation 완료 근거 수신 |
| 9 | 6.748 ms | client new path validated | `client.log:2` | client가 `61867` path validated 기록 |
| 10 | 6.885 ms | server new path validated | `server.log:4` | server가 `61867` path validated 기록 |
| 11 | 6.913 ms | connection migrated | `server.log:5` | server가 active peer path를 `61867`로 전환 |
| 12 | 7.676 ms | HTTP/3 request received | `server.log:6` | migration event 이후 `GET /` 처리 |
| 13 | 8.480 ms | response complete | `client.log:4` | client가 response 수신 성공 |
| 14 | 14.312 ms | client closed with active new path | `client.log:5` | final stats에서 `53238 active=false`, `61867 active=true` |
| 15 | 14.331 ms | server collected with active new path | `server.log:8` | final stats에서 `53238 active=false`, `61867 active=true` |

## 4. Interpretation

이 결과는 `quic-go` EC2 direct-origin positive control과 역할이 다르다.

| 구현체 | 강점 | 논문에서의 역할 |
| --- | --- | --- |
| quic-go | active migration을 직접 제어하기 쉽고 AWS direct-origin에서 이미 성공 | deployment positive control |
| quiche | path lifecycle log와 qlog 관찰성이 좋음 | migration lifecycle figure/table 근거 |

따라서 quiche 결과는 “cloud에서 성공했다”는 주장보다는 “구현체 내부에서 migration lifecycle이 어떤 이벤트와 frame sequence로 나타나는가”를 설명하는 증거로 쓰는 것이 좋다.

## 5. Limitation

- 이 artifact는 local loopback 환경이다. AWS 또는 mobile access network에서의 성공을 뜻하지 않는다.
- qlog timestamp는 client/server vantage마다 기준점이 다르므로 cross-vantage latency 계산에 쓰면 안 된다.
- 이 실험은 active migration sample path를 확인한 것이며, preferred address, multipath, CDN/proxy termination을 함께 검증하지 않는다.
- browser policy나 Android OS network switching은 이 실험 범위 밖이다.

## 6. Paper-Ready Claim

보수적으로 쓸 수 있는 claim:

> quiche provides strong observability for connection migration at the implementation level. In our local sample run, the server logged new path discovery, path validation, and migration, while qlog confirmed the corresponding PATH_CHALLENGE/PATH_RESPONSE exchange. This supports using quiche as a lifecycle-observability baseline, but not as evidence that managed HTTP/3 deployments automatically preserve end-to-end migration.

## 7. Next Step

다음 실험은 HAProxy HTTP/3 negative control이다. 목적은 다음 문장을 실험으로 뒷받침하는 것이다.

> HTTP/3 support does not imply Connection Migration support.
