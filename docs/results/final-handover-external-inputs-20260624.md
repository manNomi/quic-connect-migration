# Final Handover External Inputs Handoff

Generated: `2026-06-25`

This packet is public-safe. It lists required external inputs and validation commands without printing domains, TLS paths, private keys, AWS account IDs, device IDs, or network-change command bodies.

## Summary

| field | value |
| --- | --- |
| next trial | `controlled-public-chrome-h3-baseline-001` |
| next trial ready | `no` |
| Codex can run next trial now | `no` |
| needed-now inputs | `2` |
| public safe | `yes` |

## Inputs

| id | urgency | status | input needed | validation command | evidence |
| --- | --- | --- | --- | --- | --- |
| `disk-free-space` | `now` | `ready` | Free local disk until at least 5.0 GiB is available before heavy NetLog/qlog captures. | `python3 tools/report_artifact_storage.py --output docs/results/artifact-storage-report-20260624.md` | `current_free=9.7 GiB; target_met=True` |
| `controlled-public-baseline-config` | `now` | `needed` | Create the ignored controlled-public origin env file and fill baseline DNS/TLS/Alt-Svc/Chrome fields. | `python3 tools/check_controlled_public_config.py --require-baseline-ready` | `missing_baseline_keys=PUBLIC_ORIGIN_HOST, PUBLIC_ORIGIN_PORT, PUBLIC_ORIGIN_URL, TLS_CERT_FILE, TLS_KEY_FILE, LISTEN_ADDR, TCP_ADDR, ALT_SVC, CHROME_BIN` |
| `public-origin-host` | `now` | `needed` | Provide a public WebPKI origin that serves both TCP HTTPS Alt-Svc bootstrap and UDP HTTP/3 on the configured port. | `python3 tools/check_public_origin_readiness.py --url "$PUBLIC_ORIGIN_URL" --require-h3-alt-svc --format markdown` | `next_trial=controlled-public-chrome-h3-baseline-001; baseline_ready=False` |
| `active-network-change-path` | `after-baseline` | `needed-after-baseline` | Prepare a real active secondary path and an explicit NETWORK_CHANGE_CMD for desktop Chrome/Safari active trials. | `python3 tools/check_handover_readiness.py --format markdown && python3 tools/check_controlled_public_config.py --require-active-ready` | `secondary_path_ready=False; missing_active_keys=PUBLIC_ORIGIN_NETWORK_CHANGE_URL, CONTROLLED_PUBLIC_BASELINE_SUMMARY, NETWORK_CHANGE_AFTER_SECONDS, NETWORK_CHANGE_CMD` |
| `android-p1-feasibility` | `p1-alternative` | `optional-missing` | Connect an Android device over ADB and provide an approved Android network-change command if Android is used for P1 feasibility. | `adb devices && python3 tools/check_handover_readiness.py --format markdown` | `android_ready=False; missing_android_keys=ANDROID_NETWORK_CHANGE_CMD` |
| `aws-identity` | `automation-optional` | `optional-missing` | Provide AWS CLI identity only if automated EC2/public-origin or CloudFront follow-up provisioning should be run. | `harness/scripts/aws-preflight.sh` | `aws_identity_ok=False` |
| `final-protocol-completion` | `loop` | `incomplete` | Repeat the selected final trial packet, artifact bundle gate, validation, append, and audit loop until all requirements complete. | `python3 tools/audit_final_browser_handover_trials.py --require-complete` | `completion=0/6` |

## Safe Handling

- `disk-free-space`: Do not delete CSV-referenced raw artifacts unless they are archived and paper evidence is preserved.
- `controlled-public-baseline-config`: Keep real domain, certificate path, private key path, and account-specific values out of tracked files.
- `public-origin-host`: Run origin-host file checks on the origin host; local client reports must not expose TLS paths.
- `active-network-change-path`: Use only an operator-approved local command; do not commit machine-specific interface commands.
- `android-p1-feasibility`: Do not commit device identifiers or carrier-specific command output.
- `aws-identity`: Use local AWS profiles/SSO/env vars only; never commit credentials or access-key CSV files.
- `final-protocol-completion`: Append only with --require-final-countable and --require-artifact-bundle.
