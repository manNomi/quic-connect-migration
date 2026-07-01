#!/usr/bin/env python3
"""Build a public-safe mvfst migration test readiness report."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_OUTPUT = "docs/results/mvfst-migration-test-readiness-20260630.md"
DEFAULT_JSON_OUTPUT = "data/mvfst-migration-test-readiness-20260630.json"
DEFAULT_MVFST_DIR = "/private/tmp/quic-cm-scan-repos/mvfst"

FOCUSED_TEST_FILES = [
    {
        "kind": "path-manager",
        "file": "quic/state/test/QuicPathManagerTest.cpp",
        "buck_dir": "quic/state/test",
    },
    {
        "kind": "client-active-migration",
        "file": "quic/client/test/QuicClientTransportLiteMigrationTest.cpp",
        "buck_dir": "quic/client/test",
    },
    {
        "kind": "server-passive-migration",
        "file": "quic/server/test/QuicServerTransportMigrationTest.cpp",
        "buck_dir": "quic/server/test",
    },
]

HIGH_VALUE_TERMS = (
    "Challenge",
    "Response",
    "Timeout",
    "Switch",
    "Probe",
    "Migrate",
    "Migration",
    "NATRebinding",
    "AddressChange",
    "PortChange",
    "Validation",
    "ConnectionId",
    "Cid",
)


@dataclass(frozen=True)
class TestCase:
    macro: str
    fixture: str
    name: str
    line: int

    @property
    def full_name(self) -> str:
        return f"{self.fixture}.{self.name}"


def run(args: list[str], cwd: Path | None = None, timeout: int = 10) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def git_commit(root: Path) -> str:
    result = run(["git", "rev-parse", "HEAD"], cwd=root)
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else "unknown"


def git_remote_head(root: Path) -> str:
    result = run(["git", "ls-remote", "origin", "HEAD"], cwd=root, timeout=20)
    if result.returncode != 0 or not result.stdout.strip():
        return "unknown"
    return result.stdout.split()[0]


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def free_gib(path: Path) -> float:
    target = path if path.exists() else Path(".")
    usage = shutil.disk_usage(target)
    return round(usage.free / (1024**3), 2)


def parse_test_cases(path: Path) -> list[TestCase]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    pattern = re.compile(r"\b(TEST(?:_[FP])?)\s*\(\s*([A-Za-z0-9_:]+)\s*,\s*([A-Za-z0-9_]+)")
    cases = []
    for match in pattern.finditer(text):
        line = text[: match.start()].count("\n") + 1
        cases.append(
            TestCase(
                macro=match.group(1),
                fixture=match.group(2),
                name=match.group(3),
                line=line,
            )
        )
    return cases


def buck_target_for(root: Path, rel_file: str, buck_dir: str) -> str:
    buck = root / buck_dir / "BUCK"
    if not buck.exists():
        return "-"
    lines = buck.read_text(encoding="utf-8", errors="ignore").splitlines()
    source_name = Path(rel_file).name
    source_index = next((idx for idx, line in enumerate(lines) if source_name in line), None)
    if source_index is None:
        return "-"
    for idx in range(source_index, -1, -1):
        match = re.search(r'name\s*=\s*"([^"]+)"', lines[idx])
        if match:
            return f"{buck_dir}:{match.group(1)}"
    return "-"


def cmake_references_file(root: Path, rel_file: str) -> bool:
    test_dir = root / Path(rel_file).parent
    cmake = test_dir / "CMakeLists.txt"
    if not cmake.exists():
        return False
    return Path(rel_file).name in cmake.read_text(encoding="utf-8", errors="ignore")


def high_value_cases(cases: list[TestCase]) -> list[str]:
    selected = []
    for case in cases:
        if any(term in case.name or term in case.fixture for term in HIGH_VALUE_TERMS):
            selected.append(case.full_name)
    return selected


def build_audit(root: Path, disk_threshold_gib: float = 30.0, check_remote: bool = False) -> dict[str, Any]:
    root = root.expanduser().resolve()
    source_ready = root.exists() and (root / "quic").exists()
    getdeps = root / "build/fbcode_builder/getdeps.py"
    host_os = platform.system()
    disk_available = free_gib(root if root.exists() else Path("."))

    focused_targets = []
    all_cases: list[TestCase] = []
    for item in FOCUSED_TEST_FILES:
        rel = item["file"]
        cases = parse_test_cases(root / rel)
        all_cases.extend(cases)
        selected = high_value_cases(cases)
        focused_targets.append(
            {
                "kind": item["kind"],
                "file": rel,
                "exists": (root / rel).exists(),
                "buck_target": buck_target_for(root, rel, item["buck_dir"]),
                "cmake_direct_file_reference": cmake_references_file(root, rel),
                "test_case_count": len(cases),
                "high_value_test_count": len(selected),
                "sample_high_value_tests": selected[:12],
                "first_test_cases": [case.full_name for case in cases[:8]],
            }
        )

    buck_targets_ready = all(t["buck_target"] != "-" for t in focused_targets)
    cmake_direct_targets_ready = all(t["cmake_direct_file_reference"] for t in focused_targets)
    disk_ready = disk_available >= disk_threshold_gib
    buck2_ready = command_exists("buck2")
    getdeps_ready = getdeps.exists()
    python_ready = command_exists("python3")
    cmake_ready = command_exists("cmake")
    ninja_ready = command_exists("ninja")

    can_run_focused_buck_now = source_ready and buck_targets_ready and buck2_ready and disk_ready
    can_run_getdeps_now = source_ready and getdeps_ready and python_ready and cmake_ready and ninja_ready and disk_ready

    blockers = []
    if not source_ready:
        blockers.append("mvfst_source_missing")
    if not disk_ready:
        blockers.append("disk_below_threshold")
    if not buck2_ready:
        blockers.append("buck2_missing")
    if not getdeps_ready:
        blockers.append("getdeps_missing")
    if not cmake_ready:
        blockers.append("cmake_missing")
    if not ninja_ready:
        blockers.append("ninja_missing")
    if not cmake_direct_targets_ready:
        blockers.append("focused_files_not_directly_exposed_by_current_cmake")

    commands = {
        "buck_focused_tests": [
            f"buck2 test {target['buck_target']}"
            for target in focused_targets
            if target["buck_target"] != "-"
        ],
        "getdeps_broad_build": [
            "python3 build/fbcode_builder/getdeps.py --allow-system-packages --num-jobs 4 build mvfst",
            "python3 build/fbcode_builder/getdeps.py --allow-system-packages --num-jobs 4 test mvfst",
        ],
        "source_audit": [
            "python3 tools/check_mvfst_migration_test_readiness.py "
            "--output docs/results/mvfst-migration-test-readiness-20260630.md "
            "--json-output data/mvfst-migration-test-readiness-20260630.json",
        ],
    }

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "source_root_hint": "external checkout; set MVFST_DIR to override",
        "source_commit": git_commit(root) if source_ready else "missing",
        "remote_head": git_remote_head(root) if source_ready and check_remote else "not-checked",
        "host": {
            "os": host_os,
            "linux_recommended": host_os == "Linux",
            "disk_free_gib": disk_available,
            "disk_threshold_gib": disk_threshold_gib,
        },
        "readiness": {
            "source_ready": source_ready,
            "getdeps_ready": getdeps_ready,
            "python3_ready": python_ready,
            "cmake_ready": cmake_ready,
            "ninja_ready": ninja_ready,
            "buck2_ready": buck2_ready,
            "disk_ready": disk_ready,
            "buck_targets_ready": buck_targets_ready,
            "cmake_direct_targets_ready": cmake_direct_targets_ready,
            "can_run_focused_buck_now": can_run_focused_buck_now,
            "can_run_getdeps_now": can_run_getdeps_now,
            "validation": "ready" if can_run_focused_buck_now or can_run_getdeps_now else "blocked",
            "blocked_reasons": blockers,
        },
        "focused_targets": focused_targets,
        "total_test_cases_observed": len(all_cases),
        "total_high_value_test_cases_observed": sum(t["high_value_test_count"] for t in focused_targets),
        "generated_commands": commands,
        "supports": (
            "mvfst has focused migration/path-manager test files and BUCK targets for path-manager, "
            "client active migration, and server passive migration coverage."
        ),
        "do_not_claim": (
            "Do not claim local mvfst build/test success from this readiness report; it only fixes "
            "the focused target map and current blockers."
        ),
    }


def emit_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# mvfst Migration Test Readiness",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This document is public-safe. It records source-relative test targets and current readiness, not raw build logs.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| source commit | `{audit['source_commit']}` |",
        f"| remote head | `{audit['remote_head']}` |",
        f"| host os | `{audit['host']['os']}` |",
        f"| disk free GiB | `{audit['host']['disk_free_gib']}` |",
        f"| disk threshold GiB | `{audit['host']['disk_threshold_gib']}` |",
        f"| validation | `{audit['readiness']['validation']}` |",
        f"| blocked reasons | `{audit['readiness']['blocked_reasons']}` |",
        f"| total test cases observed | `{audit['total_test_cases_observed']}` |",
        f"| high-value migration/path cases observed | `{audit['total_high_value_test_cases_observed']}` |",
        "",
        "## Readiness",
        "",
        "| check | value |",
        "| --- | --- |",
    ]
    for key, value in audit["readiness"].items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(
        [
            "",
            "## Focused Targets",
            "",
            "| kind | source file | BUCK target | CMake direct file ref | tests | high-value tests |",
            "| --- | --- | --- | --- | ---: | ---: |",
        ]
    )
    for target in audit["focused_targets"]:
        lines.append(
            "| {kind} | `{file}` | `{buck}` | `{cmake}` | `{tests}` | `{high}` |".format(
                kind=target["kind"],
                file=target["file"],
                buck=target["buck_target"],
                cmake=target["cmake_direct_file_reference"],
                tests=target["test_case_count"],
                high=target["high_value_test_count"],
            )
        )

    lines.extend(["", "## Sample High-Value Tests", ""])
    for target in audit["focused_targets"]:
        lines.append(f"### {target['kind']}")
        if not target["sample_high_value_tests"]:
            lines.append("- none observed")
        else:
            for name in target["sample_high_value_tests"]:
                lines.append(f"- `{name}`")
        lines.append("")

    lines.extend(
        [
            "## Generated Commands",
            "",
            "Focused BUCK targets if a suitable Buck/buck2 environment is available:",
            "",
            "```bash",
        ]
    )
    lines.extend(audit["generated_commands"]["buck_focused_tests"] or ["# no BUCK targets discovered"])
    lines.extend(
        [
            "```",
            "",
            "Broad getdeps build/test fallback. This is not focused and may be expensive:",
            "",
            "```bash",
        ]
    )
    lines.extend(audit["generated_commands"]["getdeps_broad_build"])
    lines.extend(
        [
            "```",
            "",
            "## Interpretation",
            "",
            f"- Supports: {audit['supports']}",
            f"- Do not claim: {audit['do_not_claim']}",
            "- Paper use: keep mvfst as production-relevant source/test maturity evidence until a Linux/Buck/getdeps run produces executed test results.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(output: Path, json_output: Path, audit: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(audit), encoding="utf-8")
    json_output.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mvfst-dir", type=Path, default=Path(os.environ.get("MVFST_DIR", DEFAULT_MVFST_DIR)))
    parser.add_argument("--disk-threshold-gib", type=float, default=30.0)
    parser.add_argument("--check-remote", action="store_true")
    parser.add_argument("--output", type=Path, default=Path(DEFAULT_OUTPUT))
    parser.add_argument("--json-output", type=Path, default=Path(DEFAULT_JSON_OUTPUT))
    args = parser.parse_args()

    audit = build_audit(args.mvfst_dir, disk_threshold_gib=args.disk_threshold_gib, check_remote=args.check_remote)
    write_outputs(args.output, args.json_output, audit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
