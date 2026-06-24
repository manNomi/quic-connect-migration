# AWS NLB QUIC Negative-Control Results

작성일: 2026-06-24  
최종 상태: PASS_NEGATIVE_CONTROL  
주요 artifacts:

- malformed CID run: `harness/results/aws-nlb-quic-dp-20260623T155524Z/`
- explicit Server ID mismatch run: `harness/results/aws-nlb-quic-negative-cid-20260623T162423Z/`

## 1. Research Question

질문:

> AWS NLB QUIC passthrough에서 target이 healthy이고 QUIC listener가 정상이어도, backend가 NLB가 기대하는 Server ID/CID 형식을 맞추지 않으면 connection migration 또는 application payload continuity가 실패하는가?

결론:

> PASS_NEGATIVE_CONTROL. NLB `QUIC` target group과 target health는 정상이어도, CID 형식 또는 Server ID 매핑이 맞지 않으면 client handshake/payload delivery가 실패한다.

## 2. Why This Matters

이 negative control은 직전 PASS 결과의 반대쪽 증거다.

PASS run:

```text
0x00 + 8-byte Server ID + 7-byte nonce
```

위 QUIC-LB plaintext CID 형식을 사용했을 때 AWS NLB는 active migration 후에도 같은 target으로 routing했다.

Negative runs:

1. raw `8-byte Server ID + 8-byte nonce` CID
2. NLB target registration Server ID와 server-generated CID Server ID mismatch

두 조건 모두 client task가 실패했다.

## 3. Negative Control A: Malformed CID Layout

Run:

```text
harness/results/aws-nlb-quic-dp-20260623T155524Z/
```

Condition:

```text
server CID = 8-byte Server ID + 8-byte nonce
expected = 0x00 + 8-byte Server ID + 7-byte nonce
```

Observed:

| 항목 | 결과 |
| --- | --- |
| target health | healthy |
| client dial | `dial_success` |
| server accept | target-b accepted connection |
| client STREAM frames | 51 STREAM frames sent |
| server STREAM frames | 0 STREAM frames received |
| application result | failure |
| client error | `timeout: no recent network activity` |
| server error | `timeout: no recent network activity` |

CloudWatch evidence:

```json
{
  "Label": "QUIC_Unknown_Server_ID_Packet_Drop_Count",
  "Datapoints": [
    {
      "Timestamp": "2026-06-24T01:01:00+09:00",
      "Sum": 59.0,
      "Unit": "Count"
    },
    {
      "Timestamp": "2026-06-24T01:02:00+09:00",
      "Sum": 2.0,
      "Unit": "Count"
    }
  ]
}
```

Interpretation:

> This is the strongest negative-control evidence. The connection progressed far enough for `dial_success` and server `connection_accepted`, but payload STREAM delivery failed and CloudWatch reported unknown Server ID packet drops.

## 4. Negative Control B: Explicit Server ID Mismatch

Run:

```text
harness/results/aws-nlb-quic-negative-cid-20260623T162423Z/
```

NLB target registration:

| Target | Registered `QuicServerId` |
| --- | --- |
| target-a | `0xa1b2c3d4e5f65890` |
| target-b | `0xa1b2c3d4e5f65999` |

Server-generated CID Server IDs:

| Target | Server CID Server ID |
| --- | --- |
| target-a | `0xfffffffffffffff1` |
| target-b | `0xfffffffffffffff2` |

Observed:

| 항목 | 결과 |
| --- | --- |
| target health | 2/2 healthy |
| client result | `ok: false` |
| client error | `timeout: no recent network activity` |
| server accepted connection | no |
| server success count | 0 |
| summary status | `PASS_NEGATIVE_CONTROL` |
| cleanup | deleted listener, NLB, target group, instances, security group, key pair |

Client qlog:

| Frame/event | Count |
| --- | ---: |
| `transport:packet_sent` | 10 |
| `transport:packet_received` | 0 |
| `frame:crypto` | 20 |
| `transport:connection_closed` | 1 |

Interpretation:

> This run confirms that target health and `QUIC` listener availability are not enough. With a deliberate mismatch between registered Server IDs and server-generated CID Server IDs, the client never received a QUIC response and no target accepted the connection.

CloudWatch note:

> No CloudWatch datapoint appeared for this new run at query time. The evidence for this run is therefore client/server/qlog/target-health based. The CloudWatch unknown Server ID evidence is available for Negative Control A.

## 5. Paper Use

This pair of negative controls supports the following paper claim:

> CID-aware load balancing is not a binary capability. It is a deployability contract between the load balancer and the QUIC implementation. A managed NLB may support QUIC and targets may be healthy, but Connection Migration only survives if backend-generated CIDs follow the load balancer's expected QUIC-LB layout and registered Server ID mapping.

Recommended framing:

| Evidence | Claim |
| --- | --- |
| AWS NLB data-plane PASS | CID-aware LB can preserve same-target continuity after migration |
| HAProxy negative control | HTTP/3 endpoint support does not imply active CM support |
| AWS NLB malformed CID negative control | QUIC-aware LB support still requires exact CID layout |
| AWS NLB explicit mismatch negative control | target health does not imply routable QUIC CIDs |

## 6. Next Step

Recommended next experiments:

1. Repeat positive run using `TCP_QUIC` on `443`.
2. Add HTTP/3 request/upload workload on top of the successful NLB transport path.
3. Run CloudFront viewer-edge limited control.
4. Later compare custom client behavior with Cronet/Android policy.
