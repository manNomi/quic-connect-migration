#!/usr/bin/env python3
"""Regression tests for the final Chrome no-change run wrapper."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "harness" / "scripts" / "final-chrome-nochange-run.sh"


BASELINE_CONFIG = """
PUBLIC_ORIGIN_HOST=h3.test.local
PUBLIC_ORIGIN_PORT=443
PUBLIC_ORIGIN_URL='https://h3.test.local/browser-slow?duration_ms=6000&chunks=6&label=public-slow'
PUBLIC_ORIGIN_NETWORK_CHANGE_URL='https://h3.test.local/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=false&heartbeat_delay_ms=5000&label=public-downlink-noheartbeat'
PUBLIC_ORIGIN_NOCHANGE_URL='https://h3.test.local/browser-downlink?duration_ms=15000&chunks=15&bytes=65536&heartbeat=false&heartbeat_delay_ms=5000&label=public-downlink-noheartbeat'
TLS_CERT_FILE=/tmp/fullchain.pem
TLS_KEY_FILE=/tmp/privkey.pem
LISTEN_ADDR=0.0.0.0:443
TCP_ADDR=0.0.0.0:443
ALT_SVC='h3=":443"; ma=60'
CHROME_BIN=/bin/sh
CONTROLLED_PUBLIC_NOCHANGE_RUN_ID=controlled-public-chrome-downlink-noheartbeat-nochange-001
CONTROLLED_PUBLIC_NOCHANGE_ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-nochange-001
CONTROLLED_PUBLIC_NOCHANGE_SERVER_ARTIFACT_DIR=artifacts/controlled-public-chrome-downlink-noheartbeat-nochange-001
REQUIRE_H3_ALT_SVC=1
REQUIRE_CONTROLLED_PUBLIC_APPLICATION_H3=1
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


def test_wrapper_fails_closed_without_baseline_config() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        output_dir = tmp / "nochange-run-results"
        marker = tmp / "runner-called"
        env = dict(os.environ)
        env.update(
            {
                "CONTROLLED_PUBLIC_CONFIG": (tmp / "missing.env").as_posix(),
                "FINAL_CHROME_NOCHANGE_RUN_OUTPUT_DIR": output_dir.as_posix(),
                "NOCHANGE_RUNNER": marker.as_posix(),
            }
        )
        proc = run_wrapper(env)
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 1
        assert "controlled_public_baseline_config=blocked" in proc.stdout
        assert "nochange_execution=skipped(config_not_ready)" in proc.stdout
        assert "final_chrome_nochange_run=blocked" in proc.stdout
        assert (output_dir / "controlled-public-config-check.md").exists()
        assert not marker.exists()
        assert "AKIA" not in combined
        assert "PRIVATE_KEY" not in combined


def test_wrapper_runs_nochange_runner_after_baseline_config_ready() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        config = tmp / "controlled-public-origin.env"
        config.write_text(BASELINE_CONFIG, encoding="utf-8")
        output_dir = tmp / "nochange-run-results"
        artifact_dir = tmp / "controlled-public-chrome-downlink-noheartbeat-nochange-001"
        runner = tmp / "runner.sh"
        marker = tmp / "runner-called"
        runner.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "mkdir -p \"$ARTIFACT_DIR/results\"\n"
            "printf '%s\\n' \"$RUN_ID\" > \"$ARTIFACT_DIR/results/run-id.txt\"\n"
            "printf '%s\\n' \"$CONTROLLED_PUBLIC_EXPECTED_REQUESTS\" > \"$ARTIFACT_DIR/results/expected-requests.txt\"\n"
            f"touch {marker.as_posix()!r}\n",
            encoding="utf-8",
        )
        runner.chmod(0o755)
        env = dict(os.environ)
        env.update(
            {
                "CONTROLLED_PUBLIC_CONFIG": config.as_posix(),
                "ARTIFACT_DIR": artifact_dir.as_posix(),
                "FINAL_CHROME_NOCHANGE_RUN_OUTPUT_DIR": output_dir.as_posix(),
                "NOCHANGE_RUNNER": runner.as_posix(),
                "RUN_POSTCHECKS": "0",
            }
        )
        proc = run_wrapper(env)
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 0
        assert "controlled_public_baseline_config=ok" in proc.stdout
        assert "nochange_execution=ok" in proc.stdout
        assert "artifact_bundle_check=skipped(RUN_POSTCHECKS=0)" in proc.stdout
        assert "final_chrome_nochange_run=ready" in proc.stdout
        assert marker.exists()
        assert (artifact_dir / "results" / "run-id.txt").read_text(encoding="utf-8").strip() == (
            "controlled-public-chrome-downlink-noheartbeat-nochange-001"
        )
        assert (artifact_dir / "results" / "expected-requests.txt").read_text(encoding="utf-8").strip() == "4"
        assert "AKIA" not in combined
        assert "PRIVATE_KEY" not in combined


def test_heartbeat_trial_defaults_to_six_expected_requests() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        config = tmp / "controlled-public-origin.env"
        config.write_text(BASELINE_CONFIG, encoding="utf-8")
        runner = tmp / "runner.sh"
        artifact_dir_out = tmp / "artifact-dir.txt"
        expected_requests_out = tmp / "expected-requests.txt"
        runner.write_text(
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            f"printf '%s\\n' \"$ARTIFACT_DIR\" > {artifact_dir_out.as_posix()!r}\n"
            f"printf '%s\\n' \"$CONTROLLED_PUBLIC_EXPECTED_REQUESTS\" > {expected_requests_out.as_posix()!r}\n",
            encoding="utf-8",
        )
        runner.chmod(0o755)
        env = dict(os.environ)
        env.update(
            {
                "CONTROLLED_PUBLIC_CONFIG": config.as_posix(),
                "TRIAL_ID": "controlled-public-chrome-downlink-heartbeat-nochange-001",
                "FINAL_CHROME_NOCHANGE_RUN_OUTPUT_DIR": (tmp / "out").as_posix(),
                "NOCHANGE_RUNNER": runner.as_posix(),
                "RUN_POSTCHECKS": "0",
            }
        )
        proc = run_wrapper(env)
        assert proc.returncode == 0
        assert artifact_dir_out.read_text(encoding="utf-8").strip().endswith(
            "/artifacts/controlled-public-chrome-downlink-heartbeat-nochange-001"
        )
        assert expected_requests_out.read_text(encoding="utf-8").strip() == "6"


def main() -> int:
    test_wrapper_fails_closed_without_baseline_config()
    test_wrapper_runs_nochange_runner_after_baseline_config_ready()
    test_heartbeat_trial_defaults_to_six_expected_requests()
    print("final_chrome_nochange_run_wrapper=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
