# AWS Testbed Plan

이 문서는 AWS에서 QUIC Connection Migration 성숙도를 검증하기 위한 실험 계획 초안이다.

## 1. Experiment Tiers

### Tier 1. EC2 Direct Origin

목적:

- CDN/LB 없이 client와 origin server 사이에서 QUIC Connection Migration이 실제로 동작하는지 확인한다.

구성:

```text
Android Chrome or custom QUIC client
        |
        | UDP 443 / TCP 443
        |
EC2 public IPv4
        |
Instrumented QUIC/HTTP3 server
```

후보 구현체:

- s2n-quic
- quiche
- quic-go
- ngtcp2

관측:

- server qlog
- client NetLog or client qlog
- tcpdump on EC2
- application request log

성공 기준:

- migration 전후 UDP tuple이 바뀐다.
- 같은 QUIC connection 또는 migration event가 관측된다.
- `PATH_CHALLENGE` / `PATH_RESPONSE` path validation이 성공한다.
- application stream/request가 사용자 개입 없이 완료된다.

### Tier 2. CloudFront Viewer-Edge

목적:

- 관리형 edge 환경에서 viewer-side HTTP/3 continuity가 있는지 확인한다.

구성:

```text
Android Chrome
        |
        | HTTP/3 / QUIC
        |
CloudFront edge
        |
        | HTTP/1.1 or HTTP/2 to origin
        |
Origin server
```

해석:

- 이 실험은 end-to-end QUIC Connection Migration 검증이 아니다.
- viewer-to-CloudFront edge continuity 검증이다.

성공 기준:

- viewer connection이 `h3`로 협상된다.
- Wi-Fi/cellular transition 중 요청이 유지되거나 빠르게 복구된다.
- 단, CloudFront 내부 QUIC migration event는 researcher가 직접 보기 어렵다.

### Tier 3. AWS NLB QUIC Passthrough

목적:

- LB 뒤에서 QUIC CID 기반 routing이 migration을 지원하는지 확인한다.

구성:

```text
Android Chrome or custom QUIC client
        |
        | QUIC / UDP 443
        |
AWS Network Load Balancer QUIC listener
        |
        | QUIC passthrough
        |
EC2 target with QUIC Server ID-aware CID generator
```

핵심 요구사항:

- NLB target group protocol: `QUIC` or `TCP_QUIC`
- target registration requires `QuicServerId`
- server-generated CID must encode matching 8-byte Server ID
- each target needs unique Server ID

성공 기준:

- initial traffic reaches target.
- after client source IP/port changes, NLB still routes packets with same CID Server ID to same target.
- target server observes path validation/migration success.

주요 위험:

- 일반 HTTP/3 server가 AWS NLB가 요구하는 CID Server ID format을 만들지 못할 수 있다.
- s2n-quic custom CID generator 또는 AWS sample이 필요할 수 있다.

## 2. First Experiment Recommendation

첫 실험은 NLB부터 시작하지 않는다. 순서는 다음이 좋다.

1. EC2 direct origin에서 custom QUIC client/server로 migration을 먼저 재현한다.
2. 같은 서버에서 Android Chrome이 HTTP/3로 접속하는지 확인한다.
3. Android Wi-Fi/cellular transition에서 application request가 유지되는지 확인한다.
4. CloudFront viewer-edge continuity를 별도 확인한다.
5. 마지막으로 NLB QUIC passthrough를 구성한다.

## 3. Minimal Data Schema

각 trial마다 다음 정보를 저장한다.

```text
trial_id
date
client_type
client_network_before
client_network_after
server_implementation
deployment_tier
protocol
migration_trigger
source_tuple_before
source_tuple_after
connection_id_before
connection_id_after
path_validation_observed
application_task
application_success
manual_intervention_required
failure_layer
notes
```

## 4. Artifacts to Preserve

- server qlog
- client qlog or Chrome NetLog
- tcpdump pcap
- server application log
- client application metrics
- exact server version/commit
- exact AWS resource configuration

