# QUIC / HTTP/3 Connection Migration Research

이 저장소는 QUIC/HTTP/3 Connection Migration이 실제 웹 작업 연속성으로 이어지는 조건을 조사한 연구 기록이다.

핵심 질문은 단순히 "Connection Migration이 되는가?"가 아니다.

> QUIC Connection Migration은 구현체 수준에서는 어느 정도 존재하지만, 실제 HTTP/3 웹 작업 연속성으로 배포되려면 어떤 조건이 추가로 필요한가?

## 핵심 결론

현재까지의 실험 결과를 중립적으로 정리하면 다음과 같다.

1. QUIC Connection Migration은 여러 구현체에 실제 primitive와 test evidence가 있다.
2. quic-go direct-origin 환경에서는 controlled active migration이 성공했다.
3. HAProxy는 HTTP/3 baseline 요청은 처리했지만 active migration path validation은 실패했다.
4. AWS NLB는 QUIC-LB plaintext CID format과 registered `QuicServerId`가 맞을 때 migration 후 same-target continuity를 유지했다.
5. CID format이 틀리거나 Server ID가 mismatch되면 target health가 정상이어도 QUIC application payload가 실패했다.
6. controlled quic-go + AWS NLB `TCP_QUIC :443` 환경에서는 HTTP/3 post-migration request continuity와 1MiB mid-flight upload/download continuity가 관찰됐다.
7. Chrome 149 headless baseline에서 local quic-go H3 origin으로 단일 request, page+subresource sequence, polling workload가 HTTP/3로 도달하는 것을 확인했다.
8. Chrome slow subresource 중 inactive interface toggle은 workload를 깨지 않았지만 실제 QUIC path migration을 만들지는 않았다.
9. Chrome slow workload는 local Wi-Fi IP origin에서도 HTTP/3로 성립했지만, inactive interface toggle은 여전히 migration evidence를 만들지 못했다.
10. Chrome natural Alt-Svc control에서는 local self-signed 또는 mkcert origin이 h3를 광고해도 강제 QUIC 없이 실제 HTTP/3 application request가 관찰되지는 않았다. HTML diagnostic에서는 QUIC/H3 후보 연결이 열렸지만 인증서 검증 실패 또는 broken alternative service로 끝났다.
11. 아직 Chrome/Android 실제 Wi-Fi/LTE handover나 CloudFront origin end-to-end continuity를 검증한 것은 아니다.

따라서 현재 결론은 "항상 된다"도 "안 된다"도 아니다.

> 특정 조건에서는 된다. 하지만 실제 웹/모바일 배포에서 그 조건이 충족되는지는 deployment path, browser/client policy, application recovery를 추가로 검증해야 한다.

## 저장소 구조

```text
.
├── README.md
├── data/
│   ├── experiment-results.csv
│   ├── implementation-survey.csv
│   ├── literature-review-tracker.csv
│   └── quiche-path-event-timeline.csv
├── docs/
│   ├── experiment-report-ko.md
│   ├── code-architecture-ko.md
│   └── results/
│       └── 개별 실험 결과 문서
├── harness/
│   ├── config/*.example
│   ├── manifests/experiment-matrix.csv
│   └── scripts/
├── paper/
│   ├── detailed-paper-plan-ko.md
│   └── detailed-paper-plan-en.md
├── tools/
│   ├── scan_implementation_evidence.py
│   ├── scan_qlog_events.py
│   ├── summarize_experiment_results.py
│   └── validate_publication_bundle.py
└── repro/
    └── quic-go-min-repro/
```

## 주요 문서

- [실험 결과 상세 보고서](docs/experiment-report-ko.md)
- [코드/하네스 구조 설명](docs/code-architecture-ko.md)
- [재현 가이드](docs/reproducibility-guide-ko.md)
- [스캐너와 도구 설명](docs/scanners-and-tools-ko.md)
- [논문 상세안 한국어](paper/detailed-paper-plan-ko.md)
- [논문 상세안 영어](paper/detailed-paper-plan-en.md)
- [실험 결과 CSV](data/experiment-results.csv)
- [구현체 조사 CSV](data/implementation-survey.csv)

## 재현 코드

핵심 재현 코드는 [repro/quic-go-min-repro](repro/quic-go-min-repro)에 있다.

주요 구성:

- `cmd/client`: QUIC transport stream migration client
- `cmd/server`: QUIC transport stream migration server
- `cmd/h3client`: HTTP/3 workload migration client
- `cmd/h3server`: HTTP/3 workload migration server
- `internal/common`: payload, TLS, logging, AWS NLB CID helper
- `scripts`: local/EC2/AWS 실행 wrapper

가장 빠른 로컬 검증:

```bash
python3 tools/validate_publication_bundle.py
python3 tools/summarize_experiment_results.py
cd repro/quic-go-min-repro
go test ./...
RUN_ID=local-h3-workload-check ./scripts/run-local-h3-workload.sh
RUN_ID=local-h3-midflight-check ./scripts/run-local-h3-midflight.sh
```

AWS까지 포함한 재현 절차는 [재현 가이드](docs/reproducibility-guide-ko.md)에 정리했다.

## 주의

이 저장소에는 공개 가능한 source, markdown, CSV만 포함한다.

제외한 항목:

- AWS credential
- local `harness/config/aws.env`
- keylog/qlog raw artifact
- pcap
- EC2 SSH key
- 대용량 실행 artifact

개별 실험의 자세한 artifact 위치와 결과 값은 [docs/experiment-report-ko.md](docs/experiment-report-ko.md)와 [data/experiment-results.csv](data/experiment-results.csv)에 정리되어 있다.
