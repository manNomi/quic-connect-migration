# AWS s2n Phase-2 Rebinding Runner Audit

Generated: `2026-07-01`

This public-safe audit checks whether the AWS NLB+s2n live runner has a packaged phase-2 NAT-rebinding proxy mode. It does not include credentials, account IDs, hostnames, IP addresses, key material, qlogs, keylogs, pcaps, or NetLogs.

## Summary

| field | value |
| --- | --- |
| runner_mode_ready | `True` |
| chunked_client_ready | `True` |
| remote_proxy_bind_ready | `True` |
| pre_resource_preflight_recorded | `True` |
| preflight_validation | `blocked` |
| preflight_blocked_reason | `aws_identity_invalid_client_token` |
| preflight_path_change_mode | `rebinding_proxy` |
| preflight_go_found | `yes` |
| preflight_rebinding_proxy_source_ready | `yes` |
| audit_decision | `The phase-2 NAT-rebinding proxy runner is packaged and fail-closed, but AWS credential gates still block live execution.` |

## Claim Boundary

- Safe claim: The repository now has a runnable phase-2 mode that can place a UDP rebinding proxy between the s2n client and AWS NLB, force chunked client traffic after the proxy switch, and classify proxy-observed rebinding separately from forwarding echo.
- Unsafe claim: This audit proves live AWS NLB+s2n NAT-rebinding continuity, application-triggered active migration, browser handover, or current upstream s2n public active migration API support.
- Next step: After AWS identity opens, run forwarding echo first; only if that passes, run this mode with PATH_CHANGE_MODE=rebinding_proxy, PAYLOAD_CHUNKS>1, and CHUNK_DELAY_MS>0.

## Runner Checks

| check | present | meaning |
| --- | --- | --- |
| `mode_flag` | `true` | Default remains forwarding echo. |
| `rebinding_mode_gate` | `true` | Rebinding mode is explicit. |
| `proxy_build` | `true` | Proxy is built inside the run artifact. |
| `proxy_upstream_bind` | `true` | Proxy can bind local upstream sockets for remote NLB targets. |
| `chunk_env` | `true` | Client can be forced to send after the proxy switch. |
| `delay_env` | `true` | Client chunk timing is configurable. |
| `proxy_rebind_observed` | `true` | Summary separates proxy-observed rebind from forwarding echo. |
| `phase2_claim_boundary` | `true` | Result boundary avoids claiming public active migration API support. |

## s2n Client Checks

| check | present | meaning |
| --- | --- | --- |
| `payload_chunks` | `true` | Chunked send is opt-in and default-compatible. |
| `chunk_delay` | `true` | Chunk delay is opt-in and default-compatible. |
| `chunk_sender` | `true` | Payload is split across multiple sends when configured. |
| `client_result_fields` | `true` | Client result records the configured chunk count. |

## UDP Rebinding Proxy Checks

| check | present | meaning |
| --- | --- | --- |
| `upstream_bind_flag` | `true` | Proxy exposes a bind-IP flag. |
| `remote_wildcard_bind` | `true` | Remote upstream targets can use wildcard local binding. |
| `loopback_preserved` | `true` | Loopback behavior remains stable for local Chrome controls. |
| `bind_recorded` | `true` | Proxy result records the bind decision. |

## Interpretation

1. The runner still defaults to forwarding echo, so existing phase-1 semantics are preserved.
2. The phase-2 mode is explicit and requires the rebinding proxy, Go toolchain, chunked client send, and proxy-observed B-side packets before classifying a rebinding run as successful.
3. The current recorded preflight is blocked before AWS resource creation by the AWS identity gate.
4. A future PASS row must still be produced by a live AWS run; this audit only proves readiness and claim boundaries.
