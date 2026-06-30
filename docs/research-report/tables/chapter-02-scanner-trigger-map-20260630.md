# Chapter 2 Builder Trigger Map

작성일: `2026-06-30`

이 표는 Chapter 2 “CM 미사용/저가시성 원인 분석”에서 사용한 friction matrix builder가 실제로 어떤 입력 열과 matching term을 읽어 어떤 산출물을 만드는지 추적한다. Chapter 2는 source scanner나 AI semantic classifier가 아니라, CSV 기반 term matcher다.

## 1. Builder Input And Matching Logic

| 코드 위치 | trigger/input | 출력 필드 | 해석 |
| --- | --- | --- | --- |
| [build_cm_operational_friction_matrix.py#L14-L18](../../../tools/build_cm_operational_friction_matrix.py#L14-L18) | `data/cm-operational-friction-rubric.csv`, `data/experiment-results.csv`, `data/literature-review-tracker.csv` | default input/output paths | 어떤 원본 데이터로 friction matrix를 만들었는지 고정 |
| [build_cm_operational_friction_matrix.py#L21-L35](../../../tools/build_cm_operational_friction_matrix.py#L21-L35) | `FrictionRow` dataclass fields | `friction_id`, `layer`, evidence counts, `paper_use` | 보고서에 나가는 row schema |
| [build_cm_operational_friction_matrix.py#L42-L47](../../../tools/build_cm_operational_friction_matrix.py#L42-L47) | semicolon-separated terms and selected row columns | normalized lowercase text | rubric term을 부분 문자열로 비교하기 위한 전처리 |
| [build_cm_operational_friction_matrix.py#L50-L58](../../../tools/build_cm_operational_friction_matrix.py#L50-L58) | `terms_any` partial-string match | matched rows | semantic 판정이 아니며 false positive 가능성이 있음 |
| [build_cm_operational_friction_matrix.py#L67-L78](../../../tools/build_cm_operational_friction_matrix.py#L67-L78) | confidence, experiment count, literature count | `paper_use` label | local evidence와 literature evidence를 구분해 claim 강도를 낮춤 |

## 2. Experiment And Literature Trigger Columns

| 코드 위치 | trigger/input | 출력 필드 | 해석 |
| --- | --- | --- | --- |
| [build_cm_operational_friction_matrix.py#L81-L87](../../../tools/build_cm_operational_friction_matrix.py#L81-L87) | loaded rubric, experiment corpus, literature tracker | matrix rows | rubric row마다 별도 evidence count 생성 |
| [build_cm_operational_friction_matrix.py#L88-L100](../../../tools/build_cm_operational_friction_matrix.py#L88-L100) | `experiment_terms_any` against `trial_id`, `status`, `implementation`, `deployment_tier`, `migration_trigger`, `failure_layer`, `notes` | experiment matches | 로컬/AWS/브라우저 실험 row가 해당 friction에 닿는지 집계 |
| [build_cm_operational_friction_matrix.py#L101-L105](../../../tools/build_cm_operational_friction_matrix.py#L101-L105) | `literature_terms_any` against `grade`, `type`, `title`, `venue_or_status`, `relevance`, `next_action` | literature matches | RFC, 논문, 공식 문서, draft, issue row가 해당 friction에 닿는지 집계 |
| [build_cm_operational_friction_matrix.py#L106-L123](../../../tools/build_cm_operational_friction_matrix.py#L106-L123) | matched experiment status and literature grade | status/grade counts | count를 claim 자체가 아니라 근거 후보 수로만 사용 |
| [build_cm_operational_friction_matrix.py#L125-L134](../../../tools/build_cm_operational_friction_matrix.py#L125-L134) | complete row list | generated matrix object | generated date, source paths, layer count, paper-use count 포함 |

## 3. Report And CSV Emission

| 코드 위치 | trigger/input | 출력 파일 | 해석 |
| --- | --- | --- | --- |
| [build_cm_operational_friction_matrix.py#L144-L200](../../../tools/build_cm_operational_friction_matrix.py#L144-L200) | matrix object | `docs/results/cm-operational-friction-matrix-20260624.md` | paper-facing matrix와 claim boundary 문단 생성 |
| [build_cm_operational_friction_matrix.py#L203-L211](../../../tools/build_cm_operational_friction_matrix.py#L203-L211) | matrix rows | `data/cm-operational-friction-matrix-20260624.csv` | row별 재검산 가능한 CSV 생성 |
| [build_cm_operational_friction_matrix.py#L214-L232](../../../tools/build_cm_operational_friction_matrix.py#L214-L232) | CLI args | markdown/CSV regeneration | 논문 제출 전 같은 builder를 재실행 가능 |

## 4. Input/Output Files

| artifact | 역할 |
| --- | --- |
| [data/cm-operational-friction-rubric.csv](../../../data/cm-operational-friction-rubric.csv) | friction_id, layer, matching term, claim scope 정의 |
| [data/experiment-results.csv](../../../data/experiment-results.csv) | local implementation, AWS NLB, browser/public-origin 실험 row |
| [data/literature-review-tracker.csv](../../../data/literature-review-tracker.csv) | RFC, 논문, 공식 문서, draft, issue link tracker |
| [data/cm-operational-friction-matrix-20260624.csv](../../../data/cm-operational-friction-matrix-20260624.csv) | builder가 만든 row별 count CSV |
| [docs/results/cm-operational-friction-matrix-20260624.md](../../results/cm-operational-friction-matrix-20260624.md) | 보고서/논문용 friction matrix |

## 5. False-Positive Guards

| guard | 코드 근거 | 방지하는 오해 |
| --- | --- | --- |
| term matcher임을 명시 | [build_cm_operational_friction_matrix.py#L50-L58](../../../tools/build_cm_operational_friction_matrix.py#L50-L58) | term hit를 의미론적 결론으로 오해하는 것 |
| count와 claim 분리 | [build_cm_operational_friction_matrix.py#L67-L78](../../../tools/build_cm_operational_friction_matrix.py#L67-L78) | count가 많으면 더 중요하다고 자동 결론내는 것 |
| source path 고정 | [build_cm_operational_friction_matrix.py#L14-L18](../../../tools/build_cm_operational_friction_matrix.py#L14-L18) | 어떤 corpus에서 뽑았는지 모르는 hallucinated matrix가 되는 것 |
| claim boundary 출력 | [build_cm_operational_friction_matrix.py#L194-L198](../../../tools/build_cm_operational_friction_matrix.py#L194-L198) | Chrome/Safari/Android handover 성공을 premature하게 쓰는 것 |
