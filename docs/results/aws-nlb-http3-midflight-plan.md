# AWS NLB HTTP/3 Mid-flight Workload Plan

작성일: 2026-06-24  
상태: local/AWS 실행 완료  
결과 문서: `experiments/aws-nlb-http3-midflight-results-20260624.md`

## 1. Purpose

이전 챕터는 HTTP/3 request 사이의 migration을 검증했다.

```text
POST /upload before
  -> active migration
  -> GET /download after
```

이번 챕터는 더 강한 조건을 검증한다.

```text
HTTP/3 body transfer starts
  -> body transfer is still in flight
  -> active migration
  -> body transfer completes
```

즉, 논문에서 “작업 연속성”에 더 직접적으로 가까운 실험이다.

## 2. Research Questions

RQ1:

> HTTP/3 upload body 전송 중 active Connection Migration을 수행해도 server가 전체 body를 정확히 한 번 수신하는가?

RQ2:

> HTTP/3 download body 수신 중 active Connection Migration을 수행해도 client가 전체 response body를 정확히 한 번 수신하는가?

## 3. Local Gate Design

두 workload는 별도 connection으로 실행한다.

### A. Mid-flight Upload

1. client가 HTTP/3 POST `/upload`를 시작한다.
2. request body reader가 일정 byte threshold에 도달하면 migration을 trigger한다.
3. migration은 `AddPath -> Probe -> Switch` 순서로 수행한다.
4. body reader가 남은 payload를 계속 전송한다.
5. server는 full body checksum을 검증한다.

### B. Mid-flight Download

1. client가 HTTP/3 GET `/download?stream=true`를 시작한다.
2. server가 response body를 chunk 단위로 천천히 write한다.
3. client response body reader가 일정 byte threshold에 도달하면 migration을 trigger한다.
4. client는 남은 response body를 계속 수신한다.
5. client는 full body checksum을 검증한다.

## 4. Success Criteria

| 항목 | 성공 조건 |
| --- | --- |
| upload status | HTTP 200 |
| upload integrity | server decoded payload bytes/checksum match |
| download status | HTTP 200 |
| download integrity | client decoded payload bytes/checksum match |
| migration trigger | threshold 이후 migration trigger timestamp 기록 |
| path validation | PATH_CHALLENGE/PATH_RESPONSE 확인 |
| tuple change | client local addr가 socket B로 변경 |
| manual retry | 필요 없음 |

## 5. Local Command

실행 command:

```bash
cd /Users/manwook-han/Desktop/lab/quic-connection-migration-research/experiments/quic-go-min-repro
./scripts/run-local-h3-midflight.sh
```

결과:

| workload | status |
| --- | --- |
| mid-flight upload | PASS |
| mid-flight download | PASS |

## 6. AWS Extension

local gate 통과 후 기존 NLB script를 다음처럼 확장 실행했다.

```bash
WORKLOAD=h3-midflight-upload NLB_PROTOCOL=TCP_QUIC PORT=443 ./harness/scripts/run-aws-nlb-quic-data-plane.sh
WORKLOAD=h3-midflight-download NLB_PROTOCOL=TCP_QUIC PORT=443 ./harness/scripts/run-aws-nlb-quic-data-plane.sh
```

결과:

| workload | status | artifact |
| --- | --- | --- |
| mid-flight upload | PASS | `harness/results/aws-nlb-h3-midflight-upload-20260623T172119Z/` |
| mid-flight download | PASS | `harness/results/aws-nlb-h3-midflight-download-retry-20260623T173500Z/` |

주의: 첫 download attempt는 client dial 단계에서 timeout이 발생해 retry했다. retry에서는 target health 2/2 이후 client start delay를 두고 성공했다.

## 7. Paper Use

이 챕터 통과로 논문 주장은 다음 단계로 강화됐다.

> AWS NLB `TCP_QUIC :443` can preserve not only post-migration HTTP/3 request continuity, but also selected mid-flight HTTP/3 body transfer continuity under a controlled client-driven migration.

단, 여전히 browser/Cronet policy와 실제 Wi-Fi/LTE handover는 별도 검증으로 남는다.
