#!/usr/bin/env python3
"""Shared UTC clock helpers for reproducible research artifacts."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_date_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()

