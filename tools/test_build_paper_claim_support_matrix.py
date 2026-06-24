#!/usr/bin/env python3
"""Regression tests for the paper claim-support matrix builder."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

from build_paper_claim_support_matrix import build_matrix, emit_markdown, write_csv


def write_fixture(path: Path, text: str) -> None:
    path.write_text(dedent(text).lstrip(), encoding="utf-8")


def install_fixture(root: Path) -> dict[str, Path]:
    paths = {
        "experiments": root / "experiments.csv",
        "implementations": root / "implementations.csv",
        "workload": root / "workload.csv",
        "application_recovery": root / "application-recovery.csv",
        "downlink_recovery": root / "downlink-recovery.csv",
        "polling": root / "polling.csv",
        "requirements": root / "requirements.csv",
    }
    write_fixture(
        paths["experiments"],
        """
        trial_id,date,status,implementation,deployment_tier,protocol,migration_trigger,path_validation_observed,tuple_change_observed,application_task,application_success,manual_intervention_required,failure_layer,artifact_dir,notes
        quic-go-h3,2026-06-24,PASS,quic-go + HTTP/3,local direct origin,HTTP/3 over QUIC,AddPath,true,true,1MiB upload,true,false,none,artifacts/a,positive control
        chrome-neg,2026-06-24,PASS_NEGATIVE_CONTROL,Chrome,local browser,HTTP/3 over QUIC,reconnect,false,true,poll,true,false,browser-multiple-quic-sessions-no-network-change,artifacts/b,negative control
        """,
    )
    write_fixture(
        paths["implementations"],
        """
        priority,name,category,usage_reason,rfc_primitives,passive_migration,active_migration_api,preferred_address,observability,tests,lb_or_cloud_deployability,aws_suitability,current_level,evidence_status,next_action
        1,quic-go,library,reason,yes,yes,yes,partial,qlog,yes,manual,high,L4,source,next
        2,HAProxy,proxy,reason,partial,partial,no,limited,logs,unknown,server,medium,L1_L2,source,next
        """,
    )
    write_fixture(
        paths["workload"],
        """
        workload,drop_window_ms,datasets,runs,pass_count,fail_count,application_complete_count,status_summary,classification_summary,complete_ms_min,complete_ms_median,complete_ms_max,error_ms_min,error_ms_median,error_ms_max,chrome_quic_sessions_min,chrome_quic_sessions_max
        downlink,5000,d,3,2,1,2,FAIL=1; PASS=2,mixed,1,1,1,1,1,1,1,1
        downlink,6000,d,3,0,3,0,FAIL=3,fail,,,,1,1,1,1,1
        upload,4600,u,3,3,0,3,PASS=3,pass,1,1,1,,,,1,1
        upload,4900,u,3,0,3,0,FAIL=3,fail,,,,1,1,1,2,2
        """,
    )
    write_fixture(
        paths["application_recovery"],
        """
        retry_attempts,retry_delay_ms,drop_window_ms,datasets,runs,pass_count,fail_count,application_complete_count,status_summary,classification_summary,complete_ms_min,complete_ms_median,complete_ms_max,error_ms_min,error_ms_median,error_ms_max,chrome_quic_sessions_min,chrome_quic_sessions_max,upload_sink_requests_min,upload_sink_requests_max,upload_bytes_min,upload_bytes_max
        0,0,4600,no retry,3,3,0,3,PASS=3,pass,1,1,1,,,,1,1,1,1,1048576,1048576
        0,0,4900,no retry,3,0,3,0,FAIL=3,fail,,,,1,1,1,2,2,1,1,0,0
        1,1000,12000,one retry,3,3,0,3,PASS=3,pass,1,1,1,,,,3,3,2,2,1048576,1048576
        1,1000,15000,one retry,3,0,3,0,FAIL=3,fail,,,,1,1,1,3,3,1,1,0,0
        2,1000,18000,two retry,3,3,0,3,PASS=3,pass,1,1,1,,,,4,4,2,2,1048576,1048576
        2,1000,21000,two retry,3,0,3,0,FAIL=3,fail,,,,1,1,1,4,4,1,1,0,0
        """,
    )
    write_fixture(
        paths["downlink_recovery"],
        """
        policy,source_csv,drop_window_ms,runs,pass_count,fail_count,application_complete_count,retries_used_summary,classification_summary,complete_ms_min,complete_ms_median,complete_ms_max,error_ms_min,error_ms_median,error_ms_max,chrome_quic_sessions_min,chrome_quic_sessions_max
        wait_only_no_retry,wait.csv,6000,3,0,3,0,-=3,fail,,,,1,1,1,1,1
        retry_enabled_1x500ms,retry.csv,6000,3,3,0,3,1=3,pass,1,1,1,,,,2,2
        """,
    )
    write_fixture(
        paths["polling"],
        """
        drop_window_ms,datasets,runs,pass_count,fail_count,application_complete_count,server_request_count_min,server_request_count_max,chrome_quic_sessions_min,chrome_quic_sessions_max,qlog_path_challenge_min,qlog_path_challenge_max,qlog_path_response_min,qlog_path_response_max,status_summary,classification_summary
        250,poll,3,3,0,3,7,7,2,2,0,0,0,0,PASS=3,multiple
        4000,poll,3,1,2,1,2,7,2,2,0,7,0,4,FAIL=2; PASS=1,mixed
        6000,poll,3,0,3,0,2,2,2,2,0,0,0,0,FAIL=3,fail
        """,
    )
    write_fixture(
        paths["requirements"],
        """
        requirement_id,phase,browser,description,min_count,accepted_statuses,trial_id_contains_all,deployment_contains_all,trigger_contains_all,task_contains_all,notes_contains_all,notes_contains_any,notes_excludes_any
        chrome-controlled-public-application-h3-baseline,baseline,Chrome,baseline,1,PASS,controlled-public;baseline,controlled public,,browser,,controlled_public_application_h3_confirmed,
        """,
    )
    return paths


def test_matrix_keeps_final_browser_claim_blocked() -> None:
    with TemporaryDirectory() as tmp:
        paths = install_fixture(Path(tmp))
        matrix = build_matrix(
            paths["experiments"],
            paths["implementations"],
            paths["workload"],
            paths["application_recovery"],
            paths["downlink_recovery"],
            paths["polling"],
            paths["requirements"],
        )
        rows = {row["claim_id"]: row for row in matrix["rows"]}
        assert rows["browser-local-h3-is-ready-but-final-handover-is-pending"]["support_level"] == "not_supported_yet"
        assert rows["publication-ready-browser-cm-claim-remains-blocked"]["support_level"] == "not_supported_yet"
        assert "0/1" in rows["publication-ready-browser-cm-claim-remains-blocked"]["computed_evidence"]
        assert "Do not claim Chrome" in rows["browser-local-h3-is-ready-but-final-handover-is-pending"]["do_not_claim"]


def test_matrix_reports_retry_boundaries_and_is_writable() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        paths = install_fixture(root)
        output = root / "claim.csv"
        matrix = build_matrix(
            paths["experiments"],
            paths["implementations"],
            paths["workload"],
            paths["application_recovery"],
            paths["downlink_recovery"],
            paths["polling"],
            paths["requirements"],
        )
        markdown = emit_markdown(matrix)
        write_csv(matrix, output)
        assert "1 retry stable-through=12000ms" in markdown
        assert "max Chrome sessions=4" in markdown
        assert "AWS_SECRET" not in markdown
        assert output.exists()


def main() -> int:
    test_matrix_keeps_final_browser_claim_blocked()
    test_matrix_reports_retry_boundaries_and_is_writable()
    print("build_paper_claim_support_matrix=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
