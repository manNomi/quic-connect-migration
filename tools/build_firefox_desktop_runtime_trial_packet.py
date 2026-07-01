#!/usr/bin/env python3
"""Build a public-safe Firefox desktop runtime trial packet."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from research_clock import utc_date_iso


DEFAULT_OUTPUT = "docs/results/firefox-desktop-runtime-trial-packet-20260701.md"
DEFAULT_JSON_OUTPUT = "data/firefox-desktop-runtime-trial-packet-20260701.json"
DEFAULT_DESKTOP_PATH_READINESS = "data/noniphone-desktop-path-change-readiness-20260701.json"
DEFAULT_FIREFOX_PATHS = (
    "/Applications/Firefox.app/Contents/MacOS/firefox",
    "/Applications/Firefox Developer Edition.app/Contents/MacOS/firefox",
)
NEQO_LOCAL_RECIPE_URL = (
    "https://github.com/mozilla/neqo/blob/"
    "3ba227d37f46a5684e984ead831b73344d9fec63/README.md#L154"
)
FIREFOX_NEQO_BOUNDARY_DOC = "docs/results/firefox-neqo-browser-boundary-audit-20260701.md"


@dataclass(frozen=True)
class LocalTool:
    name: str
    command: str
    found: bool
    executable: bool
    version: str
    path: str


@dataclass(frozen=True)
class Trial:
    rank: int
    trial_id: str
    phase: str
    target: str
    prerequisite: str
    command_template: str
    required_artifacts: tuple[str, ...]
    acceptance_gate: str
    safe_interpretation: str
    do_not_claim: str


FORBIDDEN_PUBLIC_TERMS = [
    "AWS_" + "SECRET_ACCESS_KEY",
    "BEGIN " + "PRIVATE KEY",
    "AKIA",
    "ASIA",
    "arn:aws:" + "iam::",
]


def run(args: list[str], timeout: int = 6) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def first_existing(paths: tuple[str, ...]) -> str:
    for path in paths:
        if Path(path).exists():
            return path
    found = shutil.which("firefox")
    return found or paths[0]


def command_version(command: str, args: list[str]) -> str:
    if not (shutil.which(command) or Path(command).exists()):
        return ""
    try:
        proc = run([command, *args])
    except (OSError, subprocess.TimeoutExpired):
        return ""
    text = (proc.stdout or proc.stderr).strip()
    return text.splitlines()[0] if text else ""


def tool_from_path(name: str, command: str, version_args: list[str]) -> LocalTool:
    path = command if Path(command).exists() else (shutil.which(command) or "")
    found = bool(path)
    executable = found and os.access(path, os.X_OK)
    return LocalTool(
        name=name,
        command=command,
        found=found,
        executable=executable,
        version=command_version(path or command, version_args) if found else "",
        path=path,
    )


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def yes_no(value: bool) -> str:
    return "yes" if value else "no"


def firefox_user_js_snippet() -> str:
    return "\n".join(
        [
            'user_pref("network.http.http3.enabled", true);',
            'user_pref("network.http.http3.alt-svc-mapping-for-testing", "localhost;h3=\\":12345\\"");',
            'user_pref("network.http.http3.disable_when_third_party_roots_found", false);',
        ]
    )


def build_trials() -> list[Trial]:
    return [
        Trial(
            rank=1,
            trial_id="firefox-local-neqo-h3-baseline",
            phase="local-baseline",
            target="Firefox -> local neqo-server",
            prerequisite="Firefox binary, local Neqo checkout, temporary Firefox profile with HTTP/3 testing preferences.",
            command_template=(
                "NEQO_CHECKOUT=/private/tmp/quic-cm-scan-repos/neqo\n"
                "cd \"$NEQO_CHECKOUT\"\n"
                "QLOGDIR=/tmp/firefox-neqo-qlog cargo run --bin neqo-server -- 'localhost:12345'\n"
                "FIREFOX_PROFILE=/tmp/firefox-cm-profile\n"
                "mkdir -p \"$FIREFOX_PROFILE\"\n"
                "# write the documented HTTP/3 test prefs to $FIREFOX_PROFILE/user.js, then launch Firefox to https://localhost:12345/"
            ),
            required_artifacts=(
                "neqo-server qlog directory",
                "Firefox profile preferences used for the run",
                "browser navigation result or WebDriver/manual timestamp",
                "server access/log evidence for HTTP/3 request",
            ),
            acceptance_gate="baseline_only: Firefox reaches the local H3 target and server qlog confirms HTTP/3.",
            safe_interpretation="Firefox can be connected to the local Neqo H3 test target.",
            do_not_claim="Connection Migration, public-origin behavior, or browser handover.",
        ),
        Trial(
            rank=2,
            trial_id="firefox-controlled-public-h3-baseline",
            phase="public-baseline",
            target="Firefox -> controlled public H3 origin",
            prerequisite="Firefox binary, controlled public origin with WebPKI TLS and Alt-Svc h3, packet/server qlog capture enabled.",
            command_template=(
                "PUBLIC_ORIGIN_BASE=${PUBLIC_ORIGIN_BASE:?set controlled H3 origin}\n"
                "FIREFOX_BIN=${FIREFOX_BIN:-/Applications/Firefox.app/Contents/MacOS/firefox}\n"
                "FIREFOX_PROFILE=/tmp/firefox-public-h3-profile\n"
                "\"$FIREFOX_BIN\" --new-instance --profile \"$FIREFOX_PROFILE\" \"$PUBLIC_ORIGIN_BASE/browser-slow?duration_ms=3000&chunks=3&label=firefox-public-baseline\""
            ),
            required_artifacts=(
                "public origin readiness with Alt-Svc h3",
                "server qlog or H3 access evidence",
                "Firefox version/profile metadata",
                "packet capture if browser-internal logging is unavailable",
            ),
            acceptance_gate="baseline_only: public H3 request completes and server-side H3 evidence is present.",
            safe_interpretation="Firefox public H3 baseline is usable for a later active path-change row.",
            do_not_claim="Network-change migration or same-session continuity.",
        ),
        Trial(
            rank=3,
            trial_id="firefox-controlled-public-range-active-001",
            phase="active-network-change",
            target="Firefox -> controlled public byte-range workload",
            prerequisite=(
                "Firefox public baseline PASS, non-iPhone desktop path-change command, before/after route snapshots, "
                "server qlog, and packet capture."
            ),
            command_template=(
                "PUBLIC_ORIGIN_BASE=${PUBLIC_ORIGIN_BASE:?set controlled H3 origin}\n"
                "NETWORK_CHANGE_CMD=${NETWORK_CHANGE_CMD:?set non-iPhone desktop path-change command}\n"
                "python3 tools/capture_network_path_snapshot.py --label firefox-before --url \"$PUBLIC_ORIGIN_BASE\" --output /tmp/firefox-before.json\n"
                "# launch Firefox to /browser-range-download and trigger NETWORK_CHANGE_CMD after first range completes\n"
                "$NETWORK_CHANGE_CMD\n"
                "python3 tools/capture_network_path_snapshot.py --label firefox-after --url \"$PUBLIC_ORIGIN_BASE\" --output /tmp/firefox-after.json"
            ),
            required_artifacts=(
                "before/after route snapshots",
                "server qlog PATH_CHALLENGE/PATH_RESPONSE or equivalent path validation evidence",
                "server remote tuple/path evidence",
                "workload completion state",
                "Firefox logging/profile/profiler artifact if available",
            ),
            acceptance_gate=(
                "feasibility_or_strong_with_extra_browser_logs: task completion + client path change + server path validation; "
                "strong browser claim additionally needs Firefox/Necko/Neqo same-connection attribution."
            ),
            safe_interpretation="Firefox range workload survived or failed under a controlled active path-change attempt.",
            do_not_claim="Chrome-equivalent NetLog proof or Firefox single-session CM without same-connection browser/runtime attribution.",
        ),
        Trial(
            rank=4,
            trial_id="firefox-controlled-public-upload-active-001",
            phase="active-network-change",
            target="Firefox -> controlled public upload workload",
            prerequisite="Same as range active row, but with upload endpoint and client-sending workload evidence.",
            command_template=(
                "PUBLIC_ORIGIN_BASE=${PUBLIC_ORIGIN_BASE:?set controlled H3 origin}\n"
                "NETWORK_CHANGE_CMD=${NETWORK_CHANGE_CMD:?set non-iPhone desktop path-change command}\n"
                "# launch Firefox to /browser-upload, trigger NETWORK_CHANGE_CMD mid-upload, then classify server/qlog/workload artifacts"
            ),
            required_artifacts=(
                "before/after route snapshots",
                "server qlog path validation evidence",
                "upload completion and received byte count",
                "server tuple/path evidence",
                "Firefox logging/profile/profiler artifact if available",
            ),
            acceptance_gate="same as range active row, with upload byte-count continuity.",
            safe_interpretation="Firefox upload continuity can be compared with Chrome upload local/public evidence.",
            do_not_claim="Application upload success as pure QUIC CM unless the same-session chain is proven.",
        ),
    ]


def build_packet(desktop_path_readiness: Path = Path(DEFAULT_DESKTOP_PATH_READINESS)) -> dict[str, Any]:
    firefox_command = first_existing(DEFAULT_FIREFOX_PATHS)
    firefox = tool_from_path("Firefox", firefox_command, ["--version"])
    geckodriver = tool_from_path("geckodriver", "geckodriver", ["--version"])
    tcpdump = tool_from_path("tcpdump", "tcpdump", ["--version"])
    route = tool_from_path("route", "route", ["-n", "get", "default"])
    desktop_path = load_json(desktop_path_readiness)
    desktop_path_ready = bool(desktop_path.get("noniphone_desktop_path_ready"))

    gates = {
        "firefox_binary_ready": firefox.executable,
        "geckodriver_ready": geckodriver.executable,
        "packet_capture_ready": tcpdump.executable and route.found,
        "noniphone_desktop_path_ready": desktop_path_ready,
        "firefox_runtime_rows_executed": False,
    }
    blockers: list[str] = []
    if not gates["firefox_binary_ready"]:
        blockers.append("Firefox binary is not installed or not executable on the current host")
    if not gates["geckodriver_ready"]:
        blockers.append("geckodriver is not installed, so automation would be manual or require another driver")
    if not gates["packet_capture_ready"]:
        blockers.append("packet/route observability is incomplete for Firefox rows")
    if not desktop_path_ready:
        blockers.append("no active non-iPhone desktop path-change gate is open")

    return {
        "generated": utc_date_iso(),
        "public_safe": True,
        "scope": "firefox_desktop_runtime_trial_packet",
        "source_boundary_doc": FIREFOX_NEQO_BOUNDARY_DOC,
        "neqo_local_recipe_url": NEQO_LOCAL_RECIPE_URL,
        "local_tools": {
            "firefox": asdict(firefox),
            "geckodriver": asdict(geckodriver),
            "tcpdump": asdict(tcpdump),
            "route": asdict(route),
        },
        "gates": gates,
        "blockers": blockers,
        "desktop_path_readiness_source": desktop_path_readiness.as_posix(),
        "desktop_path_readiness_exists": desktop_path_readiness.exists(),
        "firefox_user_js_snippet": firefox_user_js_snippet(),
        "trials": [asdict(trial) for trial in build_trials()],
        "safe_claim": (
            "This packet makes Firefox runtime evidence reproducible and fail-closed; it does not "
            "add a Firefox runtime result until a trial row with artifacts exists."
        ),
        "unsafe_claim": (
            "Neqo transport tests, this packet, or a Firefox H3 baseline prove Firefox single-session "
            "Connection Migration across an active path change."
        ),
        "next_non_iphone_gate": (
            "Install Firefox/geckodriver or run a manual Firefox profile, open a non-iPhone desktop "
            "path-change gate, then start with local Neqo H3 baseline before any active public row."
        ),
    }


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    def cell(value: object) -> str:
        return str(value if value is not None else "").replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    lines.extend("| " + " | ".join(cell(value) for value in row) + " |" for row in rows)
    return "\n".join(lines)


def emit_markdown(packet: dict[str, Any]) -> str:
    tools = packet["local_tools"]
    gates = packet["gates"]
    lines = [
        "# Firefox Desktop Runtime Trial Packet",
        "",
        f"Generated: `{packet['generated']}`",
        "",
        "This public-safe packet turns the Firefox/Neqo boundary audit into an executable research gate. It is not a Firefox Connection Migration result; it defines the evidence required before Firefox can be used as a runtime row.",
        "",
        "## Summary",
        "",
        markdown_table(
            ["field", "value"],
            [
                ["scope", f"`{packet['scope']}`"],
                ["source boundary doc", f"`{packet['source_boundary_doc']}`"],
                ["Neqo local Firefox recipe", f"[Neqo README]({packet['neqo_local_recipe_url']})"],
                ["Firefox binary ready", f"`{yes_no(gates['firefox_binary_ready'])}`"],
                ["geckodriver ready", f"`{yes_no(gates['geckodriver_ready'])}`"],
                ["packet capture ready", f"`{yes_no(gates['packet_capture_ready'])}`"],
                ["non-iPhone desktop path ready", f"`{yes_no(gates['noniphone_desktop_path_ready'])}`"],
                ["Firefox runtime rows executed", f"`{yes_no(gates['firefox_runtime_rows_executed'])}`"],
            ],
        ),
        "",
        "## Local Tooling",
        "",
        markdown_table(
            ["tool", "found", "executable", "version"],
            [
                [name, yes_no(bool(item["found"])), yes_no(bool(item["executable"])), item["version"] or "-"]
                for name, item in tools.items()
            ],
        ),
        "",
        "## Firefox Profile Preferences",
        "",
        "```js",
        packet["firefox_user_js_snippet"],
        "```",
        "",
        "## Trial Plan",
        "",
        markdown_table(
            [
                "rank",
                "trial id",
                "phase",
                "target",
                "prerequisite",
                "required artifacts",
                "acceptance gate",
                "safe interpretation",
                "do not claim",
            ],
            [
                [
                    item["rank"],
                    f"`{item['trial_id']}`",
                    f"`{item['phase']}`",
                    item["target"],
                    item["prerequisite"],
                    "<br>".join(item["required_artifacts"]),
                    item["acceptance_gate"],
                    item["safe_interpretation"],
                    item["do_not_claim"],
                ]
                for item in packet["trials"]
            ],
        ),
        "",
        "## Command Templates",
        "",
    ]
    for item in packet["trials"]:
        lines.extend(
            [
                f"### {item['trial_id']}",
                "",
                "```bash",
                item["command_template"],
                "```",
                "",
            ]
        )

    lines.extend(
        [
            "## Claim Boundary",
            "",
            f"- Safe claim: {packet['safe_claim']}",
            f"- Unsafe claim: {packet['unsafe_claim']}",
            f"- Next non-iPhone gate: {packet['next_non_iphone_gate']}",
            "",
            "## Current Blockers",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in packet["blockers"] or ["none"])
    text = "\n".join(lines).rstrip() + "\n"
    for forbidden in FORBIDDEN_PUBLIC_TERMS:
        if forbidden in text:
            raise ValueError(f"public output contains forbidden term: {forbidden}")
    return text


def write_outputs(output: Path, json_output: Path, packet: dict[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(emit_markdown(packet), encoding="utf-8")
    json_output.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--desktop-path-readiness", default=DEFAULT_DESKTOP_PATH_READINESS)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--json-output", default=DEFAULT_JSON_OUTPUT)
    args = parser.parse_args()

    packet = build_packet(Path(args.desktop_path_readiness))
    write_outputs(Path(args.output), Path(args.json_output), packet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
