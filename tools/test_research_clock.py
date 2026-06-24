#!/usr/bin/env python3
"""Regression tests for shared research artifact clock helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from research_clock import utc_date_iso


def test_utc_date_iso_uses_utc_day() -> None:
    assert utc_date_iso() == datetime.now(timezone.utc).date().isoformat()


def main() -> int:
    test_utc_date_iso_uses_utc_day()
    print("research_clock=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
