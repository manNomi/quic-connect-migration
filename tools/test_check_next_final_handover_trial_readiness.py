#!/usr/bin/env python3
"""Regression tests for next final handover trial readiness rules."""

from __future__ import annotations

from check_next_final_handover_trial_readiness import evaluate_required_gates, required_gate_names


def trial(phase: str, browser: str) -> dict:
    return {"phase": phase, "browser": browser}


def test_baseline_does_not_require_network_change() -> None:
    gates = required_gate_names(trial("baseline", "Chrome"))
    assert "network_change_command_present" not in gates
    assert "baseline_summary_ready" not in gates
    assert "desktop_secondary_path_ready" not in gates
    assert "chrome_ready" in gates


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


def main() -> int:
    test_baseline_does_not_require_network_change()
    test_chrome_active_requires_baseline_network_command_and_secondary_path()
    test_safari_p1_requires_safari_and_secondary_path()
    test_android_p1_requires_android_command_and_adb()
    test_evaluate_required_gates_reports_missing()
    print("check_next_final_handover_trial_readiness=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
