# AWS NLB + s2n-quic Live Runner

작성일: `2026-06-30`

## 1. 목적

이 문서는 `AWS NLB + s2n-quic` live data-plane 실험을 위한 전용 runner를 추가한 결과다.

핵심 경계:

> 이 문서는 live AWS NLB forwarding 성공 결과가 아니다. 현재 단계에서는 s2n 전용 live runner, server/client binary, local echo smoke, fail-closed AWS identity gate를 확보했다. 실제 AWS resource 생성은 현재 credential이 `invalid_client_token`이므로 실행하지 않았다.

## 2. 추가한 코드

| 파일 | 역할 |
| --- | --- |
| [harness/scripts/run-aws-s2n-nlb-live-data-plane.sh](../../harness/scripts/run-aws-s2n-nlb-live-data-plane.sh) | AWS identity가 유효할 때만 EC2 target A/B, NLB, QUIC target group, listener를 생성하고 s2n client echo를 실행하는 live runner |
| [experiments/s2n-quic-nlb-cid-provider/src/bin/nlb_live_server.rs](../../experiments/s2n-quic-nlb-cid-provider/src/bin/nlb_live_server.rs) | AWS NLB-compatible CID provider를 설치한 s2n-quic echo server |
| [experiments/s2n-quic-nlb-cid-provider/src/bin/nlb_live_client.rs](../../experiments/s2n-quic-nlb-cid-provider/src/bin/nlb_live_client.rs) | server certificate를 trust anchor로 사용해 NLB endpoint에 deterministic payload를 보내고 echo를 검증하는 s2n-quic client |
| [experiments/s2n-quic-nlb-cid-provider/src/bin/generate_localhost_cert.rs](../../experiments/s2n-quic-nlb-cid-provider/src/bin/generate_localhost_cert.rs) | `rcgen`으로 s2n/rustls가 신뢰 가능한 short-lived localhost certificate/key 생성 |

runner가 AWS identity 확인 전에 하는 일은 public-safe readiness 기록뿐이다. `aws_identity_ok=no`이면 EC2, NLB, target group, security group, key pair를 만들지 않는다.

## 3. Live Runner가 하는 일

AWS identity가 유효할 경우 runner 흐름은 다음과 같다.

| 단계 | 내용 |
| --- | --- |
| 1 | `tools/check_aws_identity_readiness.py`로 STS identity를 redacted/public-safe 방식으로 확인 |
| 2 | s2n crate source, live server/client source, Cargo 존재 확인 |
| 3 | `rcgen` certificate 생성 및 crate packaging |
| 4 | default VPC/subnet/AMI 조회 |
| 5 | EC2 target A/B 생성, Rust toolchain/bootstrap, s2n live server build/run |
| 6 | NLB, QUIC target group, listener 생성 |
| 7 | target A/B를 `QuicServerId`와 함께 등록 |
| 8 | local s2n live client가 NLB endpoint로 echo workload 실행 |
| 9 | target artifact 수집, summary/result.env 작성, AWS resource cleanup |

## 4. 현재 로컬 검증

### 4.1 Rust build check

```bash
cargo check --manifest-path experiments/s2n-quic-nlb-cid-provider/Cargo.toml --bins
```

결과:

```text
Finished `dev` profile [unoptimized + debuginfo] target(s)
```

### 4.2 Local live server/client smoke

AWS를 거치지 않고 새 `nlb_live_server`와 `nlb_live_client`가 같은 certificate/CID-provider 전제에서 echo를 완료하는지 확인했다.

결과 요약:

```text
client status=PASS
client echo_matches=true
client payload_bytes=2048
client received_bytes=2048
server status=PASS
server received_bytes=2048
server echoed_bytes=2048
```

이 smoke는 AWS NLB forwarding evidence가 아니다. live runner에 들어간 server/client binary가 같은 s2n-quic API와 TLS 전제로 동작한다는 로컬 검증이다.

### 4.3 Fail-closed AWS blocked run

Command:

```bash
RUN_ID=aws-s2n-nlb-live-local-blocked-20260630 \
  harness/scripts/run-aws-s2n-nlb-live-data-plane.sh
```

Result:

```text
run_id=aws-s2n-nlb-live-local-blocked-20260630
aws_region=ap-northeast-2
aws_identity_ok=no
aws_identity_classification=invalid_client_token
aws_cli_found=yes
cargo_found=yes
crate_ready=yes
server_binary_source_ready=yes
client_binary_source_ready=yes
live_phase=pre_resource_gate
validation=blocked
blocked_reason=aws_identity_invalid_client_token
```

해석:

> 현재 구현/runner는 준비됐지만, AWS identity가 `invalid_client_token`이므로 live resource creation은 의도적으로 실행하지 않았다.

## 5. Claim Boundary

쓸 수 있는 주장:

> The repository now contains a dedicated fail-closed AWS NLB + s2n-quic live runner. The live server/client binaries compile and pass a local echo smoke test, and the runner records the current AWS credential blocker before creating resources.

한국어 표현:

> AWS NLB + s2n-quic 전용 live runner를 추가했다. s2n live server/client는 로컬 echo smoke를 통과했고, runner는 현재 AWS credential이 `invalid_client_token`이면 EC2/NLB 생성 전에 fail-closed artifact를 남긴다.

피해야 할 주장:

| 금지 claim | 이유 |
| --- | --- |
| s2n-quic이 AWS NLB 뒤에서 active migration에 성공했다 | live AWS forwarding과 active migration은 아직 실행하지 않음 |
| s2n live runner가 browser handover를 검증한다 | runner는 s2n client/server echo이며 browser workload가 아님 |
| local echo smoke가 NLB routing proof다 | local smoke는 NLB를 거치지 않음 |
| AWS credential만 고치면 active migration까지 자동으로 입증된다 | 현재 live runner phase는 forwarding echo이며 active source migration은 별도 후속 |

## 6. 다음 단계

| 우선순위 | 작업 | 성공 근거 |
| ---: | --- | --- |
| 1 | AWS credential refresh 후 `run-aws-s2n-nlb-live-data-plane.sh` 실행 | `validation=ok`, `client_echo_matches=true`, `server_success_count=1` |
| 2 | same-target forwarding 확인 | target A/B 중 하나만 `server.json` PASS |
| 3 | active source-port migration variant 설계 | s2n public API 또는 controlled proxy/rebind path evidence |
| 4 | qlog/event observability 보강 | server/client path validation event 또는 packet-level evidence |

이 순서 때문에 현재 s2n/NLB 결과는 “live runner ready but AWS blocked”로 분류한다.
