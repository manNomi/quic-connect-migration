#!/usr/bin/env python3
"""Regression checks for final browser handover trial matching rules."""

from __future__ import annotations

from pathlib import Path

from audit_final_browser_handover_trials import evaluate, load_rows


REQUIREMENTS = Path("data/final-browser-handover-required-trials.csv")


FIELDS = [
    "trial_id",
    "date",
    "status",
    "implementation",
    "deployment_tier",
    "protocol",
    "migration_trigger",
    "path_validation_observed",
    "tuple_change_observed",
    "application_task",
    "application_success",
    "manual_intervention_required",
    "failure_layer",
    "artifact_dir",
    "notes",
]


def row(**overrides: str) -> dict[str, str]:
    base = {
        "trial_id": "",
        "date": "2026-06-24",
        "status": "PASS",
        "implementation": "Chrome 149 + controlled public quic-go H3",
        "deployment_tier": "controlled public browser active network-change",
        "protocol": "HTTP/3 over QUIC",
        "migration_trigger": "active path change during downlink streaming",
        "path_validation_observed": "true",
        "tuple_change_observed": "true",
        "application_task": "GET /browser-downlink then streaming GET /downlink-stream",
        "application_success": "true",
        "manual_intervention_required": "false",
        "failure_layer": "none",
        "artifact_dir": "repro/quic-go-min-repro/artifacts/synthetic",
        "notes": "classification possible_connection_migration; client_path_change=client_active_path_changed",
    }
    base.update(overrides)
    return {field: base.get(field, "") for field in FIELDS}


def complete_fixture_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = [
        row(
            trial_id="controlled-public-chrome-h3-baseline-001",
            deployment_tier="controlled public browser baseline",
            migration_trigger="no network change",
            application_task="browser application H3 baseline",
            notes="controlled_public_application_h3_confirmed; server qlog H3 evidence",
        ),
    ]
    for index in range(1, 4):
        rows.append(
            row(
                trial_id=f"controlled-public-chrome-downlink-noheartbeat-network-change-{index:03d}",
                application_task="GET /browser-downlink then streaming GET /downlink-stream",
                notes="classification possible_connection_migration; client_path_change=client_active_path_changed",
            )
        )
        rows.append(
            row(
                trial_id=f"controlled-public-chrome-downlink-heartbeat-network-change-{index:03d}",
                application_task="GET /browser-downlink then streaming GET /downlink-stream plus GET /heartbeat",
                notes="classification possible_connection_migration; client_path_change=client_active_path_changed",
            )
        )
    rows.extend(
        [
            row(
                trial_id="controlled-public-chrome-downlink-noheartbeat-nochange-001",
                deployment_tier="controlled public browser no-change baseline",
                migration_trigger="no network change",
                path_validation_observed="false",
                tuple_change_observed="false",
                notes="classification no_path_change_baseline; application H3 baseline confirmed",
            ),
            row(
                trial_id="controlled-public-chrome-downlink-heartbeat-nochange-001",
                deployment_tier="controlled public browser no-change baseline",
                migration_trigger="no network change",
                path_validation_observed="false",
                tuple_change_observed="false",
                application_task="GET /browser-downlink then streaming GET /downlink-stream plus GET /heartbeat",
                notes="classification no_path_change_baseline; application H3 baseline confirmed",
            ),
            row(
                trial_id="controlled-public-safari-downlink-network-change-001",
                status="PASS_FEASIBILITY",
                implementation="Safari + controlled public quic-go H3",
                notes="classification possible_connection_migration_server_qlog_only; Safari navigation_ok=true",
            ),
        ]
    )
    return rows


def assert_complete_fixture(requirements: list[dict[str, str]]) -> None:
    results = evaluate(requirements, complete_fixture_rows())
    incomplete = [result for result in results if not result.complete]
    if incomplete:
        detail = ", ".join(f"{item.requirement_id}={item.matched_count}/{item.min_count}" for item in incomplete)
        raise AssertionError(f"complete fixture did not satisfy all requirements: {detail}")


def assert_negative_controls_excluded(requirements: list[dict[str, str]]) -> None:
    rows = complete_fixture_rows()
    rows = [
        {
            **item,
            "notes": item["notes"].replace("classification possible_connection_migration", "classification reconnect_or_multiple_sessions"),
        }
        if "noheartbeat-network-change" in item["trial_id"]
        else item
        for item in rows
    ]
    results = {result.requirement_id: result for result in evaluate(requirements, rows)}
    noheartbeat = results["chrome-downlink-noheartbeat-active-cm"]
    if noheartbeat.complete or noheartbeat.matched_count != 0:
        raise AssertionError(
            "reconnect_or_multiple_sessions rows must not satisfy chrome-downlink-noheartbeat-active-cm"
        )


def main() -> int:
    requirements = load_rows(REQUIREMENTS)
    assert_complete_fixture(requirements)
    assert_negative_controls_excluded(requirements)
    print("final_browser_handover_trial_audit_regression=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
