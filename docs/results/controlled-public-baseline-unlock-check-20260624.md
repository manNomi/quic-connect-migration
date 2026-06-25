# Controlled Public Baseline Unlock Check

Generated: `2026-06-25`

This public-safe check decides whether a controlled-public Chrome HTTP/3 baseline can unlock active browser network-change trials.

## Summary

| field | value |
| --- | --- |
| trial_id | `controlled-public-chrome-h3-baseline-001` |
| artifact_dir | `repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001` |
| summary_path | `-` |
| summary status | `-` |
| summary classification | `-` |
| baseline summary PASS | `no` |
| counts toward final protocol | `no` |
| artifact bundle complete | `no` |
| unlocks active trials | `no` |
| claim strength | `summary_missing` |
| public safe | `yes` |

## Allowed Unlock Classifications

- `controlled_public_application_h3_confirmed`
- `controlled_public_server_qlog_h3_confirmed_browser_netlog_inconclusive`

## Matched Final Requirements

- -

## Warnings

- no known final handover summary found under repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001

## Blockers

- baseline summary is not an unlocking PASS classification: status=- classification=-
- baseline validation does not count toward final browser handover protocol
- missing artifact: server result (repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001/results/server.json)
- missing artifact: server qlog directory (repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001/qlog)
- missing artifact: public origin readiness (repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001/results/public-origin-readiness.json)
- missing artifact: classifier summary (repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001/results/controlled-public-h3-baseline-summary.json)
- missing artifact: Chrome bootstrap NetLog (repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001/chrome/bootstrap-netlog.json)
- missing artifact: Chrome second NetLog (repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001/chrome/second-netlog.json)
- missing artifact: Chrome public H3 summary (repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001/results/chrome-public-h3-summary.json)
- validation unavailable: no known final handover summary found under repro/quic-go-min-repro/artifacts/controlled-public-chrome-h3-baseline-001
