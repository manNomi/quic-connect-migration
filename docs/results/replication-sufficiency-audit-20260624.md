# Replication Sufficiency Audit

Generated: `2026-06-24`

This audit is public-safe. It does not create new experiment results; it checks how cautiously the current repeated local controls should be worded in the paper.

## Summary

| field | value |
| --- | --- |
| audited conditions | `30` |
| source counts | `{'downlink_recovery': 4, 'polling_transition': 6, 'upload_recovery': 13, 'workload_transition': 7}` |
| evidence roles | `{'failure_candidate': 11, 'stable_candidate': 14, 'transition_zone': 5}` |
| local stable lower-bound target | `0.8` |
| local failure upper-bound target | `0.2` |

## Condition Audit

| source | condition | PASS/runs | Wilson 95% CI | role | paper use | additional runs |
| --- | --- | --- | --- | --- | --- | --- |
| workload_transition | `downlink-5000ms` | 2/3 | 0.208-0.939 | transition_zone | transition-zone evidence; avoid binary threshold wording | - |
| workload_transition | `downlink-5500ms` | 2/3 | 0.208-0.939 | transition_zone | transition-zone evidence; avoid binary threshold wording | - |
| workload_transition | `downlink-6000ms` | 0/3 | 0.000-0.562 | failure_candidate | directional local evidence; avoid reliability probability wording | 13 |
| workload_transition | `upload-4600ms` | 3/3 | 0.438-1.000 | stable_candidate | directional local evidence; avoid reliability probability wording | 13 |
| workload_transition | `upload-4750ms` | 1/3 | 0.061-0.792 | transition_zone | transition-zone evidence; avoid binary threshold wording | - |
| workload_transition | `upload-4900ms` | 0/3 | 0.000-0.562 | failure_candidate | directional local evidence; avoid reliability probability wording | 13 |
| workload_transition | `upload-5000ms` | 0/3 | 0.000-0.562 | failure_candidate | directional local evidence; avoid reliability probability wording | 13 |
| upload_recovery | `upload-retry0-4600ms` | 3/3 | 0.438-1.000 | stable_candidate | directional local evidence; avoid reliability probability wording | 13 |
| upload_recovery | `upload-retry0-4750ms` | 1/3 | 0.061-0.792 | transition_zone | transition-zone evidence; avoid binary threshold wording | - |
| upload_recovery | `upload-retry0-4900ms` | 0/3 | 0.000-0.562 | failure_candidate | directional local evidence; avoid reliability probability wording | 13 |
| upload_recovery | `upload-retry0-5000ms` | 0/3 | 0.000-0.562 | failure_candidate | directional local evidence; avoid reliability probability wording | 13 |
| upload_recovery | `upload-retry1-4900ms` | 3/3 | 0.438-1.000 | stable_candidate | directional local evidence; avoid reliability probability wording | 13 |
| upload_recovery | `upload-retry1-5000ms` | 3/3 | 0.438-1.000 | stable_candidate | directional local evidence; avoid reliability probability wording | 13 |
| upload_recovery | `upload-retry1-6000ms` | 3/3 | 0.438-1.000 | stable_candidate | directional local evidence; avoid reliability probability wording | 13 |
| upload_recovery | `upload-retry1-9000ms` | 3/3 | 0.438-1.000 | stable_candidate | directional local evidence; avoid reliability probability wording | 13 |
| upload_recovery | `upload-retry1-12000ms` | 3/3 | 0.438-1.000 | stable_candidate | directional local evidence; avoid reliability probability wording | 13 |
| upload_recovery | `upload-retry1-15000ms` | 0/3 | 0.000-0.562 | failure_candidate | directional local evidence; avoid reliability probability wording | 13 |
| upload_recovery | `upload-retry2-15000ms` | 3/3 | 0.438-1.000 | stable_candidate | directional local evidence; avoid reliability probability wording | 13 |
| upload_recovery | `upload-retry2-18000ms` | 3/3 | 0.438-1.000 | stable_candidate | directional local evidence; avoid reliability probability wording | 13 |
| upload_recovery | `upload-retry2-21000ms` | 0/3 | 0.000-0.562 | failure_candidate | directional local evidence; avoid reliability probability wording | 13 |
| downlink_recovery | `downlink-wait_only_no_retry-6000ms` | 0/3 | 0.000-0.562 | failure_candidate | directional local evidence; avoid reliability probability wording | 13 |
| downlink_recovery | `downlink-wait_only_no_retry-9000ms` | 0/3 | 0.000-0.562 | failure_candidate | directional local evidence; avoid reliability probability wording | 13 |
| downlink_recovery | `downlink-retry_enabled_1x500ms-6000ms` | 3/3 | 0.438-1.000 | stable_candidate | directional local evidence; avoid reliability probability wording | 13 |
| downlink_recovery | `downlink-retry_enabled_1x500ms-9000ms` | 3/3 | 0.438-1.000 | stable_candidate | directional local evidence; avoid reliability probability wording | 13 |
| polling_transition | `poll-250ms` | 3/3 | 0.438-1.000 | stable_candidate | directional local evidence; avoid reliability probability wording | 13 |
| polling_transition | `poll-1500ms` | 3/3 | 0.438-1.000 | stable_candidate | directional local evidence; avoid reliability probability wording | 13 |
| polling_transition | `poll-3000ms` | 3/3 | 0.438-1.000 | stable_candidate | directional local evidence; avoid reliability probability wording | 13 |
| polling_transition | `poll-4000ms` | 1/3 | 0.061-0.792 | transition_zone | transition-zone evidence; avoid binary threshold wording | - |
| polling_transition | `poll-6000ms` | 0/3 | 0.000-0.562 | failure_candidate | directional local evidence; avoid reliability probability wording | 13 |
| polling_transition | `poll-9000ms` | 0/3 | 0.000-0.562 | failure_candidate | directional local evidence; avoid reliability probability wording | 13 |

## Next Actions

| condition | next action |
| --- | --- |
| `downlink-5000ms` | add narrower outage windows or more repetitions; report as mixed transition zone for now |
| `downlink-5500ms` | add narrower outage windows or more repetitions; report as mixed transition zone for now |
| `downlink-6000ms` | add 13 same-outcome repetitions before claiming a strong local failure condition |
| `upload-4600ms` | add 13 same-outcome repetitions before claiming a strong local stable condition |
| `upload-4750ms` | add narrower outage windows or more repetitions; report as mixed transition zone for now |
| `upload-4900ms` | add 13 same-outcome repetitions before claiming a strong local failure condition |
| `upload-5000ms` | add 13 same-outcome repetitions before claiming a strong local failure condition |
| `upload-retry0-4600ms` | add 13 same-outcome repetitions before claiming a strong local stable condition |
| `upload-retry0-4750ms` | add narrower outage windows or more repetitions; report as mixed transition zone for now |
| `upload-retry0-4900ms` | add 13 same-outcome repetitions before claiming a strong local failure condition |
| `upload-retry0-5000ms` | add 13 same-outcome repetitions before claiming a strong local failure condition |
| `upload-retry1-4900ms` | add 13 same-outcome repetitions before claiming a strong local stable condition |
| `upload-retry1-5000ms` | add 13 same-outcome repetitions before claiming a strong local stable condition |
| `upload-retry1-6000ms` | add 13 same-outcome repetitions before claiming a strong local stable condition |
| `upload-retry1-9000ms` | add 13 same-outcome repetitions before claiming a strong local stable condition |
| `upload-retry1-12000ms` | add 13 same-outcome repetitions before claiming a strong local stable condition |
| `upload-retry1-15000ms` | add 13 same-outcome repetitions before claiming a strong local failure condition |
| `upload-retry2-15000ms` | add 13 same-outcome repetitions before claiming a strong local stable condition |
| `upload-retry2-18000ms` | add 13 same-outcome repetitions before claiming a strong local stable condition |
| `upload-retry2-21000ms` | add 13 same-outcome repetitions before claiming a strong local failure condition |
| `downlink-wait_only_no_retry-6000ms` | add 13 same-outcome repetitions before claiming a strong local failure condition |
| `downlink-wait_only_no_retry-9000ms` | add 13 same-outcome repetitions before claiming a strong local failure condition |
| `downlink-retry_enabled_1x500ms-6000ms` | add 13 same-outcome repetitions before claiming a strong local stable condition |
| `downlink-retry_enabled_1x500ms-9000ms` | add 13 same-outcome repetitions before claiming a strong local stable condition |
| `poll-250ms` | add 13 same-outcome repetitions before claiming a strong local stable condition |
| `poll-1500ms` | add 13 same-outcome repetitions before claiming a strong local stable condition |
| `poll-3000ms` | add 13 same-outcome repetitions before claiming a strong local stable condition |
| `poll-4000ms` | add narrower outage windows or more repetitions; report as mixed transition zone for now |
| `poll-6000ms` | add 13 same-outcome repetitions before claiming a strong local failure condition |
| `poll-9000ms` | add 13 same-outcome repetitions before claiming a strong local failure condition |

## Interpretation

- Mixed rows are useful transition-zone evidence, not a binary threshold.
- All-pass and all-fail rows with only three repetitions remain directional unless additional repetitions narrow the interval.
- This audit supports cautious wording such as observed boundary or local control result, not guarantee or probability claims.
