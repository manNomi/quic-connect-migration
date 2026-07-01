#!/usr/bin/env python3
"""Shared UTC clock helpers for reproducible research artifacts."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


KST = timezone(timedelta(hours=9))


def utc_date_iso() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def kst_date_iso() -> str:
    return datetime.now(KST).date().isoformat()


def utc_kst_date_label() -> str:
    return f"{utc_date_iso()} UTC / {kst_date_iso()} KST"
