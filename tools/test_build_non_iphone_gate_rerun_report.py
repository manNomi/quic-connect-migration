#!/usr/bin/env python3
"""Regression tests for the non-iPhone gate rerun report builder."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_non_iphone_gate_rerun_report import build_report, emit_markdown, write_outputs


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
    "i18" + "nexus",
]


def write_fixture(root: Path) -> tuple[Path, Path, Path]:
    aws_env = root / "result.env"
    aws_env.write_text(
        "\n".join(
            [
                "aws_identity_ok=no",
                "aws_identity_classification=invalid_client_token",
                "s2n_live_nlb_runner_ready=yes",
                "can_run_live_s2n_nlb_now=no",
                "blocked_reason=aws_identity_invalid_client_token",
                "",
            ]
        ),
        encoding="utf-8",
    )
    browser_json = root / "browser.json"
    browser_json.write_text(
        json.dumps(
            {
                "chrome_netlog_ready": True,
                "safari_webdriver_binary_ready": True,
                "safari_webdriver_session_checked": True,
                "safari_webdriver_session_ready": False,
                "safari_webdriver_session_error": "Could not create a session: You must enable 'Allow remote automation'",
                "safari_webdriver_ready": False,
                "packet_capture_tooling_ready": True,
            }
        ),
        encoding="utf-8",
    )
    public_origin_json = root / "public-origin.json"
    public_origin_json.write_text(
        json.dumps(
            {
                "ok": True,
                "tcp_tls_ok": True,
                "curl_https_ok": True,
                "final_status": "HTTP/2 200",
                "has_h3_alt_svc": False,
                "redacted": True,
                "errors": ["tls: certificate verify failed"],
            }
        ),
        encoding="utf-8",
    )
    return aws_env, browser_json, public_origin_json


def test_report_classifies_closed_gates() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        aws_env, browser_json, public_origin_json = write_fixture(Path(tmpdir))
        report = build_report(
            aws_env,
            browser_json,
            public_origin_json,
            "exit_1_password_prompt_required",
            "2026-07-01",
        )
    assert report["public_safe"] is True
    assert report["open_gates"] == []
    assert report["all_key_gates_blocked"] is True
    assert report["aws"]["blocked_reason"] == "aws_identity_invalid_client_token"
    assert report["safari"]["safari_session_error_class"] == "allow_remote_automation_disabled"
    assert report["public_origin"]["has_h3_alt_svc"] is False
    assert report["public_origin"]["error_class"] == "certificate_verify_failed"


def test_markdown_is_public_safe_and_names_next_inputs() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        aws_env, browser_json, public_origin_json = write_fixture(Path(tmpdir))
        report = build_report(
            aws_env,
            browser_json,
            public_origin_json,
            "exit_1_password_prompt_required",
            "2026-07-01",
        )
    markdown = emit_markdown(report)
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "Refresh AWS credentials" in markdown
    assert "Enable Allow remote automation" in markdown
    assert "Configure H3 origin and Alt-Svc" in markdown


def test_outputs_are_valid_json_and_markdown() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        aws_env, browser_json, public_origin_json = write_fixture(root)
        report = build_report(
            aws_env,
            browser_json,
            public_origin_json,
            "exit_1_password_prompt_required",
            "2026-07-01",
        )
        out = root / "report.md"
        jout = root / "report.json"
        write_outputs(out, jout, report)
        assert out.read_text(encoding="utf-8").startswith("# Non-iPhone Gate Rerun Report")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["all_key_gates_blocked"] is True


def main() -> int:
    test_report_classifies_closed_gates()
    test_markdown_is_public_safe_and_names_next_inputs()
    test_outputs_are_valid_json_and_markdown()
    print("build_non_iphone_gate_rerun_report=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
