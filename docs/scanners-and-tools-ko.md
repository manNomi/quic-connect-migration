# 스캐너와 도구 설명

작성일: 2026-06-24  
목적: 연구 과정에서 사용한 수동 검수 절차를 공개 repo에서 반복 가능한 스캐너와 요약 도구로 고정한다.

## 1. `tools/validate_publication_bundle.py`

공개 repo에 올리기 직전 실행하는 안전성/재현성 검증기다.

실행:

```bash
python3 tools/validate_publication_bundle.py
```

검사 항목:

| 항목 | 검사 내용 |
| --- | --- |
| forbidden artifacts | tracked 파일 중 keylog, qlog raw, pcap, pem, tarball 포함 여부 |
| secret patterns | AWS key, secret label, GitHub token, private key, IAM ARN 패턴 |
| CSV parse | `data/*.csv`, `harness/manifests/*.csv` 파싱 가능 여부 |
| Markdown links | repo 내부 Markdown link 존재 여부 |
| harness paths | 공개 repo에서 사용할 수 없는 과거 `experiments/` 경로 참조 여부 |

이 도구는 논문용 public artifact를 만들 때 반드시 먼저 통과해야 한다.

기본값은 git-tracked 파일만 검사한다. 로컬 ignored artifact까지 일부러 확인하려면 다음처럼 실행한다.

```bash
python3 tools/validate_publication_bundle.py --include-untracked
```

## 2. `tools/summarize_experiment_results.py`

[data/experiment-results.csv](../data/experiment-results.csv)를 읽어서 trial 상태를 요약한다.

실행:

```bash
python3 tools/summarize_experiment_results.py --format markdown
python3 tools/summarize_experiment_results.py --format json
```

출력:

- 전체 trial 수
- status별 count
- application success별 count
- trial별 implementation, deployment tier, protocol, failure layer

논문 표를 만들 때 이 도구의 출력과 원본 CSV를 함께 사용한다.

## 3. `tools/scan_implementation_evidence.py`

QUIC 구현체 repo를 대상으로 connection migration 관련 evidence를 찾는 scanner다.

실행 예시:

```bash
python3 tools/scan_implementation_evidence.py ../quic-go ../quiche ../s2n-quic --format markdown
```

출력 형식:

```bash
python3 tools/scan_implementation_evidence.py ../quic-go --format csv
python3 tools/scan_implementation_evidence.py ../quic-go --format json
```

스캔 범주:

| category | 대표 키워드 |
| --- | --- |
| `path_validation` | `PATH_CHALLENGE`, `PATH_RESPONSE`, `path validation` |
| `active_migration_api` | `AddPath`, `Probe`, `Switch`, `perform-migration`, `probe_path` |
| `passive_rebinding` | `NAT rebinding`, `rebinding`, `peer address`, `tuple change` |
| `disable_migration_policy` | `disable_active_migration`, `DisableActiveMigration` |
| `preferred_address` | `preferred address`, `preferred_address`, `PreferredAddress` |
| `cid_and_load_balancing` | `ConnectionIDGenerator`, `QuicServerId`, `QUIC-LB`, `Server ID` |
| `observability` | `qlog`, `PathEvent`, `NetLog`, `tracing` |
| `tests` | `migration test`, `rebinding test`, `path test` |

해석 규칙:

- match count가 높다고 성숙도가 높다는 뜻은 아니다.
- test-only API와 production API를 구분해야 한다.
- active migration, passive rebinding, preferred address는 서로 다른 능력이다.
- HTTP/3 client가 그 기능을 실제로 노출하는지 별도로 확인해야 한다.
- CDN/LB 환경에서는 CID routing과 backend affinity가 별도 검증 대상이다.

## 4. `tools/scan_qlog_events.py`

실험 후 생성된 qlog/qlog-derived text에서 migration evidence를 카운트한다.

실행:

```bash
python3 tools/scan_qlog_events.py repro/quic-go-min-repro/artifacts/local-h3-midflight-check --format markdown
```

카운트 항목:

| 항목 | 의미 |
| --- | --- |
| `path_challenge` | 새 path validation challenge |
| `path_response` | 새 path validation response |
| `connection_started` | connection 생성 evidence |
| `connection_closed` | connection 종료 evidence |
| `packet_sent` | packet sent event |
| `packet_received` | packet received event |
| `http3_frame` | HTTP/3 frame event |
| `chosen_alpn` | ALPN `h3` negotiation evidence |
| `migration` | migration 문자열 evidence |
| `path` | path 관련 event evidence |

주의:

이 도구는 qlog를 정식 schema parser로 해석하지 않고, 반복 가능한 keyword count를 만든다. 논문에는 qlog scanner 결과만 단독 근거로 쓰지 말고, client/server result JSON과 함께 사용한다.

## 5. 실험 실행 코드

핵심 코드는 [repro/quic-go-min-repro](../repro/quic-go-min-repro)에 있다.

| 파일 | 역할 |
| --- | --- |
| `cmd/client/main.go` | QUIC transport stream migration client |
| `cmd/server/main.go` | QUIC transport stream migration server |
| `cmd/h3client/main.go` | HTTP/3 workload migration client |
| `cmd/h3server/main.go` | HTTP/3 upload/download server |
| `internal/common/aws_nlb_cid.go` | AWS NLB QUIC-LB plaintext CID generator |
| `internal/common/payload.go` | deterministic payload/checksum |
| `internal/common/logging.go` | JSONL/result JSON writer |
| `internal/common/tls.go` | self-signed TLS config |

로컬 wrapper:

| 파일 | 역할 |
| --- | --- |
| `scripts/run-local-happy-path.sh` | transport-level local migration |
| `scripts/run-local-h3-workload.sh` | HTTP/3 POST before, migrate, GET after |
| `scripts/run-local-h3-midflight.sh` | HTTP/3 upload/download body in-flight migration |
| `scripts/run-ec2-client.sh` | AWS/NLB transport client runner |
| `scripts/run-h3-client.sh` | AWS/NLB HTTP/3 client runner |
| `scripts/run-h3-server.sh` | AWS/NLB HTTP/3 target server runner |
| `scripts/package-for-ec2.sh` | EC2 target 배포용 tarball 생성 |

AWS wrapper:

| 파일 | 역할 |
| --- | --- |
| `harness/scripts/aws-preflight.sh` | AWS CLI, region, VPC/subnet 사전 확인 |
| `harness/scripts/package-quic-go-ec2.sh` | public repo 구조 기준 EC2 package 생성 |
| `harness/scripts/run-aws-nlb-quic-data-plane.sh` | EC2 A/B, NLB, target group, client, cleanup end-to-end |
| `harness/scripts/run-local-quic-go.sh` | harness 결과 디렉터리에 local transport 실행 |
| `harness/scripts/validate-quic-go-artifacts.sh` | local transport artifact 검증 |
| `harness/scripts/run-local-s2n-nlb-cid-proof.sh` | NLB CID provider local proof wrapper |

## 6. 최소 검증 세트

논문용 결과를 갱신하기 전 최소한 다음은 통과시킨다.

```bash
python3 tools/validate_publication_bundle.py
python3 tools/summarize_experiment_results.py --format markdown
python3 tools/scan_implementation_evidence.py repro/quic-go-min-repro --format markdown

cd repro/quic-go-min-repro
go test ./...
RUN_ID=local-h3-workload-check ./scripts/run-local-h3-workload.sh
RUN_ID=local-h3-midflight-check ./scripts/run-local-h3-midflight.sh
```

AWS 결과를 갱신할 때는 [재현 가이드](reproducibility-guide-ko.md)의 cleanup 확인까지 포함한다.
