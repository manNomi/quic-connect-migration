# AWS NLB QUIC Feasibility Results

작성일: 2026-06-23  
상태: PASS_FEASIBILITY  
범위: AWS Network Load Balancer의 QUIC/TCP_QUIC control-plane 지원과 `s2n-quic` CID provider 적합성을 검수한다.

## 1. 결론

이번 챕터의 결론은 다음이다.

> 현재 AWS 계정의 `ap-northeast-2` 리전에서 QUIC/TCP_QUIC target group 생성은 실제 API로 가능하며, `s2n-quic`는 public connection ID provider API를 통해 AWS NLB가 요구하는 8-byte Server ID를 CID에 포함하도록 구현할 수 있다.

단, 아직 실제 NLB listener, EC2 target A/B, migration 후 backend affinity는 검증하지 않았다. 즉 이번 결과는 deployment experiment의 feasibility check이지, NLB data-plane migration 성공 결과는 아니다.

## 2. Official Constraints

근거 문서:

- AWS NLB listener documentation: <https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-listeners.html>
- AWS NLB target registration documentation: <https://docs.aws.amazon.com/elasticloadbalancing/latest/network/target-group-register-targets.html>
- AWS NLB target group documentation: <https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-target-groups.html>
- AWS QUIC NLB launch blog: <https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-quic-protocol-support-for-network-load-balancer-accelerating-mobile-first-applications/>

요약:

| 항목 | 공식 제약 |
| --- | --- |
| NLB mode | QUIC passthrough, TLS/QUIC session을 NLB가 terminate하지 않음 |
| listener protocol | `QUIC` 또는 `TCP_QUIC` |
| target group protocol | listener와 맞는 `QUIC` 또는 `TCP_QUIC` |
| routing key | established CID에 포함된 Server ID |
| initial traffic | Server ID가 없는 initial connection attempt는 flow hash 사용 |
| target registration | `QUIC`/`TCP_QUIC` target은 `QuicServerId` 필요 |
| Server ID | 8 bytes, `0x` + 16 hexadecimal characters |
| uniqueness | listener 안에서 target별 Server ID가 unique해야 함 |
| mutability | 등록 후 Server ID 변경 불가, 변경하려면 deregister 후 재등록 |
| reuse | 다른 target에 같은 Server ID를 재사용하려면 6시간 회피 권고 |
| health check | `QUIC`/`TCP_QUIC` 자체 health check는 지원하지 않고 TCP 등 사용 |
| load balancer shape | QUIC/TCP_QUIC listener는 IPv4 NLB, security group 없음 조건 필요 |

논문용 해석:

> AWS NLB QUIC is not a generic UDP hash balancer. It exposes a QUIC-aware passthrough mode that relies on an 8-byte Server ID embedded in the QUIC Connection ID. Therefore, implementation support for custom CID generation is a deployment prerequisite.

## 3. AWS API Probe

### 3.1 Environment

```text
AWS_PROFILE=quic-cm-lab
AWS_REGION=ap-northeast-2
VPC_ID=vpc-06a40dc01682a9a56
AWS CLI=2.34.38
```

Artifact:

- `experiments/aws-nlb-quic-feasibility-20260623/logs/probe.env`
- `experiments/aws-nlb-quic-feasibility-20260623/logs/sts.json`

### 3.2 CLI Model Check

`aws elbv2 create-target-group help` includes:

- `QUIC`
- `TCP_QUIC`

`aws elbv2 register-targets help` includes:

- `QuicServerId`
- required for `QUIC` or `TCP_QUIC`
- `0x` prefix followed by 16 hexadecimal characters

### 3.3 Actual Control-Plane Probe

Created and immediately deleted a `QUIC` target group:

```text
name=qcm-quic-1336
protocol=QUIC
port=4242
target_type=instance
health_check_protocol=TCP
ip_address_type=ipv4
arn=arn:aws:elasticloadbalancing:ap-northeast-2:<aws-account-id>:targetgroup/qcm-quic-1336/<target-group-id>
```

Created and immediately deleted a `TCP_QUIC` target group:

```text
name=qcm-tcpquic-1336
protocol=TCP_QUIC
port=443
target_type=instance
health_check_protocol=TCP
ip_address_type=ipv4
arn=arn:aws:elasticloadbalancing:ap-northeast-2:<aws-account-id>:targetgroup/qcm-tcpquic-1336/<target-group-id>
```

Deletion check:

```text
TargetGroupNotFound
```

Artifacts:

- `experiments/aws-nlb-quic-feasibility-20260623/logs/create-target-group-quic.json`
- `experiments/aws-nlb-quic-feasibility-20260623/logs/create-target-group-tcp-quic.json`
- `experiments/aws-nlb-quic-feasibility-20260623/logs/delete-target-group-quic.json`
- `experiments/aws-nlb-quic-feasibility-20260623/logs/delete-target-group-tcp-quic.json`
- `experiments/aws-nlb-quic-feasibility-20260623/logs/describe-after-delete.err`

Control-plane conclusion:

> `ap-northeast-2` accepts both `QUIC` and `TCP_QUIC` Network Load Balancer target groups in this account.

## 4. s2n-quic CID Provider Feasibility

Source checked:

```text
repository=https://github.com/aws/s2n-quic
commit=547e973da525aef637a7cc1db2f1733ce42be929
```

Relevant source evidence:

| Source | Evidence |
| --- | --- |
| `quic/s2n-quic/src/server/builder.rs` | `Server::builder().with_connection_id(...)` supports custom connection ID provider |
| `quic/s2n-quic/src/provider/connection_id.rs` | public `Generator`, `Validator`, `LocalId`, `ConnectionInfo` re-exports |
| `quic/s2n-quic-core/src/connection/id.rs` | `Generator::generate(...) -> LocalId`; `Validator::validate(...) -> Option<usize>` |
| `quic/s2n-quic/src/provider/connection_id.rs` | default CID is random 16-byte format |
| `quic/s2n-quic-tests/src/tests/endpoint_limits.rs` | custom max-size CID format test demonstrates provider injection |

Important distinction:

- Default `s2n-quic` CID generation is not AWS NLB-specific.
- AWS NLB deployment requires a custom provider so that every server-generated CID carries the registered 8-byte `QuicServerId`.

## 5. Proof Crate

Created a small local proof crate:

- `experiments/s2n-quic-nlb-cid-provider/Cargo.toml`
- `experiments/s2n-quic-nlb-cid-provider/src/lib.rs`

Provider shape:

```text
CID bytes = 0x00 config byte || 8-byte AWS Server ID || 7-byte local sequence/nonce
```

The proof implements:

- `connection_id::Generator`
- `connection_id::Validator`
- QUIC-LB plaintext Server ID field check
- unique CID generation for successive calls
- rejection for unknown Server ID
- rejection for short packets

Verification:

```bash
cargo test --manifest-path experiments/s2n-quic-nlb-cid-provider/Cargo.toml
```

Result:

```text
running 2 tests
test tests::generated_cid_starts_with_aws_server_id ... ok
test tests::validator_rejects_unknown_server_id_and_short_packets ... ok
test result: ok. 2 passed; 0 failed
```

Artifact:

- `experiments/aws-nlb-quic-feasibility-20260623/logs/s2n-quic-nlb-cid-provider-test-pass.log`

## 6. Interpretation

This chapter establishes the next deployment experiment is feasible.

| Question | Answer |
| --- | --- |
| Does AWS API expose QUIC/TCP_QUIC target groups in this account/region? | Yes |
| Does target registration require a Server ID? | Yes |
| Is the Server ID exactly 8 bytes? | Yes |
| Can s2n-quic expose custom CID generation? | Yes |
| Did the custom provider compile and pass local tests? | Yes |
| Did we verify NLB data-plane routing after migration? | Not yet |

## 7. Remaining Risk

- The proof provider only validates CID formatting. It does not yet run a full `s2n-quic` server behind NLB.
- The provider uses a simple deterministic sequence suffix. A production provider should include stronger uniqueness/randomness and avoid linkability beyond the required AWS Server ID.
- NLB listener creation was not performed in this chapter. Listener constraints such as no security groups and IPv4-only shape must be enforced in the next runbook.
- Target registration with `QuicServerId` was not performed because no EC2 target was created in this chapter.
- Data-plane metrics such as `QUIC_Unknown_Server_ID_Packet_Drop_Count` were not collected yet.

## 8. Next Experiment

Next chapter should create the actual NLB data-plane control:

```text
custom client
        |
        | QUIC/TCP_QUIC NLB listener
        v
AWS NLB
        |
        +--> EC2 target A, QuicServerId=0xa1b2c3d4e5f65890
        |
        +--> EC2 target B, QuicServerId=0xa1b2c3d4e5f65999
```

Success criteria:

1. Target A/B register with unique `QuicServerId`.
2. Initial connection reaches one target.
3. Server-generated CID contains the target's registered Server ID.
4. Client source tuple changes.
5. Migrated packets route to the same target.
6. Wrong or unknown Server ID produces observable NLB drop or target miss.
