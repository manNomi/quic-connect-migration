#!/usr/bin/env python3
"""Regression tests for final handover operator checklist action ordering."""

from __future__ import annotations

from build_final_handover_operator_checklist import build_actions


def incomplete_config() -> dict:
    return {
        "baseline_config_ready": False,
        "active_network_change_config_ready": False,
        "android_network_change_config_ready": False,
    }


def complete_config() -> dict:
    return {
        "baseline_config_ready": True,
        "active_network_change_config_ready": True,
        "android_network_change_config_ready": True,
    }


def cleanup(target_met: bool) -> dict:
    return {
        "target_met_by_selected": target_met,
        "remaining_gap_human": "1.7 GiB" if not target_met else "0 B",
        "selected_reclaimable_human": "2.0 GiB",
    }


def next_readiness(ready: bool) -> dict:
    return {
        "ready": ready,
        "missing_required_gates": [] if ready else ["controlled_public_config_present", "disk_ready"],
        "next_trial": {"trial_id": "controlled-public-chrome-h3-baseline-001"},
        "handover": {
            "secondary_path_ready": ready,
            "android_ready": ready,
        },
    }


def final_audit(complete: bool) -> dict:
    return {
        "complete": complete,
        "complete_count": 6 if complete else 0,
        "requirement_count": 6,
    }


def test_blocked_state_prioritizes_config_storage_and_next_trial() -> None:
    actions = build_actions(incomplete_config(), next_readiness(False), cleanup(False), final_audit(False))
    statuses = {(item.priority, item.scope): item.status for item in actions}
    assert statuses[(1, "controlled public baseline")] == "todo-now"
    assert statuses[(2, "storage")] == "todo-now"
    assert statuses[(3, "next trial")] == "blocked-now"
    assert statuses[(7, "final protocol")] == "incomplete"
    assert actions == sorted(actions, key=lambda item: item.priority)


def test_ready_baseline_state_marks_next_trial_runnable() -> None:
    actions = build_actions(complete_config(), next_readiness(True), cleanup(True), final_audit(True))
    statuses = {(item.priority, item.scope): item.status for item in actions}
    assert statuses[(1, "controlled public baseline")] == "ready"
    assert statuses[(2, "storage")] == "ready"
    assert statuses[(3, "next trial")] == "ready-to-run"
    assert all(item.scope != "final protocol" for item in actions)


def main() -> int:
    test_blocked_state_prioritizes_config_storage_and_next_trial()
    test_ready_baseline_state_marks_next_trial_runnable()
    print("build_final_handover_operator_checklist=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
