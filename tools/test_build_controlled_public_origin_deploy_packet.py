#!/usr/bin/env python3
"""Regression tests for controlled public origin deploy packets."""

from __future__ import annotations

import argparse
import contextlib
import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from build_controlled_public_origin_deploy_packet import build_packet, emit_markdown, write_output


def fake_args(**overrides):
    values = {
        "package_script": "harness/scripts/package-quic-go-ec2.sh",
        "package_path": "",
        "build_package": False,
        "package_timeout": 60,
        "ssh_user": "ec2-user",
        "origin_host_placeholder": "<origin-host-or-ip>",
        "remote_dir": "/home/ec2-user/quic-go-min-repro",
        "run_id": "controlled-public-chrome-h3-baseline-001",
        "expected_requests": 4,
    }
    values.update(overrides)
    return argparse.Namespace(**values)


def test_default_packet_is_public_safe() -> None:
    packet = build_packet(fake_args())
    markdown = emit_markdown(packet)
    assert packet.public_safe is True
    assert "controlled-public-chrome-h3-baseline-001" in markdown
    assert "<public-origin-host>" in markdown
    assert "<webpki-private-key-path>" in markdown
    assert "AWS_SECRET" not in markdown
    assert "AKIA" not in markdown
    assert "PRIVATE KEY" not in markdown


def test_custom_package_path_is_used_without_building() -> None:
    packet = build_packet(fake_args(package_path="harness/results/packages/example.tar.gz"))
    markdown = emit_markdown(packet)
    assert packet.package_built is False
    assert "harness/results/packages/example.tar.gz" in markdown
    assert "package built now | `no`" in markdown


def test_dash_output_prints_stdout_without_dash_file() -> None:
    original_cwd = Path.cwd()
    with TemporaryDirectory() as tmp:
        try:
            os.chdir(tmp)
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                write_output("deploy-packet\n", "-")
            assert buffer.getvalue() == "deploy-packet\n"
            assert not Path("-").exists()
        finally:
            os.chdir(original_cwd)


def main() -> int:
    test_default_packet_is_public_safe()
    test_custom_package_path_is_used_without_building()
    test_dash_output_prints_stdout_without_dash_file()
    print("build_controlled_public_origin_deploy_packet=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
