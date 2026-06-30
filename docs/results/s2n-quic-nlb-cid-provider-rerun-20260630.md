# s2n-quic AWS NLB CID Provider Rerun

작성일: `2026-06-30`

## 1. 목적

기존 `harness/scripts/run-local-s2n-nlb-cid-proof.sh`는 `experiments/s2n-quic-nlb-cid-provider` crate를 가리키고 있었지만, 현재 worktree에는 해당 crate가 빠져 있어 재현 경로가 깨져 있었다.

이번 보강의 목적은 다음이다.

> AWS NLB live 실험 전에 필요한 s2n-quic custom Connection ID provider proof를 현재 repo에서 다시 실행 가능하게 복원하고, 실제 s2n-quic local echo endpoint에 provider가 주입되는지 재검증한다.

## 2. 복원한 코드

| 파일 | 역할 |
| --- | --- |
| [experiments/s2n-quic-nlb-cid-provider/Cargo.toml](../../experiments/s2n-quic-nlb-cid-provider/Cargo.toml) | s2n-quic git rev `0f5a4f8...` 기반 proof crate |
| [experiments/s2n-quic-nlb-cid-provider/src/lib.rs](../../experiments/s2n-quic-nlb-cid-provider/src/lib.rs) | `AwsNlbCidFormat`, CID parser/router simulation, unit tests |
| [experiments/s2n-quic-nlb-cid-provider/src/bin/local_data_plane_proof.rs](../../experiments/s2n-quic-nlb-cid-provider/src/bin/local_data_plane_proof.rs) | local s2n-quic server/client echo proof |
| [harness/scripts/run-local-s2n-nlb-cid-proof.sh](../../harness/scripts/run-local-s2n-nlb-cid-proof.sh) | wrapper script |

CID layout:

```text
0x00 + 8-byte AWS NLB QuicServerId + 7-byte nonce
```

## 3. 실행 결과

Command:

```bash
./harness/scripts/run-local-s2n-nlb-cid-proof.sh
```

Result directory:

```text
experiments/s2n-quic-nlb-cid-provider/results/local-data-plane-20260630T101625Z/
```

요약:

| 항목 | 결과 |
| --- | --- |
| `cargo test` | PASS |
| unit tests | `3 passed; 0 failed` |
| local proof binary | PASS |
| target A Server ID | `a1b2c3d4e5f65890` |
| target B Server ID | `a1b2c3d4e5f65999` |
| generated target A CID | `00a1b2c3d4e5f6589000000000000000` |
| generated target B CID | `00a1b2c3d4e5f6599900000000000000` |
| target A route result | `target-a` |
| target B route result | `target-b` |
| wrong CID route result | `null` |
| local s2n-quic echo | `echo_matches=true` |

`result.json` summary:

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
    "server_addr": "127.0.0.1:57723",
    "client_local_addr": "127.0.0.1:55146",
    "server_observed_remote_addr": "127.0.0.1:55146",
    "payload_bytes": 27,
    "echo_matches": true
  }
}
```

## 4. 검증 의미

확인된 것:

1. s2n-quic `Server::builder().with_connection_id(...)`에 AWS NLB용 custom CID provider를 주입할 수 있다.
2. provider가 생성한 CID는 `0x00 + 8-byte Server ID + 7-byte nonce` layout을 따른다.
3. simulated CID-aware router가 Server ID로 target A/B를 구분하고 unknown Server ID를 거부한다.
4. custom provider를 설치한 실제 s2n-quic server endpoint와 s2n-quic client가 local QUIC echo workload를 완료했다.

확인하지 않은 것:

1. 이번 rerun은 AWS NLB packet forwarding이 아니다.
2. 이번 rerun은 active path migration이 아니다.
3. 이번 rerun은 s2n-quic server가 AWS NLB 뒤에서 migrated packet을 실제로 받는지까지 검증하지 않는다.

## 5. 논문용 안전 문장

> We restored and reran the local s2n-quic AWS NLB CID-provider proof. The proof shows that a custom s2n-quic connection ID provider can emit AWS NLB-compatible QUIC-LB plaintext CIDs and can be installed in a real local s2n-quic endpoint that completes an echo workload. This is a deployment prerequisite, not an AWS NLB forwarding or migration result by itself.

한국어 표현:

> s2n-quic AWS NLB CID-provider proof를 복원해 재실행했다. custom connection ID provider가 AWS NLB가 기대하는 `0x00 + 8-byte Server ID + 7-byte nonce` CID를 생성하고, 실제 local s2n-quic endpoint에 주입된 상태로 echo workload가 성공함을 확인했다. 다만 이는 AWS NLB forwarding 또는 active migration 결과가 아니라 배포 전제 조건 검증이다.

## 6. 후속 작업

다음 단계는 AWS live 환경에서 s2n-quic server를 target A/B로 올리고, NLB target registration `QuicServerId`와 provider-generated Server ID가 일치할 때 migrated packet이 같은 target으로 유지되는지 확인하는 것이다.
