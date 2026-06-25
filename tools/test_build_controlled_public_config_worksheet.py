#!/usr/bin/env python3
"""Regression tests for the controlled-public config worksheet."""

from __future__ import annotations

import tempfile
from pathlib import Path

from build_controlled_public_config_worksheet import build_worksheet, emit_markdown


def test_missing_config_reports_baseline_next_step() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config = Path(tmp) / "missing.env"
        worksheet = build_worksheet(config, check_files=False)
        assert worksheet["config_exists"] is False
        assert worksheet["baseline_config_ready"] is False
        assert worksheet["next_step"] == "fill_baseline_config"
        assert "PUBLIC_ORIGIN_HOST" in worksheet["baseline_missing"]
        assert "init-controlled-public-config.sh" in emit_markdown(worksheet)


def test_valid_config_is_public_safe_without_printing_values() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config = Path(tmp) / "controlled-public-origin.env"
        config.write_text(
            "\n".join(
                [
                    "PUBLIC_ORIGIN_HOST=h3.private-lab.test",
                    "PUBLIC_ORIGIN_PORT=443",
                    "PUBLIC_ORIGIN_URL=https://h3.private-lab.test/browser-slow",
                    "PUBLIC_ORIGIN_NETWORK_CHANGE_URL=https://h3.private-lab.test/browser-slow?duration_ms=15000",
                    "TLS_CERT_FILE=/private/lab/fullchain.pem",
                    "TLS_KEY_FILE=/private/lab/privkey.pem",
                    "LISTEN_ADDR=0.0.0.0:443",
                    "TCP_ADDR=0.0.0.0:443",
                    "ALT_SVC='h3=\":443\"; ma=60'",
                    "CONTROLLED_PUBLIC_BASELINE_SUMMARY=artifacts/baseline/results/controlled-public-h3-baseline-summary.json",
                    "NETWORK_CHANGE_AFTER_SECONDS=3",
                    "NETWORK_CHANGE_CMD='printf path-change'",
                    "ANDROID_NETWORK_CHANGE_CMD='adb shell cmd connectivity airplane-mode enable'",
                    "CHROME_BIN=/bin/sh",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        worksheet = build_worksheet(config, check_files=False)
        markdown = emit_markdown(worksheet)
        assert worksheet["baseline_config_ready"] is True
        assert worksheet["active_network_change_config_ready"] is True
        assert worksheet["android_network_change_config_ready"] is True
        assert worksheet["next_step"] == "config_ready_for_all_declared_stages"
        assert "h3.private-lab.test" not in markdown
        assert "/private/lab/privkey.pem" not in markdown
        assert "printf path-change" not in markdown
        assert "port equals PUBLIC_ORIGIN_PORT" in markdown


def main() -> int:
    test_missing_config_reports_baseline_next_step()
    test_valid_config_is_public_safe_without_printing_values()
    print("build_controlled_public_config_worksheet=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
