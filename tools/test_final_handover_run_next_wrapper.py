#!/usr/bin/env python3
"""Regression tests for the final handover run-next dispatcher."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "harness" / "scripts" / "final-handover-run-next.sh"


def readiness(*, ready: bool, trial_id: str = "", phase: str = "", browser: str = "Chrome", expected: int = 4) -> dict:
    next_trial = None
    if trial_id:
        next_trial = {
            "trial_id": trial_id,
            "phase": phase,
            "browser": browser,
            "expected_requests": expected,
        }
    return {
        "ready": ready,
        "next_trial": next_trial,
        "missing_required_gates": [] if ready else ["controlled_public_config_present"],
    }


def write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def stub_wrapper(path: Path, marker: Path) -> Path:
    path.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"printf 'trial=%s\\nphase_expected=%s\\nmin_free=%s\\n' \"$TRIAL_ID\" \"${{CONTROLLED_PUBLIC_EXPECTED_REQUESTS:-}}\" \"${{MIN_ARTIFACT_FREE_GIB:-}}\" > {marker.as_posix()!r}\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return path


def run_dispatcher(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", WRAPPER.as_posix()],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )


def base_env(tmp: Path, fixture: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "FINAL_HANDOVER_RUN_NEXT_OUTPUT_DIR": (tmp / "out").as_posix(),
            "FINAL_HANDOVER_RUN_NEXT_READINESS_FIXTURE": fixture.as_posix(),
            "FINAL_HANDOVER_RUN_NEXT_READINESS_MD": (tmp / "out" / "readiness.md").as_posix(),
            "RUN_POSTCHECKS": "0",
        }
    )
    return env


def test_blocked_readiness_does_not_dispatch() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        fixture = write_json(tmp / "blocked.json", readiness(ready=False))
        marker = tmp / "called"
        env = base_env(tmp, fixture)
        env["FINAL_P0_BASELINE_WRAPPER"] = stub_wrapper(tmp / "baseline.sh", marker).as_posix()
        proc = run_dispatcher(env)
        assert proc.returncode == 1
        assert "final_handover_run_next=blocked" in proc.stdout
        assert not marker.exists()


def test_dispatcher_uses_seven_gib_readiness_gate_by_default() -> None:
    text = WRAPPER.read_text(encoding="utf-8")
    assert 'FINAL_HANDOVER_MIN_DISK_GIB="${FINAL_HANDOVER_MIN_DISK_GIB:-7}"' in text
    assert '--min-disk-gib "$FINAL_HANDOVER_MIN_DISK_GIB"' in text


def test_baseline_trial_dispatches_p0_wrapper() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        fixture = write_json(
            tmp / "baseline.json",
            readiness(
                ready=True,
                trial_id="controlled-public-chrome-h3-baseline-001",
                phase="baseline",
                expected=4,
            ),
        )
        marker = tmp / "baseline-called"
        env = base_env(tmp, fixture)
        env["FINAL_P0_BASELINE_WRAPPER"] = stub_wrapper(tmp / "baseline.sh", marker).as_posix()
        proc = run_dispatcher(env)
        assert proc.returncode == 0
        assert "dispatch=final-p0-baseline-run" in proc.stdout
        marker_text = marker.read_text(encoding="utf-8")
        assert "trial=controlled-public-chrome-h3-baseline-001" in marker_text
        assert "min_free=7" in marker_text


def test_nochange_trial_dispatches_nochange_wrapper() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        fixture = write_json(
            tmp / "nochange.json",
            readiness(
                ready=True,
                trial_id="controlled-public-chrome-downlink-heartbeat-nochange-001",
                phase="no-change-baseline",
                expected=6,
            ),
        )
        marker = tmp / "nochange-called"
        env = base_env(tmp, fixture)
        env["FINAL_CHROME_NOCHANGE_WRAPPER"] = stub_wrapper(tmp / "nochange.sh", marker).as_posix()
        proc = run_dispatcher(env)
        marker_text = marker.read_text(encoding="utf-8")
        assert proc.returncode == 0
        assert "dispatch=final-chrome-nochange-run" in proc.stdout
        assert "trial=controlled-public-chrome-downlink-heartbeat-nochange-001" in marker_text
        assert "phase_expected=6" in marker_text
        assert "min_free=7" in marker_text


def test_active_trial_dispatches_network_change_wrapper() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        fixture = write_json(
            tmp / "active.json",
            readiness(
                ready=True,
                trial_id="controlled-public-chrome-downlink-noheartbeat-network-change-001",
                phase="active-network-change",
                expected=2,
            ),
        )
        marker = tmp / "active-called"
        env = base_env(tmp, fixture)
        env["FINAL_CHROME_NETWORK_CHANGE_WRAPPER"] = stub_wrapper(tmp / "active.sh", marker).as_posix()
        proc = run_dispatcher(env)
        marker_text = marker.read_text(encoding="utf-8")
        assert proc.returncode == 0
        assert "dispatch=final-chrome-network-change-run" in proc.stdout
        assert "trial=controlled-public-chrome-downlink-noheartbeat-network-change-001" in marker_text
        assert "phase_expected=2" in marker_text
        assert "min_free=7" in marker_text


def main() -> int:
    test_blocked_readiness_does_not_dispatch()
    test_dispatcher_uses_seven_gib_readiness_gate_by_default()
    test_baseline_trial_dispatches_p0_wrapper()
    test_nochange_trial_dispatches_nochange_wrapper()
    test_active_trial_dispatches_network_change_wrapper()
    print("final_handover_run_next_wrapper=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
