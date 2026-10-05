"""Opening the served catalog."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def connect_readonly(path: Path | str) -> sqlite3.Connection:
    """Open an existing catalog strictly read-only: no schema script, no WAL, no writes."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"catalog {p} does not exist")
    conn = sqlite3.connect(f"file:{p}?mode=ro&immutable=1", uri=True)
    conn.row_factory = sqlite3.Row
    return conn
