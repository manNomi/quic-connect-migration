#!/usr/bin/env python3
"""Build synthetic controls for the P0 baseline preflight guard."""

from __future__ import annotations

import argparse
import csv
import io
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent

from check_p0_baseline_preflight import build_preflight
from research_clock import utc_date_iso


DEFAULT_OUTPUT = "docs/results/p0-baseline-preflight-control-report-20260624.md"
DEFAULT_CSV_OUTPUT = "data/p0-baseline-preflight-control-report-20260624.csv"

CSV_FIELDS = [
    "scenario",
    "expected_go",
    "actual_go",
    "ok",
    "allowed_next_action",
    "packet_state",
    "needed_now_gates",
    "missing_required_gates",
    "failed_checks",
    "interpretation",
]


@dataclass(frozen=True)
class ControlRow:
    scenario: str
    expected_go: bool
    actual_go: bool
    ok: bool
    allowed_next_action: str
    packet_state: str
    needed_now_gates: str
    missing_required_gates: str
    failed_checks: str
    interpretation: str


def write_fixture(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dedent(text).lstrip(), encoding="utf-8")


def write_common_fixtures(root: Path, config_exists: bool) -> dict[str, Path]:
    paths = {
        "experiments": root / "experiments.csv",
        "requirements": root / "requirements.csv",
        "scorecard": root / "scorecard.csv",
        "config": root / "controlled-public-origin.env",
    }
    write_fixture(
        paths["experiments"],
        """
        trial_id,implementation,deployment_tier,protocol,migration_trigger,application_task,status,failure_layer,notes
        unrelated-local-control,quic-go,local,QUIC,none,echo,PASS,,local control
        """,
    )
    write_fixture(
        paths["requirements"],
        """
        requirement_id,phase,browser,description,min_count,accepted_statuses,trial_id_contains_all,deployment_contains_all,trigger_contains_all,task_contains_all,notes_contains_all,notes_contains_any,notes_excludes_any
        chrome-controlled-public-application-h3-baseline,baseline,Chrome,baseline,1,PASS,controlled-public;baseline,controlled public,,browser,,controlled_public_application_h3_confirmed,
        """,
    )
    write_fixture(
        paths["scorecard"],
        """
        requirement_id,complete
        chrome-controlled-public-application-h3-baseline,False
        """,
    )
    if config_exists:
        write_fixture(
            paths["config"],
            f"""
            PUBLIC_ORIGIN_HOST=synthetic-h3.test
            PUBLIC_ORIGIN_PORT=443
            PUBLIC_ORIGIN_URL=https://synthetic-h3.test/browser-slow
            TLS_CERT_FILE=/tmp/synthetic/fullchain.pem
            TLS_KEY_FILE=/tmp/synthetic/privkey.pem
            LISTEN_ADDR=0.0.0.0:443
            TCP_ADDR=0.0.0.0:443
            ALT_SVC='h3=":443"; ma=60'
            CHROME_BIN={sys.executable}
            """,
        )
    return paths


def write_matrix(path: Path, ready: bool, missing_gates: list[str]) -> None:
    state = "ready" if ready else "blocked"
    required_gates = [
        "controlled_public_config_present",
        "public_origin_host_configured",
        "public_origin_url_configured",
        "tls_config_present",
        "disk_ready",
        "chrome_ready",
    ]
    write_fixture(
        path,
        f"""
        order,trial_id,requirement_id,phase,browser,heartbeat,ready,state,required_gates,missing_gates
        1,controlled-public-chrome-h3-baseline-001,chrome-controlled-public-application-h3-baseline,baseline,Chrome,n/a,{ready},{state},{";".join(required_gates)},{";".join(missing_gates)}
        """,
    )


def make_args(paths: dict[str, Path], matrix: Path) -> argparse.Namespace:
    return argparse.Namespace(
        matrix=matrix.as_posix(),
        scorecard=paths["scorecard"].as_posix(),
        experiments=paths["experiments"].as_posix(),
        requirements=paths["requirements"].as_posix(),
        config=paths["config"].as_posix(),
        repetitions=3,
        prefer_p1="safari",
        chrome_bin=sys.executable,
        safari_bin="/Applications/Safari.app/Contents/MacOS/Safari",
        safari_tp_bin="/Applications/Safari Technology Preview.app/Contents/MacOS/Safari Technology Preview",
        min_disk_gib=1.0,
        check_local_files=False,
        check_public_origin=False,
        timeout=1.0,
    )


def evaluate_scenario(
    root: Path,
    scenario: str,
    *,
    config_exists: bool,
    matrix_ready: bool,
    matrix_missing: list[str],
    expected_go: bool,
    interpretation: str,
) -> ControlRow:
    scenario_root = root / scenario
    paths = write_common_fixtures(scenario_root, config_exists)
    matrix = scenario_root / "matrix.csv"
    write_matrix(matrix, matrix_ready, matrix_missing)
    preflight = build_preflight(make_args(paths, matrix))
    failed = [row["check"] for row in preflight["checks"] if row["required"] and not row["ok"]]
    actual_go = bool(preflight["go_for_p0_baseline_capture"])
    return ControlRow(
        scenario=scenario,
        expected_go=expected_go,
        actual_go=actual_go,
        ok=actual_go is expected_go,
        allowed_next_action=preflight["allowed_next_action"],
        packet_state=str(preflight["packet_state"]),
        needed_now_gates=";".join(preflight["needed_now_gates"]) or "-",
        missing_required_gates=";".join(preflight["missing_required_gates"]) or "-",
        failed_checks=";".join(failed) or "-",
        interpretation=interpretation,
    )


def build_report() -> dict[str, object]:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        rows = [
            evaluate_scenario(
                root,
                "missing_config_blocks_capture",
                config_exists=False,
                matrix_ready=False,
                matrix_missing=[
                    "controlled_public_config_present",
                    "public_origin_host_configured",
                    "public_origin_url_configured",
                    "tls_config_present",
                ],
                expected_go=False,
                interpretation="Fail closed when the private controlled-public baseline config is absent.",
            ),
            evaluate_scenario(
                root,
                "synthetic_ready_allows_baseline_capture",
                config_exists=True,
                matrix_ready=True,
                matrix_missing=[],
                expected_go=True,
                interpretation="Open only for a syntactically ready P0 baseline fixture; this does not prove public browser CM.",
            ),
            evaluate_scenario(
                root,
                "stale_needed_now_gate_blocks_capture",
                config_exists=True,
                matrix_ready=False,
                matrix_missing=["controlled_public_config_present"],
                expected_go=False,
                interpretation="Fail closed if the P0 status still reports a needed-now gate, even when packet readiness is otherwise satisfied.",
            ),
        ]
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "scenario_count": len(rows),
        "all_controls_passed": all(row.ok for row in rows),
        "rows": [asdict(row) for row in rows],
    }


def bool_text(value: bool) -> str:
    return "yes" if value else "no"


def emit_markdown(report: dict[str, object]) -> str:
    rows = list(report["rows"])  # type: ignore[arg-type]
    lines = [
        "# P0 Baseline Preflight Control Report",
        "",
        f"Generated: `{report['generated']}`",
        "",
        "This public-safe control report uses synthetic fixtures to check that the P0 preflight guard opens and closes only under the intended readiness states.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| scenarios | `{report['scenario_count']}` |",
        f"| all controls passed | `{bool_text(bool(report['all_controls_passed']))}` |",
        f"| public safe | `{bool_text(bool(report['public_safe']))}` |",
        "",
        "## Controls",
        "",
        "| scenario | expected go | actual go | ok | action | failed checks | interpretation |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['scenario']}`",
                    f"`{bool_text(bool(row['expected_go']))}`",
                    f"`{bool_text(bool(row['actual_go']))}`",
                    f"`{bool_text(bool(row['ok']))}`",
                    f"`{row['allowed_next_action']}`",
                    f"`{row['failed_checks']}`",
                    row["interpretation"],
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- These controls validate the guard logic, not real public-origin reachability.",
            "- A synthetic `actual go=yes` only means the preflight state machine can open when all modeled gates are satisfied.",
            "- Real paper claims still require the controlled-public Chrome baseline artifacts and later active path-change trials.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def csv_text(report: dict[str, object]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(report["rows"])  # type: ignore[arg-type]
    return buffer.getvalue()


def write_csv(report: dict[str, object], path_arg: Path | str) -> None:
    if str(path_arg) == "-":
        sys.stdout.write(csv_text(report))
        return
    path = Path(path_arg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(csv_text(report), encoding="utf-8")


def write_output(text: str, output_arg: str | None) -> None:
    if output_arg == "-":
        sys.stdout.write(text)
        return
    if not output_arg:
        sys.stdout.write(text)
        return
    output = Path(output_arg)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    args = parser.parse_args()

    report = build_report()
    write_csv(report, args.csv_output)
    write_output(emit_markdown(report), args.output)
    return 0 if report["all_controls_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
