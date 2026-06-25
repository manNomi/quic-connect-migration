#!/usr/bin/env python3
"""Regression tests for the final Chrome network-change run wrapper."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "harness" / "scripts" / "final-chrome-network-change-run.sh"


ACTIVE_CONFIG = """
PUBLIC_ORIGIN_HOST=h3.test.local
PUBLIC_ORIGIN_PORT=443
PUBLIC_ORIGIN_URL='https://h3.test.local/browser-slow?duration_ms=6000&chunks=6&label=public-slow'
PUBLIC_ORIGIN_NETWORK_CHANGE_URL='https://h3.test.local/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=false&heartbeat_delay_ms=5000&label=public-downlink-noheartbeat'
TLS_CERT_FILE=/tmp/fullchain.pem
TLS_KEY_FILE=/tmp/privkey.pem
LISTEN_ADDR=0.0.0.0:443
TCP_ADDR=0.0.0.0:443
ALT_SVC='h3=":443"; ma=60'
CHROME_BIN=/bin/sh
CONTROLLED_PUBLIC_BASELINE_ARTIFACT_DIR=artifacts/controlled-public-chrome-h3-baseline-001
CONTROLLED_PUBLIC_BASELINE_SUMMARY=artifacts/controlled-public-chrome-h3-baseline-001/results/controlled-public-h3-baseline-summary.json
CONTROLLED_PUBLIC_NETWORK_CHANGE_RUN_ID=controlled-public-chrome-downlink-noheartbeat-network-change-001
CONTROLLED_PUBLIC_NETWORK_CHANGE_ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001
CONTROLLED_PUBLIC_NETWORK_CHANGE_SERVER_ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-network-change-001
CONTROLLED_PUBLIC_EXPECTED_REQUESTS=2
NETWORK_CHANGE_AFTER_SECONDS=3
NETWORK_CHANGE_CMD='printf network-change'
REQUIRE_H3_ALT_SVC=1
REQUIRE_CONTROLLED_PUBLIC_BASELINE=1
"""


def run_wrapper(env: dict[str, str], timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", WRAPPER.as_posix()],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def test_wrapper_fails_closed_without_active_config() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        output_dir = tmp / "active-run-results"
        marker = tmp / "runner-called"
        env = dict(os.environ)
        env.update(
            {
                "CONTROLLED_PUBLIC_CONFIG": (tmp / "missing.env").as_posix(),
                "FINAL_CHROME_NETWORK_CHANGE_RUN_OUTPUT_DIR": output_dir.as_posix(),
                "NETWORK_CHANGE_RUNNER": marker.as_posix(),
            }
        )
        proc = run_wrapper(env)
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 1
        assert "controlled_public_active_config=blocked" in proc.stdout
        assert "baseline_unlock=skipped(config_not_ready)" in proc.stdout
        assert "network_change_execution=skipped(readiness_not_met)" in proc.stdout
        assert "final_chrome_network_change_run=blocked" in proc.stdout
        assert (output_dir / "controlled-public-config-check.md").exists()
        assert not marker.exists()
        assert "AKIA" not in combined
        assert "PRIVATE_KEY" not in combined


def test_wrapper_runs_network_change_runner_after_active_config_ready() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        config = tmp / "controlled-public-origin.env"
        config.write_text(ACTIVE_CONFIG, encoding="utf-8")
        output_dir = tmp / "active-run-results"
        artifact_dir = tmp / "controlled-public-chrome-downlink-noheartbeat-network-change-001"
        runner = tmp / "runner.sh"
        marker = tmp / "runner-called"
        runner.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "mkdir -p \"$ARTIFACT_DIR/results\"\n"
            "printf '%s\\n' \"$RUN_ID\" > \"$ARTIFACT_DIR/results/run-id.txt\"\n"
            f"touch {marker.as_posix()!r}\n",
            encoding="utf-8",
        )
        runner.chmod(0o755)
        env = dict(os.environ)
        env.update(
            {
                "CONTROLLED_PUBLIC_CONFIG": config.as_posix(),
                "ARTIFACT_DIR": artifact_dir.as_posix(),
                "FINAL_CHROME_NETWORK_CHANGE_RUN_OUTPUT_DIR": output_dir.as_posix(),
                "NETWORK_CHANGE_RUNNER": runner.as_posix(),
                "CHECK_BASELINE_UNLOCK": "0",
                "RUN_POSTCHECKS": "0",
            }
        )
        proc = run_wrapper(env)
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 0
        assert "controlled_public_active_config=ok" in proc.stdout
        assert "baseline_unlock=skipped(CHECK_BASELINE_UNLOCK=0)" in proc.stdout
        assert "network_change_execution=ok" in proc.stdout
        assert "artifact_bundle_check=skipped(RUN_POSTCHECKS=0)" in proc.stdout
        assert "final_chrome_network_change_run=ready" in proc.stdout
        assert marker.exists()
        assert (artifact_dir / "results" / "run-id.txt").read_text(encoding="utf-8").strip() == (
            "controlled-public-chrome-downlink-noheartbeat-network-change-001"
        )
        assert "AKIA" not in combined
        assert "PRIVATE_KEY" not in combined


def main() -> int:
    test_wrapper_fails_closed_without_active_config()
    test_wrapper_runs_network_change_runner_after_active_config_ready()
    print("final_chrome_network_change_run_wrapper=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
