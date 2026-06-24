#!/usr/bin/env python3
"""Regression tests for replication sufficiency audit."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

from build_replication_sufficiency_audit import build_audit, emit_markdown, wilson_interval, write_csv


def write_fixture(path: Path, text: str) -> None:
    path.write_text(dedent(text).lstrip(), encoding="utf-8")


def install_fixture(root: Path) -> dict[str, Path]:
    paths = {
        "workload": root / "workload.csv",
        "application_recovery": root / "application-recovery.csv",
        "downlink_recovery": root / "downlink-recovery.csv",
        "polling": root / "polling.csv",
    }
    write_fixture(
        paths["workload"],
        """
        workload,drop_window_ms,datasets,runs,pass_count,fail_count,application_complete_count,status_summary,classification_summary,complete_ms_min,complete_ms_median,complete_ms_max,error_ms_min,error_ms_median,error_ms_max,chrome_quic_sessions_min,chrome_quic_sessions_max
        downlink,5000,d,3,2,1,2,FAIL=1; PASS=2,mixed,1,1,1,1,1,1,1,1
        upload,4900,u,3,0,3,0,FAIL=3,fail,,,,1,1,1,2,2
        """,
    )
    write_fixture(
        paths["application_recovery"],
        """
        retry_attempts,retry_delay_ms,drop_window_ms,datasets,runs,pass_count,fail_count,application_complete_count,status_summary,classification_summary,complete_ms_min,complete_ms_median,complete_ms_max,error_ms_min,error_ms_median,error_ms_max,chrome_quic_sessions_min,chrome_quic_sessions_max,upload_sink_requests_min,upload_sink_requests_max,upload_bytes_min,upload_bytes_max
        1,1000,12000,one retry,3,3,0,3,PASS=3,pass,1,1,1,,,,3,3,2,2,1048576,1048576
        """,
    )
    write_fixture(
        paths["downlink_recovery"],
        """
        policy,source_csv,drop_window_ms,runs,pass_count,fail_count,application_complete_count,retries_used_summary,classification_summary,complete_ms_min,complete_ms_median,complete_ms_max,error_ms_min,error_ms_median,error_ms_max,chrome_quic_sessions_min,chrome_quic_sessions_max
        wait_only_no_retry,wait.csv,6000,3,0,3,0,-=3,fail,,,,1,1,1,1,1
        """,
    )
    write_fixture(
        paths["polling"],
        """
        drop_window_ms,datasets,runs,pass_count,fail_count,application_complete_count,server_request_count_min,server_request_count_max,chrome_quic_sessions_min,chrome_quic_sessions_max,qlog_path_challenge_min,qlog_path_challenge_max,qlog_path_response_min,qlog_path_response_max,status_summary,classification_summary
        250,poll,9,9,0,9,7,7,2,2,0,0,0,0,PASS=9,multiple
        """,
    )
    return paths


def test_wilson_interval_is_conservative_for_small_n() -> None:
    low, high = wilson_interval(3, 3)
    assert 0.43 < low < 0.45
    assert high == 1.0


def test_audit_classifies_mixed_rows_as_transition_zone() -> None:
    with TemporaryDirectory() as tmp:
        paths = install_fixture(Path(tmp))
        audit = build_audit(
            paths["workload"],
            paths["application_recovery"],
            paths["downlink_recovery"],
            paths["polling"],
        )
        rows = {row["condition_id"]: row for row in audit["rows"]}
        assert rows["downlink-5000ms"]["evidence_role"] == "transition_zone"
        assert rows["upload-4900ms"]["evidence_role"] == "failure_candidate"
        assert rows["upload-retry1-12000ms"]["evidence_role"] == "stable_candidate"
        assert rows["downlink-5000ms"]["additional_same_outcome_runs_for_rule_of_thumb"] == "-"


def test_audit_is_public_safe_and_writable() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        paths = install_fixture(root)
        output = root / "audit.csv"
        audit = build_audit(
            paths["workload"],
            paths["application_recovery"],
            paths["downlink_recovery"],
            paths["polling"],
        )
        markdown = emit_markdown(audit)
        write_csv(audit, output)
        assert "transition-zone evidence" in markdown
        assert "PRIVATE_KEY" not in markdown
        assert "AKIA" not in markdown
        assert output.exists()


def main() -> int:
    test_wilson_interval_is_conservative_for_small_n()
    test_audit_classifies_mixed_rows_as_transition_zone()
    test_audit_is_public_safe_and_writable()
    print("build_replication_sufficiency_audit=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
