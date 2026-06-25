#!/usr/bin/env python3
"""Build a public-safe execution packet for the P0 controlled-public baseline."""

from __future__ import annotations

import argparse
import csv
import io
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from build_final_handover_trial_packet import build_packet
from build_p0_unblock_status import build_status as build_p0_status
from check_next_final_handover_trial_readiness import DEFAULT_CHROME, DEFAULT_CONFIG, DEFAULT_SAFARI, DEFAULT_SAFARI_TP
from research_clock import utc_date_iso
from select_next_final_handover_trial import DEFAULT_EXPERIMENTS
from plan_final_browser_handover_runs import DEFAULT_REQUIRED_TRIALS


DEFAULT_MATRIX = "data/final-protocol-readiness-matrix-20260624.csv"
DEFAULT_SCORECARD = "data/final-trial-acceptance-scorecard-20260624.csv"
DEFAULT_OUTPUT = "docs/results/p0-baseline-execution-packet-20260624.md"
DEFAULT_CSV_OUTPUT = "data/p0-baseline-execution-packet-20260624.csv"


CSV_FIELDS = [
    "stage",
    "order",
    "status",
    "owner",
    "action",
    "command",
    "stop_condition",
]


@dataclass(frozen=True)
class StageRow:
    stage: str
    order: int
    status: str
    owner: str
    action: str
    command: str
    stop_condition: str


def packet_args(args: argparse.Namespace) -> argparse.Namespace:
    return argparse.Namespace(
        experiments=args.experiments,
        requirements=args.requirements,
        config=args.config,
        use_local_config=False,
        repetitions=args.repetitions,
        prefer_p1=args.prefer_p1,
        chrome_bin=args.chrome_bin,
        safari_bin=args.safari_bin,
        safari_tp_bin=args.safari_tp_bin,
        min_disk_gib=args.min_disk_gib,
        check_local_files=False,
        check_public_origin=False,
        timeout=args.timeout,
    )


def build_stage_rows(packet: dict[str, object], p0_status: dict[str, object]) -> list[StageRow]:
    rows: list[StageRow] = []
    p0_rows = list(p0_status["rows"])  # type: ignore[arg-type]
    needed_now = [row for row in p0_rows if row["status"] == "needed-now"]
    next_ready = bool(packet["next_trial_ready"])

    rows.append(
        StageRow(
            stage="0-private-config",
            order=1,
            status="blocked" if needed_now else "ready",
            owner="operator",
            action="Create and fill the ignored controlled-public origin config.",
            command=(
                "bash harness/scripts/init-controlled-public-config.sh && "
                "$EDITOR harness/config/controlled-public-origin.env"
            ),
            stop_condition="stop until needed-now gates are cleared",
        )
    )
    rows.append(
        StageRow(
            stage="1-preflight",
            order=2,
            status="blocked" if not next_ready else "ready",
            owner="operator",
            action="Run the final P0 baseline preflight wrapper before starting server/client artifacts.",
            command="bash harness/scripts/final-p0-baseline-preflight.sh",
            stop_condition="stop if any required gate remains missing",
        )
    )

    next_trial = packet["next_trial"]  # type: ignore[assignment]
    if next_trial:
        trial = next_trial  # type: ignore[assignment]
        artifact_dir = f"repro/quic-go-min-repro/{trial['artifact_dir']}"
        rows.append(
            StageRow(
                stage="2-origin-server",
                order=3,
                status="blocked" if not next_ready else "ready",
                owner="origin-host",
                action="Start the controlled public H3 origin server for the selected baseline trial.",
                command=str(packet["server_command"]),
                stop_condition="stop if baseline preflight is not ready",
            )
        )
        rows.append(
            StageRow(
                stage="3-browser-client",
                order=4,
                status="blocked" if not next_ready else "ready",
                owner="client-host",
                action="Run the final P0 Chrome baseline wrapper and collect/validate browser artifacts.",
                command="bash harness/scripts/final-p0-baseline-run.sh",
                stop_condition="stop if server/origin terminal is not running or wrapper postchecks fail",
            )
        )
        rows.append(
            StageRow(
                stage="4-post-trial-registration",
                order=5,
                status="blocked" if not next_ready else "pending-after-run",
                owner="operator",
                action="Validate artifacts, append the final handover row, and regenerate final-trial audit outputs.",
                command=(
                    f"TRIAL_ID={trial['trial_id']} ARTIFACT_DIR={artifact_dir} APPLY=1 "
                    "bash harness/scripts/final-handover-register-trial.sh"
                ),
                stop_condition="stop if raw artifact bundle or final-countable validation fails",
            )
        )
    return rows


def local_readiness_from_packet(args: argparse.Namespace, packet: dict[str, object]) -> dict[str, object]:
    return {
        "ready": bool(packet.get("next_trial_ready")),
        "config_path": args.config,
        "config_exists": Path(args.config).exists(),
        "next_trial": packet.get("next_trial") or {},
        "required_gates": list(packet.get("required_gates") or []),  # type: ignore[arg-type]
        "missing_required_gates": list(packet.get("missing_required_gates") or []),  # type: ignore[arg-type]
    }


def build_execution_packet(args: argparse.Namespace) -> dict[str, object]:
    packet = build_packet(packet_args(args))
    p0_status = build_p0_status(
        Path(args.matrix),
        Path(args.scorecard),
        local_readiness=local_readiness_from_packet(args, packet),
    )
    rows = build_stage_rows(packet, p0_status)
    needed_now = [row for row in p0_status["rows"] if row["status"] == "needed-now"]  # type: ignore[index]
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "next_trial": packet["next_trial"] or {},
        "next_trial_ready": packet["next_trial_ready"],
        "packet_state": packet["state"],
        "needed_now_gates": [row["unblock_item"] for row in needed_now],
        "stage_rows": [asdict(row) for row in rows],
    }


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(value.replace("|", "\\|").replace("\n", "<br>") for value in row) + " |")
    return "\n".join(lines)


def emit_markdown(execution: dict[str, object]) -> str:
    next_trial = execution["next_trial"]  # type: ignore[assignment]
    needed = execution["needed_now_gates"] or ["-"]  # type: ignore[operator]
    rows = list(execution["stage_rows"])  # type: ignore[arg-type]
    detail_rows = [
        [
            row["stage"],
            str(row["order"]),
            f"`{row['status']}`",
            row["owner"],
            row["action"],
            f"`{row['command']}`",
            row["stop_condition"],
        ]
        for row in rows
    ]
    sections = [
        "# P0 Baseline Execution Packet",
        "",
        f"Generated: `{execution['generated']}`",
        "",
        "This packet is public-safe. It orders the next controlled-public Chrome baseline from private config setup through artifact validation without printing private domains, TLS paths, or network-change commands.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| next trial | `{next_trial.get('trial_id', '-')}` |",
        f"| next phase | `{next_trial.get('phase', '-')}` |",
        f"| next trial ready | `{'yes' if execution['next_trial_ready'] else 'no'}` |",
        f"| packet state | `{execution['packet_state']}` |",
        f"| needed-now gates | `{'; '.join(needed)}` |",
        "",
        "## Ordered Stages",
        "",
        markdown_table(
            ["stage", "order", "status", "owner", "action", "command", "stop condition"],
            detail_rows,
        ),
        "",
        "## Interpretation",
        "",
        "- Run stage 0 and stage 1 first; do not start server/client artifact capture while needed-now gates remain.",
        "- The origin-server command remains a public-template command; the client wrapper reads the private config locally.",
        "- After a PASS baseline is registered, regenerate P0 status; the next blocker should move from baseline config to active path-change readiness.",
    ]
    return "\n".join(sections).rstrip() + "\n"


def csv_text(execution: dict[str, object]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_FIELDS, lineterminator="\n")
    writer.writeheader()
    writer.writerows(execution["stage_rows"])  # type: ignore[arg-type]
    return buffer.getvalue()


def write_csv(execution: dict[str, object], path_arg: Path | str) -> None:
    if str(path_arg) == "-":
        sys.stdout.write(csv_text(execution))
        return
    path = Path(path_arg)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(csv_text(execution), encoding="utf-8")


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
    parser.add_argument("--matrix", default=DEFAULT_MATRIX)
    parser.add_argument("--scorecard", default=DEFAULT_SCORECARD)
    parser.add_argument("--experiments", default=DEFAULT_EXPERIMENTS)
    parser.add_argument("--requirements", default=DEFAULT_REQUIRED_TRIALS)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--prefer-p1", choices=["safari", "android", "both"], default="safari")
    parser.add_argument("--chrome-bin", default=DEFAULT_CHROME)
    parser.add_argument("--safari-bin", default=DEFAULT_SAFARI)
    parser.add_argument("--safari-tp-bin", default=DEFAULT_SAFARI_TP)
    parser.add_argument("--min-disk-gib", type=float, default=7.0)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    args = parser.parse_args()

    execution = build_execution_packet(args)
    write_csv(execution, args.csv_output)
    write_output(emit_markdown(execution), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
