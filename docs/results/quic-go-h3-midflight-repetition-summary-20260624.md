# quic-go HTTP/3 Mid-Flight Migration Repetition Summary

Generated: `2026-06-24`

This summary aggregates local quic-go HTTP/3 active-migration repetitions. It is a library-controlled positive control, not a browser handover result.

## Aggregate

| field | value |
| --- | --- |
| cases | `6` |
| status counts | `{'PASS': 6}` |
| mode counts | `{'midflight-download': 3, 'midflight-upload': 3}` |
| mode/status counts | `{'midflight-download::PASS': 3, 'midflight-upload::PASS': 3}` |

## Cases

| run | mode | status | socket B | migration triggered | migration bytes | request bytes | response bytes | decode ok | client migration event lines |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |
| r1 | midflight-upload | PASS | true | true | 524288 | 1048576 | 3 | true | 5 |
| r1 | midflight-download | PASS | true | true | 524288 |  | 1048576 | true | 5 |
| r2 | midflight-upload | PASS | true | true | 524288 | 1048576 | 3 | true | 5 |
| r2 | midflight-download | PASS | true | true | 524288 |  | 1048576 | true | 5 |
| r3 | midflight-upload | PASS | true | true | 524288 | 1048576 | 3 | true | 5 |
| r3 | midflight-download | PASS | true | true | 524288 |  | 1048576 | true | 5 |

## Interpretation Boundary

Use these rows as implementation-level positive controls: quic-go can perform controlled active migration during HTTP/3 upload and download tasks while preserving application completion. They do not prove that Chrome, Safari, or Android Chrome expose the same behavior during real network handover.
