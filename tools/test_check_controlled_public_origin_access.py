#!/usr/bin/env python3
"""Regression tests for controlled public origin access diagnostics."""

from __future__ import annotations

import tempfile
from pathlib import Path

from check_controlled_public_origin_access import (
    build_report,
    classify_ssh_stderr,
    classify_tcp_exception,
    emit_markdown,
)


PRIVATE_HOST = "private-origin.example.test"
PRIVATE_CERT = "/private/lab/fullchain.pem"
PRIVATE_KEY = "/private/lab/privkey.pem"


def test_tcp_exception_classifier_keeps_public_safe_labels() -> None:
    assert classify_tcp_exception(ConnectionRefusedError()) == "connection_refused"
    assert classify_tcp_exception(TimeoutError()) == "timeout"
    assert classify_tcp_exception(OSError("No route to host")) == "network_unreachable"


def test_ssh_classifier_uses_stderr_only_for_categories() -> None:
    assert classify_ssh_stderr("Permission denied (publickey).", 255) == "auth_failed"
    assert classify_ssh_stderr("ssh: connect to host x port 22: Connection refused", 255) == "connection_refused"
    assert classify_ssh_stderr("", 0) == "ok"


def test_report_redacts_configured_host_paths_and_skips_probes() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config = Path(tmpdir) / "controlled-public-origin.env"
        config.write_text(
            f"""
PUBLIC_ORIGIN_HOST={PRIVATE_HOST}
PUBLIC_ORIGIN_PORT=443
PUBLIC_ORIGIN_URL='https://{PRIVATE_HOST}/browser-slow'
TLS_CERT_FILE={PRIVATE_CERT}
TLS_KEY_FILE={PRIVATE_KEY}
""",
            encoding="utf-8",
        )
        report = build_report(
            config,
            timeout=0.1,
            ssh_users=["secret-user"],
            probe_network=False,
            probe_ssh=False,
            probe_aws=False,
        )
    markdown = emit_markdown(report)
    assert "not_probed" in markdown
    assert "user-1" in markdown
    for private in [PRIVATE_HOST, PRIVATE_CERT, PRIVATE_KEY, "secret-user"]:
        assert private not in markdown


def main() -> int:
    test_tcp_exception_classifier_keeps_public_safe_labels()
    test_ssh_classifier_uses_stderr_only_for_categories()
    test_report_redacts_configured_host_paths_and_skips_probes()
    print("check_controlled_public_origin_access=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
