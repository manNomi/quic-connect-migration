# Final Handover Operator Checklist

Generated: `2026-06-30`

## Summary

| field | value |
| --- | --- |
| next trial | `controlled-public-chrome-downlink-noheartbeat-network-change-001` |
| next trial ready | `no` |
| sensitive values redacted | `no` |
| baseline config ready | `yes` |
| active config ready | `no` |
| Android config ready | `no` |
| current disk free | `12.4 GiB` |
| target free GiB | `7.0` |
| storage target met by artifact cleanup | `yes` |
| remaining external cleanup gap | `0 B` |
| final trial completion | `3/6` |

## Actions

| priority | status | scope | action | reason |
| ---: | --- | --- | --- | --- |
| 1 | `ready` | controlled public baseline | Controlled public baseline config is ready. | Baseline config keys are present and non-placeholder. |
| 2 | `ready` | storage | Disk target can be met by reviewed artifact cleanup candidates. | Selected cleanup candidates reclaim 0 B. |
| 3 | `blocked-now` | next trial | Do not run the next final handover trial yet. | Missing required gates: baseline_summary_ready, network_change_command_present, desktop_path_change_ready |
| 4 | `todo-later` | active network-change | Prepare active network-change config before Chrome/Safari active trials. | The final protocol requires active path-change trials after the baseline/no-change rows are registered. |
| 5 | `todo-later` | desktop path-change | Provide a real active secondary path before desktop active network-change trials. | Chrome/Safari active trials require a path change, but the current machine has no secondary active non-loopback IPv4 path. |
| 6 | `todo-later` | Android P1 | Connect an Android device over ADB before Android Chrome feasibility trials. | The P1 feasibility requirement can be satisfied by Safari or Android, but Android remains unavailable. |
| 7 | `incomplete` | final protocol | Continue the final trial loop until all required rows are counted. | Current final completion is 3/6. |

## Commands

### 1. controlled public baseline

```bash
python3 tools/build_controlled_public_config_worksheet.py --output docs/results/controlled-public-config-worksheet-20260624.md
python3 tools/check_controlled_public_config.py --require-baseline-ready
```

### 2. storage

```bash
python3 tools/plan_artifact_cleanup.py --target-free-gib 7 --candidate-policy review-unreferenced --output docs/results/artifact-cleanup-dry-run-20260624.md
python3 tools/apply_artifact_cleanup_plan.py --target-free-gib 7 --candidate-policy review-unreferenced --output docs/results/artifact-cleanup-apply-report-20260625.md
python3 tools/audit_artifact_cleanup_safety.py --target-free-gib 7 --output docs/results/artifact-cleanup-safety-audit-20260624.md
```

### 3. next trial

```bash
bash harness/scripts/final-handover-run-next.sh
python3 tools/check_next_final_handover_trial_readiness.py --min-disk-gib 7 --output docs/results/final-handover-next-trial-readiness-20260624.md
```

### 4. active network-change

```bash
python3 tools/check_controlled_public_config.py --require-active-ready
python3 tools/check_final_browser_handover_readiness.py --output docs/results/final-browser-handover-readiness-20260624.md
```

### 5. desktop path-change

```bash
python3 tools/check_handover_readiness.py --format markdown
```

### 6. Android P1

```bash
adb devices
python3 tools/check_handover_readiness.py --format markdown
```

### 7. final protocol

```bash
python3 tools/audit_final_browser_handover_trials.py --require-complete
```
