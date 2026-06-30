# Scanner Trigger Audit Index

작성일: `2026-06-30`

이 문서는 조사/실험에서 사용한 scanner, classifier, builder가 어디에서 어떤 조건을 읽어 어떤 산출물을 만들었는지 한 번에 추적하기 위한 감사 인덱스다. 목적은 "AI가 그럴듯하게 쓴 말인지, 실제 코드와 artifact를 읽은 결과인지"를 검증 가능하게 만드는 것이다.

## 1. 전체 구조

| layer | code family | 주 역할 | 상세 trigger map |
| --- | --- | --- | --- |
| implementation source survey | `scan_implementation_evidence.py` | 공개 QUIC 구현체 source tree keyword first-pass scan | [tables/scanner-trigger-summary-20260630.md](tables/scanner-trigger-summary-20260630.md) |
| operational friction matrix | `build_cm_operational_friction_matrix.py` | experiment/literature corpus를 friction_id별로 집계 | [tables/chapter-02-scanner-trigger-map-20260630.md](tables/chapter-02-scanner-trigger-map-20260630.md) |
| implementation positive control | quic-go repro scripts and qlog scanner | local active migration positive control artifact 생성/검증 | [tables/chapter-03-scanner-trigger-map-20260630.md](tables/chapter-03-scanner-trigger-map-20260630.md) |
| deployment path positive/negative controls | AWS NLB CID generator, NLB harness, H3 repro | cloud LB, proxy, CDN boundary와 AWS NLB data-plane 조건 검증 | [tables/chapter-04-scanner-trigger-map-20260630.md](tables/chapter-04-scanner-trigger-map-20260630.md) |
| browser observability | Chrome/Safari/Android readiness and classifiers | browser artifact claim ceiling 설정 | [tables/chapter-05-scanner-trigger-map-20260630.md](tables/chapter-05-scanner-trigger-map-20260630.md) |
| local NAT rebinding | UDP rebinding proxy, Chrome runner, local classifiers | controlled local Chrome rebinding/return-path controls | [tables/chapter-06-scanner-trigger-map-20260630.md](tables/chapter-06-scanner-trigger-map-20260630.md) |
| controlled public origin | readiness/config/baseline scanners | public application H3 baseline gate | [tables/chapter-07-scanner-trigger-map-20260630.md](tables/chapter-07-scanner-trigger-map-20260630.md) |
| public network change | final Chrome runner, path snapshots, network-change classifier | active path change and workload result classification | [tables/chapter-08-scanner-trigger-map-20260630.md](tables/chapter-08-scanner-trigger-map-20260630.md) |
| byte-range retry | range workload parser and result-row guards | application range retry vs CM evidence separation | [tables/chapter-09-scanner-trigger-map-20260630.md](tables/chapter-09-scanner-trigger-map-20260630.md) |
| upload retry | upload workload parser and summarizer | upload retry success vs single-session CM separation | [tables/chapter-10-scanner-trigger-map-20260630.md](tables/chapter-10-scanner-trigger-map-20260630.md) |
| media workload | media/buffered-media summarizers | completion/QoE/session attribution separation | [tables/chapter-11-scanner-trigger-map-20260630.md](tables/chapter-11-scanner-trigger-map-20260630.md) |
| literature claim positioning | `build_literature_claim_positioning.py` | supports/does_not_support/experiment_gap 분리 | [tables/chapter-12-scanner-trigger-map-20260630.md](tables/chapter-12-scanner-trigger-map-20260630.md) |

## 2. Implementation Source Scanner

| code location | trigger/input | output | hallucination guard |
| --- | --- | --- | --- |
| [scan_implementation_evidence.py#L60-L121](../../tools/scan_implementation_evidence.py#L60-L121) | `PATH_CHALLENGE`, `PATH_RESPONSE`, `AddPath`, `Probe(`, `Switch(`, `rebinding`, `disable_active_migration`, `preferred_address`, `qlog`, test patterns | category match schema | keyword hit만 maturity로 해석하지 않음 |
| [scan_implementation_evidence.py#L132-L146](../../tools/scan_implementation_evidence.py#L132-L146) | checked-out source tree files, skip dirs/suffixes | scan file set | artifact/vendor/binary noise 감소 |
| [scan_implementation_evidence.py#L149-L176](../../tools/scan_implementation_evidence.py#L149-L176) | each non-empty line against compiled regexes | match count, files, examples | line-level candidate만 생성 |
| [scan_implementation_evidence.py#L194-L227](../../tools/scan_implementation_evidence.py#L194-L227) | rows | markdown/csv output | source code를 대량 복사하지 않고 file/line anchor만 남김 |
| [scan_implementation_evidence.py#L230-L258](../../tools/scan_implementation_evidence.py#L230-L258) | CLI args: roots, format, max file bytes, max examples | reproducible scan command | missing repo는 exit 2로 실패 |

Scanner output:

- [tables/scanner-trigger-summary-20260630.md](tables/scanner-trigger-summary-20260630.md)

해석 boundary:

- match count는 성숙도 점수가 아니다.
- scanner는 conformance test가 아니다.
- 최종 판정은 source/test/manual run과 결합해야 한다.
- Chromium/Cronet, AWS CloudFront, AWS NLB는 full source scanner 대상이 아니므로 공식 docs와 별도 실험으로 다룬다.

## 3. Friction Matrix Builder

| code location | trigger/input | output | hallucination guard |
| --- | --- | --- | --- |
| [build_cm_operational_friction_matrix.py#L14-L18](../../tools/build_cm_operational_friction_matrix.py#L14-L18) | rubric, experiment corpus, literature tracker paths | fixed default inputs | 어떤 데이터에서 집계했는지 고정 |
| [build_cm_operational_friction_matrix.py#L50-L58](../../tools/build_cm_operational_friction_matrix.py#L50-L58) | `terms_any` partial-string matching | matched rows | semantic classifier가 아님을 명시 |
| [build_cm_operational_friction_matrix.py#L81-L123](../../tools/build_cm_operational_friction_matrix.py#L81-L123) | `experiment_terms_any`, `literature_terms_any` | friction row with counts | count와 claim을 분리 |
| [build_cm_operational_friction_matrix.py#L144-L200](../../tools/build_cm_operational_friction_matrix.py#L144-L200) | matrix object | markdown report with claim boundary | "CM이 없다" 같은 단정 방지 |
| [build_cm_operational_friction_matrix.py#L214-L232](../../tools/build_cm_operational_friction_matrix.py#L214-L232) | CLI outputs | markdown/CSV regeneration | 재현 가능한 산출물 |

Input/output files:

- [data/cm-operational-friction-rubric.csv](../../data/cm-operational-friction-rubric.csv)
- [data/experiment-results.csv](../../data/experiment-results.csv)
- [data/literature-review-tracker.csv](../../data/literature-review-tracker.csv)
- [data/cm-operational-friction-matrix-20260624.csv](../../data/cm-operational-friction-matrix-20260624.csv)
- [docs/results/cm-operational-friction-matrix-20260624.md](../results/cm-operational-friction-matrix-20260624.md)

## 4. Browser And Network-Change Classifiers

| code location | trigger/input | output | hallucination guard |
| --- | --- | --- | --- |
| [classify_chrome_h3_artifacts.py#L13-L24](../../tools/classify_chrome_h3_artifacts.py#L13-L24) | qlog strings such as `path_challenge`, `path_response`, `chosen_alpn`, `http3:frame` | qlog counters | qlog evidence를 명시적 field로 분리 |
| [classify_chrome_h3_artifacts.py#L27-L39](../../tools/classify_chrome_h3_artifacts.py#L27-L39) | NetLog event names containing migration terms | mode/trigger/success/failure class | mode event와 success event를 분리 |
| [classify_chrome_h3_artifacts.py#L88-L141](../../tools/classify_chrome_h3_artifacts.py#L88-L141) | NetLog JSON target host/port | target QUIC sessions and HTTP stream jobs | browser session attribution |
| [classify_chrome_h3_artifacts.py#L144-L171](../../tools/classify_chrome_h3_artifacts.py#L144-L171) | incomplete NetLog text fallback | conservative counts | broken NetLog를 성공으로 과장하지 않음 |
| [classify_chrome_h3_artifacts.py#L193-L206](../../tools/classify_chrome_h3_artifacts.py#L193-L206) | DOM dump data attributes | workload completion | transport evidence와 app outcome 분리 |
| [classify_chrome_h3_artifacts.py#L247-L290](../../tools/classify_chrome_h3_artifacts.py#L247-L290) | server reachability, qlog, NetLog, proxy switch, client path, DOM | classification label | task failure, multiple sessions, tuple-only change를 PASS로 처리하지 않음 |
| [classify_controlled_public_h3_baseline.py#L25-L60](../../tools/classify_controlled_public_h3_baseline.py#L25-L60) | server request list | request/proto/ALPN/remote addr summary | server-side application evidence |
| [classify_controlled_public_h3_baseline.py#L94-L139](../../tools/classify_controlled_public_h3_baseline.py#L94-L139) | Chrome CDP `body_dataset` | workload complete/success/error keys | app task result를 DOM에서 직접 읽음 |
| [classify_controlled_public_h3_baseline.py#L142-L158](../../tools/classify_controlled_public_h3_baseline.py#L142-L158) | server ok, qlog H3, browser H3 | baseline PASS/negative/feasibility | H3 discovery-only overclaim 방지 |
| [classify_controlled_public_h3_network_change.py#L16-L31](../../tools/classify_controlled_public_h3_network_change.py#L16-L31) | target workload labels | filter list | helper/bootstrap request와 target workload 분리 |
| [classify_controlled_public_h3_network_change.py#L54-L68](../../tools/classify_controlled_public_h3_network_change.py#L54-L68) | client path summary JSON | active path change fields | network command와 실제 path change 분리 |
| [classify_controlled_public_h3_network_change.py#L71-L84](../../tools/classify_controlled_public_h3_network_change.py#L71-L84) | server target H3 requests | target remote tuple count | tuple evidence만 별도 집계 |
| [classify_controlled_public_h3_network_change.py#L87-L152](../../tools/classify_controlled_public_h3_network_change.py#L87-L152) | server/qlog/NetLog/path/app/browser fields | PASS, PASS_FEASIBILITY, PASS_NEGATIVE_CONTROL, FAIL | qlog path validation, session count, app success가 모두 맞아야 강한 claim |
| [classify_controlled_public_h3_network_change.py#L168-L226](../../tools/classify_controlled_public_h3_network_change.py#L168-L226) | artifact files | combined summary object | 어떤 raw artifact를 읽었는지 추적 가능 |

Core artifacts/classes:

- `server.json`, `public-origin-readiness.json`, `network-change.json`
- `client-path-change-summary.json`, `client-path-eventual-change-summary.json`
- Chrome NetLog, Chrome CDP DOM dataset, server qlog

## 5. Workload-Specific Trigger Maps

| workload/chapter | implementation trigger | result parser | main overclaim guard |
| --- | --- | --- | --- |
| full-response downlink, Chapter 8 | [chapter-08 trigger map](tables/chapter-08-scanner-trigger-map-20260630.md) | `classify_controlled_public_h3_network_change.py` | application failure and missing qlog path validation are negative controls |
| byte-range retry, Chapter 9 | [chapter-09 trigger map](tables/chapter-09-scanner-trigger-map-20260630.md) | `classify_controlled_public_h3_baseline.py`, `draft_final_handover_result_row.py`, range summarizer | retry completion is application recovery, not CM proof |
| upload retry, Chapter 10 | [chapter-10 trigger map](tables/chapter-10-scanner-trigger-map-20260630.md) | upload DOM parser and upload summarizer | upload success with multiple sessions is not single-session CM |
| media/streaming, Chapter 11 | [chapter-11 trigger map](tables/chapter-11-scanner-trigger-map-20260630.md) | media and buffered-media summarizers | playback complete must be paired with QoE/session metrics |

## 6. Literature Claim Builder

| code location | trigger/input | output | hallucination guard |
| --- | --- | --- | --- |
| [build_literature_claim_positioning.py#L17-L30](../../tools/build_literature_claim_positioning.py#L17-L30) | required matrix fields | CSV/report schema | source마다 same fields 강제 |
| [build_literature_claim_positioning.py#L33-L216](../../tools/build_literature_claim_positioning.py#L33-L216) | `SOURCE_ROWS` | source_id, URL, supports, does_not_support, experiment_gap | reference를 결론에 끼워 맞추지 않음 |
| [build_literature_claim_positioning.py#L239-L255](../../tools/build_literature_claim_positioning.py#L239-L255) | compact rows and source links | markdown table/link list | source traceability |
| [build_literature_claim_positioning.py#L258-L315](../../tools/build_literature_claim_positioning.py#L258-L315) | Korean report builder | strengthened claims and claims on hold | Chrome/Safari CM success overclaim 방지 |
| [build_literature_claim_positioning.py#L318-L375](../../tools/build_literature_claim_positioning.py#L318-L375) | English report builder | paper-facing English matrix | 같은 claim boundary 유지 |
| [build_literature_claim_positioning.py#L378-L384](../../tools/build_literature_claim_positioning.py#L378-L384) | file writes | CSV, Korean report, English report | 재생성 가능 |

Output files:

- [data/literature-claim-positioning-20260629.csv](../../data/literature-claim-positioning-20260629.csv)
- [docs/results/literature-claim-positioning-20260629.md](../results/literature-claim-positioning-20260629.md)
- [docs/paper/literature-claim-positioning-en-20260629.md](../paper/literature-claim-positioning-en-20260629.md)

## 7. Reproducibility Command Index

| scope | command shape | note |
| --- | --- | --- |
| implementation source scan | `python3 tools/scan_implementation_evidence.py <repo...> --format csv --max-examples 3` | clone list is in [chapter-01-reference-and-scanner-evidence.md](chapter-01-reference-and-scanner-evidence.md) |
| friction matrix | `python3 tools/build_cm_operational_friction_matrix.py` | reads rubric, experiment corpus, literature tracker |
| literature matrix | `python3 tools/build_literature_claim_positioning.py` | regenerates Chapter 12 source matrix |
| browser readiness | `python3 tools/check_browser_cm_observability.py --format markdown` | readiness only, not CM success |
| public origin readiness | `python3 tools/check_public_origin_readiness.py --url "$PUBLIC_ORIGIN_URL" --require-h3-alt-svc --redact-sensitive --format markdown` | real host/IP must stay in ignored config |
| public baseline classifier | `PYTHONPATH=tools python3 tools/classify_controlled_public_h3_baseline.py <artifact> --server-artifact-dir <server> --url "$URL"` | H3 baseline gate |
| public network-change classifier | `PYTHONPATH=tools python3 tools/classify_controlled_public_h3_network_change.py <artifact> --server-artifact-dir <server> --url "$URL"` | active path/workload/session classification |
| final artifact validator | `PYTHONPATH=tools python3 tools/validate_final_handover_trial_artifact.py --trial-id <id> --artifact-dir <artifact> --format markdown` | final-countable/negative-control guard |

## 8. Practical Review Checklist

검증자는 다음 순서로 보면 된다.

1. [reference-link-catalog-20260630.md](reference-link-catalog-20260630.md)에서 해당 claim의 외부 reference가 있는지 본다.
2. 챕터별 `reference-and-evidence` 문서에서 source가 무엇을 지지하고 무엇을 지지하지 않는지 본다.
3. 이 문서의 scanner/classifier line anchors를 열어 실제 trigger 조건을 본다.
4. `tables/*scanner-trigger*`에서 workload별 세부 line anchor를 확인한다.
5. 결과 문서와 CSV에서 해당 row가 `PASS`, `PASS_NEGATIVE_CONTROL`, `FAIL` 중 무엇인지 확인한다.
6. `PASS_NEGATIVE_CONTROL`을 성공으로 읽지 않는다. 이 연구에서 많은 중요한 결과는 "CM 성공이 아니라 무엇이 부족한지 확인한 negative control"이다.
