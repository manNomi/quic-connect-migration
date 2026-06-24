# AWS Direct-Origin QUIC Connection Migration Results

작성일: 2026-06-23  
상태: 성공  
Run ID: `aws-direct-origin-20260623T124641Z`

## 1. Summary

quic-go custom client/server를 사용해 AWS EC2 public IPv4 direct-origin 환경에서 QUIC Connection Migration positive control을 성공했다.

검증한 흐름:

```text
local client UDP socket A
  -> EC2 quic-go server 연결
  -> before payload 1 MiB 전송
  -> client UDP socket B 생성
  -> AddPath -> Probe -> Switch
  -> after payload 1 MiB 전송
  -> EC2 server가 같은 QUIC connection에서 before/after payload 모두 수신
```

핵심 결론:

> CDN/LB 없이 EC2 public direct-origin 경로에서는 quic-go active Connection Migration이 성공했다. 이는 이후 HAProxy, CloudFront, AWS NLB, Android/Cronet 실험의 positive control baseline으로 사용할 수 있다.

## 2. AWS Environment

| 항목 | 값 |
| --- | --- |
| AWS profile | `quic-cm-lab` |
| Region | `ap-northeast-2` |
| Instance ID | `i-0c8bc2ff8e63a765d` |
| Instance type | `t4g.micro` |
| AMI | `ami-0219a9c714fb8f719` |
| Public IP | `3.36.93.221` |
| Private IP | `172.31.1.204` |
| Security group | `sg-073e3bca49a6b6ca3` |
| Client public CIDR | `211.60.158.133/32` |

## 3. Artifacts

| Artifact | Path |
| --- | --- |
| Run directory | `harness/results/aws-direct-origin-20260623T124641Z/` |
| Client result | `harness/results/aws-direct-origin-20260623T124641Z/ec2-client/results/client.json` |
| Server result | `harness/results/aws-direct-origin-20260623T124641Z/ec2-server-collected/ec2-server-aws-direct-origin-20260623T124641Z/results/server.json` |
| Client qlog | `harness/results/aws-direct-origin-20260623T124641Z/ec2-client/qlog/19da4df8bedf3d40c60408f18e0922_client.sqlog` |
| Server qlog | `harness/results/aws-direct-origin-20260623T124641Z/ec2-server-collected/ec2-server-aws-direct-origin-20260623T124641Z/qlog/19da4df8bedf3d40c60408f18e0922_server.sqlog` |
| Combined qlog path evidence | `harness/results/aws-direct-origin-20260623T124641Z/qlog-path-validation-combined.txt` |
| Server pcap | `harness/results/aws-direct-origin-20260623T124641Z/ec2-server-collected/ec2-server-aws-direct-origin-20260623T124641Z/pcap/server-udp4242.pcap` |

## 4. Client Result

Client result:

```json
{
  "ok": true,
  "server_addr": "3.36.93.221:4242",
  "socket_a_local_addr": "[::]:64273",
  "socket_b_local_addr": "[::]:58085",
  "connection_local_addr_after_dial": "[::]:64273",
  "connection_local_addr_after_probe": "[::]:64273",
  "connection_local_addr_after_switch": "[::]:64273",
  "connection_local_addr_after_after_payload": "[::]:58085",
  "switch_before_probe_error": "path not yet validated",
  "switch_before_probe_matched": true,
  "probe_duration_millis": 11,
  "local_addr_changed_to_socket_b": true
}
```

Client sent payloads:

| Label | Bytes | Stream ID | SHA-256 |
| --- | ---: | --- | --- |
| before | 1048576 | 2 | `e59b10ce8e18ca1db44526202f0287fcc77eb0cebe041bb686d8b16a91bc9482` |
| after | 1048576 | 6 | `c1d467c8adf86f5b3ebafc910c09b1240b3f249888d7cefa30958243243a3aec` |

## 5. Server Result

Server result:

```json
{
  "ok": true,
  "listen_addr": "0.0.0.0:4242",
  "connection_local_addr": "172.31.1.204:4242",
  "connection_remote_addr": "211.60.158.133:64273"
}
```

Server received payloads:

| Label | Bytes | Stream ID | Remote address at receive | SHA-256 |
| --- | ---: | --- | --- | --- |
| before | 1048576 | 2 | `211.60.158.133:64273` | `e59b10ce8e18ca1db44526202f0287fcc77eb0cebe041bb686d8b16a91bc9482` |
| after | 1048576 | 6 | `211.60.158.133:58085` | `c1d467c8adf86f5b3ebafc910c09b1240b3f249888d7cefa30958243243a3aec` |

해석:

- server는 같은 QUIC connection에서 before/after payload를 모두 받았다.
- migration 후 server가 관찰한 client UDP source port가 `64273`에서 `58085`로 바뀌었다.
- payload SHA-256이 client/server 사이에서 일치한다.

## 6. qlog and pcap Evidence

qlog path validation evidence:

```text
path_challenge/path_response combined occurrences: 6
```

대표 qlog sequence:

```text
client packet_sent: path_challenge
server packet_received: path_challenge
server packet_sent: path_response + path_challenge
client packet_received: path_response + path_challenge
client packet_sent: path_response
server packet_received: path_response
```

server pcap:

```text
server-udp4242.pcap size: 2,300,147 bytes
packets involving client port 64273: 981
packets involving client port 58085: 922
```

## 7. Success Criteria

| 기준 | 결과 |
| --- | --- |
| client `ok: true` | PASS |
| server `ok: true` | PASS |
| PATH_CHALLENGE/PATH_RESPONSE qlog | PASS |
| source tuple change | PASS: `211.60.158.133:64273 -> 211.60.158.133:58085` |
| before/after payload continuity | PASS |
| no application reconnect | PASS |
| pcap collected | PASS |

## 8. Interpretation

이 실험은 다음을 주장할 수 있게 한다.

> quic-go active Connection Migration은 AWS EC2 public direct-origin 환경에서 성공했다.

하지만 다음은 아직 주장하면 안 된다.

- AWS NLB 뒤에서도 성공한다.
- CloudFront/CDN 환경에서도 end-to-end CM이 된다.
- HAProxy 같은 HTTP/3 proxy에서도 CM이 된다.
- Android Chrome/Cronet workload에서 웹 작업 연속성이 유지된다.

따라서 다음 실험은 실패 계층을 분리하기 위한 negative/limited/deployment control이어야 한다.

## 9. Next Experiment

추천 다음 순서:

1. quiche path-event timeline extraction
2. HAProxy HTTP/3 negative control
3. AWS NLB QUIC + s2n-quic CID-aware routing feasibility
4. CloudFront viewer-edge limited control
5. Cronet Android application workload
