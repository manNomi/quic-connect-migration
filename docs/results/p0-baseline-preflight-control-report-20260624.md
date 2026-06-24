# P0 Baseline Preflight Control Report

Generated: `2026-06-24`

This public-safe control report uses synthetic fixtures to check that the P0 preflight guard opens and closes only under the intended readiness states.

## Summary

| field | value |
| --- | --- |
| scenarios | `3` |
| all controls passed | `yes` |
| public safe | `yes` |

## Controls

| scenario | expected go | actual go | ok | action | failed checks | interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| `missing_config_blocks_capture` | `no` | `no` | `yes` | `fill-private-controlled-public-config` | `baseline_config_ready;needed_now_gates_cleared;next_trial_ready` | Fail closed when the private controlled-public baseline config is absent. |
| `synthetic_ready_allows_baseline_capture` | `yes` | `yes` | `yes` | `start-origin-server-and-client-baseline-capture` | `-` | Open only for a syntactically ready P0 baseline fixture; this does not prove public browser CM. |
| `stale_needed_now_gate_blocks_capture` | `no` | `no` | `yes` | `fill-private-controlled-public-config` | `needed_now_gates_cleared` | Fail closed if the P0 status still reports a needed-now gate, even when packet readiness is otherwise satisfied. |

## Interpretation

- These controls validate the guard logic, not real public-origin reachability.
- A synthetic `actual go=yes` only means the preflight state machine can open when all modeled gates are satisfied.
- Real paper claims still require the controlled-public Chrome baseline artifacts and later active path-change trials.
