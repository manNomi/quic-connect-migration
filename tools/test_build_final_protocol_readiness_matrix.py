#!/usr/bin/env python3
"""Regression tests for the final protocol readiness matrix."""

from __future__ import annotations

from build_final_protocol_readiness_matrix import required_gates_for_trial, row_state


def test_baseline_requires_chrome_but_not_active_path() -> None:
    plan = {
        "trial_id": "controlled-public-chrome-h3-baseline-001",
        "requirement_id": "chrome-controlled-public-application-h3-baseline",
        "phase": "baseline",
        "browser": "Chrome",
    }
    gates = required_gates_for_trial(plan)
    assert "chrome_ready" in gates
    assert "baseline_summary_ready" not in gates
    assert "network_change_command_present" not in gates
    assert "desktop_secondary_path_ready" not in gates


def test_active_chrome_requires_baseline_network_command_and_secondary_path() -> None:
    plan = {
        "trial_id": "controlled-public-chrome-downlink-noheartbeat-network-change-001",
        "requirement_id": "chrome-downlink-noheartbeat-active-cm",
        "phase": "active-network-change",
        "browser": "Chrome",
    }
    gates = required_gates_for_trial(plan)
    assert "chrome_ready" in gates
    assert "baseline_summary_ready" in gates
    assert "network_change_command_present" in gates
    assert "desktop_secondary_path_ready" in gates


def test_android_p1_requires_android_specific_command() -> None:
    plan = {
        "trial_id": "controlled-public-android-chrome-downlink-network-change-001",
        "requirement_id": "p1-safari-or-android-feasibility",
        "phase": "p1-feasibility",
        "browser": "Android Chrome",
    }
    gates = required_gates_for_trial(plan)
    assert "android_adb_ready" in gates
    assert "android_network_change_command_present" in gates
    assert "desktop_secondary_path_ready" not in gates


def test_row_state_priority() -> None:
    plan = {
        "trial_id": "controlled-public-chrome-h3-baseline-001",
        "requirement_id": "chrome-controlled-public-application-h3-baseline",
    }
    assert row_state(plan, {"controlled-public-chrome-h3-baseline-001"}, {"chrome-controlled-public-application-h3-baseline"}, []) == "recorded"
    assert row_state(plan, set(), set(), []) == "requirement-complete"
    assert row_state(plan, set(), {"chrome-controlled-public-application-h3-baseline"}, []) == "ready"
    assert row_state(plan, set(), {"chrome-controlled-public-application-h3-baseline"}, ["tls_config_present"]) == "blocked"


def main() -> int:
    test_baseline_requires_chrome_but_not_active_path()
    test_active_chrome_requires_baseline_network_command_and_secondary_path()
    test_android_p1_requires_android_specific_command()
    test_row_state_priority()
    print("build_final_protocol_readiness_matrix=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
