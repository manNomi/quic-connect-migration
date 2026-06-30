#!/usr/bin/env python3
"""Regression tests for non-iPhone public workload trial packet."""

from __future__ import annotations

import csv
import tempfile
from pathlib import Path

from build_noniphone_public_workload_trial_packet import build_packet, emit_markdown


FIELDS = [
    "workload_group",
    "completion_rate",
    "chrome_sessions",
    "single_session_rows",
    "multi_session_rows",
    "path_validation_rows",
    "qoe_signal",
]


def write_synthesis(path: Path) -> None:
    rows = [
        {
            "workload_group": "large byte-range download",
            "completion_rate": "2/2",
            "chrome_sessions": "1-1",
            "single_session_rows": "2",
            "multi_session_rows": "0",
            "path_validation_rows": "2",
            "qoe_signal": "elapsed median 3000ms",
        },
        {
            "workload_group": "large upload",
            "completion_rate": "1/1",
            "chrome_sessions": "1-1",
            "single_session_rows": "1",
            "multi_session_rows": "0",
            "path_validation_rows": "1",
            "qoe_signal": "upload bytes 131072-131072",
        },
        {
            "workload_group": "buffered video playback",
            "completion_rate": "14/14",
            "chrome_sessions": "2-3",
            "single_session_rows": "0",
            "multi_session_rows": "14",
            "path_validation_rows": "13",
            "qoe_signal": "rebuffer 1-14",
        },
        {
            "workload_group": "music-like segment",
            "completion_rate": "4/8",
            "chrome_sessions": "2-3",
            "single_session_rows": "0",
            "multi_session_rows": "8",
            "path_validation_rows": "0",
            "qoe_signal": "elapsed median 14000ms",
        },
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def test_packet_prioritizes_crisp_workloads_before_streaming() -> None:
    with tempfile.TemporaryDirectory() as raw:
        synthesis = Path(raw) / "synthesis.csv"
        write_synthesis(synthesis)
        packet = build_packet(synthesis)
        trials = packet["trials"]
        assert trials[1]["workload"] == "large byte-range download"
        assert trials[2]["phase"] == "active-network-change"
        assert trials[3]["workload"] == "large upload"
        assert trials[5]["workload"] == "buffered video playback"
        assert packet["active_trial_repetitions"] == 18
        assert "Chrome target QUIC session count is one" in packet["strong_cm_acceptance"]
        text = emit_markdown(packet)
        assert "excludes iPhone-based triggers" in text
        assert "run-controlled-public-h3-network-change.sh" in text
        assert "Number(document.body.dataset.rangeCompletedChunks" in text
        assert "single 2; multi 0" in text
        assert "network-change-00001" not in text
        assert "network-change-001" in text


def main() -> int:
    test_packet_prioritizes_crisp_workloads_before_streaming()
    print("build_noniphone_public_workload_trial_packet=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
