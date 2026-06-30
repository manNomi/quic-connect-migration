#!/usr/bin/env python3
"""Build a public-safe rerun report for non-iPhone research gates."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_AWS_RESULT_ENV = "harness/results/s2n-nlb-live-readiness-20260701-gate/results/result.env"
DEFAULT_BROWSER_JSON = "harness/results/browser-cm-observability-20260701-after-safaridriver-enable/results/browser-cm-observability.json"
DEFAULT_PUBLIC_ORIGIN_JSON = "harness/results/user-provided-public-origin-readiness-20260701-gate/results/public-origin-readiness-redacted.json"
DEFAULT_OUTPUT = "docs/results/non-iphone-gate-rerun-20260701.md"
DEFAULT_JSON_OUTPUT = "data/non-iphone-gate-rerun-20260701.json"


def local_date_iso() -> str:
    return datetime.now().date().isoformat()


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def redact_error_class(message: str) -> str:
    lower = message.lower()
    if "allow remote automation" in lower:
        return "allow_remote_automation_disabled"
    if "certificate_verify_failed" in lower or "certificate verify failed" in lower:
        return "certificate_verify_failed"
    if "invalidclienttokenid" in lower or "invalid_client_token" in lower:
        return "invalid_client_token"
    if "password" in lower:
        return "password_prompt_required"
    return "present" if message else "-"


def build_report(
    aws_result_env: Path,
    browser_json: Path,
    public_origin_json: Path,
    safaridriver_enable_status: str,
    local_check_date: str,
) -> dict[str, Any]:
    aws = read_env(aws_result_env)
    browser = read_json(browser_json)
    public_origin = read_json(public_origin_json)
    missing_inputs = [
        path.as_posix()
        for path, loaded in [
            (aws_result_env, aws),
            (browser_json, browser),
            (public_origin_json, public_origin),
        ]
        if not loaded
    ]

    aws_summary = {
        "input_path": aws_result_env.as_posix(),
        "input_exists": aws_result_env.exists(),
        "identity_ok": aws.get("aws_identity_ok", "unknown"),
        "identity_classification": aws.get("aws_identity_classification", "unknown"),
        "s2n_live_nlb_runner_ready": aws.get("s2n_live_nlb_runner_ready", "unknown"),
        "can_run_live_s2n_nlb_now": aws.get("can_run_live_s2n_nlb_now", "unknown"),
        "blocked_reason": aws.get("blocked_reason", "unknown"),
    }

    safari_error = str(browser.get("safari_webdriver_session_error", ""))
    safari_summary = {
        "input_path": browser_json.as_posix(),
        "input_exists": browser_json.exists(),
        "chrome_netlog_ready": bool(browser.get("chrome_netlog_ready", False)),
        "safari_webdriver_binary_ready": bool(browser.get("safari_webdriver_binary_ready", False)),
        "safari_webdriver_session_checked": bool(browser.get("safari_webdriver_session_checked", False)),
        "safari_webdriver_session_ready": bool(browser.get("safari_webdriver_session_ready", False)),
        "safari_webdriver_ready": bool(browser.get("safari_webdriver_ready", False)),
        "safari_session_error_class": redact_error_class(safari_error),
        "safaridriver_enable_status": safaridriver_enable_status,
        "packet_capture_tooling_ready": bool(browser.get("packet_capture_tooling_ready", False)),
    }

    origin_errors = "; ".join(str(error) for error in public_origin.get("errors", []))
    public_origin_summary = {
        "input_path": public_origin_json.as_posix(),
        "input_exists": public_origin_json.exists(),
        "ok": bool(public_origin.get("ok", False)),
        "tcp_tls_ok": bool(public_origin.get("tcp_tls_ok", False)),
        "curl_https_ok": bool(public_origin.get("curl_https_ok", False)),
        "final_status": public_origin.get("final_status", "-"),
        "has_h3_alt_svc": bool(public_origin.get("has_h3_alt_svc", False)),
        "redacted": bool(public_origin.get("redacted", False)),
        "error_class": redact_error_class(origin_errors),
    }

    open_gates: list[str] = []
    if aws_summary["can_run_live_s2n_nlb_now"] == "yes":
        open_gates.append("aws-s2n-nlb-live-forwarding")
    if safari_summary["safari_webdriver_session_ready"]:
        open_gates.append("safari-webdriver-session")
    if public_origin_summary["has_h3_alt_svc"]:
        open_gates.append("controlled-public-h3-origin")

    return {
        "generated_local_date": local_check_date,
        "public_safe": True,
        "missing_inputs": missing_inputs,
        "open_gates": open_gates,
        "all_key_gates_blocked": not open_gates,
        "aws": aws_summary,
        "safari": safari_summary,
        "public_origin": public_origin_summary,
        "next_required_inputs": [
            "Refresh AWS credentials for AWS NLB+s2n live forwarding.",
            "Configure a controlled public H3 origin with WebPKI TLS, Alt-Svc, and workload endpoints.",
            "Enable Safari Allow remote automation if Safari feasibility trials are needed.",
        ],
        "claim_boundary": "This rerun is readiness evidence only. It is not browser Connection Migration, AWS NLB forwarding, or Safari HTTP/3 continuity evidence.",
    }


def emit_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Non-iPhone Gate Rerun Report",
        "",
        f"Local check date: `{report['generated_local_date']}`",
        "",
        "This report summarizes the non-iPhone gates that were rechecked before starting the next research run. It is public-safe and does not include credentials, account IDs, hostnames, IP addresses, qlogs, keylogs, pcaps, or NetLogs.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| open gates | `{report['open_gates']}` |",
        f"| all key gates blocked | `{str(report['all_key_gates_blocked']).lower()}` |",
        f"| missing inputs | `{report['missing_inputs']}` |",
        f"| claim boundary | {report['claim_boundary']} |",
        "",
        "## Gate Results",
        "",
        "| gate | current result | blocker | next input |",
        "| --- | --- | --- | --- |",
        f"| AWS NLB+s2n live forwarding | `can_run_live_s2n_nlb_now={report['aws']['can_run_live_s2n_nlb_now']}` | `{report['aws']['blocked_reason']}` | Refresh AWS credentials |",
        f"| Safari WebDriver session | `session_ready={str(report['safari']['safari_webdriver_session_ready']).lower()}` | `{report['safari']['safari_session_error_class']}`; `safaridriver_enable={report['safari']['safaridriver_enable_status']}` | Enable Allow remote automation |",
        f"| controlled public H3 origin | `h3_alt_svc={str(report['public_origin']['has_h3_alt_svc']).lower()}`; `{report['public_origin']['final_status']}` | `no_h3_alt_svc` | Configure H3 origin and Alt-Svc |",
        "",
        "## Detailed Fields",
        "",
        "| group | field | value |",
        "| --- | --- | --- |",
    ]
    for group in ("aws", "safari", "public_origin"):
        for key, value in report[group].items():
            if key.endswith("_path"):
                continue
            lines.append(f"| `{group}` | `{key}` | `{value}` |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "1. AWS remains the highest-value non-iPhone path, but live resource creation is still blocked by invalid credentials.",
            "2. Safari automation is not unlocked on this host. The non-interactive `safaridriver --enable` attempt requires a password/authorization path, so Safari trials remain a user-setting gate.",
            "3. The user-provided public HTTPS origin is reachable but not H3-ready because it does not advertise `Alt-Svc: h3`.",
            "4. The next real experimental run should start only after one of these gates opens; until then, this is readiness/blocker evidence rather than CM success evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(markdown_path: Path, json_path: Path, report: dict[str, Any]) -> None:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(emit_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aws-result-env", default=DEFAULT_AWS_RESULT_ENV)
    parser.add_argument("--browser-json", default=DEFAULT_BROWSER_JSON)
    parser.add_argument("--public-origin-json", default=DEFAULT_PUBLIC_ORIGIN_JSON)
    parser.add_argument(
        "--safaridriver-enable-status",
        default="exit_1_password_prompt_required",
        help="Public-safe summary of the non-interactive safaridriver --enable attempt.",
    )
    parser.add_argument("--local-check-date", default=local_date_iso())
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    report = build_report(
        Path(args.aws_result_env),
        Path(args.browser_json),
        Path(args.public_origin_json),
        args.safaridriver_enable_status,
        args.local_check_date,
    )
    write_outputs(Path(args.output), Path(args.json_output), report)
    print(f"wrote {args.output}")
    print(f"wrote {args.json_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
