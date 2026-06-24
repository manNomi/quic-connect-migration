#!/usr/bin/env python3
"""Generate a reproducible run plan for the final browser handover trials."""

from __future__ import annotations

import argparse
import csv
import json
import shlex
from collections import Counter
from dataclasses import asdict, dataclass
from research_clock import utc_date_iso
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = "harness/config/controlled-public-origin.env"
DEFAULT_REQUIRED_TRIALS = "data/final-browser-handover-required-trials.csv"
DEFAULT_OUTPUT = "docs/results/final-browser-handover-run-plan-20260624.md"

PUBLIC_TEMPLATE_VALUES = {
    "PUBLIC_ORIGIN_HOST": "h3.example.com",
    "PUBLIC_ORIGIN_PORT": "443",
    "PUBLIC_ORIGIN_URL": "https://h3.example.com/browser-slow?duration_ms=6000&chunks=6&label=public-slow",
    "TLS_CERT_FILE": "/etc/letsencrypt/live/h3.example.com/fullchain.pem",
    "TLS_KEY_FILE": "/etc/letsencrypt/live/h3.example.com/privkey.pem",
    "LISTEN_ADDR": "0.0.0.0:443",
    "TCP_ADDR": "0.0.0.0:443",
    "ALT_SVC": 'h3=":443"; ma=60',
    "CONTROLLED_PUBLIC_BASELINE_SUMMARY": (
        "artifacts/controlled-public-chrome-h3-baseline-001/results/"
        "controlled-public-h3-baseline-summary.json"
    ),
    "NETWORK_CHANGE_AFTER_SECONDS": "3",
    "NETWORK_CHANGE_CMD": "...",
    "ANDROID_NETWORK_CHANGE_CMD": "...",
    "CHROME_RUNNER": "cdp",
    "CHROME_HOLD_SECONDS": "18",
    "CHROME_TIMEOUT_SECONDS": "30",
    "CHROME_NET_LOG_CAPTURE_MODE": "Default",
    "REQUIRE_H3_ALT_SVC": "1",
    "REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3": "1",
}


@dataclass
class RequiredTrial:
    requirement_id: str
    phase: str
    browser: str
    description: str
    min_count: int
    accepted_statuses: str


@dataclass
class TrialPlan:
    requirement_id: str
    trial_id: str
    phase: str
    browser: str
    workload: str
    heartbeat: str
    expected_requests: int
    artifact_dir: str
    claim_gate: str
    server_command: str
    client_command: str
    registration_hint: str


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        try:
            parts = shlex.split(line, comments=True, posix=True)
        except ValueError:
            parts = [line]
        for part in parts:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            if key:
                values[key] = value
    return values


def load_required_trials(path: Path) -> list[RequiredTrial]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fp:
        rows = csv.DictReader(fp)
        return [
            RequiredTrial(
                requirement_id=row["requirement_id"],
                phase=row["phase"],
                browser=row["browser"],
                description=row["description"],
                min_count=int(row["min_count"]),
                accepted_statuses=row["accepted_statuses"],
            )
            for row in rows
        ]


def shell_quote(value: str | int) -> str:
    return shlex.quote(str(value))


def shell_command(env: list[tuple[str, str | int]], script: str) -> str:
    lines = ["cd repro/quic-go-min-repro"]
    for key, value in env:
        lines.append(f"{key}={shell_quote(value)} \\")
    lines.append(script)
    return "\n".join(lines)


def origin_base(values: dict[str, str]) -> str:
    host = values.get("PUBLIC_ORIGIN_HOST") or "h3.example.com"
    port = values.get("PUBLIC_ORIGIN_PORT") or "443"
    if port == "443":
        return f"https://{host}"
    return f"https://{host}:{port}"


def downlink_url(values: dict[str, str], heartbeat: bool, label: str) -> str:
    heartbeat_value = "true" if heartbeat else "false"
    return (
        f"{origin_base(values)}/browser-downlink?"
        f"duration_ms=15000&chunks=15&bytes=65536&heartbeat={heartbeat_value}"
        f"&heartbeat_delay_ms=5000&label={label}"
    )


def server_command(values: dict[str, str], run_id: str, expected_requests: int) -> str:
    artifact_dir = f"artifacts/{run_id}"
    env = [
        ("RUN_ID", run_id),
        ("ARTIFACT_DIR", artifact_dir),
        ("PUBLIC_ORIGIN_HOST", values["PUBLIC_ORIGIN_HOST"]),
        ("PUBLIC_ORIGIN_PORT", values["PUBLIC_ORIGIN_PORT"]),
        ("TLS_CERT_FILE", values["TLS_CERT_FILE"]),
        ("TLS_KEY_FILE", values["TLS_KEY_FILE"]),
        ("LISTEN_ADDR", values["LISTEN_ADDR"]),
        ("TCP_ADDR", values["TCP_ADDR"]),
        ("ALT_SVC", values["ALT_SVC"]),
        ("EXPECTED_REQUESTS", expected_requests),
        ("TIMEOUT", "300s"),
        ("COMPLETION_GRACE", "2s"),
    ]
    return shell_command(env, "./scripts/run-controlled-public-h3-server.sh")


def chrome_baseline_command(values: dict[str, str], run_id: str, url: str, expected_requests: int) -> str:
    artifact_dir = f"artifacts/{run_id}"
    env = [
        ("RUN_ID", run_id),
        ("ARTIFACT_DIR", artifact_dir),
        ("CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR", artifact_dir),
        ("PUBLIC_ORIGIN_URL", url),
        ("SECOND_URL", url),
        ("CONTROLLED_PUBLIC_EXPECTED_REQUESTS", expected_requests),
        ("REQUIRE_H3_ALT_SVC", values["REQUIRE_H3_ALT_SVC"]),
        ("REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3", values["REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3"]),
    ]
    return shell_command(env, "./scripts/run-controlled-public-h3-browser-baseline.sh")


def chrome_network_change_command(values: dict[str, str], run_id: str, url: str, expected_requests: int) -> str:
    artifact_dir = f"artifacts/{run_id}"
    env = [
        ("RUN_ID", run_id),
        ("ARTIFACT_DIR", artifact_dir),
        ("CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR", artifact_dir),
        ("CONTROLLED_PUBLIC_BASELINE_SUMMARY", values["CONTROLLED_PUBLIC_BASELINE_SUMMARY"]),
        ("PUBLIC_ORIGIN_URL", url),
        ("CONTROLLED_PUBLIC_EXPECTED_REQUESTS", expected_requests),
        ("REQUIRE_H3_ALT_SVC", values["REQUIRE_H3_ALT_SVC"]),
        ("REQUIRE_CONTROLLED_PUBLIC_BASELINE", "1"),
        ("CHROME_RUNNER", values["CHROME_RUNNER"]),
        ("CHROME_HOLD_SECONDS", values["CHROME_HOLD_SECONDS"]),
        ("CHROME_TIMEOUT_SECONDS", values["CHROME_TIMEOUT_SECONDS"]),
        ("CHROME_NET_LOG_CAPTURE_MODE", values["CHROME_NET_LOG_CAPTURE_MODE"]),
        ("NETWORK_CHANGE_AFTER_SECONDS", values["NETWORK_CHANGE_AFTER_SECONDS"]),
        ("NETWORK_CHANGE_CMD", values["NETWORK_CHANGE_CMD"]),
    ]
    return shell_command(env, "./scripts/run-controlled-public-h3-network-change.sh")


def safari_network_change_command(values: dict[str, str], run_id: str, url: str, expected_requests: int) -> str:
    artifact_dir = f"artifacts/{run_id}"
    env = [
        ("RUN_ID", run_id),
        ("ARTIFACT_DIR", artifact_dir),
        ("CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR", artifact_dir),
        ("CONTROLLED_PUBLIC_BASELINE_SUMMARY", values["CONTROLLED_PUBLIC_BASELINE_SUMMARY"]),
        ("PUBLIC_ORIGIN_URL", url),
        ("CONTROLLED_PUBLIC_EXPECTED_REQUESTS", expected_requests),
        ("REQUIRE_H3_ALT_SVC", values["REQUIRE_H3_ALT_SVC"]),
        ("REQUIRE_CONTROLLED_PUBLIC_BASELINE", "1"),
        ("NETWORK_CHANGE_AFTER_SECONDS", values["NETWORK_CHANGE_AFTER_SECONDS"]),
        ("NETWORK_CHANGE_CMD", values["NETWORK_CHANGE_CMD"]),
    ]
    return shell_command(env, "./scripts/run-safari-controlled-public-network-change.sh")


def android_network_change_command(values: dict[str, str], run_id: str, url: str, expected_requests: int) -> str:
    artifact_dir = f"artifacts/{run_id}"
    android_cmd = values.get("ANDROID_NETWORK_CHANGE_CMD") or values["NETWORK_CHANGE_CMD"]
    env = [
        ("RUN_ID", run_id),
        ("ARTIFACT_DIR", artifact_dir),
        ("CONTROLLED_PUBLIC_SERVER_ARTIFACT_DIR", artifact_dir),
        ("CONTROLLED_PUBLIC_BASELINE_SUMMARY", values["CONTROLLED_PUBLIC_BASELINE_SUMMARY"]),
        ("PUBLIC_ORIGIN_URL", url),
        ("CONTROLLED_PUBLIC_EXPECTED_REQUESTS", expected_requests),
        ("REQUIRE_H3_ALT_SVC", values["REQUIRE_H3_ALT_SVC"]),
        ("REQUIRE_CONTROLLED_PUBLIC_BASELINE", "1"),
        ("NETWORK_CHANGE_AFTER_SECONDS", values["NETWORK_CHANGE_AFTER_SECONDS"]),
        ("ANDROID_NETWORK_CHANGE_CMD", android_cmd),
    ]
    return shell_command(env, "./scripts/run-android-chrome-controlled-public-network-change.sh")


def make_plan(values: dict[str, str], repetitions: int, prefer_p1: str) -> list[TrialPlan]:
    plans: list[TrialPlan] = []

    baseline_id = "controlled-public-chrome-h3-baseline-001"
    baseline_url = values["PUBLIC_ORIGIN_URL"]
    plans.append(
        TrialPlan(
            requirement_id="chrome-controlled-public-application-h3-baseline",
            trial_id=baseline_id,
            phase="baseline",
            browser="Chrome",
            workload="browser-slow application H3 baseline",
            heartbeat="n/a",
            expected_requests=4,
            artifact_dir=f"artifacts/{baseline_id}",
            claim_gate="status PASS; controlled_public_application_h3_confirmed; server qlog H3 confirmed",
            server_command=server_command(values, baseline_id, 4),
            client_command=chrome_baseline_command(values, baseline_id, baseline_url, 4),
            registration_hint="Record as PASS baseline before any active path-change trial.",
        )
    )

    noheartbeat_url = downlink_url(values, heartbeat=False, label="public-downlink-noheartbeat")
    heartbeat_url = downlink_url(values, heartbeat=True, label="public-downlink-heartbeat")
    for run_id, url, heartbeat, expected in [
        ("controlled-public-chrome-downlink-noheartbeat-nochange-001", noheartbeat_url, "false", 4),
        ("controlled-public-chrome-downlink-heartbeat-nochange-001", heartbeat_url, "true", 6),
    ]:
        requirement_id = (
            "chrome-downlink-heartbeat-nochange-baseline"
            if heartbeat == "true"
            else "chrome-downlink-noheartbeat-nochange-baseline"
        )
        plans.append(
            TrialPlan(
                requirement_id=requirement_id,
                trial_id=run_id,
                phase="no-change-baseline",
                browser="Chrome",
                workload="browser-downlink no network change",
                heartbeat=heartbeat,
                expected_requests=expected,
                artifact_dir=f"artifacts/{run_id}",
                claim_gate="no active network-change command; server/browser workload completes; classification no_path_change_baseline",
                server_command=server_command(values, run_id, expected),
                client_command=chrome_baseline_command(values, run_id, url, expected),
                registration_hint=(
                    "Record migration_trigger as 'no network change' and notes with no_path_change_baseline. "
                    "If heartbeat creates extra sessions or source tuples without a path-change command, keep it as baseline evidence, not CM success."
                ),
            )
        )

    for suffix in range(1, repetitions + 1):
        run_id = f"controlled-public-chrome-downlink-noheartbeat-network-change-{suffix:03d}"
        plans.append(
            TrialPlan(
                requirement_id="chrome-downlink-noheartbeat-active-cm",
                trial_id=run_id,
                phase="active-network-change",
                browser="Chrome",
                workload="browser-downlink active path change",
                heartbeat="false",
                expected_requests=2,
                artifact_dir=f"artifacts/{run_id}",
                claim_gate=(
                    "classification possible_connection_migration; client_active_path_changed; "
                    "server tuple changed; qlog path validation true"
                ),
                server_command=server_command(values, run_id, 2),
                client_command=chrome_network_change_command(values, run_id, noheartbeat_url, 2),
                registration_hint="Reject as CM success if classifier reports reconnect_or_multiple_sessions or no_path_change_after_trigger.",
            )
        )

    for suffix in range(1, repetitions + 1):
        run_id = f"controlled-public-chrome-downlink-heartbeat-network-change-{suffix:03d}"
        plans.append(
            TrialPlan(
                requirement_id="chrome-downlink-heartbeat-active-cm",
                trial_id=run_id,
                phase="active-network-change",
                browser="Chrome",
                workload="browser-downlink active path change",
                heartbeat="true",
                expected_requests=3,
                artifact_dir=f"artifacts/{run_id}",
                claim_gate=(
                    "classification possible_connection_migration; client_active_path_changed; "
                    "server tuple changed; qlog path validation true; heartbeat response observed"
                ),
                server_command=server_command(values, run_id, 3),
                client_command=chrome_network_change_command(values, run_id, heartbeat_url, 3),
                registration_hint="Compare only against the heartbeat no-change baseline; do not treat extra sessions alone as CM.",
            )
        )

    p1_url = downlink_url(values, heartbeat=False, label="p1-downlink-noheartbeat")
    if prefer_p1 in {"safari", "both"}:
        run_id = "controlled-public-safari-downlink-network-change-001"
        plans.append(
            TrialPlan(
                requirement_id="p1-safari-or-android-feasibility",
                trial_id=run_id,
                phase="p1-feasibility",
                browser="Safari",
                workload="browser-downlink active path change",
                heartbeat="false",
                expected_requests=2,
                artifact_dir=f"artifacts/{run_id}",
                claim_gate="PASS_FEASIBILITY; server-qlog-only possible_connection_migration evidence",
                server_command=server_command(values, run_id, 2),
                client_command=safari_network_change_command(values, run_id, p1_url, 2),
                registration_hint="Record status as PASS_FEASIBILITY unless browser-internal QUIC evidence is added.",
            )
        )
    if prefer_p1 in {"android", "both"}:
        run_id = "controlled-public-android-chrome-downlink-network-change-001"
        plans.append(
            TrialPlan(
                requirement_id="p1-safari-or-android-feasibility",
                trial_id=run_id,
                phase="p1-feasibility",
                browser="Android Chrome",
                workload="browser-downlink active path change",
                heartbeat="false",
                expected_requests=2,
                artifact_dir=f"artifacts/{run_id}",
                claim_gate="PASS_FEASIBILITY; server-qlog-only possible_connection_migration evidence",
                server_command=server_command(values, run_id, 2),
                client_command=android_network_change_command(values, run_id, p1_url, 2),
                registration_hint="Record status as PASS_FEASIBILITY unless Android browser-internal QUIC evidence is added.",
            )
        )
    return plans


def coverage(required: list[RequiredTrial], plans: list[TrialPlan]) -> list[dict[str, Any]]:
    counts = Counter(plan.requirement_id for plan in plans)
    rows: list[dict[str, Any]] = []
    for item in required:
        planned = counts[item.requirement_id]
        rows.append(
            {
                "requirement_id": item.requirement_id,
                "phase": item.phase,
                "browser": item.browser,
                "min_count": item.min_count,
                "planned_count": planned,
                "planned_satisfies_minimum": planned >= item.min_count,
                "accepted_statuses": item.accepted_statuses,
            }
        )
    return rows


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    values = dict(PUBLIC_TEMPLATE_VALUES)
    config_source = "public template"
    if args.use_local_config:
        values.update({key: value for key, value in parse_env_file(Path(args.config)).items() if value})
        config_source = args.config
    overrides = {
        "PUBLIC_ORIGIN_HOST": args.public_origin_host,
        "PUBLIC_ORIGIN_PORT": args.public_origin_port,
        "PUBLIC_ORIGIN_URL": args.public_origin_url,
        "CONTROLLED_PUBLIC_BASELINE_SUMMARY": args.baseline_summary,
        "NETWORK_CHANGE_CMD": args.network_change_cmd,
        "ANDROID_NETWORK_CHANGE_CMD": args.android_network_change_cmd,
    }
    values.update({key: value for key, value in overrides.items() if value})

    required = load_required_trials(Path(args.required_trials))
    plans = make_plan(values, args.repetitions, args.prefer_p1)
    cov = coverage(required, plans)
    return {
        "generated": utc_date_iso(),
        "config_source": config_source,
        "public_safe_default": not args.use_local_config,
        "repetitions": args.repetitions,
        "prefer_p1": args.prefer_p1,
        "requirement_count": len(required),
        "planned_trial_count": len(plans),
        "coverage": cov,
        "plans": [asdict(plan) for plan in plans],
        "post_run_verification_commands": [
            "python3 tools/audit_final_browser_handover_trials.py --output docs/results/final-browser-handover-trial-audit-20260624.md",
            "python3 tools/build_paper_tables.py --output docs/results/paper-tables-20260624.md",
            "python3 tools/audit_research_bundle.py --output docs/results/research-bundle-audit-20260624.md",
            "python3 tools/verify_research_bundle.py --output docs/results/research-verification-report-20260624.md",
            "python3 tools/validate_publication_bundle.py",
        ],
    }


def markdown_bool(value: bool) -> str:
    return "yes" if value else "no"


def emit_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Final Browser Handover Run Plan",
        "",
        f"Generated: `{report['generated']}`",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| config source | `{report['config_source']}` |",
        f"| public-safe default | `{markdown_bool(report['public_safe_default'])}` |",
        f"| Chrome active repetitions per variant | `{report['repetitions']}` |",
        f"| P1 feasibility target | `{report['prefer_p1']}` |",
        f"| required trial groups | `{report['requirement_count']}` |",
        f"| planned executions | `{report['planned_trial_count']}` |",
        "",
        "이 문서는 실험을 실행하지 않는다. 실제 도메인, 인증서 경로, network-change 명령을 추적 문서에 남기지 않기 위해 기본 출력은 public template 값으로 생성된다.",
        "",
        "## Coverage",
        "",
        "| requirement | phase | browser | min | planned | satisfies | accepted status |",
        "| --- | --- | --- | ---: | ---: | --- | --- |",
    ]
    for item in report["coverage"]:
        lines.append(
            "| `{requirement_id}` | {phase} | {browser} | {min_count} | {planned_count} | `{satisfies}` | `{accepted}` |".format(
                requirement_id=item["requirement_id"],
                phase=item["phase"],
                browser=item["browser"],
                min_count=item["min_count"],
                planned_count=item["planned_count"],
                satisfies=markdown_bool(item["planned_satisfies_minimum"]),
                accepted=item["accepted_statuses"],
            )
        )

    lines.extend(
        [
            "",
            "## Execution Queue",
            "",
            "| order | trial_id | requirement | phase | browser | heartbeat | expected requests |",
            "| ---: | --- | --- | --- | --- | --- | ---: |",
        ]
    )
    for index, plan in enumerate(report["plans"], 1):
        lines.append(
            f"| {index} | `{plan['trial_id']}` | `{plan['requirement_id']}` | {plan['phase']} | {plan['browser']} | `{plan['heartbeat']}` | {plan['expected_requests']} |"
        )

    lines.extend(["", "## Trial Commands", ""])
    for index, plan in enumerate(report["plans"], 1):
        lines.extend(
            [
                f"### {index}. `{plan['trial_id']}`",
                "",
                f"- requirement: `{plan['requirement_id']}`",
                f"- artifact dir: `{plan['artifact_dir']}`",
                f"- claim gate: {plan['claim_gate']}",
                f"- registration: {plan['registration_hint']}",
                "",
                "Server/origin terminal:",
                "",
                "```bash",
                plan["server_command"],
                "```",
                "",
                "Browser/client terminal:",
                "",
                "```bash",
                plan["client_command"],
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## Post-run Verification",
            "",
            "각 trial의 공개 가능한 요약 row를 `data/experiment-results.csv`에 등록한 뒤 다음을 실행한다.",
            "",
            "```bash",
            "\n".join(report["post_run_verification_commands"]),
            "```",
            "",
            "최종 논문 Results에서 browser/mobile CM 본 실험 완료를 주장하려면 다음 명령이 exit 0이어야 한다.",
            "",
            "```bash",
            "python3 tools/audit_final_browser_handover_trials.py --require-complete",
            "```",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--required-trials", default=DEFAULT_REQUIRED_TRIALS)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--prefer-p1", choices=["safari", "android", "both"], default="safari")
    parser.add_argument("--use-local-config", action="store_true")
    parser.add_argument("--public-origin-host", default="")
    parser.add_argument("--public-origin-port", default="")
    parser.add_argument("--public-origin-url", default="")
    parser.add_argument("--baseline-summary", default="")
    parser.add_argument("--network-change-cmd", default="")
    parser.add_argument("--android-network-change-cmd", default="")
    args = parser.parse_args()

    if args.repetitions < 1:
        raise SystemExit("--repetitions must be positive")

    report = build_report(args)
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n" if args.format == "json" else emit_markdown(report)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
