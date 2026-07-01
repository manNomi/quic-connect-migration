# non-iPhone Reviewer Risk and Validity Audit

Generated: `2026-07-01`

This audit is public-safe. It converts the current non-iPhone claim dashboard and professor decision packet into reviewer-facing risks, defensive wording, and remaining evidence gaps.

## Summary

| field | value |
| --- | --- |
| risk count | `9` |
| critical risks | `['guarantee_overclaim', 'public_positive_absence']` |
| high risks | `['local_rebinding_external_validity', 'aws_s2n_scope_confusion', 'streaming_completion_qoe_confound', 'terminology_mobile_unstable']` |
| allowed claim count | `5` |
| blocked claim count | `3` |
| audit decision | The paper is defensible as a conservative maturity/gap analysis if critical overclaims are avoided; positive browser/AWS claims require opening external gates. |

## Risk Register

| risk | severity | reviewer objection | vulnerable wording | defensible wording | mitigation | remaining gap | professor decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `guarantee_overclaim` | `critical` | The paper may overstate that HTTP/3 Connection Migration guarantees web task continuity. | HTTP/3 Connection Migration guarantees seamless work continuity. | We evaluate where QUIC/HTTP/3 migration primitives, deployment routing, browser policy, and workload behavior do or do not support continuity. | Use evaluate/assess/classify language, and keep transport continuity separate from application task completion. | A positive public browser CM success row is still absent. | Decide whether the paper is a maturity/gap analysis or must wait for a positive public/browser result. |
| `local_rebinding_external_validity` | `high` | Local UDP rebinding may not generalize to Wi-Fi/LTE, desktop interface handover, or public origin behavior. | Chrome handover works because local rebinding controls pass. | Local rebinding controls are controlled browser/workload probes; public handover remains a separate gate. | Label local results as controls and require public-origin active path-change rows for browser CM success. | No active non-iPhone secondary desktop path and no H3-ready controlled public origin are available. | Open public Chrome gates or keep local controls as methodological evidence only. |
| `public_positive_absence` | `critical` | The paper lacks a successful controlled-public Chrome single-session migration result. | Chrome public-origin Connection Migration is validated. | Tracked public Chrome rows currently provide H3 baselines and negative/gap evidence, not strong CM success. | Report strong CM acceptance criteria and state that current strong success count is zero. | Need application completion, client active path change, server tuple change, qlog path validation, and one target Chrome QUIC session in the same active row. | Choose whether to run public Chrome trials after opening origin and desktop path gates. |
| `aws_s2n_scope_confusion` | `high` | AWS NLB+s2n readiness may be confused with live forwarding or active migration success. | AWS NLB+s2n migration works. | The repository has local CID-provider prerequisite evidence and a fail-closed live runner; live AWS forwarding is credential-blocked and active migration is a later design step. | Split AWS claims into local prerequisite, live forwarding echo, and active path-change variant. | AWS identity is invalid on the current host; live forwarding has not run. | Refresh AWS credentials if AWS deployment evidence is required for the paper. |
| `streaming_completion_qoe_confound` | `high` | Streaming completion can hide rebuffering, retry/reconnect, and multiple QUIC sessions. | Video and music workloads are continuous because playback completed. | Streaming workloads are reported with QoE and session attribution; completion alone is not continuity. | Always report rebuffer count, startup delay, retry count, target session count, tuple change, and qlog path evidence together. | No public streaming handover rows exist yet. | Decide whether streaming is a main evaluation axis or a QoE appendix. |
| `implementation_survey_heterogeneity` | `medium` | Implementation evidence mixes runtime tests, source audits, app demos, and readiness gates. | All surveyed implementations are equally mature. | The survey uses evidence levels and claim boundaries; runtime, source, app-demo, and readiness evidence are not treated as equal. | Keep current_level/evidence_status columns visible and do not collapse them into a single binary support label. | Some large production stacks still need Linux/build-focused execution. | Decide whether additional implementation appendix depth is needed after the current broad survey. |
| `terminology_mobile_unstable` | `high` | Terms like unstable mobile network or mobile handover may be ambiguous or overbroad. | Unstable mobile networks are evaluated. | The current non-iPhone work evaluates controlled path-change readiness, local rebinding controls, public-origin gates, and workload continuity boundaries. | Avoid claiming LTE/5G/Wi-Fi handover unless those rows exist; define path change, NAT rebinding, public-origin handover, and application recovery separately. | No non-iPhone public active path-change row exists yet. | Approve terminology before writing the final introduction and abstract. |
| `safari_claim_ceiling` | `medium` | Safari evidence has weaker observability than Chrome and is currently blocked at WebDriver session creation. | Safari Connection Migration behavior is evaluated. | Safari is a feasibility appendix candidate; current evidence is readiness-blocked and has lower browser-internal observability. | Do not include Safari in main claims until session smoke and controlled-public baseline pass. | Safari Allow remote automation is not enabled. | Decide whether Safari should be excluded, deferred, or kept as a feasibility appendix. |
| `security_public_artifact_hygiene` | `medium` | Public artifacts may accidentally expose credentials, hosts, IPs, qlogs, NetLogs, or account data. | Raw artifacts are included for reproducibility. | The public repository includes sanitized summaries, tools, manifests, and claim boundaries; raw sensitive artifacts remain excluded. | Continue secret scan, publication bundle validation, and generated evidence-to-claim mapping before every push. | Raw artifact archival policy for private review is separate from the public repository. | Decide whether private raw artifacts need an offline appendix or institutional storage. |

## Reviewer-Safe Paper Posture

- Treat implementation maturity, deployment routing, browser policy, and workload continuity as separate layers.
- Present local Chrome rebinding rows as controlled probes, not public handover proof.
- Keep public Chrome CM success, live AWS+s2n success, and Safari handover success out of the main claims until their gates open.
- Use streaming workloads to discuss QoE and session attribution, not zero-impact continuity.
- Ask the professor to choose between a conservative maturity/gap paper and additional positive-result gate work.
