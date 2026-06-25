#!/usr/bin/env python3
"""Regression tests for next final handover trial readiness rules."""

from __future__ import annotations

import contextlib
import io
import os
import argparse
import tempfile
from pathlib import Path

from check_next_final_handover_trial_readiness import (
    DEFAULT_CHROME,
    DEFAULT_REQUIREMENTS,
    DEFAULT_SAFARI,
    DEFAULT_SAFARI_TP,
    build_readiness,
    evaluate_required_gates,
    required_gate_names,
    write_output,
)


def trial(phase: str, browser: str) -> dict:
    return {"phase": phase, "browser": browser}


def test_baseline_does_not_require_network_change() -> None:
    gates = required_gate_names(trial("baseline", "Chrome"))
    assert "network_change_command_present" not in gates
    assert "baseline_summary_ready" not in gates
    assert "desktop_secondary_path_ready" not in gates
    assert "tls_cert_file_exists" not in gates
    assert "tls_key_file_exists" not in gates
    assert "chrome_ready" in gates


def test_local_file_check_requires_tls_paths_on_origin_host() -> None:
    gates = required_gate_names(trial("baseline", "Chrome"), check_local_files=True)
    assert "tls_config_present" in gates
    assert "tls_cert_file_exists" in gates
    assert "tls_key_file_exists" in gates


def test_chrome_active_requires_baseline_network_command_and_secondary_path() -> None:
    gates = required_gate_names(trial("active-network-change", "Chrome"))
    assert "baseline_summary_ready" in gates
    assert "network_change_command_present" in gates
    assert "desktop_secondary_path_ready" in gates
    assert "android_adb_ready" not in gates


def test_safari_p1_requires_safari_and_secondary_path() -> None:
    gates = required_gate_names(trial("p1-feasibility", "Safari"))
    assert "safari_webdriver_ready" in gates
    assert "desktop_secondary_path_ready" in gates
    assert "baseline_summary_ready" in gates
    assert "network_change_command_present" in gates


def test_android_p1_requires_android_command_and_adb() -> None:
    gates = required_gate_names(trial("p1-feasibility", "Android Chrome"))
    assert "android_adb_ready" in gates
    assert "android_network_change_command_present" in gates
    assert "desktop_secondary_path_ready" not in gates


def test_evaluate_required_gates_reports_missing() -> None:
    ready, missing = evaluate_required_gates(["a", "b"], {"a": True, "b": False, "c": False})
    assert ready is False
    assert missing == ["b"]
    ready, missing = evaluate_required_gates(["a"], {"a": True})
    assert ready is True
    assert missing == []


def test_dash_output_prints_stdout_without_dash_file() -> None:
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        try:
            os.chdir(tmp)
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                write_output("ready\n", "-")
            assert buffer.getvalue() == "ready\n"
            assert not Path("-").exists()
        finally:
            os.chdir(original_cwd)


def test_placeholder_config_does_not_open_baseline_readiness() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        config = Path(tmp) / "controlled-public-origin.env"
        config.write_text(
            "\n".join(
                [
                    "PUBLIC_ORIGIN_HOST=h3.example.com",
                    "PUBLIC_ORIGIN_PORT=443",
                    "PUBLIC_ORIGIN_URL=https://h3.example.com/browser-slow",
                    "TLS_CERT_FILE=/etc/letsencrypt/live/h3.example.com/fullchain.pem",
                    "TLS_KEY_FILE=/etc/letsencrypt/live/h3.example.com/privkey.pem",
                    "LISTEN_ADDR=0.0.0.0:443",
                    "TCP_ADDR=0.0.0.0:443",
                    "ALT_SVC='h3=\":443\"; ma=60'",
                    "CHROME_BIN=/bin/sh",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        readiness = build_readiness(
            argparse.Namespace(
                experiments="data/experiment-results.csv",
                requirements=DEFAULT_REQUIREMENTS,
                config=config.as_posix(),
                use_local_config_for_plan=False,
                repetitions=3,
                prefer_p1="safari",
                chrome_bin=DEFAULT_CHROME,
                safari_bin=DEFAULT_SAFARI,
                safari_tp_bin=DEFAULT_SAFARI_TP,
                min_disk_gib=0.0,
                check_local_files=False,
                check_public_origin=False,
                timeout=1,
            )
        )
        assert readiness["ready"] is False
        assert "public_origin_host_configured" in readiness["missing_required_gates"]
        assert "public_origin_url_configured" in readiness["missing_required_gates"]
        assert "tls_config_present" in readiness["missing_required_gates"]


def main() -> int:
    test_baseline_does_not_require_network_change()
    test_local_file_check_requires_tls_paths_on_origin_host()
    test_chrome_active_requires_baseline_network_command_and_secondary_path()
    test_safari_p1_requires_safari_and_secondary_path()
    test_android_p1_requires_android_command_and_adb()
    test_evaluate_required_gates_reports_missing()
    test_dash_output_prints_stdout_without_dash_file()
    test_placeholder_config_does_not_open_baseline_readiness()
    print("check_next_final_handover_trial_readiness=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
