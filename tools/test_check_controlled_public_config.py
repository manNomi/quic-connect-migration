#!/usr/bin/env python3
"""Regression tests for controlled-public config schema checks."""

from __future__ import annotations

import tempfile
from pathlib import Path

from check_controlled_public_config import build_report


BASELINE_CONFIG = """
PUBLIC_ORIGIN_HOST=h3.test.local
PUBLIC_ORIGIN_PORT=443
PUBLIC_ORIGIN_URL='https://h3.test.local/browser-slow?duration_ms=6000&chunks=6&label=public-slow'
TLS_CERT_FILE=/tmp/fullchain.pem
TLS_KEY_FILE=/tmp/privkey.pem
LISTEN_ADDR=0.0.0.0:443
TCP_ADDR=0.0.0.0:443
ALT_SVC='h3=":443"; ma=60'
CHROME_BIN=/bin/sh
"""


ACTIVE_EXTRA = """
PUBLIC_ORIGIN_NETWORK_CHANGE_URL='https://h3.test.local/browser-slow?duration_ms=15000&chunks=15&label=handover-slow'
CONTROLLED_PUBLIC_BASELINE_SUMMARY=artifacts/controlled-public-chrome-h3-baseline-001/results/controlled-public-h3-baseline-summary.json
NETWORK_CHANGE_AFTER_SECONDS=3
NETWORK_CHANGE_CMD='sudo networksetup -setairportpower Wi-Fi off'
ANDROID_NETWORK_CHANGE_CMD='adb shell svc wifi disable'
"""


def test_missing_config_is_not_ready() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        report = build_report(Path(tmp) / "missing.env")
    assert report["config_exists"] is False
    assert report["baseline_config_ready"] is False
    assert any("config file is missing" in blocker for blocker in report["blockers"])


def test_baseline_ready_does_not_require_active_keys() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "controlled-public-origin.env"
        path.write_text(BASELINE_CONFIG, encoding="utf-8")
        report = build_report(path)
    assert report["baseline_config_ready"] is True
    assert report["active_network_change_config_ready"] is False
    assert any("NETWORK_CHANGE_CMD" in blocker for blocker in report["blockers"])


def test_active_ready_when_all_keys_present() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "controlled-public-origin.env"
        path.write_text(BASELINE_CONFIG + ACTIVE_EXTRA, encoding="utf-8")
        report = build_report(path)
    assert report["baseline_config_ready"] is True
    assert report["active_network_change_config_ready"] is True
    assert report["android_network_change_config_ready"] is True


def test_example_placeholders_are_not_ready() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "controlled-public-origin.env"
        path.write_text(
            """
PUBLIC_ORIGIN_HOST=h3.example.com
PUBLIC_ORIGIN_PORT=443
PUBLIC_ORIGIN_URL='https://h3.example.com/browser-slow?duration_ms=6000'
TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem
TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem
LISTEN_ADDR=0.0.0.0:443
TCP_ADDR=0.0.0.0:443
ALT_SVC='h3=":443"; ma=60'
CHROME_BIN=/bin/sh
""",
            encoding="utf-8",
        )
        report = build_report(path)
    assert report["baseline_config_ready"] is False
    host = next(item for item in report["key_checks"] if item["key"] == "PUBLIC_ORIGIN_HOST")
    assert host["placeholder"] is True
    assert host["valid"] is False


def main() -> int:
    test_missing_config_is_not_ready()
    test_baseline_ready_does_not_require_active_keys()
    test_active_ready_when_all_keys_present()
    test_example_placeholders_are_not_ready()
    print("check_controlled_public_config=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
