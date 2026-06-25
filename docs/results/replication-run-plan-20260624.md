# Replication Run Plan

Generated: `2026-06-25`

This plan is public-safe. It turns the replication sufficiency audit into a staged execution plan and keeps the final public/browser handover protocol as the first priority.

## Summary

| field | value |
| --- | --- |
| plan rows | `17` |
| P0 public/browser rows | `1` |
| L1 transition-zone rows | `0` |
| L1 transition-zone reviewed rows | `5` |
| L2 anchor rows | `11` |
| transition repetitions per condition | `6` |

## Staged Plan

| stage | priority | condition | current PASS/runs | suggested reps | purpose | run when |
| --- | --- | --- | --- | --- | --- | --- |
| P0-public-browser-handover | 0 | `controlled-public-final-protocol` | 0/6 final requirements | 6 required trial rows | Produce the missing publishable browser/mobile active path-change evidence before broad CM claims. | after controlled public origin config, active secondary path, and network-change command are ready |
| L1-transition-zone-reviewed | 3 | `poll-4000ms` | 1/6 | 0 | Record that the planned local transition-zone repetition target has been reached. | no immediate local repetition; revisit only if the paper needs narrower windows or a different workload. |
| L1-transition-zone-reviewed | 3 | `upload-retry0-4750ms` | 3/6 | 0 | Record that the planned local transition-zone repetition target has been reached. | no immediate local repetition; revisit only if the paper needs narrower windows or a different workload. |
| L1-transition-zone-reviewed | 3 | `upload-4750ms` | 3/6 | 0 | Record that the planned local transition-zone repetition target has been reached. | no immediate local repetition; revisit only if the paper needs narrower windows or a different workload. |
| L1-transition-zone-reviewed | 3 | `downlink-5000ms` | 5/6 | 0 | Record that the planned local transition-zone repetition target has been reached. | no immediate local repetition; revisit only if the paper needs narrower windows or a different workload. |
| L1-transition-zone-reviewed | 3 | `downlink-5500ms` | 4/6 | 0 | Record that the planned local transition-zone repetition target has been reached. | no immediate local repetition; revisit only if the paper needs narrower windows or a different workload. |
| L2-boundary-anchor-replication | 2 | `downlink-wait_only_no_retry-6000ms` | 0/3 | 13 | Turn an important all-pass/all-fail local boundary anchor from directional evidence into stronger local support. | only if the paper needs stronger local reliability wording after public handover trials are attempted |
| L2-boundary-anchor-replication | 2 | `downlink-retry_enabled_1x500ms-6000ms` | 3/3 | 13 | Turn an important all-pass/all-fail local boundary anchor from directional evidence into stronger local support. | only if the paper needs stronger local reliability wording after public handover trials are attempted |
| L2-boundary-anchor-replication | 2 | `poll-3000ms` | 3/3 | 13 | Turn an important all-pass/all-fail local boundary anchor from directional evidence into stronger local support. | only if the paper needs stronger local reliability wording after public handover trials are attempted |
| L2-boundary-anchor-replication | 2 | `poll-6000ms` | 0/3 | 13 | Turn an important all-pass/all-fail local boundary anchor from directional evidence into stronger local support. | only if the paper needs stronger local reliability wording after public handover trials are attempted |
| L2-boundary-anchor-replication | 2 | `upload-retry1-12000ms` | 3/3 | 13 | Turn an important all-pass/all-fail local boundary anchor from directional evidence into stronger local support. | only if the paper needs stronger local reliability wording after public handover trials are attempted |
| L2-boundary-anchor-replication | 2 | `upload-retry1-15000ms` | 0/3 | 13 | Turn an important all-pass/all-fail local boundary anchor from directional evidence into stronger local support. | only if the paper needs stronger local reliability wording after public handover trials are attempted |
| L2-boundary-anchor-replication | 2 | `upload-retry2-18000ms` | 3/3 | 13 | Turn an important all-pass/all-fail local boundary anchor from directional evidence into stronger local support. | only if the paper needs stronger local reliability wording after public handover trials are attempted |
| L2-boundary-anchor-replication | 2 | `upload-retry2-21000ms` | 0/3 | 13 | Turn an important all-pass/all-fail local boundary anchor from directional evidence into stronger local support. | only if the paper needs stronger local reliability wording after public handover trials are attempted |
| L2-boundary-anchor-replication | 2 | `upload-4600ms` | 3/3 | 13 | Turn an important all-pass/all-fail local boundary anchor from directional evidence into stronger local support. | only if the paper needs stronger local reliability wording after public handover trials are attempted |
| L2-boundary-anchor-replication | 2 | `upload-4900ms` | 0/3 | 13 | Turn an important all-pass/all-fail local boundary anchor from directional evidence into stronger local support. | only if the paper needs stronger local reliability wording after public handover trials are attempted |
| L2-boundary-anchor-replication | 2 | `downlink-6000ms` | 0/3 | 13 | Turn an important all-pass/all-fail local boundary anchor from directional evidence into stronger local support. | only if the paper needs stronger local reliability wording after public handover trials are attempted |

## Command Sources

| condition | command source | notes |
| --- | --- | --- |
| `controlled-public-final-protocol` | docs/results/final-handover-trial-packet-20260624.md | This remains higher priority than optional local replication because it closes the main paper blocker. |
| `poll-4000ms` | docs/reproducibility-guide-ko.md sections 34-36; run-chrome-h3-rebinding-transient-boundary-repetition.sh | Target repetitions reached; keep the condition as transition-zone evidence instead of treating it as a binary threshold. |
| `upload-retry0-4750ms` | docs/reproducibility-guide-ko.md sections 32-33; run-chrome-h3-rebinding-transient-boundary-repetition.sh with upload retry env | Target repetitions reached; keep the condition as transition-zone evidence instead of treating it as a binary threshold. |
| `upload-4750ms` | docs/reproducibility-guide-ko.md sections 34-36; run-chrome-h3-rebinding-transient-boundary-repetition.sh | Target repetitions reached; keep the condition as transition-zone evidence instead of treating it as a binary threshold. |
| `downlink-5000ms` | docs/reproducibility-guide-ko.md sections 34-36; run-chrome-h3-rebinding-transient-boundary-repetition.sh | Target repetitions reached; keep the condition as transition-zone evidence instead of treating it as a binary threshold. |
| `downlink-5500ms` | docs/reproducibility-guide-ko.md sections 34-36; run-chrome-h3-rebinding-transient-boundary-repetition.sh | Target repetitions reached; keep the condition as transition-zone evidence instead of treating it as a binary threshold. |
| `downlink-wait_only_no_retry-6000ms` | docs/reproducibility-guide-ko.md section 35; run-chrome-h3-rebinding-transient-boundary-repetition.sh with downlink retry/wait env | The suggested count assumes future rows preserve the same all-pass or all-fail outcome. |
| `downlink-retry_enabled_1x500ms-6000ms` | docs/reproducibility-guide-ko.md section 35; run-chrome-h3-rebinding-transient-boundary-repetition.sh with downlink retry/wait env | The suggested count assumes future rows preserve the same all-pass or all-fail outcome. |
| `poll-3000ms` | docs/reproducibility-guide-ko.md sections 34-36; run-chrome-h3-rebinding-transient-boundary-repetition.sh | The suggested count assumes future rows preserve the same all-pass or all-fail outcome. |
| `poll-6000ms` | docs/reproducibility-guide-ko.md sections 34-36; run-chrome-h3-rebinding-transient-boundary-repetition.sh | The suggested count assumes future rows preserve the same all-pass or all-fail outcome. |
| `upload-retry1-12000ms` | docs/reproducibility-guide-ko.md sections 32-33; run-chrome-h3-rebinding-transient-boundary-repetition.sh with upload retry env | The suggested count assumes future rows preserve the same all-pass or all-fail outcome. |
| `upload-retry1-15000ms` | docs/reproducibility-guide-ko.md sections 32-33; run-chrome-h3-rebinding-transient-boundary-repetition.sh with upload retry env | The suggested count assumes future rows preserve the same all-pass or all-fail outcome. |
| `upload-retry2-18000ms` | docs/reproducibility-guide-ko.md sections 32-33; run-chrome-h3-rebinding-transient-boundary-repetition.sh with upload retry env | The suggested count assumes future rows preserve the same all-pass or all-fail outcome. |
| `upload-retry2-21000ms` | docs/reproducibility-guide-ko.md sections 32-33; run-chrome-h3-rebinding-transient-boundary-repetition.sh with upload retry env | The suggested count assumes future rows preserve the same all-pass or all-fail outcome. |
| `upload-4600ms` | docs/reproducibility-guide-ko.md sections 34-36; run-chrome-h3-rebinding-transient-boundary-repetition.sh | The suggested count assumes future rows preserve the same all-pass or all-fail outcome. |
| `upload-4900ms` | docs/reproducibility-guide-ko.md sections 34-36; run-chrome-h3-rebinding-transient-boundary-repetition.sh | The suggested count assumes future rows preserve the same all-pass or all-fail outcome. |
| `downlink-6000ms` | docs/reproducibility-guide-ko.md sections 34-36; run-chrome-h3-rebinding-transient-boundary-repetition.sh | The suggested count assumes future rows preserve the same all-pass or all-fail outcome. |

## Interpretation

- Do not spend the remaining disk budget on broad local replication before the controlled-public final protocol is unblocked.
- If public/browser handover remains externally blocked, L1 transition-zone rows are the highest-value local repetitions.
- Transition-zone rows that have reached the planned repetition count should be used to refine wording, not rerun blindly.
- L2 anchor repetitions are optional unless the paper needs stronger local reliability wording.
