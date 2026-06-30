# Non-iPhone Gate Rerun Report

Local check date: `2026-07-01`

This report summarizes the non-iPhone gates that were rechecked before starting the next research run. It is public-safe and does not include credentials, account IDs, hostnames, IP addresses, qlogs, keylogs, pcaps, or NetLogs.

## Summary

| field | value |
| --- | --- |
| open gates | `[]` |
| all key gates blocked | `true` |
| missing inputs | `[]` |
| claim boundary | This rerun is readiness evidence only. It is not browser Connection Migration, AWS NLB forwarding, or Safari HTTP/3 continuity evidence. |

## Gate Results

| gate | current result | blocker | next input |
| --- | --- | --- | --- |
| AWS NLB+s2n live forwarding | `can_run_live_s2n_nlb_now=no` | `aws_identity_invalid_client_token` | Refresh AWS credentials |
| Safari WebDriver session | `session_ready=false` | `allow_remote_automation_disabled`; `safaridriver_enable=exit_1_password_prompt_required` | Enable Allow remote automation |
| controlled public H3 origin | `h3_alt_svc=false`; `HTTP/2 200` | `no_h3_alt_svc` | Configure H3 origin and Alt-Svc |

## Detailed Fields

| group | field | value |
| --- | --- | --- |
| `aws` | `input_exists` | `True` |
| `aws` | `identity_ok` | `no` |
| `aws` | `identity_classification` | `invalid_client_token` |
| `aws` | `s2n_live_nlb_runner_ready` | `yes` |
| `aws` | `can_run_live_s2n_nlb_now` | `no` |
| `aws` | `blocked_reason` | `aws_identity_invalid_client_token` |
| `safari` | `input_exists` | `True` |
| `safari` | `chrome_netlog_ready` | `True` |
| `safari` | `safari_webdriver_binary_ready` | `True` |
| `safari` | `safari_webdriver_session_checked` | `True` |
| `safari` | `safari_webdriver_session_ready` | `False` |
| `safari` | `safari_webdriver_ready` | `False` |
| `safari` | `safari_session_error_class` | `allow_remote_automation_disabled` |
| `safari` | `safaridriver_enable_status` | `exit_1_password_prompt_required` |
| `safari` | `packet_capture_tooling_ready` | `True` |
| `public_origin` | `input_exists` | `True` |
| `public_origin` | `ok` | `True` |
| `public_origin` | `tcp_tls_ok` | `True` |
| `public_origin` | `curl_https_ok` | `True` |
| `public_origin` | `final_status` | `HTTP/2 200` |
| `public_origin` | `has_h3_alt_svc` | `False` |
| `public_origin` | `redacted` | `True` |
| `public_origin` | `error_class` | `certificate_verify_failed` |

## Interpretation

1. AWS remains the highest-value non-iPhone path, but live resource creation is still blocked by invalid credentials.
2. Safari automation is not unlocked on this host. The non-interactive `safaridriver --enable` attempt requires a password/authorization path, so Safari trials remain a user-setting gate.
3. The user-provided public HTTPS origin is reachable but not H3-ready because it does not advertise `Alt-Svc: h3`.
4. The next real experimental run should start only after one of these gates opens; until then, this is readiness/blocker evidence rather than CM success evidence.
