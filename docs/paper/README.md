# Paper Draft Workspace

Generated: `2026-06-29`

This folder contains paper-facing drafts generated from the current research evidence. These files are not final manuscript text; they are controlled snapshots that preserve claim boundaries.

## Read Order

1. `terminology-and-scope-boundaries-20260629.md`
   - Defines the study scope and replaces vague phrases such as "unstable mobile network".
2. `cm-underuse-and-deployment-friction-ko-20260629.md`
   - Korean chapter explaining why QUIC CM is underused or conservatively deployed.
3. `cm-underuse-and-deployment-friction-en-20260629.md`
   - English chapter explaining why QUIC CM is underused or conservatively deployed.
4. `current-evidence-paper-skeleton-ko-20260629.md`
   - Korean title/abstract/contribution/structure skeleton.
5. `current-evidence-paper-skeleton-en-20260629.md`
   - English title/abstract/contribution/structure skeleton.
6. `workload-prioritized-experiment-design-ko-20260629.md`
   - Korean next-experiment design prioritizing upload/download, Range, video, music, Safari, and Android.
7. `workload-prioritized-experiment-design-en-20260629.md`
   - English next-experiment design prioritizing upload/download, Range, video, music, Safari, and Android.
8. `current-evidence-methods-results-ko-20260629.md`
   - Korean Methods/Results draft based on current artifacts.
9. `current-evidence-methods-results-en-20260629.md`
   - English Methods/Results draft based on current artifacts.
10. `threats-to-validity-and-reviewer-defense-ko-20260629.md`
    - Korean limitations and reviewer-defense chapter that separates supported claims from overclaims.
11. `threats-to-validity-and-reviewer-defense-en-20260629.md`
    - English limitations and reviewer-defense chapter that separates supported claims from overclaims.

## Claim Boundary

The current paper should be framed as a QUIC Connection Migration maturity and workload-continuity study. It should not yet be framed as proof that Chrome or Safari successfully preserves a single HTTP/3 QUIC session across Wi-Fi-to-cellular failover.

The final browser handover protocol remains incomplete until:

- Chrome no-heartbeat active path-change rows: `0/3 -> 3/3`
- Chrome heartbeat active path-change rows: `0/3 -> 3/3`
- Safari or Android feasibility row: `0/1 -> 1/1`

## Regeneration

Regenerate the paper-facing drafts after adding new experiment rows:

```bash
python3 tools/build_paper_claim_readiness_audit.py \
  --json-output data/paper-claim-readiness-audit-20260629.json

python3 tools/build_current_evidence_manuscript_sections.py
python3 tools/build_cm_underuse_chapter.py
python3 tools/build_current_paper_skeleton.py
python3 tools/build_workload_prioritized_experiment_design.py
python3 tools/build_threats_and_reviewer_defense.py
```
