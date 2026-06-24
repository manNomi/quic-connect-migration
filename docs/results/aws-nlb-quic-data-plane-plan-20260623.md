# AWS NLB QUIC Data-Plane Control Plan

작성일: 2026-06-23  
상태: 계획 및 셀프 리뷰 완료, 2026-06-24 실행 PASS  
목적: AWS NLB QUIC passthrough가 Connection Migration 후에도 CID-aware routing으로 같은 backend target을 유지하는지 검증한다.

실행 결과:

- 결과 문서: `experiments/aws-nlb-quic-data-plane-results-20260624.md`
- PASS artifact: `harness/results/aws-nlb-quic-dp-20260623T160418Z/`
- 핵심 수정: AWS NLB용 CID는 raw `8-byte Server ID + nonce`가 아니라 QUIC-LB plaintext `0x00 + 8-byte Server ID + 7-byte nonce` 형식이어야 했다.

## 1. Goal

이번 챕터의 목표는 다음 질문에 답하는 것이다.

> AWS Network Load Balancer의 QUIC/TCP_QUIC passthrough가 8-byte `QuicServerId`를 포함한 QUIC Connection ID를 사용해, client UDP tuple 변경 후에도 같은 EC2 target으로 packet을 라우팅하는가?

이 실험은 이전 챕터들의 다음 단계다.

| 이전 근거 | 상태 | 이번 계획에서의 역할 |
| --- | --- | --- |
| quic-go EC2 direct-origin | PASS | public network에서 active migration 자체는 가능하다는 positive control |
| HAProxy HTTP/3 negative control | PASS_NEGATIVE_CONTROL | HTTP/3 지원과 CM 지원이 다름을 보여주는 반례 |
| AWS NLB QUIC feasibility | PASS_FEASIBILITY | `QUIC`/`TCP_QUIC` target group 생성 가능성 확인 |
| s2n-quic CID provider proof | PASS | 8-byte Server ID를 CID에 encode할 수 있음 |

## 2. Non-Goals

이번 챕터에서 하지 않을 것:

- Android Chrome 또는 Cronet 실험
- CloudFront viewer-edge continuity 실험
- 대용량 파일 업로드나 dashboard workload
- production-grade CID 암호화/난독화
- 장시간 성능/부하 테스트
- 모든 리전/모든 NLB protocol 조합 검증

## 3. Hypothesis

H1.

> `s2n-quic` server가 target별로 등록된 8-byte `QuicServerId`를 CID에 포함하면, NLB는 client source port migration 이후에도 같은 target으로 packet을 전달한다.

H2.

> server-generated CID가 등록된 `QuicServerId`를 포함하지 않으면, migration 이후 packet은 NLB에서 drop되거나 target miss로 관찰된다.

## 4. Architecture

추천 구성:

```text
local client
  - quiche-client --perform-migration, or custom client
  - starts on UDP tuple A
  - migrates to UDP tuple B
        |
        | QUIC over UDP
        v
AWS NLB
  - scheme: internet-facing
  - address type: ipv4
  - no security group
  - listener: QUIC :443 or QUIC :4242
        |
        +--> target A
        |     EC2 instance
        |     UDP QUIC server
        |     TCP health-check sidecar
        |     QuicServerId=0xa1b2c3d4e5f65890
        |
        +--> target B
              EC2 instance
              UDP QUIC server
              TCP health-check sidecar
              QuicServerId=0xa1b2c3d4e5f65999
```

권장 protocol:

| Option | 장점 | 단점 | 결정 |
| --- | --- | --- | --- |
| `QUIC` on 4242 | direct-origin quic-go 실험과 비슷한 포트, HTTP/TCP fallback 없음 | TCP health check sidecar 필요 | 1차 추천 |
| `TCP_QUIC` on 443 | HTTPS fallback과 실제 배포에 가까움 | TCP/QUIC 동시 구성 복잡도 증가 | 2차 후보 |

1차 실험은 `QUIC` target group/listener on UDP `4242`로 진행한다. health check는 TCP `4242` sidecar로 통과시킨다.

## 5. Implementation Strategy

### 5.1 Client Strategy

우선순위:

1. `quiche-client --enable-active-migration --perform-migration`
   - 장점: 이미 local migration과 HAProxy negative control에서 사용 성공
   - 필요 조건: target server가 HTTP/3를 처리해야 함
2. custom client
   - 장점: workload와 migration timing을 직접 제어 가능
   - 단점: s2n-quic public active migration API 확인 필요
3. quic-go custom client
   - 장점: active migration API 이미 검증됨
   - 단점: s2n-quic server와 raw stream/application protocol interop 설계 필요

실행 전 local gate:

> AWS 리소스를 만들기 전에, 선택한 client와 `s2n-quic` server가 local direct-origin에서 handshake/request/migration을 통과해야 한다.

### 5.2 Server Strategy

서버는 다음 기능을 가져야 한다.

- target별 `AwsNlbCidFormat(server_id)` 주입
- server-generated CID가 `QuicServerId` prefix를 포함하는지 로그 출력
- connection/stream별 target identity 로그 출력
- qlog 또는 structured log artifact 저장
- TCP health-check sidecar 실행
- graceful shutdown 및 artifact flush

기존 proof crate:

- `experiments/s2n-quic-nlb-cid-provider/`

확장 후보:

- `experiments/s2n-quic-nlb-repro/`

### 5.3 Health Check Strategy

중요:

> NLB `QUIC`/`TCP_QUIC` target group은 health check protocol로 QUIC 자체를 쓰지 않는다. 기본 health check는 TCP이며, target이 healthy가 되려면 같은 traffic port에서 TCP를 받아주는 sidecar가 필요하다.

계획:

- QUIC server: UDP `4242`
- health sidecar: TCP `4242`
- EC2 target security group:
  - UDP `4242` from local client public CIDR, because client IP preservation applies
  - TCP `4242` from VPC CIDR or NLB subnet private IP ranges for health checks
  - TCP `22` from local client public CIDR for SSH

## 6. AWS Resource Plan

Resource prefix:

```text
quic-cm-nlb-dp-<timestamp>
```

Resources:

| Resource | Count | Notes |
| --- | ---: | --- |
| EC2 key pair | 1 | import local temporary SSH key |
| Security group for targets | 1 | allow SSH, UDP QUIC, TCP health |
| EC2 target instances | 2 | target A/B, preferably `t4g.micro` |
| NLB | 1 | internet-facing, ipv4, no security group |
| Target group | 1 | protocol `QUIC`, port `4242`, target type `instance` |
| Listener | 1 | protocol `QUIC`, port `4242` |
| Target registrations | 2 | each with unique `QuicServerId` |

Target registration example:

```bash
aws elbv2 register-targets \
  --target-group-arn "$TG_ARN" \
  --targets \
    Id="$INSTANCE_A",Port=4242,QuicServerId=0xa1b2c3d4e5f65890 \
    Id="$INSTANCE_B",Port=4242,QuicServerId=0xa1b2c3d4e5f65999
```

Cleanup order:

1. Stop client/server processes.
2. Collect artifacts.
3. Delete listener.
4. Delete load balancer.
5. Deregister targets.
6. Delete target group.
7. Terminate EC2 instances.
8. Delete security group.
9. Delete AWS key pair.
10. Keep local artifacts and logs.

## 7. Execution Gates

### Gate 0: Readiness

Commands:

```bash
./harness/scripts/aws-preflight.sh
cargo test --manifest-path experiments/s2n-quic-nlb-cid-provider/Cargo.toml
```

Pass:

- AWS identity and region confirmed.
- CID provider tests pass.

### Gate 1: Local Data-Plane Proof

Goal:

> client and s2n-quic server communicate locally with Server ID-aware CID before AWS resources are created.

Pass:

- local server starts with `QuicServerId`.
- client request/stream succeeds.
- server log shows QUIC-LB plaintext CID uses configured Server ID.
- migration attempt succeeds locally, or limitation is recorded before AWS spend.

### Gate 2: AWS Control Plane

Pass:

- NLB created with no security group.
- `QUIC` target group created.
- target A/B registered with unique `QuicServerId`.
- both targets become healthy.

### Gate 3: AWS Positive Data Plane

Pass:

- initial connection succeeds through NLB DNS.
- target A or B logs initial connection.
- client migration changes source tuple.
- same target logs migrated packet/request.
- client task succeeds without reconnect/manual retry.

### Gate 4: AWS Negative Control

Pass:

- server with default/random CID or wrong Server ID causes migration failure, NLB drop metric, or no same-target continuity.
- `QUIC_Unknown_Server_ID_Packet_Drop_Count` or equivalent metric/log is collected when available.

## 8. Measurement Plan

Record these fields.

| Field | Source |
| --- | --- |
| trial id | local run manifest |
| NLB DNS name | AWS CLI output |
| target A/B instance IDs | AWS CLI output |
| target A/B Server IDs | run manifest |
| initial target | target logs |
| migrated target | target logs |
| source tuple before/after | client log, target log, pcap |
| QUIC-LB CID Server ID field | server/client log or qlog |
| PATH_CHALLENGE/PATH_RESPONSE | qlog or event logs |
| application task result | client/server result JSON |
| NLB metrics | CloudWatch |
| cleanup status | cleanup log |

Recommended result row:

```text
trial_id=aws-nlb-quic-data-plane-001
status=PASS or FAIL_CLASSIFIED
implementation=s2n-quic server + quiche/custom client
deployment_tier=AWS NLB QUIC passthrough
protocol=QUIC
migration_trigger=client source port/path change
path_validation_observed=true/false
tuple_change_observed=true/false
application_task=GET / or stream payload
application_success=true/false
failure_layer=none | client | target-health | nlb-routing | cid-format | security-group | unknown
```

## 9. Failure Classification

| Symptom | Likely Layer | Diagnosis |
| --- | --- | --- |
| target remains unhealthy | health check / SG | TCP sidecar missing, SG not allowing VPC health check |
| handshake timeout before migration | NLB/Security group/client UDP | listener wrong, UDP blocked, target unhealthy |
| initial request succeeds but post-migration fails | CID routing or path validation | inspect QUIC-LB CID layout, NLB unknown Server ID metric, qlog |
| migration succeeds but different target logs packet | NLB affinity failure or Server ID mismatch | compare registered `QuicServerId` with CID Server ID field |
| local proof fails before AWS | implementation/client strategy | switch client strategy or avoid AWS spend |
| direct EC2 target succeeds but NLB fails | NLB routing/health/CID | use as deployability gap evidence |

## 10. Expected Paper Contribution

이 챕터가 성공하면 논문에서 다음 문장을 강하게 쓸 수 있다.

> Connection Migration deployment behind a cloud load balancer requires not only transport-level migration support but also load-balancer-aware CID generation. In AWS NLB QUIC passthrough, this means target-specific 8-byte Server IDs must be embedded into server-generated CIDs.

실패해도 의미가 있다.

> If the direct-origin and local provider proof succeed but NLB data-plane migration fails, the failure can be classified as a deployment maturity gap rather than a missing RFC 9000 transport primitive.

## 11. Self Review

### Accepted Findings

High: TCP health check sidecar is required.

- Evidence: AWS NLB QUIC/TCP_QUIC target groups use TCP health checks, not QUIC health checks.
- Risk: without a TCP listener, targets remain unhealthy and the experiment fails before testing migration.
- Decision: include TCP `4242` sidecar in the plan.

High: target security group must account for client IP preservation.

- Evidence: QUIC/UDP target groups preserve client IP, so target packets can appear to come from the local client public IP rather than an NLB security group.
- Risk: target SG that only allows VPC CIDR can block client QUIC traffic.
- Decision: allow UDP target port from local client CIDR and TCP health checks from VPC/NLB subnets.

Medium: one target is insufficient.

- Evidence: a single target can make routing appear successful even if affinity logic is not tested.
- Risk: false positive.
- Decision: require target A/B and a negative control.

Medium: client strategy is uncertain.

- Evidence: `quiche-client` has proven migration support, but it expects HTTP/3; custom clients provide control but require more implementation.
- Decision: add Gate 1 local proof before AWS resource creation.

Medium: deterministic CID suffix is not production-grade.

- Evidence: proof provider uses 8-byte sequence suffix.
- Risk: linkability and uniqueness limitations if used as production design.
- Decision: acceptable for controlled lab proof; document as non-production.

### No Critical Findings

No critical blocker remains in the plan after adding the health-check sidecar, client-IP-preservation security group rule, two-target requirement, and local proof gate.

### Deferred Items

- Production-safe CID randomization/encryption.
- Full HTTP/3 application workload.
- Android/Cronet mobile network transition.
- Cross-region NLB behavior.

## 12. Final Reviewed Plan

1. Build local `s2n-quic` NLB-aware server from the CID provider proof.
2. Pick the lowest-risk migration client through local proof.
3. Only after local proof passes, create AWS EC2 target A/B.
4. Run QUIC server plus TCP health sidecar on both targets.
5. Create NLB, QUIC target group, listener, and register targets with unique `QuicServerId`.
6. Wait until targets are healthy.
7. Run positive migration through NLB.
8. Run negative CID mismatch/default CID control.
9. Collect target logs, client logs, qlog/pcap, CloudWatch metrics, and AWS config.
10. Cleanup all AWS resources and write result row.
