#!/usr/bin/env python3
"""Regression tests for the Firefox desktop runtime trial packet."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from build_firefox_desktop_runtime_trial_packet import (
    LocalTool,
    build_packet,
    emit_markdown,
    write_outputs,
)


FORBIDDEN_PUBLIC_TEXT = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AK" + "IA",
    "AS" + "IA",
    "arn:aws:" + "iam::",
]


def write_desktop_path(path: Path, ready: bool) -> None:
    path.write_text(
        json.dumps(
            {
                "noniphone_desktop_path_ready": ready,
                "ready_candidates": ["macos_wifi_power_cutover"] if ready else [],
            }
        )
        + "\n",
        encoding="utf-8",
    )


def fake_tool(name: str, command: str, version_args: list[str]) -> LocalTool:
    versions = {
        "Firefox": "Mozilla Firefox 127.0",
        "geckodriver": "geckodriver 0.34.0",
        "tcpdump": "tcpdump version 4.99.0",
        "route": "route ok",
    }
    return LocalTool(
        name=name,
        command=command,
        found=True,
        executable=True,
        version=versions.get(name, ""),
        path=f"/mock/{name.lower()}",
    )


def missing_tool(name: str, command: str, version_args: list[str]) -> LocalTool:
    return LocalTool(name=name, command=command, found=False, executable=False, version="", path="")


def test_packet_blocks_when_firefox_and_path_are_missing() -> None:
    with tempfile.TemporaryDirectory() as raw:
        desktop = Path(raw) / "desktop.json"
        write_desktop_path(desktop, ready=False)
        with patch("build_firefox_desktop_runtime_trial_packet.tool_from_path", side_effect=missing_tool):
            packet = build_packet(desktop)
    assert packet["public_safe"] is True
    assert packet["gates"]["firefox_binary_ready"] is False
    assert packet["gates"]["geckodriver_ready"] is False
    assert packet["gates"]["noniphone_desktop_path_ready"] is False
    assert packet["gates"]["firefox_runtime_rows_executed"] is False
    assert "Firefox binary is not installed" in " ".join(packet["blockers"])
    assert "no active non-iPhone desktop path-change gate" in " ".join(packet["blockers"])
    assert packet["unsafe_claim"].startswith("Neqo transport tests")


def test_ready_fixture_keeps_runtime_rows_unexecuted_until_artifacts_exist() -> None:
    with tempfile.TemporaryDirectory() as raw:
        desktop = Path(raw) / "desktop.json"
        write_desktop_path(desktop, ready=True)
        with patch("build_firefox_desktop_runtime_trial_packet.tool_from_path", side_effect=fake_tool):
            packet = build_packet(desktop)
    assert packet["gates"]["firefox_binary_ready"] is True
    assert packet["gates"]["geckodriver_ready"] is True
    assert packet["gates"]["packet_capture_ready"] is True
    assert packet["gates"]["noniphone_desktop_path_ready"] is True
    assert packet["gates"]["firefox_runtime_rows_executed"] is False
    assert len(packet["trials"]) == 4
    assert packet["trials"][0]["phase"] == "local-baseline"
    assert packet["trials"][2]["phase"] == "active-network-change"


def test_markdown_is_public_safe_and_has_claim_boundaries() -> None:
    with tempfile.TemporaryDirectory() as raw:
        desktop = Path(raw) / "desktop.json"
        write_desktop_path(desktop, ready=False)
        with patch("build_firefox_desktop_runtime_trial_packet.tool_from_path", side_effect=missing_tool):
            markdown = emit_markdown(build_packet(desktop))
    for forbidden in FORBIDDEN_PUBLIC_TEXT:
        assert forbidden not in markdown
    assert "Firefox Desktop Runtime Trial Packet" in markdown
    assert "Firefox runtime rows executed" in markdown
    assert "Safe claim" in markdown
    assert "Unsafe claim" in markdown
    assert "Chrome-equivalent NetLog proof" in markdown
    assert "user_pref" in markdown


def test_outputs_are_valid_json_and_markdown() -> None:
    with tempfile.TemporaryDirectory() as raw:
        desktop = Path(raw) / "desktop.json"
        write_desktop_path(desktop, ready=False)
        out = Path(raw) / "packet.md"
        jout = Path(raw) / "packet.json"
        with patch("build_firefox_desktop_runtime_trial_packet.tool_from_path", side_effect=missing_tool):
            packet = build_packet(desktop)
        write_outputs(out, jout, packet)
        assert out.read_text(encoding="utf-8").startswith("# Firefox Desktop Runtime Trial Packet")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["scope"] == "firefox_desktop_runtime_trial_packet"


def main() -> int:
    test_packet_blocks_when_firefox_and_path_are_missing()
    test_ready_fixture_keeps_runtime_rows_unexecuted_until_artifacts_exist()
    test_markdown_is_public_safe_and_has_claim_boundaries()
    test_outputs_are_valid_json_and_markdown()
    print("build_firefox_desktop_runtime_trial_packet=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
