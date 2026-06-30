#!/usr/bin/env python3
"""Regression tests for AWS s2n phase-2 artifact classification."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from classify_aws_s2n_phase2_artifact import classify_summary, contract, emit_markdown


def forwarding_summary() -> dict[str, object]:
    return {
        "status": "PASS",
        "path_change_mode": "forwarding_echo",
        "client_echo_matches": True,
        "server_success_count": 1,
        "successful_target": "target-a",
    }


def rebinding_summary() -> dict[str, object]:
    return {
        "status": "PASS",
        "path_change_mode": "rebinding_proxy",
        "client_echo_matches": True,
        "client_payload_chunks": 8,
        "client_chunk_delay_ms": 250,
        "server_success_count": 1,
        "successful_target": "target-a",
        "proxy_rebind_observed": True,
        "rebinding_proxy": {
            "switched": True,
            "client_packets": 24,
            "server_packets_a": 12,
            "server_packets_b": 7,
            "upstream_a_addr": "127.0.0.1:49152",
            "upstream_b_addr": "127.0.0.1:49153",
        },
    }


def test_forwarding_echo_is_only_phase1_positive() -> None:
    result = classify_summary(forwarding_summary())
    assert result["accepted"] is True
    assert result["classification"] == "phase1_forwarding_echo_positive"
    assert result["claim_strength"] == "aws_s2n_forwarding_echo_only"
    assert "NAT-rebinding" in result["do_not_claim"]


def test_rebinding_positive_requires_proxy_and_chunked_client() -> None:
    result = classify_summary(rebinding_summary())
    assert result["accepted"] is True
    assert result["classification"] == "phase2_nat_rebinding_proxy_positive"
    gates = {row["name"]: row["ok"] for row in result["gates"]}
    assert gates["proxy_has_a_and_b_server_packets"] is True
    assert gates["chunked_client_after_switch"] is True


def test_rebinding_without_b_side_packets_is_not_positive() -> None:
    summary = rebinding_summary()
    summary["rebinding_proxy"] = dict(summary["rebinding_proxy"])  # type: ignore[arg-type]
    summary["rebinding_proxy"]["server_packets_b"] = 0  # type: ignore[index]
    result = classify_summary(summary)
    assert result["accepted"] is False
    assert result["classification"] == "phase2_nat_rebinding_proxy_not_positive"
    assert "proxy_has_a_and_b_server_packets" in result["missing_gates"]


def test_rebinding_without_chunk_delay_is_not_positive() -> None:
    summary = rebinding_summary()
    summary["client_chunk_delay_ms"] = 0
    result = classify_summary(summary)
    assert result["accepted"] is False
    assert "chunked_client_after_switch" in result["missing_gates"]


def test_contract_documents_boundaries() -> None:
    doc = contract()
    markdown = emit_markdown(doc)
    assert "phase2_required_gates" in doc
    assert "not public s2n active migration API support" in markdown


if __name__ == "__main__":
    test_forwarding_echo_is_only_phase1_positive()
    test_rebinding_positive_requires_proxy_and_chunked_client()
    test_rebinding_without_b_side_packets_is_not_positive()
    test_rebinding_without_chunk_delay_is_not_positive()
    test_contract_documents_boundaries()
    print("classify_aws_s2n_phase2_artifact=ok")
