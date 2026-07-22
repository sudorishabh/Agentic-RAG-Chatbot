"""Shared DAO helpers for the catalog package.

Small pieces every catalog module would otherwise duplicate: the current UTC
timestamp, and the whitelisted-identifier guard for the two configurable table
names (a bad ``ingest_state_table``/``ingest_log_table`` setting must not become
a SQL-injection vector via f-string interpolation).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.config import get_settings


def now() -> datetime:
    return datetime.now(timezone.utc)


def safe_table(name: str, default: str) -> str:
    return name if name.replace("_", "").isalnum() else default


def state_table() -> str:
    return safe_table(get_settings().ingest_state_table, "documents")


def log_table() -> str:
    return safe_table(get_settings().ingest_log_table, "ingest_log")
