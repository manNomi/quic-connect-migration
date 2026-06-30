# s2n-quic AWS NLB Live Readiness

작성일: `2026-06-30`

## 1. 목적

이 문서는 AWS NLB + s2n-quic live data-plane 실험으로 넘어가기 전에, iPhone 없이 확인할 수 있는 readiness gate를 고정한 결과다.

핵심 경계:

> 이 문서는 AWS NLB + s2n-quic migration 성공 결과가 아니다. 현재 단계의 결론은 "local s2n CID provider proof는 통과하지만, 현재 AWS identity가 `invalid_client_token`이고 dedicated s2n live NLB runner가 아직 없으므로 live AWS 실험은 진행하지 않는다"이다.

## 2. 추가한 runner

```bash
harness/scripts/check-s2n-nlb-live-readiness.sh
```

runner가 수행하는 일:

| 단계 | 내용 | 산출물 |
| --- | --- | --- |
| AWS identity gate | `tools/check_aws_identity_readiness.py`로 STS identity를 public-safe redaction 후 분류 | `results/aws-identity-readiness.md`, `results/aws-identity-readiness.json` |
| local CID provider proof | `harness/scripts/run-local-s2n-nlb-cid-proof.sh` 실행 | `local-s2n-proof/result.json`, `cargo-test.log`, `run.log` |
| runner availability check | 기존 quic-go NLB runner와 dedicated s2n live runner 존재 여부 확인 | `results/result.env` |
| final gate | live s2n NLB 실험을 지금 진행할 수 있는지 `can_run_live_s2n_nlb_now`로 판정 | `blocked_reason` |

## 3. 최신 로컬 실행

Command:

```bash
RUN_ID=s2n-nlb-live-readiness-local-20260630 \
  harness/scripts/check-s2n-nlb-live-readiness.sh
```

Result:

```text
run_id=s2n-nlb-live-readiness-local-20260630
aws_region=ap-northeast-2
aws_identity_ok=no
aws_identity_classification=invalid_client_token
aws_cli_found=yes
cargo_found=yes
local_proof_status=PASS
local_proof_exit=0
local_proof_echo_matches=yes
cid_provider_crate_ready=yes
existing_quic_go_nlb_runner_ready=yes
s2n_live_nlb_runner_ready=no
can_run_live_s2n_nlb_now=no
blocked_reason=aws_identity_invalid_client_token
```

## 4. 해석

확인된 것:

1. 현재 로컬 AWS CLI는 설치되어 있지만 STS identity가 `invalid_client_token`으로 닫힌다.
2. s2n-quic AWS NLB CID provider crate는 존재한다.
3. local proof는 `PASS`이고, 실제 local s2n-quic endpoint echo도 `echo_matches=yes`다.
4. 기존 quic-go 기반 AWS NLB data-plane runner는 존재한다.
5. dedicated s2n live NLB data-plane runner는 아직 없다.

따라서 현재 blocker는 두 층이다.

| blocker | 의미 |
| --- | --- |
| `aws_identity_invalid_client_token` | live AWS resource 생성/삭제 자동화를 지금 실행하면 안 됨 |
| `s2n_live_nlb_runner_ready=no` | 기존 live NLB 검증은 quic-go 경로이고, s2n target A/B용 dedicated runner는 후속 구현 필요 |

## 5. 논문 claim boundary

쓸 수 있는 주장:

> The s2n-quic AWS NLB prerequisite path is locally ready at the CID-provider level: the custom provider emits AWS NLB-compatible CIDs and completes a local s2n-quic echo workload. However, live AWS NLB forwarding with s2n targets remains unexecuted because current credentials are invalid and a dedicated s2n live runner is not yet implemented.

한국어 표현:

> s2n-quic은 AWS NLB가 요구하는 routable CID를 생성하고 local echo endpoint에 주입되는 전제 조건은 통과했다. 하지만 현재 AWS credential이 `invalid_client_token`이고 dedicated s2n live NLB runner가 없으므로, AWS NLB 뒤에서 s2n target A/B가 migrated packet을 유지하는지는 아직 검증하지 않았다.

피해야 할 주장:

| 금지 claim | 이유 |
| --- | --- |
| s2n-quic이 AWS NLB 뒤에서 active migration에 성공했다 | live AWS NLB forwarding 실험을 실행하지 않음 |
| local s2n echo proof가 NLB routing proof다 | local echo는 NLB를 거치지 않음 |
| AWS credential만 고치면 연구가 완료된다 | dedicated s2n live runner와 target evidence 수집도 필요 |
| quic-go NLB success가 곧 s2n NLB success다 | CID provider와 server implementation이 다르므로 별도 target 검증이 필요 |

## 6. 다음 단계

| 우선순위 | 작업 | 필요한 evidence |
| ---: | --- | --- |
| 1 | AWS credential refresh 후 readiness rerun | `aws_identity_ok=yes` |
| 2 | dedicated `run-aws-s2n-nlb-live-data-plane.sh` 구현 | EC2 target A/B에 s2n server 배포 |
| 3 | target registration `QuicServerId`와 provider Server ID 일치 확인 | AWS target registration summary, redacted |
| 4 | desktop client path/source-port change 유도 | before/after path evidence |
| 5 | same-target continuity 확인 | target A/B logs, payload echo/checksum, path validation evidence |

## 7. 참고

연결된 기존 근거:

| 문서/코드 | 의미 |
| --- | --- |
| [s2n-quic NLB CID provider rerun](s2n-quic-nlb-cid-provider-rerun-20260630.md) | local provider proof와 echo PASS |
| [AWS NLB QUIC feasibility](aws-nlb-quic-feasibility-20260623.md) | QUIC/TCP_QUIC target group과 `QuicServerId` control-plane feasibility |
| [AWS NLB QUIC data-plane results](aws-nlb-quic-data-plane-results-20260624.md) | quic-go 기반 AWS NLB positive control |
| [check-s2n-nlb-live-readiness.sh](../../harness/scripts/check-s2n-nlb-live-readiness.sh) | current readiness gate runner |
