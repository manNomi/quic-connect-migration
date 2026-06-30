# Final Capture Storage Budget

Generated: `2026-06-30`

This public-safe budget estimates whether the local machine can store remaining final browser handover NetLog/qlog artifacts before reaching the minimum free-space floor.

## Summary

| field | value |
| --- | --- |
| next trial | `controlled-public-chrome-downlink-noheartbeat-network-change-001` |
| remaining planned executions | `7` |
| per-trial reserve GiB | `2.0` |
| disk free GiB | `13.24` |
| minimum free GiB floor | `5.0` |
| usable GiB before floor | `8.24` |
| max executions before floor | `4` |
| current local artifact roots | `36.3 GiB` |

## Budget Rows

| scope | planned executions | required GiB | storage ready | cleanup needed GiB | interpretation |
| --- | ---: | ---: | --- | ---: | --- |
| `next-planned-execution` | 1 | 2.0 | `yes` | 0.0 | Enough space to attempt only the next selected capture if storage_ready=yes. |
| `all-remaining-final-executions` | 7 | 14.0 | `no` | 5.76 | Enough space for the full remaining final browser handover queue if storage_ready=yes. |

## Interpretation

- This is a conservative planning estimate, not a measurement of future artifact size.
- If only `next-planned-execution` is ready, run one capture and re-check storage before the next trial.
- Do not delete ignored raw artifacts until the cleanup safety audit and paper evidence references are reviewed.
