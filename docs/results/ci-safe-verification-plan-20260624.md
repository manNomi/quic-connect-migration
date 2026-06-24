# CI Safe Verification Plan

작성일: 2026-06-24

## 목적

GitHub Actions에서 논문 재현성 bundle이 깨졌는지 자동으로 확인한다. CI는 외부 네트워크 전환, AWS provisioning, browser NetLog capture, qlog-heavy trial을 실행하지 않는다. 대신 public-safe, non-destructive 검증만 수행한다.

Workflow:

- `.github/workflows/research-verify.yml`

## CI가 실행하는 검증

| step | command | purpose |
| --- | --- | --- |
| publication bundle | `python3 tools/validate_publication_bundle.py` | tracked 문서/CSV에 secret, raw artifact, 깨진 링크가 없는지 확인 |
| research verifier | `python3 tools/verify_research_bundle.py --scratch-dir ...` | paper tables, final gate, readiness, regression tests를 scratch output으로 검증 |
| Go unit tests | `go test ./...` in `repro/quic-go-min-repro` | payload/CID helper 등 core repro code 검증 |
| shell syntax | `bash -n harness/scripts/*.sh` and `bash -n repro/.../scripts/*.sh` | wrapper script syntax regression 방지 |
| no tracked mutation | `git diff --exit-code` | verification이 tracked report를 변경하지 않는지 확인 |

## CI에서 제외하는 것

| excluded | reason |
| --- | --- |
| local H3 migration runs | qlog/keylog/raw artifacts 생성; runner 네트워크 환경이 논문 실험 환경과 다름 |
| Chrome/Safari browser captures | browser availability와 NetLog format이 runner마다 다름 |
| AWS NLB experiments | credential/resource 비용/cleanup risk |
| controlled public active handover | public origin, real secondary path, operator-approved network-change command 필요 |
| Android Chrome handover | physical device/ADB/cellular path 필요 |

## 해석

CI green은 “논문 실험이 완료됐다”는 뜻이 아니다. CI green은 다음만 보장한다.

- 문서/CSV bundle이 public-safe하다.
- verifier와 regression tests가 통과한다.
- final browser handover가 아직 incomplete라면 incomplete로 올바르게 보고된다.
- core Go repro code가 unit-test level에서 깨지지 않았다.

final claim은 여전히 `docs/results/research-bundle-audit-20260624.md`와 final browser handover audit의 상태를 기준으로 판단한다.
