#!/usr/bin/env python3
"""Regression tests for Chrome HTTP/3 artifact classification."""

from __future__ import annotations

from classify_chrome_h3_artifacts import classify, dump_application_complete, dump_task_timing


def base_summary(
    *,
    request_reached_server: bool = True,
    qlog_path_validation: bool = True,
    remote_addr_count: int = 1,
    target_quic_sessions: int = 1,
    target_using_quic_jobs: int = 1,
    qlog_path_probe: bool = True,
    network_change_requested: bool = False,
    client_path_classification: str | None = None,
    rebinding_proxy_switched: bool = False,
    dump_application_complete: bool = True,
    dump_has_chrome_error: bool = False,
) -> dict:
    client_path_change = None
    if client_path_classification is not None:
        client_path_change = {"classification": client_path_classification}
    return {
        "request_reached_server": request_reached_server,
        "qlog_has_path_validation": qlog_path_validation,
        "qlog_has_path_probe": qlog_path_probe,
        "server_remote_addr_count": remote_addr_count,
        "netlog_target_quic_session_count": target_quic_sessions,
        "netlog_target_using_quic_job_count": target_using_quic_jobs,
        "network_change_exit": 0 if network_change_requested else None,
        "client_path_change": client_path_change,
        "rebinding_proxy": {"switched": True} if rebinding_proxy_switched else None,
        "dump_application_complete": dump_application_complete,
        "dump_has_chrome_error": dump_has_chrome_error,
    }


def test_rebinding_path_validation_without_tuple_change_gets_nat_label() -> None:
    assert (
        classify(base_summary(rebinding_proxy_switched=True))
        == "nat_rebinding_path_validation_without_observed_tuple_change"
    )


def test_rebinding_probe_without_response_is_not_validation() -> None:
    assert (
        classify(
            base_summary(
                rebinding_proxy_switched=True,
                qlog_path_validation=False,
                qlog_path_probe=True,
            )
        )
        == "nat_rebinding_path_probe_without_validation"
    )


def test_rebinding_tuple_change_with_multiple_sessions_gets_nat_label() -> None:
    assert (
        classify(
            base_summary(
                rebinding_proxy_switched=True,
                remote_addr_count=2,
                target_quic_sessions=2,
            )
        )
        == "nat_rebinding_multiple_quic_sessions"
    )


def test_non_rebinding_multiple_sessions_keep_network_change_labels() -> None:
    assert (
        classify(base_summary(remote_addr_count=2, target_quic_sessions=2))
        == "multiple_quic_sessions_without_network_change"
    )
    assert (
        classify(
            base_summary(
                remote_addr_count=2,
                target_quic_sessions=2,
                network_change_requested=True,
                client_path_classification="no_client_path_change_observed",
            )
        )
        == "multiple_quic_sessions_without_client_path_change"
    )


def test_rebinding_single_session_tuple_change_is_only_possible_continuity() -> None:
    assert (
        classify(
            base_summary(
                rebinding_proxy_switched=True,
                remote_addr_count=2,
                target_quic_sessions=1,
            )
        )
        == "nat_rebinding_possible_session_continuity"
    )


def test_browser_application_failure_overrides_transport_evidence() -> None:
    assert (
        classify(
            base_summary(
                rebinding_proxy_switched=True,
                dump_application_complete=False,
            )
        )
        == "browser_application_task_failed"
    )
    assert (
        classify(
            base_summary(
                rebinding_proxy_switched=True,
                dump_has_chrome_error=True,
            )
        )
        == "browser_application_task_failed"
    )


def test_dump_task_timing_reads_elapsed_attributes() -> None:
    dump = '<body data-downlink-elapsed-ms="8421" data-upload-error-elapsed-ms="6012"></body>'
    assert dump_task_timing(dump, "rebinding-proxy-downlink") == {
        "elapsed_ms": 8421,
        "error_elapsed_ms": None,
    }
    assert dump_task_timing(dump, "rebinding-proxy-upload") == {
        "elapsed_ms": None,
        "error_elapsed_ms": 6012,
    }


def test_media_completion_and_timing_are_detected() -> None:
    dump = '<body data-media-complete="true" data-media-elapsed-ms="8938"></body>'
    assert dump_application_complete(dump, "rebinding-proxy-media") is True
    assert dump_task_timing(dump, "rebinding-proxy-media") == {
        "elapsed_ms": 8938,
        "error_elapsed_ms": None,
    }


def test_range_completion_and_timing_are_detected() -> None:
    dump = '<body data-range-complete="true" data-range-elapsed-ms="6420"></body>'
    assert dump_application_complete(dump, "rebinding-proxy-range") is True
    assert dump_task_timing(dump, "rebinding-proxy-range") == {
        "elapsed_ms": 6420,
        "error_elapsed_ms": None,
    }


def main() -> int:
    test_rebinding_path_validation_without_tuple_change_gets_nat_label()
    test_rebinding_probe_without_response_is_not_validation()
    test_rebinding_tuple_change_with_multiple_sessions_gets_nat_label()
    test_non_rebinding_multiple_sessions_keep_network_change_labels()
    test_rebinding_single_session_tuple_change_is_only_possible_continuity()
    test_browser_application_failure_overrides_transport_evidence()
    test_dump_task_timing_reads_elapsed_attributes()
    test_media_completion_and_timing_are_detected()
    test_range_completion_and_timing_are_detected()
    print("classify_chrome_h3_artifacts=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
