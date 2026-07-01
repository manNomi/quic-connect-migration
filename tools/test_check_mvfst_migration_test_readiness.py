#!/usr/bin/env python3
"""Regression tests for mvfst migration readiness builder."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from check_mvfst_migration_test_readiness import build_audit, emit_markdown, write_outputs


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_fixture(root: Path) -> None:
    write(root / "quic/state/test/QuicPathManagerTest.cpp", "TEST_F(QuicPathManagerTest, PrepareChallengeForSending) {}\n")
    write(
        root / "quic/client/test/QuicClientTransportLiteMigrationTest.cpp",
        "TEST_F(\n  QuicClientTransportLiteMigrationTest,\n  StartPathProbeSuccessWithMigrating) {}\n",
    )
    write(
        root / "quic/server/test/QuicServerTransportMigrationTest.cpp",
        "TEST_P(QuicServerTransportAllowMigrationTest, ClientPortChangeNATRebinding) {}\n",
    )
    write(
        root / "quic/state/test/BUCK",
        'mvfst_cpp_test(\n    name = "quic_path_manager_test",\n    srcs = ["QuicPathManagerTest.cpp"],\n)\n',
    )
    write(
        root / "quic/client/test/BUCK",
        'mvfst_cpp_test(\n    name = "QuicClientTransportLiteMigrationTest",\n    srcs = ["QuicClientTransportLiteMigrationTest.cpp"],\n)\n',
    )
    write(
        root / "quic/server/test/BUCK",
        'fb_dirsync_cpp_unittest(\n    name = "QuicServerTransportMigrationTest",\n    srcs = ["QuicServerTransportMigrationTest.cpp"],\n)\n',
    )
    write(root / "quic/state/test/CMakeLists.txt", "quic_add_test(TARGET Other SOURCES Other.cpp)\n")
    write(root / "quic/client/test/CMakeLists.txt", "quic_add_test(TARGET Other SOURCES Other.cpp)\n")
    write(root / "quic/server/test/CMakeLists.txt", "quic_add_test(TARGET Other SOURCES Other.cpp)\n")
    write(root / "build/fbcode_builder/getdeps.py", "#!/usr/bin/env python3\n")


def test_fixture_builds_focused_target_map() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "mvfst"
        make_fixture(root)
        audit = build_audit(root, disk_threshold_gib=0)
        assert audit["public_safe"] is True
        assert audit["readiness"]["source_ready"] is True
        assert audit["readiness"]["buck_targets_ready"] is True
        assert audit["readiness"]["cmake_direct_targets_ready"] is False
        assert audit["total_test_cases_observed"] == 3
        assert audit["total_high_value_test_cases_observed"] == 3
        targets = {item["kind"]: item for item in audit["focused_targets"]}
        assert targets["path-manager"]["buck_target"] == "quic/state/test:quic_path_manager_test"
        assert targets["client-active-migration"]["test_case_count"] == 1
        assert targets["server-passive-migration"]["sample_high_value_tests"]


def test_outputs_are_public_safe_json_and_markdown() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir) / "mvfst"
        make_fixture(root)
        audit = build_audit(root, disk_threshold_gib=0)
        markdown = emit_markdown(audit)
        assert "PRIVATE KEY" not in markdown
        assert "AWS_SECRET" not in markdown
        out = Path(tmpdir) / "out.md"
        jout = Path(tmpdir) / "out.json"
        write_outputs(out, jout, audit)
        assert out.read_text(encoding="utf-8").startswith("# mvfst Migration Test Readiness")
        parsed = json.loads(jout.read_text(encoding="utf-8"))
        assert parsed["total_test_cases_observed"] == 3


def main() -> int:
    test_fixture_builds_focused_target_map()
    test_outputs_are_public_safe_json_and_markdown()
    print("check_mvfst_migration_test_readiness=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
