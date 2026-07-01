# Chapter 7 Reference And Evidence

작성일: `2026-06-30`

이 문서는 Chapter 7 "Controlled Public Origin 구축 및 HTTP/3 Baseline"의 실제 구현 코드, readiness scanner, baseline classifier, 원본 결과, 공식 reference link를 정리한다. 공개 안전성을 위해 hostname, IP address, certificate/private-key path, SSH target, AWS account/instance 식별자는 포함하지 않는다.

## 1. 현재 repo의 구현/실행 근거

| 역할 | 링크 | 설명 |
| --- | --- | --- |
| public origin readiness checker | [tools/check_public_origin_readiness.py](../../tools/check_public_origin_readiness.py) | DNS, TLS/curl HTTPS, status, Alt-Svc 확인 및 redaction |
| controlled public config checker | [tools/check_controlled_public_config.py](../../tools/check_controlled_public_config.py) | ignored local env의 baseline/active/Android readiness 확인 |
| controlled public baseline classifier | [tools/classify_controlled_public_h3_baseline.py](../../tools/classify_controlled_public_h3_baseline.py) | server request/qlog, Chrome public H3 summary, DOM application state를 통합 |
| baseline unlock checker | [tools/check_controlled_public_baseline_unlock.py](../../tools/check_controlled_public_baseline_unlock.py) | baseline PASS classification, final-countable 여부, artifact bundle completeness 확인 |
| controlled public H3 server wrapper | [repro/quic-go-min-repro/scripts/run-controlled-public-h3-server.sh](../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-server.sh) | WebPKI cert/key를 quic-go H3 server에 주입 |
| controlled public browser baseline wrapper | [repro/quic-go-min-repro/scripts/run-controlled-public-h3-browser-baseline.sh](../../repro/quic-go-min-repro/scripts/run-controlled-public-h3-browser-baseline.sh) | readiness -> Chrome public H3 -> combined classifier |
| controlled public preflight | [harness/scripts/controlled-public-preflight.sh](../../harness/scripts/controlled-public-preflight.sh) | local config, readiness, baseline summary, network-change command presence 확인 |
| config initializer | [harness/scripts/init-controlled-public-config.sh](../../harness/scripts/init-controlled-public-config.sh) | ignored config 생성, worksheet/check report 생성 |

## 2. Scanner Trigger Map

자세한 line-level trigger는 별도 표에 고정했다.

- [tables/chapter-07-scanner-trigger-map-20260630.md](tables/chapter-07-scanner-trigger-map-20260630.md)

요약:

| component | 핵심 trigger | 과장 방지 장치 |
| --- | --- | --- |
| `check_public_origin_readiness.py` | DNS address, TLS/curl HTTPS, `Alt-Svc` | `--redact-sensitive`로 host/IP/cert subject/issuer redaction |
| `check_controlled_public_config.py` | baseline required keys, active required keys, Android required keys | baseline ready와 active network-change ready를 분리 |
| `classify_controlled_public_h3_baseline.py` | server request count, qlog H3 evidence, Chrome application H3 job | H3 discovery만으로 PASS 처리하지 않음 |
| `check_controlled_public_baseline_unlock.py` | allowed classification, final-countable validation, bundle completeness | record-only smoke와 final-countable baseline을 구분 |
| `controlled-public-preflight.sh` | config loading, readiness, baseline summary, network-change command presence | next commands 출력 시 host/cert/key/network command redaction |

## 3. 공식 reference links

| source | 링크 | Chapter 7에서의 역할 |
| --- | --- | --- |
| RFC 9000 | [QUIC: A UDP-Based Multiplexed and Secure Transport](https://datatracker.ietf.org/doc/html/rfc9000) | QUIC transport/path validation 기준 |
| RFC 9114 | [HTTP/3](https://datatracker.ietf.org/doc/html/rfc9114) | application HTTP/3 기준 |
| qlog schema | [qlog main schema](https://quicwg.org/qlog/draft-ietf-quic-qlog-main-schema.html) | server qlog artifact 기준 |
| Chromium NetLog capture guide | [Providing Network Details for bug reports](https://www.chromium.org/for-testers/providing-network-details/) | Chrome NetLog 수집 근거 |
| Chromium NetLog event types | [net_log_event_type_list.h](https://chromium.googlesource.com/chromium/src/+/HEAD/net/log/net_log_event_type_list.h) | Chrome QUIC/session event 해석 기준 |
| quic-go HTTP/3 server docs | [Running an HTTP/3 Server](https://quic-go.net/docs/http3/server/) | controlled origin H3 server 구성 근거 |
| quic-go qlog docs | [qlog](https://quic-go.net/docs/quic/qlog/) | qlog 생성 근거 |
| AWS security groups | [Control traffic to resources using security groups](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html) | TCP/UDP 443 inbound requirement reference |
| Let's Encrypt getting started | [Getting Started](https://letsencrypt.org/getting-started/) | WebPKI certificate 준비 reference |

## 4. 원본 결과 문서와 데이터

| 결과/데이터 | 의미 |
| --- | --- |
| [docs/results/controlled-public-origin-h3-plan-20260624.md](../results/controlled-public-origin-h3-plan-20260624.md) | controlled public origin이 필요한 이유와 baseline 설계 |
| [docs/results/controlled-public-application-h3-gate-20260624.md](../results/controlled-public-application-h3-gate-20260624.md) | application H3 evidence gate |
| [docs/results/controlled-public-origin-operations-runbook-20260624.md](../results/controlled-public-origin-operations-runbook-20260624.md) | 운영 runbook |
| [docs/results/controlled-public-origin-aws-provision-20260625.md](../results/controlled-public-origin-aws-provision-20260625.md) | AWS/public origin provision public-safe report |
| [docs/results/controlled-public-origin-workload-deploy-packet-20260701.md](../results/controlled-public-origin-workload-deploy-packet-20260701.md) | non-iPhone workload trial로 이어지는 public H3 origin deployment packet |
| [data/controlled-public-origin-workload-deploy-packet-20260701.json](../../data/controlled-public-origin-workload-deploy-packet-20260701.json) | structured public origin workload deployment packet |
| [docs/results/noniphone-desktop-path-change-readiness-20260701.md](../results/noniphone-desktop-path-change-readiness-20260701.md) | iPhone을 제외한 desktop active secondary path readiness |
| [data/noniphone-desktop-path-change-readiness-20260701.json](../../data/noniphone-desktop-path-change-readiness-20260701.json) | structured non-iPhone desktop path-change readiness |
| [docs/results/controlled-public-baseline-unlock-check-20260624.md](../results/controlled-public-baseline-unlock-check-20260624.md) | final-countable baseline unlock PASS |
| [docs/results/controlled-public-config-check-20260624.md](../results/controlled-public-config-check-20260624.md) | initial config readiness |
| [docs/results/controlled-public-config-check-fresh-20260629.md](../results/controlled-public-config-check-fresh-20260629.md) | fresh config readiness |
| [docs/results/controlled-public-origin-fresh-readiness-20260629.md](../results/controlled-public-origin-fresh-readiness-20260629.md) | fresh readiness redacted output |
| [docs/results/controlled-public-chrome-fresh-origin-smoke-20260629-005-validation.md](../results/controlled-public-chrome-fresh-origin-smoke-20260629-005-validation.md) | record-only fresh origin smoke validation |
| [docs/results/controlled-public-origin-access-check-20260629.md](../results/controlled-public-origin-access-check-20260629.md) | access/recovery diagnostic, migration evidence 아님 |
| [data/controlled-public-origin-access-check-20260629.json](../../data/controlled-public-origin-access-check-20260629.json) | public-safe access diagnostic JSON |
| [data/controlled-public-origin-access-check-rerun-20260629.json](../../data/controlled-public-origin-access-check-rerun-20260629.json) | rerun access diagnostic JSON |

## 5. Reproducibility Commands

public-safe config check:

```bash
python3 tools/check_controlled_public_config.py --require-baseline-ready
```

public origin readiness check:

```bash
python3 tools/check_public_origin_readiness.py \
  --url "$PUBLIC_ORIGIN_URL" \
  --require-h3-alt-svc \
  --redact-sensitive \
  --format markdown
```

baseline unlock check:

```bash
python3 tools/check_controlled_public_baseline_unlock.py \
  --trial-id controlled-public-chrome-h3-baseline-001 \
  --artifact-dir repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001 \
  --require-unlocked
```

server/browser baseline wrappers are documented in the operations runbook and use ignored local config values. Do not commit real hostnames, certificate paths, key paths, SSH targets, or raw artifact bundles.

## 6. Verification Commands

실행한 코드 검증:

```bash
PYTHONPATH=tools python3 tools/test_check_public_origin_readiness.py
PYTHONPATH=tools python3 tools/test_check_controlled_public_config.py
PYTHONPATH=tools python3 tools/test_classify_controlled_public_h3_baseline.py
PYTHONPATH=tools python3 tools/test_check_controlled_public_baseline_unlock.py
```

결과:

| test | result |
| --- | --- |
| `test_check_public_origin_readiness.py` | `check_public_origin_readiness=ok` |
| `test_check_controlled_public_config.py` | `check_controlled_public_config=ok` |
| `test_classify_controlled_public_h3_baseline.py` | PASS, exit 0 |
| `test_check_controlled_public_baseline_unlock.py` | `check_controlled_public_baseline_unlock=ok` |

## 7. Claim Boundary

쓸 수 있는 주장:

> Controlled public application H3 baseline was confirmed with final-countable evidence, so active browser network-change trials can use it as a precondition.

쓸 수 없는 주장:

| 주장 | 이유 |
| --- | --- |
| baseline PASS is CM success | no-change application H3 baseline이다. |
| fresh smoke is final-counting trial | validation 문서상 record-only다. |
| active trial ready | config report에서 `NETWORK_CHANGE_CMD` missing이다. |
| access diagnostic is migration evidence | reachability/recovery diagnostic이다. |
