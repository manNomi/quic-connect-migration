#!/usr/bin/env python3
"""Regression tests for browser CM observability readiness scanner."""

from __future__ import annotations

from check_browser_cm_observability import build_readiness, emit_markdown


def test_default_readiness_does_not_run_safari_session_smoke() -> None:
    readiness = build_readiness(
        "/definitely-missing/chrome",
        "/definitely-missing/safari",
        "/definitely-missing/safari-tp",
    )
    assert readiness.safari_webdriver_session_checked is False
    assert readiness.safari_webdriver_session_ready is False
    assert readiness.safari_webdriver_session_error == ""
    markdown = emit_markdown(readiness)
    assert "Safari WebDriver binary ready" in markdown
    assert "Safari WebDriver session checked" in markdown


def main() -> int:
    test_default_readiness_does_not_run_safari_session_smoke()
    print("check_browser_cm_observability=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
