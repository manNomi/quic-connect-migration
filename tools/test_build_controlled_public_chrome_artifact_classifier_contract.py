#!/usr/bin/env python3
"""Regression tests for the controlled-public Chrome artifact classifier contract."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from build_controlled_public_chrome_artifact_classifier_contract import contract, emit_markdown, write_outputs


def test_contract_requires_full_single_row_cm_chain() -> None:
    doc = contract()
    active_gates = {row["name"] for row in doc["active_strong_cm_required_gates"]}
    assert "application_completion_metric_true" in active_gates
    assert "network_change_command_executed" in active_gates
    assert "client_active_path_changed" in active_gates
    assert "server_target_h3_tuple_changed" in active_gates
    assert "server_qlog_path_validation" in active_gates
    assert "chrome_single_target_quic_session" in active_gates

    markdown = emit_markdown(doc)
    assert "Application completion alone is insufficient" in markdown
    assert "one Chrome target QUIC session" in markdown
    assert "task completion, client active path change, target H3 tuple change" in markdown


def test_contract_preserves_negative_controls_and_workload_boundaries() -> None:
    doc = contract()
    negative = set(doc["negative_control_classes_to_preserve"])
    assert "tuple_changed_without_path_validation" in negative
    assert "reconnect_or_multiple_sessions" in negative
    assert "application_task_succeeded_without_observed_quic_migration" in negative

    workloads = {row["workload"]: row for row in doc["workload_rules"]}
    assert "large byte-range download" in workloads
    assert "large upload" in workloads
    assert "buffered video playback" in workloads
    assert "music-like segment" in workloads
    assert "QoE" in workloads["buffered video playback"]["primary_use"]
    assert "request tuple alone" in workloads["large upload"]["strong_cm_extra_requirement"]


def test_contract_outputs_public_safe_markdown_and_json() -> None:
    doc = contract()
    with tempfile.TemporaryDirectory() as raw:
        out = Path(raw) / "contract.md"
        jout = Path(raw) / "contract.json"
        write_outputs(out, jout, doc)
        assert out.read_text(encoding="utf-8").startswith("# Controlled Public Chrome Artifact Classifier Contract")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["public_safe"] is True
        assert parsed["source_classifier"] == "tools/classify_controlled_public_h3_network_change.py"
        text = out.read_text(encoding="utf-8")
        assert "PRIVATE KEY" not in text
        assert "AWS_" + "SECRET" not in text
        assert "AK" + "IA" not in text


def main() -> int:
    test_contract_requires_full_single_row_cm_chain()
    test_contract_preserves_negative_controls_and_workload_boundaries()
    test_contract_outputs_public_safe_markdown_and_json()
    print("build_controlled_public_chrome_artifact_classifier_contract=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
