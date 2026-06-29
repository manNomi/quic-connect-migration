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
4. `current-evidence-methods-results-ko-20260629.md`
   - Korean Methods/Results draft based on current artifacts.
5. `current-evidence-methods-results-en-20260629.md`
   - English Methods/Results draft based on current artifacts.

## Claim Boundary

The current paper should be framed as a QUIC Connection Migration maturity and workload-continuity study. It should not yet be framed as proof that Chrome or Safari successfully preserves a single HTTP/3 QUIC session across Wi-Fi-to-cellular failover.

The final browser handover protocol remains incomplete until:

- Chrome no-heartbeat active path-change rows: `0/3 -> 3/3`
- Chrome heartbeat active path-change rows: `0/3 -> 3/3`
- Safari or Android feasibility row: `0/1 -> 1/1`

## Regeneration

Regenerate the Methods/Results drafts after adding new experiment rows:

```bash
python3 tools/build_paper_claim_readiness_audit.py \
  --json-output data/paper-claim-readiness-audit-20260629.json

python3 tools/build_current_evidence_manuscript_sections.py
python3 tools/build_cm_underuse_chapter.py
```
