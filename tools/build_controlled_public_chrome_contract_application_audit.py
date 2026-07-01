#!/usr/bin/env python3
"""Apply the controlled-public Chrome artifact contract to tracked bridge rows."""

from __future__ import annotations

import argparse
import csv
import io
import json
from collections import Counter
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_BRIDGE_JSON = "data/controlled-public-chrome-bridge-synthesis-20260701.json"
DEFAULT_CONTRACT_JSON = "data/controlled-public-chrome-artifact-classifier-contract-20260701.json"
DEFAULT_OUTPUT = "docs/results/controlled-public-chrome-contract-application-audit-20260701.md"
DEFAULT_JSON_OUTPUT = "data/controlled-public-chrome-contract-application-audit-20260701.json"
DEFAULT_CSV_OUTPUT = "data/controlled-public-chrome-contract-application-audit-20260701.csv"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def client_active_path_changed(record: dict[str, Any]) -> bool:
    notes = str(record.get("notes") or "")
    return (
        "client_path_change=client_active_path_changed" in notes
        or "client_path_eventual_change=client_active_path_changed" in notes
    )


def target_tuple_changed(record: dict[str, Any]) -> bool:
    target_count = int_value(record.get("target_h3_remote_addr_count"))
    return bool(record.get("tuple_change_observed")) and target_count > 1


def active_missing_gates(record: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    if record.get("trigger_class") != "active_network_change":
        missing.append("network_change_command_executed")
    if not record.get("application_success"):
        missing.append("application_completion_metric_true")
    if not client_active_path_changed(record):
        missing.append("client_active_path_changed")
    if not target_tuple_changed(record):
        missing.append("server_target_h3_tuple_changed")
    if not record.get("path_validation_observed"):
        missing.append("server_qlog_path_validation")
    # The bridge synthesis deliberately excludes raw Chrome NetLog details. A future
    # row must still prove this gate from its classifier summary before paper use.
    missing.append("chrome_single_target_quic_session")
    return missing


def classify_record(record: dict[str, Any]) -> dict[str, Any]:
    trigger = record.get("trigger_class")
    status = record.get("status")
    classification = record.get("classification")
    application_success = bool(record.get("application_success"))
    missing = active_missing_gates(record) if trigger == "active_network_change" else []

    if trigger == "nochange_baseline" and status == "PASS" and application_success:
        contract_class = "public_h3_baseline_positive"
        claim_strength = "baseline_only"
        paper_use = "use_as_public_h3_baseline"
        safe_claim = "The tracked row confirms controlled-public Chrome application H3 for a no-change workload baseline."
        do_not_claim = "No active path change was part of the row; do not claim Connection Migration."
    elif trigger == "active_network_change" and not missing:
        contract_class = "strong_single_session_cm_positive"
        claim_strength = "browser_deployment_positive"
        paper_use = "eligible_for_strong_public_chrome_cm_claim"
        safe_claim = "The row satisfies the full public Chrome single-session CM contract."
        do_not_claim = "Keep the claim scoped to this workload and environment."
    elif trigger == "active_network_change" and application_success:
        contract_class = "application_recovery_or_reconnect"
        claim_strength = "task_recovery_not_cm"
        paper_use = "use_as_task_completion_without_cm_success"
        safe_claim = "The application task completed, but the row is missing one or more strong CM gates."
        do_not_claim = "Do not describe the row as single-session QUIC Connection Migration."
    elif status == "PASS_NEGATIVE_CONTROL" or classification in {
        "no_client_active_path_change_observed",
        "application_task_failed_without_quic_path_validation",
        "tuple_changed_without_path_validation",
    }:
        contract_class = "negative_control_record"
        claim_strength = "gap_or_negative_control"
        paper_use = "use_as_negative_or_gap_evidence"
        safe_claim = "The row documents a conservative missing-gate or failure mode."
        do_not_claim = "Do not count this row as public browser CM success."
    else:
        contract_class = "not_claimable"
        claim_strength = "not_claimable"
        paper_use = "do_not_use_for_paper_claim"
        safe_claim = "No paper claim should be made from this row."
        do_not_claim = "Do not use incomplete infrastructure rows as CM evidence."

    return {
        "source_path": record.get("source_path", ""),
        "trial_id": record.get("trial_id", ""),
        "status": status,
        "source_classification": classification,
        "trigger_class": trigger,
        "workload": record.get("workload", ""),
        "retry_policy": record.get("retry_policy", ""),
        "application_success": application_success,
        "client_active_path_changed": client_active_path_changed(record),
        "target_tuple_changed": target_tuple_changed(record),
        "path_validation_observed": bool(record.get("path_validation_observed")),
        "contract_class": contract_class,
        "claim_strength": claim_strength,
        "paper_use": paper_use,
        "missing_strong_cm_gates": missing,
        "safe_claim": safe_claim,
        "do_not_claim": do_not_claim,
    }


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(row.get(key, "-")) for row in rows).items()))


def build_audit(
    bridge_path: Path = Path(DEFAULT_BRIDGE_JSON),
    contract_path: Path = Path(DEFAULT_CONTRACT_JSON),
) -> dict[str, Any]:
    bridge = read_json(bridge_path)
    contract = read_json(contract_path)
    records = bridge.get("records", []) if isinstance(bridge.get("records"), list) else []
    rows = [classify_record(record) for record in records]
    active_rows = [row for row in rows if row["trigger_class"] == "active_network_change"]
    baseline_rows = [row for row in rows if row["trigger_class"] == "nochange_baseline"]
    missing_gate_counts = Counter(
        gate for row in active_rows for gate in row.get("missing_strong_cm_gates", [])
    )
    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "source_bridge": bridge_path.as_posix(),
        "source_contract": contract_path.as_posix(),
        "source_bridge_exists": bridge_path.exists(),
        "source_contract_exists": contract_path.exists(),
        "contract_id": contract.get("contract_id", "-"),
        "source_record_count": len(records),
        "row_count": len(rows),
        "active_row_count": len(active_rows),
        "baseline_row_count": len(baseline_rows),
        "contract_class_counts": count_by(rows, "contract_class"),
        "paper_use_counts": count_by(rows, "paper_use"),
        "active_missing_strong_gate_counts": dict(sorted(missing_gate_counts.items())),
        "strong_single_session_cm_rows": [
            row["trial_id"] for row in rows if row["contract_class"] == "strong_single_session_cm_positive"
        ],
        "baseline_rows": [
            row["trial_id"] for row in rows if row["contract_class"] == "public_h3_baseline_positive"
        ],
        "application_completion_without_cm_rows": [
            row["trial_id"] for row in rows if row["contract_class"] == "application_recovery_or_reconnect"
        ],
        "rows": rows,
        "interpretation": {
            "supported": "Applying the contract to tracked bridge rows yields public H3 baselines and conservative gap/negative-control evidence.",
            "not_supported": "No tracked row satisfies the full strong single-session public Chrome CM contract.",
            "paper_use": "Use this audit as the current public Chrome claim ledger until new raw artifacts pass the source classifier and the contract.",
        },
    }


def emit_csv(audit: dict[str, Any]) -> str:
    fields = [
        "trial_id",
        "status",
        "source_classification",
        "trigger_class",
        "workload",
        "application_success",
        "client_active_path_changed",
        "target_tuple_changed",
        "path_validation_observed",
        "contract_class",
        "claim_strength",
        "paper_use",
        "missing_strong_cm_gates",
    ]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for row in audit["rows"]:
        out = dict(row)
        out["missing_strong_cm_gates"] = ";".join(row.get("missing_strong_cm_gates", []))
        writer.writerow({field: out.get(field, "") for field in fields})
    return buffer.getvalue()


def emit_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Controlled Public Chrome Contract Application Audit",
        "",
        f"Generated: `{audit['generated']}`",
        "",
        "This public-safe audit applies the controlled-public Chrome artifact classifier contract to the tracked bridge synthesis rows. It does not inspect raw qlogs, NetLogs, pcaps, hostnames, IP addresses, credentials, or untracked local notes.",
        "",
        "## Summary",
        "",
        "| field | value |",
        "| --- | --- |",
        f"| source bridge | `{audit['source_bridge']}` |",
        f"| source contract | `{audit['source_contract']}` |",
        f"| contract id | `{audit['contract_id']}` |",
        f"| source record count | `{audit['source_record_count']}` |",
        f"| active rows | `{audit['active_row_count']}` |",
        f"| baseline rows | `{audit['baseline_row_count']}` |",
        f"| contract class counts | `{audit['contract_class_counts']}` |",
        f"| paper use counts | `{audit['paper_use_counts']}` |",
        f"| active missing strong gate counts | `{audit['active_missing_strong_gate_counts']}` |",
        f"| strong single-session CM rows | `{audit['strong_single_session_cm_rows']}` |",
        f"| application completion without CM rows | `{audit['application_completion_without_cm_rows']}` |",
        "",
        "## Interpretation",
        "",
        f"- Supported: {audit['interpretation']['supported']}",
        f"- Not supported: {audit['interpretation']['not_supported']}",
        f"- Paper use: {audit['interpretation']['paper_use']}",
        "",
        "## Contract-Applied Rows",
        "",
        "| trial | source class | trigger | workload | app | client path | tuple | qlog path | contract class | missing strong gates | paper use |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in audit["rows"]:
        lines.append(
            "| `{trial_id}` | `{source_classification}` | `{trigger_class}` | `{workload}` | `{application_success}` | `{client_active_path_changed}` | `{target_tuple_changed}` | `{path_validation_observed}` | `{contract_class}` | `{missing}` | `{paper_use}` |".format(
                trial_id=row["trial_id"],
                source_classification=row["source_classification"],
                trigger_class=row["trigger_class"],
                workload=row["workload"],
                application_success=row["application_success"],
                client_active_path_changed=row["client_active_path_changed"],
                target_tuple_changed=row["target_tuple_changed"],
                path_validation_observed=row["path_validation_observed"],
                contract_class=row["contract_class"],
                missing=";".join(row.get("missing_strong_cm_gates", [])) or "-",
                paper_use=row["paper_use"],
            )
        )
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "The two tracked active rows with application completion still miss qlog path validation and Chrome single-session evidence, so they remain task-completion-without-CM-support rows. The other active rows remain negative/gap records. The no-change rows are useful H3 baselines, but they are not active Connection Migration evidence.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(markdown_path: Path, json_path: Path, csv_path: Path, audit: dict[str, Any]) -> None:
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(emit_markdown(audit), encoding="utf-8")
    json_path.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    csv_path.write_text(emit_csv(audit), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bridge-json", default=DEFAULT_BRIDGE_JSON)
    parser.add_argument("--contract-json", default=DEFAULT_CONTRACT_JSON)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--csv-output", default=DEFAULT_CSV_OUTPUT)
    args = parser.parse_args()

    audit = build_audit(Path(args.bridge_json), Path(args.contract_json))
    write_outputs(Path(args.output), Path(args.json_output), Path(args.csv_output), audit)
    print(f"wrote {args.output}")
    print(f"wrote {args.json_output}")
    print(f"wrote {args.csv_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
