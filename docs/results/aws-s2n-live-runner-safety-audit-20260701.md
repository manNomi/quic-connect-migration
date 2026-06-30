# AWS s2n Live Runner Safety Audit

Generated: `2026-06-30`

This public-safe audit statically checks the AWS NLB + s2n-quic live runner before live resource creation. It does not include credentials, account IDs, hostnames, IP addresses, key material, qlogs, keylogs, pcaps, or NetLogs.

## Summary

| field | value |
| --- | --- |
| fail-closed gate ok | `true` |
| resource inventory ok | `true` |
| cleanup coverage ok | `true` |
| risk boundary ok | `true` |
| estimated live resources | `{'ec2_instances': 2, 'network_load_balancers': 1, 'target_groups': 1, 'listeners': 1, 'security_groups': 1, 'key_pairs': 1}` |
| current gate | `{'aws_identity_ok': 'no', 'aws_identity_classification': 'invalid_client_token', 'can_run_live_s2n_nlb_now': 'no', 'blocked_reason': 'aws_identity_invalid_client_token', 'local_proof_status': 'PASS', 's2n_live_nlb_runner_ready': 'yes'}` |
| audit decision | Do not run live AWS resources until aws_identity_ok=yes; when opened, run forwarding echo first and keep active migration as phase 2. |

## Claim Boundary

- Safe claim: The live runner has explicit pre-resource AWS identity gating, an inventoried temporary resource set, and cleanup coverage for listener, NLB, target group, instances, security group, key pair, and local key material.
- Unsafe claim: This safety audit proves live AWS forwarding, active Connection Migration, absence of cloud cost, or cleanup success under all possible process-kill/cloud-failure modes.
- Next step: After credential refresh, run the live forwarding echo with default cleanup, then inspect result.env and summary.json before designing any active path-change variant.

## Fail-closed Checks

| check | present | meaning |
| --- | --- | --- |
| `identity_checker` | `true` | AWS identity is checked before live resource creation. |
| `identity_ok_gate` | `true` | Invalid credentials stop the runner before AWS resources are created. |
| `readiness_exit_gate` | `true` | Non-zero readiness checker exit is fail-closed. |
| `blocked_result_writer` | `true` | Blocked runs write a public-safe result artifact. |
| `require_live_switch` | `true` | Operators can force blocked readiness to fail CI/local scripts when desired. |

## Temporary Resource Inventory

| check | present | meaning |
| --- | --- | --- |
| `key_pair` | `true` | Temporary SSH key pair for target bootstrap. |
| `security_group` | `true` | Temporary target security group. |
| `target_instances` | `true` | Two temporary EC2 targets. |
| `target_group` | `true` | Temporary QUIC target group. |
| `load_balancer` | `true` | Temporary internet-facing NLB. |
| `listener` | `true` | Temporary QUIC listener. |
| `target_registration` | `true` | Target registration with QuicServerId. |

## Cleanup Coverage

| check | present | meaning |
| --- | --- | --- |
| `trap_cleanup` | `true` | Cleanup runs on normal exit and most shell errors. |
| `collect_targets` | `true` | Target artifacts are collected before teardown when possible. |
| `delete_listener` | `true` | Listener teardown. |
| `delete_load_balancer` | `true` | NLB teardown. |
| `wait_lb_deleted` | `true` | Waits until NLB deletion completes. |
| `deregister_targets` | `true` | Target deregistration. |
| `delete_target_group` | `true` | Target group teardown. |
| `terminate_instances` | `true` | EC2 target termination. |
| `wait_instances_terminated` | `true` | Waits until instances terminate. |
| `delete_security_group` | `true` | Security group teardown. |
| `delete_key_pair` | `true` | AWS key pair teardown. |
| `remove_local_key` | `true` | Local private/public key cleanup. |

## Risk Boundaries

| check | present | meaning |
| --- | --- | --- |
| `keep_resources_override` | `true` | If set, cleanup can be intentionally skipped for debugging. |
| `client_public_cidr` | `true` | SSH/UDP exposure is constrained to the operator public CIDR and VPC CIDR. |
| `tag_run_id` | `true` | Resources are tagged with RunId for cleanup/forensics. |
| `claim_boundary` | `true` | The live runner only claims forwarding echo, not active migration. |

## Interpretation

1. This audit lowers execution risk but is not live AWS evidence.
2. The current gate remains closed when `aws_identity_ok` is not `yes`.
3. The first live run should prove only s2n target forwarding through AWS NLB.
4. Active source/path migration for s2n remains a later design phase because the public application API does not expose a quic-go-like AddPath/Probe/Switch trigger.
