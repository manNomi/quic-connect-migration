#!/usr/bin/env python3
"""Regression tests for final handover trial packet helpers."""

from __future__ import annotations

import argparse
import csv
import tempfile
from pathlib import Path

from build_final_handover_trial_packet import build_packet, expected_artifacts, summary_filename
from check_next_final_handover_trial_readiness import DEFAULT_CHROME, DEFAULT_REQUIREMENTS, DEFAULT_SAFARI, DEFAULT_SAFARI_TP
from draft_final_handover_result_row import CSV_FIELDS


def trial(phase: str, browser: str) -> dict:
    token = browser.lower().replace(" ", "-")
    return {
        "trial_id": f"controlled-public-{token}-{phase}-001",
        "phase": phase,
        "browser": browser,
        "artifact_dir": f"artifacts/controlled-public-{token}-{phase}-001",
    }


def paths_for(item: dict) -> set[str]:
    return {artifact["path"] for artifact in expected_artifacts(item)}


def test_baseline_summary_and_chrome_netlogs_are_expected() -> None:
    item = trial("baseline", "Chrome")
    assert summary_filename(item) == "controlled-public-h3-baseline-summary.json"
    paths = paths_for(item)
    assert any(path.endswith("/results/controlled-public-h3-baseline-summary.json") for path in paths)
    assert any(path.endswith("/chrome/bootstrap-netlog.json") for path in paths)
    assert any(path.endswith("/chrome/second-netlog.json") for path in paths)


def test_chrome_active_packet_expects_path_summary_and_netlog() -> None:
    item = trial("active-network-change", "Chrome")
    assert summary_filename(item) == "controlled-public-h3-network-change-summary.json"
    paths = paths_for(item)
    assert any(path.endswith("/results/client-path-change-summary.json") for path in paths)
    assert any(path.endswith("/chrome/network-change-netlog.json") for path in paths)


def test_safari_and_android_summary_names_are_distinct() -> None:
    safari = trial("active-network-change", "Safari")
    android = trial("active-network-change", "Android Chrome")
    assert summary_filename(safari) == "safari-controlled-public-h3-network-change-summary.json"
    assert summary_filename(android) == "android-chrome-controlled-public-h3-network-change-summary.json"
    android_paths = paths_for(android)
    assert any(path.endswith("/results/android-chrome-navigation.json") for path in android_paths)
    assert any(path.endswith("/android/ip-route-*.txt") for path in android_paths)


def write_empty_experiments(path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=CSV_FIELDS)
        writer.writeheader()


def write_private_config(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                "PUBLIC_ORIGIN_HOST=h3.private-lab.test",
                "PUBLIC_ORIGIN_PORT=443",
                "PUBLIC_ORIGIN_URL=https://h3.private-lab.test/browser-slow",
                "TLS_CERT_FILE=/private/lab/fullchain.pem",
                "TLS_KEY_FILE=/private/lab/privkey.pem",
                "LISTEN_ADDR=0.0.0.0:443",
                "TCP_ADDR=0.0.0.0:443",
                "ALT_SVC='h3=\":443\"; ma=60'",
                "NETWORK_CHANGE_CMD='printf path-change'",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def packet_args(experiments: Path, config: Path, redact_sensitive: bool) -> argparse.Namespace:
    return argparse.Namespace(
        experiments=experiments.as_posix(),
        requirements=DEFAULT_REQUIREMENTS,
        config=config.as_posix(),
        use_local_config=True,
        repetitions=3,
        prefer_p1="safari",
        chrome_bin=DEFAULT_CHROME,
        safari_bin=DEFAULT_SAFARI,
        safari_tp_bin=DEFAULT_SAFARI_TP,
        min_disk_gib=0.0,
        check_local_files=False,
        check_public_origin=False,
        timeout=1,
        redact_sensitive=redact_sensitive,
    )


def test_redacted_local_config_packet_does_not_leak_private_commands() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        experiments = tmp_path / "experiments.csv"
        config = tmp_path / "controlled-public-origin.env"
        write_empty_experiments(experiments)
        write_private_config(config)

        packet = build_packet(packet_args(experiments, config, redact_sensitive=True))

    combined = "\n".join([packet["server_command"], packet["client_command"], "\n".join(packet["preflight_commands"])])
    assert packet["public_safe_default"] is True
    assert packet["redact_sensitive"] is True
    assert "h3.private-lab.test" not in combined
    assert "/private/lab" not in combined
    assert "printf path-change" not in combined
    assert "--redact-sensitive" in combined
    assert "<redacted-public-origin-url>" in combined


def main() -> int:
    test_baseline_summary_and_chrome_netlogs_are_expected()
    test_chrome_active_packet_expects_path_summary_and_netlog()
    test_safari_and_android_summary_names_are_distinct()
    test_redacted_local_config_packet_does_not_leak_private_commands()
    print("build_final_handover_trial_packet=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
