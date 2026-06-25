#!/usr/bin/env python3
"""Regression tests for controlled-public config init wrapper."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "harness" / "scripts" / "init-controlled-public-config.sh"


def run_wrapper(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
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


def write_template(path: Path, host: str = "h3.example.com") -> Path:
    path.write_text(
        "\n".join(
            [
                f"PUBLIC_ORIGIN_HOST={host}",
                "PUBLIC_ORIGIN_PORT=443",
                f"PUBLIC_ORIGIN_URL=https://{host}/browser-slow",
                "TLS_CERT_FILE=/tmp/fullchain.pem",
                "TLS_KEY_FILE=/tmp/privkey.pem",
                "LISTEN_ADDR=0.0.0.0:443",
                "TCP_ADDR=0.0.0.0:443",
                "ALT_SVC='h3=\":443\"; ma=60'",
                "CHROME_BIN=/bin/sh",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return path


def base_env(tmp: Path, template: Path, config: Path) -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "CONTROLLED_PUBLIC_TEMPLATE": template.as_posix(),
            "CONTROLLED_PUBLIC_CONFIG": config.as_posix(),
            "CONTROLLED_PUBLIC_CONFIG_INIT_OUTPUT_DIR": (tmp / "out").as_posix(),
        }
    )
    return env


def test_missing_config_is_created_without_requiring_ready() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        template = write_template(tmp / "template.env")
        config = tmp / "controlled-public-origin.env"
        proc = run_wrapper(base_env(tmp, template, config))
        combined = proc.stdout + proc.stderr
        assert proc.returncode == 0
        assert config.exists()
        assert "init_status=created" in proc.stdout
        assert "controlled_public_config_init=needs_edit" in proc.stdout
        assert (tmp / "out" / "controlled-public-config-worksheet.md").exists()
        assert (tmp / "out" / "controlled-public-config-check.md").exists()
        assert "PRIVATE_KEY" not in combined
        assert "AKIA" not in combined


def test_existing_config_is_not_overwritten_by_default() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        template = write_template(tmp / "template.env", host="h3.example.com")
        config = tmp / "controlled-public-origin.env"
        config.write_text("PUBLIC_ORIGIN_HOST=keep.test\n", encoding="utf-8")
        proc = run_wrapper(base_env(tmp, template, config))
        assert proc.returncode == 0
        assert "init_status=exists" in proc.stdout
        assert config.read_text(encoding="utf-8") == "PUBLIC_ORIGIN_HOST=keep.test\n"


def test_overwrite_replaces_existing_config_when_explicit() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        template = write_template(tmp / "template.env", host="h3.new.test")
        config = tmp / "controlled-public-origin.env"
        config.write_text("PUBLIC_ORIGIN_HOST=old.test\n", encoding="utf-8")
        env = base_env(tmp, template, config)
        env["OVERWRITE"] = "1"
        proc = run_wrapper(env)
        assert proc.returncode == 0
        assert "init_status=overwritten" in proc.stdout
        assert "PUBLIC_ORIGIN_HOST=h3.new.test" in config.read_text(encoding="utf-8")


def test_require_baseline_ready_fails_for_placeholder_template() -> None:
    with TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        template = write_template(tmp / "template.env", host="h3.example.com")
        config = tmp / "controlled-public-origin.env"
        env = base_env(tmp, template, config)
        env["REQUIRE_BASELINE_READY"] = "1"
        proc = run_wrapper(env)
        assert proc.returncode == 1
        assert "controlled_public_config_init=blocked" in proc.stdout


def main() -> int:
    test_missing_config_is_created_without_requiring_ready()
    test_existing_config_is_not_overwritten_by_default()
    test_overwrite_replaces_existing_config_when_explicit()
    test_require_baseline_ready_fails_for_placeholder_template()
    print("init_controlled_public_config_wrapper=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
