"""Licence and citation fields attached to every result, and the NonCommercial switch."""

from __future__ import annotations

import json
import re
import sqlite3

NC_MARK = "/by-nc"
_CC = re.compile(r"creativecommons\.org/licenses/([a-z-]+)/(\d\.\d)", re.IGNORECASE)
NC_FILTER = ("NOT EXISTS (SELECT 1 FROM copies nc WHERE nc.copy_id = t.copy_id "
             f"AND nc.licence_url LIKE '%{NC_MARK}%')")


def licence_label(url: str | None) -> str | None:
    """'http://creativecommons.org/licenses/by/4.0/' → 'CC BY 4.0'; other URLs are returned unchanged."""
    if not url:
        return None
    m = _CC.search(url)
    return f"CC {m.group(1).upper()} {m.group(2)}" if m else url


def is_nc(url: str | None) -> bool:
    return bool(url) and NC_MARK in url.lower()


def work_licence(conn: sqlite3.Connection, work_id: str) -> str | None:
    """Licence URL of the text we serve: the canonical copy's, else the first copy's, else the work's own."""
    row = conn.execute("SELECT licence_url FROM copies WHERE work_id=? ORDER BY canonical DESC LIMIT 1",
                       (work_id,)).fetchone()
    if row:
        return row[0]
    work = conn.execute("SELECT licences_json FROM works WHERE work_id=?", (work_id,)).fetchone()
    for entry in json.loads(work[0]) if work and work[0] else []:
        if entry.get("url"):
            return entry["url"]
    return None


def nc_work_ids(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute(
        f"SELECT DISTINCT work_id FROM copies WHERE licence_url LIKE '%{NC_MARK}%'")}


def _authors(authors_json: str | None) -> str:
    names = [a.get("family") or a.get("name") or "" for a in json.loads(authors_json or "[]")]
    names = [n for n in names if n]
    return ", ".join(names[:3]) + (" et al." if len(names) > 3 else "")


def cite(conn: sqlite3.Connection, work_id: str, licence_url: str | None) -> str | None:
    w = conn.execute("SELECT doi, title, venue, year, authors_json FROM works WHERE work_id=?",
                     (work_id,)).fetchone()
    if w is None:
        return None
    parts = [_authors(w["authors_json"]), w["title"], f"{w['venue'] or ''} {w['year'] or ''}".strip(),
             f"doi:{w['doi']}" if w["doi"] else None, licence_label(licence_url)]
    return ", ".join(p for p in parts if p)


def annotate(conn: sqlite3.Connection, row: dict, licence_url: str | None = None) -> dict:
    """Add `licence`, `licence_url` and `cite` to a result dict that has a `work_id`."""
    url = licence_url or work_licence(conn, row["work_id"])
    return {**row, "licence": licence_label(url), "licence_url": url, "cite": cite(conn, row["work_id"], url)}
