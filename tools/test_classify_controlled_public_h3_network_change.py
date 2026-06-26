#!/usr/bin/env python3
"""Regression tests for controlled-public network-change classification."""

from __future__ import annotations

from classify_controlled_public_h3_network_change import classify


def base_summary(
    *,
    browser_kind: str = "chrome",
    client_path_error: str | None = None,
    client_path_classification: str = "client_active_path_changed",
    client_active_path_changed: bool = True,
    remote_addr_count: int = 2,
    qlog_path_validation: bool = True,
    quic_sessions: int = 1,
) -> dict:
    return {
        "server_error": None,
        "server_ok": True,
        "server_qlog_has_application_h3": True,
        "server_qlog_has_path_validation": qlog_path_validation,
        "browser_kind": browser_kind,
        "server_requests": {
            "reached_expected_count": True,
            "remote_addr_count": remote_addr_count,
        },
        "network_change": {
            "error": None,
            "command_present": True,
            "exit": 0,
        },
        "client_path_change": {
            "error": client_path_error,
            "classification": client_path_classification,
            "active_path_changed": client_active_path_changed,
        },
        "client_path_eventual_change": {
            "error": None,
            "classification": "",
            "active_path_changed": False,
        },
        "netlog": {
            "target_quic_session_count": quic_sessions,
        },
    }


def test_chrome_positive_requires_client_active_path_change() -> None:
    status, classification = classify(base_summary())
    assert status == "PASS"
    assert classification == "possible_connection_migration"


def test_missing_client_path_snapshot_is_negative_control() -> None:
    status, classification = classify(
        base_summary(
            client_path_error="missing",
            client_path_classification="",
            client_active_path_changed=False,
        )
    )
    assert status == "PASS_NEGATIVE_CONTROL"
    assert classification == "path_snapshot_missing"


def test_no_client_active_path_change_is_negative_control() -> None:
    status, classification = classify(
        base_summary(
            client_path_classification="no_client_path_change_observed",
            client_active_path_changed=False,
        )
    )
    assert status == "PASS_NEGATIVE_CONTROL"
    assert classification == "no_client_active_path_change_observed"


def test_safari_feasibility_also_requires_client_active_path_change() -> None:
    status, classification = classify(
        base_summary(
            browser_kind="safari",
            client_path_classification="no_client_path_change_observed",
            client_active_path_changed=False,
        )
    )
    assert status == "PASS_NEGATIVE_CONTROL"
    assert classification == "no_client_active_path_change_observed"

    status, classification = classify(base_summary(browser_kind="safari"))
    assert status == "PASS_FEASIBILITY"
    assert classification == "possible_connection_migration_server_qlog_only"


def test_eventual_client_path_change_with_application_failure_is_negative_control() -> None:
    summary = base_summary(
        client_path_classification="interface_set_changed_without_route_change",
        client_active_path_changed=False,
        qlog_path_validation=False,
        remote_addr_count=1,
    )
    summary["client_path_eventual_change"] = {
        "error": None,
        "classification": "client_active_path_changed",
        "active_path_changed": True,
    }
    summary["application"] = {
        "workload": "downlink",
        "complete": False,
        "success": False,
        "error_keys": ["downlinkError"],
    }
    status, classification = classify(summary)
    assert status == "PASS_NEGATIVE_CONTROL"
    assert classification == "application_task_failed_without_quic_path_validation"


def test_incomplete_application_without_error_is_distinct_negative_control() -> None:
    summary = base_summary(
        qlog_path_validation=False,
        remote_addr_count=1,
    )
    summary["application"] = {
        "workload": "downlink",
        "complete": False,
        "success": False,
        "error_keys": [],
        "body_dataset": {"downlinkBytes": "4120"},
    }
    status, classification = classify(summary)
    assert status == "PASS_NEGATIVE_CONTROL"
    assert classification == "application_task_incomplete_without_quic_path_validation"


def test_successful_application_without_target_h3_tuple_change_is_not_cm() -> None:
    summary = base_summary(
        qlog_path_validation=False,
        remote_addr_count=5,
    )
    summary["server_requests"]["target_h3_remote_addr_count"] = 1
    summary["application"] = {
        "workload": "downlink",
        "complete": True,
        "success": True,
        "error_keys": [],
        "body_dataset": {"downlinkComplete": "true"},
    }
    status, classification = classify(summary)
    assert status == "PASS_NEGATIVE_CONTROL"
    assert classification == "application_task_succeeded_without_observed_quic_migration"


def main() -> int:
    test_chrome_positive_requires_client_active_path_change()
    test_missing_client_path_snapshot_is_negative_control()
    test_no_client_active_path_change_is_negative_control()
    test_safari_feasibility_also_requires_client_active_path_change()
    test_eventual_client_path_change_with_application_failure_is_negative_control()
    test_incomplete_application_without_error_is_distinct_negative_control()
    test_successful_application_without_target_h3_tuple_change_is_not_cm()
    print("classify_controlled_public_h3_network_change=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
