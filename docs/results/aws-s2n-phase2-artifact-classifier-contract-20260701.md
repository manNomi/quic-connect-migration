# AWS s2n Phase-2 Artifact Classifier Contract

Generated: `2026-07-01`

This public-safe document defines how future AWS NLB+s2n forwarding-echo and NAT-rebinding proxy artifacts must be classified before they are used in the paper.

## Summary

| field | value |
| --- | --- |
| classifier | `tools/classify_aws_s2n_phase2_artifact.py` |
| summary schema source | `harness/scripts/run-aws-s2n-nlb-live-data-plane.sh` |
| paper use | Use this classifier before turning any future AWS live artifact into a paper result row. |

## Required Gates

| phase | required gates | safe boundary |
| --- | --- | --- |
| phase 1 forwarding echo | `summary_status_pass, client_echo_matches, single_successful_target` | Forwarding echo only; not active migration. |
| phase 2 NAT-rebinding proxy | `summary_status_pass, client_echo_matches, single_successful_target, proxy_rebind_observed, proxy_switched_to_b, proxy_has_client_packets, proxy_has_a_and_b_server_packets, upstream_tuple_changed, chunked_client_after_switch` | Controlled NAT-rebinding proxy continuity only; not public s2n active migration API support. |

## Interpretation

1. A forwarding-echo PASS is only an AWS routing prerequisite.
2. A phase-2 PASS requires client continuity, exactly one successful target, proxy-observed A/B tuples, B-side server packets, and chunked client traffic after switch.
3. Even a phase-2 PASS must not be described as public s2n AddPath/Probe/Switch-style active migration.
