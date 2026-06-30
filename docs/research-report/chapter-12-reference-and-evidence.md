# Chapter 12 Reference And Evidence

작성일: `2026-06-30`

이 문서는 Chapter 12 "Literature-Based Claim Positioning"의 실제 source files, builder code, external links, claim boundary를 정리한다.

## 1. 현재 repo의 문헌/claim 근거

| 역할 | 링크 | 설명 |
| --- | --- | --- |
| literature tracker | [data/literature-review-tracker.csv](../../data/literature-review-tracker.csv) | multi-cycle literature/source tracker |
| claim positioning CSV | [data/literature-claim-positioning-20260629.csv](../../data/literature-claim-positioning-20260629.csv) | source_id별 supports/does_not_support/experiment_gap |
| Korean positioning report | [docs/results/literature-claim-positioning-20260629.md](../results/literature-claim-positioning-20260629.md) | 한국어 claim positioning |
| English positioning report | [docs/paper/literature-claim-positioning-en-20260629.md](../paper/literature-claim-positioning-en-20260629.md) | 영어 claim positioning |
| builder script | [tools/build_literature_claim_positioning.py](../../tools/build_literature_claim_positioning.py) | source row definition and report generation |
| claim readiness audit | [docs/results/paper-claim-readiness-audit-20260629.md](../results/paper-claim-readiness-audit-20260629.md) | 논문 claim readiness and gaps |
| claim support matrix | [docs/results/paper-claim-support-matrix-20260624.md](../results/paper-claim-support-matrix-20260624.md) | 실험 claim support matrix |

## 2. Builder Trigger Map

자세한 line-level trigger는 별도 표에 고정했다.

- [tables/chapter-12-scanner-trigger-map-20260630.md](tables/chapter-12-scanner-trigger-map-20260630.md)

요약:

| component | 핵심 trigger | 과장 방지 장치 |
| --- | --- | --- |
| `SOURCE_ROWS` | source_id, grade, claim_axis, source, url, supports, does_not_support, experiment_gap | source마다 supported/unsupported boundary를 강제 |
| `compact_rows()` | report table row generation | paper use, supports, does_not_support, gap을 같은 row에 둠 |
| `source_list()` | external source links | link traceability |
| `build_ko()` / `build_en()` | strengthened claims and claims-on-hold sections | 결론 선긋기 |
| external link check table | `curl -L -I` status | broken/blocked link visibility |

## 3. Core External Reference Links

| source_id | source | link | Chapter 12 role |
| --- | --- | --- | --- |
| `ccr2025-wild-cm` | An Analysis of QUIC Connection Migration in the Wild | [ACM DOI](https://dl.acm.org/doi/10.1145/3727063.3727066), [arXiv](https://arxiv.org/abs/2410.06066) | primary related work and gap anchor |
| `rfc9000-cm` | QUIC transport | [RFC 9000](https://datatracker.ietf.org/doc/html/rfc9000) | normative CM/path validation basis |
| `rfc9114-h3-discovery` | HTTP/3 | [RFC 9114](https://datatracker.ietf.org/doc/html/rfc9114) | H3 endpoint discovery baseline |
| `rfc9308-rfc9312-ops` | QUIC applicability/manageability | [RFC 9308](https://datatracker.ietf.org/doc/html/rfc9308), [RFC 9312](https://datatracker.ietf.org/doc/html/rfc9312) | deployment/manageability caution |
| `chromium-cronet-policy` | Cronet migration options | [Android Cronet API](https://developer.android.com/develop/connectivity/cronet/reference/org/chromium/net/ConnectionMigrationOptions) | browser/runtime policy layer |
| `quic-go-docs` | quic-go CM docs | [quic-go Connection Migration](https://quic-go.net/docs/quic/connection-migration/) | implementation positive-control model |
| `ietf-multipath` | multipath QUIC draft | [IETF draft](https://datatracker.ietf.org/doc/draft-ietf-quic-multipath/) | future path-management boundary |
| `swiftshift-2026` | media migration/QoE | [ACM DOI](https://dl.acm.org/doi/10.1145/3798065.3798080) | media/QoE motivation |
| `encor-2026` | mobile handover/application continuity | [arXiv HTML](https://arxiv.org/html/2605.22524v2) | downlink/heartbeat motivation |
| `qasm-2026` | QUIC-aware middleboxes | [arXiv](https://arxiv.org/abs/2602.03354) | manageability friction |
| `quicstep-2026` | CM and censorship circumvention | [PoPETs](https://petsymposium.org/popets/2026/popets-2026-0014.php) | security/privacy value and sensitivity |
| `quic-exfil-2025` | preferred-address misuse | [arXiv](https://arxiv.org/abs/2505.05292) | operational caution |
| `aws-nlb-quic` | AWS NLB QUIC support | [AWS blog](https://aws.amazon.com/blogs/networking-and-content-delivery/introducing-quic-protocol-support-for-network-load-balancer-accelerating-mobile-first-applications/) | CID-aware deployment axis |

## 4. External Link Check

전체 결과는 별도 표에 고정했다.

- [tables/chapter-12-external-link-check-20260630.md](tables/chapter-12-external-link-check-20260630.md)

해석:

| link group | result |
| --- | --- |
| standards and docs | `200` |
| arXiv/PoPETs/AWS/quic-go/Android | `200` |
| ACM DOI pages | `403` via `curl -L -I`, publisher access-control behavior로 기록. alternative source가 있으면 arXiv도 함께 표기 |
| old RFC Editor `.html` link | 기존 산출물에서 `404`였고, datatracker RFC 9308 link로 수정 |

## 5. Reproducibility Commands

Claim positioning matrix regeneration:

```bash
python3 tools/build_literature_claim_positioning.py
```

External link check shape:

```bash
curl -L -I -sS -o /dev/null -w '%{http_code} %{url_effective}' "$URL"
```

## 6. Claim Boundary

쓸 수 있는 주장:

> The literature supports treating browser-visible HTTP/3 Connection Migration as a layered evidence problem involving standards, implementation controls, runtime policy, deployment routing, observability, and workload recovery.

쓸 수 없는 주장:

| 주장 | 이유 |
| --- | --- |
| literature proves Chrome/Safari single-session CM in our handover scenario | runtime artifact가 필요하다 |
| RFC 9000 path validation alone guarantees web task continuity | application workload and browser session evidence가 필요하다 |
| CDN/LB support equals end-to-end origin CM | deployment tier에 따라 continuity 의미가 다르다 |
| media migration paper proves our browser media results | workload/system differs; use only as motivation/QoE framing |
