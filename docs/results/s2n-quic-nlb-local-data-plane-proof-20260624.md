# s2n-quic AWS NLB CID Local Data-Plane Proof

작성일: 2026-06-24  
상태: PASS  
목적: AWS NLB QUIC data-plane 실험 전, `s2n-quic` 서버에 AWS NLB용 QUIC-LB plaintext CID provider를 실제로 주입할 수 있고 로컬 QUIC workload가 성공하는지 확인한다.

2026-06-30 재검수:

- 누락되어 있던 `experiments/s2n-quic-nlb-cid-provider` proof crate를 복원했다.
- `./harness/scripts/run-local-s2n-nlb-cid-proof.sh`를 재실행했고, `cargo test` 3개와 local s2n-quic echo proof가 PASS했다.
- 상세 결과는 [s2n-quic-nlb-cid-provider-rerun-20260630.md](s2n-quic-nlb-cid-provider-rerun-20260630.md)에 정리했다.

## Result

Command:

```bash
./harness/scripts/run-local-s2n-nlb-cid-proof.sh
```

Artifacts:

```text
experiments/s2n-quic-nlb-cid-provider/results/local-data-plane-20260623T152749Z/
experiments/s2n-quic-nlb-cid-provider/results/local-data-plane-20260623T161659Z/
```

Summary:

| Field | Value |
| --- | --- |
| status | PASS |
| target A Server ID | `a1b2c3d4e5f65890` |
| target B Server ID | `a1b2c3d4e5f65999` |
| generated target A CID | `00a1b2c3d4e5f6589000000000000000` |
| generated target B CID | `00a1b2c3d4e5f6599900000000000000` |
| target A CID route result | `target-a` |
| target B CID route result | `target-b` |
| wrong CID route result | `null` |
| QUIC echo | `echo_matches=true` |

## Interpretation

This proof does not yet test AWS NLB packet forwarding or client path migration.

It does prove the local prerequisite for the AWS NLB data-plane chapter:

1. `AwsNlbCidFormat` can generate QUIC-LB plaintext CIDs with layout `0x00 + 8-byte QuicServerId + 7-byte nonce`.
2. The same provider can be installed into a real `s2n-quic` server endpoint.
3. A local `s2n-quic` client/server QUIC echo workload completes successfully with that provider installed.
4. A simple CID-aware router simulation routes target A/B CIDs to the expected target and rejects an unknown CID.

## Evidence

`result.json`:

```json
{
  "status": "PASS",
  "target_a_server_id": "a1b2c3d4e5f65890",
  "target_b_server_id": "a1b2c3d4e5f65999",
  "generated_target_a_cid": "00a1b2c3d4e5f6589000000000000000",
  "generated_target_b_cid": "00a1b2c3d4e5f6599900000000000000",
  "route_generated_target_a_cid": "target-a",
  "route_generated_target_b_cid": "target-b",
  "route_wrong_cid": null,
  "quic_echo": {
    "server_addr": "127.0.0.1:58609",
    "client_local_addr": "127.0.0.1:62106",
    "server_observed_remote_addr": "127.0.0.1:62106",
    "payload_bytes": 29,
    "echo_matches": true
  }
}
```

## Self Review

Accepted:

- This is a valid Gate 1 proof because it checks the actual `s2n-quic` endpoint integration, not just isolated CID generation.
- It is intentionally not an AWS NLB proof by itself. The later AWS data-plane experiment confirms the same QUIC-LB plaintext format against EC2 target A/B and NLB `QUIC` target registration with `QuicServerId`.
- It is not a full migration proof. Client path migration remains covered by the earlier quic-go EC2 positive control and quiche local path-event result; this proof only closes the AWS NLB CID-provider prerequisite.

This proof is now consistent with the successful AWS NLB data-plane run in `experiments/aws-nlb-quic-data-plane-results-20260624.md`.
