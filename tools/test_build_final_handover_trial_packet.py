#!/usr/bin/env python3
"""Regression tests for final handover trial packet helpers."""

from __future__ import annotations

from build_final_handover_trial_packet import expected_artifacts, summary_filename


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


def main() -> int:
    test_baseline_summary_and_chrome_netlogs_are_expected()
    test_chrome_active_packet_expects_path_summary_and_netlog()
    test_safari_and_android_summary_names_are_distinct()
    print("build_final_handover_trial_packet=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
