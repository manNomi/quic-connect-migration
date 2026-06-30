# Chapter 4 Deployment Path Trigger Map

작성일: `2026-06-30`

이 표는 Chapter 4 “배포 경로 검수: AWS NLB, Proxy, CDN”에서 사용한 AWS NLB CID generator, NLB harness, HTTP/3 workload extension이 어떤 조건을 만들고 어떤 산출물을 검증하는지 추적한다. 공개 보고용 문서에는 공인 IP, hostname, EC2 instance id, account id, SSH target을 적지 않는다.

## 1. AWS NLB Routable CID Generator

| 코드 위치 | trigger/input | 출력 필드 | 해석 |
| --- | --- | --- | --- |
| [aws_nlb_cid.go#L13-L18](../../../repro/quic-go-min-repro/internal/common/aws_nlb_cid.go#L13-L18) | config rotation byte, 8-byte Server ID, 7-byte nonce | 16-byte CID layout | NLB가 읽을 수 있는 plaintext Server ID 포함 |
| [aws_nlb_cid.go#L20-L36](../../../repro/quic-go-min-repro/internal/common/aws_nlb_cid.go#L20-L36) | configured server id and random nonce | generated QUIC Connection ID | backend가 NLB-routable CID를 발급 |
| [aws_nlb_cid.go#L38-L44](../../../repro/quic-go-min-repro/internal/common/aws_nlb_cid.go#L38-L44) | generator state | CID length and Server ID hex | manifest/report용 서버 ID 확인 |
| [aws_nlb_cid.go#L46-L61](../../../repro/quic-go-min-repro/internal/common/aws_nlb_cid.go#L46-L61) | hex string, optional `0x` prefix | parsed 8-byte Server ID or error | 잘못된 Server ID를 early fail |
| [aws_nlb_cid_test.go#L5-L42](../../../repro/quic-go-min-repro/internal/common/aws_nlb_cid_test.go#L5-L42) | generated CIDs | length/config byte/server id/nonce uniqueness assertions | CID layout regression guard |
| [aws_nlb_cid_test.go#L44-L56](../../../repro/quic-go-min-repro/internal/common/aws_nlb_cid_test.go#L44-L56) | valid and short hex values | parse success/failure | malformed Server ID negative guard |

## 2. Server Integration

| 코드 위치 | trigger/input | 출력 필드 | 해석 |
| --- | --- | --- | --- |
| [server/main.go#L71-L81](../../../repro/quic-go-min-repro/cmd/server/main.go#L71-L81) | `--server-id` flag | `connection_id_mode=aws-quic-lb-plaintext` | transport server가 CID-aware mode로 동작 |
| [server/main.go#L133-L139](../../../repro/quic-go-min-repro/cmd/server/main.go#L133-L139) | optional `ConnectionIDGenerator` | QUIC transport listener | NLB positive/negative control의 backend |
| [h3server/main.go#L102-L112](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L102-L112) | H3 `--server-id` flag | H3 server CID mode | HTTP/3 workload에서도 같은 CID mode 사용 |
| [h3server/main.go#L159-L176](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L159-L176) | H3 QUIC transport and listener | H3 listener | H3 request layer로 deployment 검증 확장 |
| [h3server/main.go#L187-L226](../../../repro/quic-go-min-repro/cmd/h3server/main.go#L187-L226) | request method/path/remote addr/proto/ALPN/workload | `requests[]` record | same backend request continuity 확인 |

## 3. AWS NLB Harness Resource Lifecycle

| 코드 위치 | trigger/input | 생성/검증 artifact | 해석 |
| --- | --- | --- | --- |
| [run-aws-nlb-quic-data-plane.sh#L17-L45](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L17-L45) | region, protocol, workload, Server IDs, expected outcome | run config and artifact dirs | positive/negative run 조건 고정 |
| [run-aws-nlb-quic-data-plane.sh#L75-L82](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L75-L82) | `WORKLOAD` enum | transport/H3/midflight modes | 실험 workload 제한 |
| [run-aws-nlb-quic-data-plane.sh#L98-L163](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L98-L163) | trap cleanup | delete listener/LB/TG/instances/SG/keypair | 비용/보안 cleanup guard |
| [run-aws-nlb-quic-data-plane.sh#L194-L231](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L194-L231) | target IP, target name, server id | remote target bootstrap and server start | 각 target이 지정 Server ID로 QUIC server 실행 |
| [run-aws-nlb-quic-data-plane.sh#L260-L283](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L260-L283) | run config values | `manifest.env` | 재현 조건 기록. 공개 문서에는 민감값 미복사 |
| [run-aws-nlb-quic-data-plane.sh#L323-L331](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L323-L331) | repro package builder | EC2 deployment package | 동일 코드 배포 |
| [run-aws-nlb-quic-data-plane.sh#L333-L348](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L333-L348) | temporary key and security group | keypair/SG/logs | ephemeral infra setup |
| [run-aws-nlb-quic-data-plane.sh#L350-L381](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L350-L381) | AMI, instance type, subnets | two EC2 targets | two target backend topology |
| [run-aws-nlb-quic-data-plane.sh#L390-L404](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L390-L404) | protocol, port, VPC, health check | target group | `QUIC` 또는 `TCP_QUIC` data plane |
| [run-aws-nlb-quic-data-plane.sh#L406-L429](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L406-L429) | subnets and target group | internet-facing NLB and listener | client-facing endpoint 생성 |
| [run-aws-nlb-quic-data-plane.sh#L431-L436](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L431-L436) | target A/B and `QuicServerId` | target registration | CID Server ID와 target routing 계약 |
| [run-aws-nlb-quic-data-plane.sh#L438-L448](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L438-L448) | target health polling | final target-health log | health와 CM readiness를 별도 확인 |

## 4. Client Run And Summary Classification

| 코드 위치 | trigger/input | 출력 필드 | 해석 |
| --- | --- | --- | --- |
| [run-aws-nlb-quic-data-plane.sh#L450-L483](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L450-L483) | NLB address, workload mode, payload, probe, artifact dir | client artifacts | NLB를 통과한 migration client run |
| [run-aws-nlb-quic-data-plane.sh#L487-L539](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L487-L539) | client result and collected server results | `summary.json` | client ok + same target success를 PASS로 분류 |
| [run-aws-nlb-quic-data-plane.sh#L513-L524](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L513-L524) | successful server count and expected requests | `PASS`, `FAIL_CLASSIFIED`, `PASS_NEGATIVE_CONTROL` | positive와 negative control 분리 |
| [run-aws-nlb-quic-data-plane.sh#L541-L548](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L541-L548) | `EXPECTED_OUTCOME=client-failure` | exit code override for negative control | 실패해야 성공인 run을 별도 처리 |
| [run-ec2-client.sh#L33-L44](../../../repro/quic-go-min-repro/scripts/run-ec2-client.sh#L33-L44) | transport client flags | client result/qlog/keylog | transport workload 실행 |
| [run-ec2-client.sh#L46-L50](../../../repro/quic-go-min-repro/scripts/run-ec2-client.sh#L46-L50) | qlog path strings | `qlog-path-validation.txt` | transport path evidence |

## 5. HTTP/3 Workload Extension

| 코드 위치 | trigger/input | 출력 필드 | 해석 |
| --- | --- | --- | --- |
| [h3client/main.go#L93-L109](../../../repro/quic-go-min-repro/cmd/h3client/main.go#L93-L109) | server, authority, mode, payload, migration threshold, chunk settings | H3 client config | upload/download/midflight workload 조건 |
| [h3client/main.go#L190-L228](../../../repro/quic-go-min-repro/cmd/h3client/main.go#L190-L228) | UDP socket A, QUIC dial, H3 client conn | initial H3 connection | H3 over same QUIC connection |
| [h3client/main.go#L230-L237](../../../repro/quic-go-min-repro/cmd/h3client/main.go#L230-L237) | `mode` switch | upload-download or midflight functions | workload별 실행 분기 |
| [h3client/main.go#L260-L285](../../../repro/quic-go-min-repro/cmd/h3client/main.go#L260-L285) | upload before, migration, download after | H3 before/after tasks | request-layer continuity positive control |
| [h3client/main.go#L287-L320](../../../repro/quic-go-min-repro/cmd/h3client/main.go#L287-L320) | upload byte threshold trigger | midflight upload migration event | upload 중 active switch |
| [h3client/main.go#L323-L357](../../../repro/quic-go-min-repro/cmd/h3client/main.go#L323-L357) | download byte threshold trigger | midflight download migration event | downlink 중 active switch |
| [h3client/main.go#L359-L375](../../../repro/quic-go-min-repro/cmd/h3client/main.go#L359-L375) | socket B and `AddPath` | migration path | H3 workload의 second path |
| [h3client/main.go#L391-L434](../../../repro/quic-go-min-repro/cmd/h3client/main.go#L391-L434) | switch-before-probe, probe, switch-after-probe | migration event | H3에서도 path validation 후 switch |
| [h3client/main.go#L436-L447](../../../repro/quic-go-min-repro/cmd/h3client/main.go#L436-L447) | post-migration local addr check | `local_addr_changed_to_socket_b` | H3 workload 성공 overclaim 방지 |
| [run-h3-client.sh#L38-L60](../../../repro/quic-go-min-repro/scripts/run-h3-client.sh#L38-L60) | H3 client flags and qlog scan | H3 client artifacts | `http3:frame`, `chosen_alpn`, path frame evidence |
| [run-h3-server.sh#L23-L34](../../../repro/quic-go-min-repro/scripts/run-h3-server.sh#L23-L34) | H3 server flags including `SERVER_ID` and expected requests | H3 server artifacts | target-side H3 request records |

## 6. False-Positive Guards

| guard | 코드 근거 | 방지하는 오해 |
| --- | --- | --- |
| NLB health와 continuity 분리 | [run-aws-nlb-quic-data-plane.sh#L438-L448](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L438-L448), [run-aws-nlb-quic-data-plane.sh#L513-L524](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L513-L524) | target health만으로 CM readiness라고 주장하는 것 |
| same target success 요구 | [run-aws-nlb-quic-data-plane.sh#L513-L520](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L513-L520) | before/after가 서로 다른 backend로 간 것을 continuity로 쓰는 것 |
| negative control 별도 status | [run-aws-nlb-quic-data-plane.sh#L521-L548](../../../harness/scripts/run-aws-nlb-quic-data-plane.sh#L521-L548) | 실패해야 하는 조건을 일반 실패로만 남기거나 성공으로 오해하는 것 |
| CID layout unit test | [aws_nlb_cid_test.go#L5-L56](../../../repro/quic-go-min-repro/internal/common/aws_nlb_cid_test.go#L5-L56) | CID Server ID 위치 오류를 실험 실패 원인으로 놓치는 것 |
| H3 post-migration addr check | [h3client/main.go#L436-L447](../../../repro/quic-go-min-repro/cmd/h3client/main.go#L436-L447) | H3 request가 됐다는 이유만으로 path switch를 주장하는 것 |
