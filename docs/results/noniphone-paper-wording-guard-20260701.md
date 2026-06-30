# non-iPhone Paper Wording Guard

Generated: `2026-06-30`

This public-safe guard converts reviewer risks into bilingual wording rules for the abstract, introduction, method, results, limitations, and artifact policy sections.

## Summary

| field | value |
| --- | --- |
| rule count | `9` |
| sections | `['abstract', 'artifact_policy', 'introduction', 'limitations', 'method', 'results']` |
| allowed claim count | `5` |
| blocked claim count | `3` |
| critical risks | `['guarantee_overclaim', 'public_positive_absence']` |
| missing risk ids | `{}` |
| guard decision | Use conservative evaluate/classify wording unless public browser or AWS positive gates are opened. |

## Wording Rules

| section | risk ids | avoid | use EN | use KO | evidence boundary |
| --- | --- | --- | --- | --- | --- |
| `abstract` | `guarantee_overclaim`, `public_positive_absence` | HTTP/3 Connection Migration guarantees seamless task continuity under unstable mobile networks. | This study assesses how QUIC/HTTP/3 connection-migration primitives, deployment routing, browser behavior, and workload design shape application-level continuity. | 본 연구는 QUIC/HTTP/3 Connection Migration primitive, 배포 라우팅, 브라우저 동작, workload 설계가 애플리케이션 수준 작업 연속성에 어떤 경계를 만드는지 평가한다. | Do not claim public Chrome CM success or guarantee language. |
| `introduction` | `terminology_mobile_unstable`, `local_rebinding_external_validity` | We evaluate unstable mobile networks such as Wi-Fi/LTE handover. | We distinguish controlled local UDP rebinding, public-origin active path change, deployment routing, and application recovery, because these layers expose different failure modes. | 본 연구는 local UDP rebinding, public-origin active path change, 배포 라우팅, 애플리케이션 복구를 구분한다. 각 계층은 서로 다른 실패 원인을 드러내기 때문이다. | Do not use LTE/5G/Wi-Fi handover wording unless those rows are actually collected. |
| `method` | `implementation_survey_heterogeneity` | Each implementation was tested equivalently. | Implementation evidence is classified by level: runtime positive controls, app demos, source/test audits, deployment gates, and negative controls are reported separately. | 구현체 근거는 runtime positive control, app demo, source/test audit, deployment gate, negative control로 구분해 보고한다. | Do not collapse source audits and runtime results into one binary support label. |
| `method` | `public_positive_absence` | A public Chrome migration run is successful if the task completes. | A strong public Chrome CM row requires application completion, client active path change, target server tuple change, qlog path validation, and one target Chrome QUIC session in the same active trial. | 강한 public Chrome CM row는 동일 active trial 안에서 application completion, client active path change, target server tuple change, qlog path validation, Chrome target QUIC session 1개를 모두 요구한다. | Task completion alone is not a CM success criterion. |
| `results` | `local_rebinding_external_validity` | Chrome handover succeeds in our experiments. | Local Chrome forced-H3 rebinding controls show workload-sensitive behavior under a controlled path perturbation, but they do not substitute for public-origin handover evidence. | Local Chrome forced-H3 rebinding control은 통제된 path perturbation에서 workload-sensitive behavior를 보여주지만, public-origin handover 근거를 대체하지 않는다. | Keep local controls separate from public browser claims. |
| `results` | `aws_s2n_scope_confusion` | AWS NLB+s2n migration is validated. | The AWS path currently contains local CID-provider prerequisite evidence and a fail-closed live runner; live forwarding and active migration remain blocked or future steps. | AWS 경로는 현재 local CID-provider prerequisite evidence와 fail-closed live runner를 확보한 상태이며, live forwarding과 active migration은 아직 blocked 또는 future step이다. | Do not claim live AWS forwarding or active migration before credentials and trial rows exist. |
| `results` | `streaming_completion_qoe_confound` | Video and music workloads remain continuous because playback completes. | Streaming completion is reported together with rebuffering, startup delay, retry behavior, and Chrome target session count; completion alone is treated as insufficient continuity evidence. | Streaming completion은 rebuffering, startup delay, retry behavior, Chrome target session count와 함께 보고하며, completion만으로는 연속성 근거가 부족하다고 본다. | Do not interpret multi-session retry recovery as single-session CM. |
| `limitations` | `public_positive_absence`, `safari_claim_ceiling` | The browser behavior section is complete. | The current public/browser evidence is intentionally conservative: no tracked active public Chrome row satisfies strong CM success, and Safari remains a lower-observability feasibility follow-up. | 현재 public/browser 근거는 의도적으로 보수적으로 해석한다. tracked active public Chrome row 중 strong CM success를 만족한 것은 없고, Safari는 낮은 관찰성의 feasibility follow-up으로 남아 있다. | State the absence of strong public success as a limitation, not as hidden success. |
| `artifact_policy` | `security_public_artifact_hygiene` | Raw artifacts are published for reproducibility. | The public artifact includes sanitized summaries, reproducible tools, manifests, and claim boundaries; raw sensitive traces are excluded from the public repository. | 공개 artifact에는 sanitized summary, 재현 도구, manifest, claim boundary를 포함하고, 민감한 raw trace는 공개 저장소에서 제외한다. | Continue publication-bundle validation and secret scanning before push. |

## Safe Writing Posture

- Prefer evaluate, assess, classify, separate, and boundary wording.
- Avoid guarantee, prove, validated, seamless, and works unless the specific strong evidence row exists.
- Keep local rebinding, public path change, AWS deployment, browser behavior, and application recovery in separate paragraphs.
- Put unresolved public Chrome, AWS+s2n, and Safari claims in limitations or future work.
