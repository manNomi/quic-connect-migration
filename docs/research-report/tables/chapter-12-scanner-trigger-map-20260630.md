# Chapter 12 Builder Trigger Map

작성일: `2026-06-30`

이 표는 Chapter 12 literature claim positioning에서 어떤 builder 코드가 어떤 근거를 생성하는지 line-level로 정리한다.

## 1. Source Row Schema

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [build_literature_claim_positioning.py#L17-L30](../../../tools/build_literature_claim_positioning.py#L17-L30) | `MATRIX_FIELDS` | required CSV/report fields | source별 boundary schema |
| [build_literature_claim_positioning.py#L33-L216](../../../tools/build_literature_claim_positioning.py#L33-L216) | `SOURCE_ROWS` | source_id, grade, claim_axis, url, supports, does_not_support, experiment_gap | hallucination 방지 핵심 구조 |
| [build_literature_claim_positioning.py#L231-L236](../../../tools/build_literature_claim_positioning.py#L231-L236) | `SOURCE_ROWS` and `MATRIX_FIELDS` | CSV output | machine-readable claim positioning |
| [build_literature_claim_positioning.py#L239-L251](../../../tools/build_literature_claim_positioning.py#L239-L251) | compact source rows | markdown matrix rows | report table |
| [build_literature_claim_positioning.py#L254-L255](../../../tools/build_literature_claim_positioning.py#L254-L255) | source URL list | Source Links section | external traceability |

## 2. Claim Boundary Sections

| 코드 위치 | trigger/input | 출력/효과 | 해석 |
| --- | --- | --- | --- |
| [build_literature_claim_positioning.py#L258-L315](../../../tools/build_literature_claim_positioning.py#L258-L315) | Korean report builder | purpose, matrix, strengthened claims, claims on hold, next priority | Korean claim boundary |
| [build_literature_claim_positioning.py#L318-L375](../../../tools/build_literature_claim_positioning.py#L318-L375) | English report builder | English equivalent positioning | paper draft reuse |
| [build_literature_claim_positioning.py#L378-L384](../../../tools/build_literature_claim_positioning.py#L378-L384) | file writes | CSV, Korean report, English report | reproducible generation |

## 3. Source-Level Guards

| source row | 코드 위치 | guard |
| --- | --- | --- |
| wild CM measurement | [build_literature_claim_positioning.py#L33-L47](../../../tools/build_literature_claim_positioning.py#L33-L47) | Internet-wide support unevenness does not prove browser workload continuity |
| RFC 9000 | [build_literature_claim_positioning.py#L48-L61](../../../tools/build_literature_claim_positioning.py#L48-L61) | path validation is necessary but not sufficient |
| RFC 9114 | [build_literature_claim_positioning.py#L62-L75](../../../tools/build_literature_claim_positioning.py#L62-L75) | H3 discovery does not imply migration |
| RFC 9308/9312 | [build_literature_claim_positioning.py#L76-L89](../../../tools/build_literature_claim_positioning.py#L76-L89) | deployment maturity separate from transport feature existence |
| Chromium/Cronet | [build_literature_claim_positioning.py#L90-L103](../../../tools/build_literature_claim_positioning.py#L90-L103) | policy knobs do not prove runtime migration |
| quic-go | [build_literature_claim_positioning.py#L104-L117](../../../tools/build_literature_claim_positioning.py#L104-L117) | library positive control does not generalize to browser handover |
| multipath | [build_literature_claim_positioning.py#L118-L131](../../../tools/build_literature_claim_positioning.py#L118-L131) | multipath does not prove current single-path browser CM |
| media/QoE | [build_literature_claim_positioning.py#L132-L145](../../../tools/build_literature_claim_positioning.py#L132-L145) | media migration paper motivates QoE but does not prove our rows |
| mobile handover | [build_literature_claim_positioning.py#L146-L159](../../../tools/build_literature_claim_positioning.py#L146-L159) | adjacent mobile handover does not replace direct browser measurement |
| middlebox | [build_literature_claim_positioning.py#L160-L173](../../../tools/build_literature_claim_positioning.py#L160-L173) | middlebox friction does not prove a specific failure cause |
| security/privacy | [build_literature_claim_positioning.py#L174-L201](../../../tools/build_literature_claim_positioning.py#L174-L201) | security value/risk is not continuity evidence |
| AWS NLB | [build_literature_claim_positioning.py#L202-L215](../../../tools/build_literature_claim_positioning.py#L202-L215) | LB CID behavior not a substitute for end-to-end browser-origin CM |

## 4. False-Positive Guards

| guard | 코드 근거 | 방지하는 오해 |
| --- | --- | --- |
| `does_not_support` required | [build_literature_claim_positioning.py#L24-L29](../../../tools/build_literature_claim_positioning.py#L24-L29) | source를 결론에 끼워 맞추는 것 |
| claims-on-hold section | [build_literature_claim_positioning.py#L292-L296](../../../tools/build_literature_claim_positioning.py#L292-L296) | Chrome/Safari CM success overclaim |
| English claims-on-hold section | [build_literature_claim_positioning.py#L352-L356](../../../tools/build_literature_claim_positioning.py#L352-L356) | paper draft에서 같은 overclaim 반복 |
| source links section | [build_literature_claim_positioning.py#L306-L312](../../../tools/build_literature_claim_positioning.py#L306-L312) | unsupported citation/reference drift |
