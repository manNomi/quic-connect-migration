#!/usr/bin/env python3
"""Regression tests for applying the Chrome artifact contract to bridge rows."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_controlled_public_chrome_contract_application_audit import (
    build_audit,
    classify_record,
    emit_markdown,
    write_outputs,
)


def test_contract_application_preserves_current_public_chrome_boundary() -> None:
    audit = build_audit()
    assert audit["public_safe"] is True
    assert audit["source_record_count"] >= 18
    assert audit["active_row_count"] >= 12
    assert audit["baseline_row_count"] >= 6
    assert audit["strong_single_session_cm_rows"] == []
    assert len(audit["baseline_rows"]) >= 6
    assert len(audit["application_completion_without_cm_rows"]) >= 2
    counts = audit["contract_class_counts"]
    assert counts["public_h3_baseline_positive"] >= 6
    assert counts["application_recovery_or_reconnect"] >= 2
    assert counts["negative_control_record"] >= 1
    missing = audit["active_missing_strong_gate_counts"]
    assert missing["chrome_single_target_quic_session"] == audit["active_row_count"]
    assert missing["server_qlog_path_validation"] >= 1


def test_active_completion_without_qlog_is_not_strong_cm() -> None:
    row = classify_record(
        {
            "trial_id": "active-complete-no-qlog",
            "status": "PASS_NEGATIVE_CONTROL",
            "classification": "tuple_changed_without_path_validation",
            "trigger_class": "active_network_change",
            "workload": "byte_range_download",
            "retry_policy": "application_retry",
            "application_success": True,
            "path_validation_observed": False,
            "tuple_change_observed": True,
            "target_h3_remote_addr_count": "2",
            "notes": "client_path_change=client_active_path_changed; target h3 remote addr count 2",
        }
    )
    assert row["contract_class"] == "application_recovery_or_reconnect"
    assert "server_qlog_path_validation" in row["missing_strong_cm_gates"]
    assert "chrome_single_target_quic_session" in row["missing_strong_cm_gates"]


def test_markdown_is_public_safe_and_names_claim_boundary() -> None:
    markdown = emit_markdown(build_audit())
    assert "Controlled Public Chrome Contract Application Audit" in markdown
    assert "No tracked row satisfies the full strong single-session public Chrome CM contract" in markdown
    assert "PRIVATE KEY" not in markdown
    assert "AWS_" + "SECRET" not in markdown
    assert "AK" + "IA" not in markdown


def test_outputs_are_valid_json_markdown_and_csv() -> None:
    audit = build_audit()
    with tempfile.TemporaryDirectory() as raw:
        md = Path(raw) / "audit.md"
        js = Path(raw) / "audit.json"
        csv = Path(raw) / "audit.csv"
        write_outputs(md, js, csv, audit)
        assert md.read_text(encoding="utf-8").startswith("# Controlled Public Chrome Contract Application Audit")
        parsed = json.loads(js.read_text(encoding="utf-8"))
        assert parsed["row_count"] == audit["row_count"]
        assert csv.read_text(encoding="utf-8").splitlines()[0].startswith("trial_id,status,source_classification")


def main() -> int:
    test_contract_application_preserves_current_public_chrome_boundary()
    test_active_completion_without_qlog_is_not_strong_cm()
    test_markdown_is_public_safe_and_names_claim_boundary()
    test_outputs_are_valid_json_markdown_and_csv()
    print("build_controlled_public_chrome_contract_application_audit=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
