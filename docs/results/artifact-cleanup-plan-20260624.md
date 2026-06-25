# Local artifact cleanup plan

작성일: 2026-06-24

## 1. 목적

현재 browser handover 본 실험을 막는 blocker 중 하나는 낮은 디스크 여유 공간이다. 2026-06-24 기준 local artifact root는 약 908.3 MiB이고, 전체 볼륨 여유 공간은 약 2.44 GiB다. 장시간 Chrome NetLog, qlog, packet capture를 수집하려면 최소 floor 5 GiB에 다음 capture reserve 2 GiB를 더한 7 GiB 이상을 확보하는 것이 안전하다.

이 문서는 삭제를 실행하지 않는다. 어떤 artifact가 cleanup 후보인지와 삭제 전 확인할 조건만 정리한다.

자동 dry-run 계산 결과는 `docs/results/artifact-cleanup-dry-run-20260624.md`에 있다.

## 2. 현재 상위 cleanup 후보

`tools/report_artifact_storage.py` 기준 상위 artifact directory:

| 후보 | 크기 | 메모 |
| --- | ---: | --- |
| `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-localhost-20260624` | 383.5 MiB | Chrome local Alt-Svc negative/control artifact |
| `repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-local-20260624` | 382.6 MiB | Chrome local Alt-Svc negative/control artifact |
| `repro/quic-go-min-repro/artifacts/chrome-public-h3-cloudflare-quic-20260624` | 7.4 MiB | public H3 discovery/control artifact |
| `repro/quic-go-min-repro/artifacts/chrome-public-h3-youtube-generate204-20260624` | 5.9 MiB | public H3 discovery/control artifact |
| `repro/quic-go-min-repro/artifacts/controlled-public-h3-browser-wrapper-google-smoke-20260624` | 5.7 MiB | wrapper smoke/control artifact |

상위 두 directory만 정리해도 약 766 MiB를 회수할 수 있다. 다만 전체 볼륨 여유 공간을 7 GiB 이상으로 만들려면 repository 외부의 다른 파일 정리도 필요할 가능성이 높다.

## 3. 삭제 전 확인 조건

삭제 전에 다음을 확인한다.

| 확인 항목 | 기준 |
| --- | --- |
| 결과 요약 문서 | 해당 artifact 결과가 `docs/results/*.md`에 요약되어 있음 |
| CSV 기록 | 필요한 경우 `data/experiment-results.csv`에 trial 요약이 있음 |
| raw 재분석 필요성 | NetLog/qlog 원본 재분석 계획이 없거나, 별도 백업이 있음 |
| 공개 검증 | `python3 tools/validate_publication_bundle.py` 통과 |

## 4. 수동 cleanup 예시

삭제를 승인한 뒤에만 실행한다.

```bash
rm -rf repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-localhost-20260624
rm -rf repro/quic-go-min-repro/artifacts/chrome-h3-alt-svc-local-20260624
python3 tools/report_artifact_storage.py --output docs/results/artifact-storage-report-20260624.md
python3 tools/audit_research_bundle.py --output docs/results/research-bundle-audit-20260624.md
```

이 명령은 자동 실행하지 않는다. raw artifact 보존 여부는 연구자가 결정한다.

## 5. 논문상 의미

디스크 상태는 실험 결과 자체가 아니라 실험 가능성 조건이다. 논문에는 raw artifact를 포함하지 않지만, 재현성 부록에서는 다음처럼 기록할 수 있다.

```text
Large browser NetLog/qlog artifacts were kept outside the public repository. Storage readiness was tracked separately, and heavy capture experiments were deferred when free disk space fell below the 7 GiB final-capture threshold.
```
