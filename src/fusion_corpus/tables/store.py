"""Search over the table store (tables.sqlite: FTS5 over caption, header and cells), read-only."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fusion_corpus.index.normalize import fts_query, fts_query_any

MAX_ROWS_IN_HIT = 6


def render(header: list[list[str]], rows: list[list[str]]) -> str:
    """A table as plain text: one line per row, cells separated by ' | '."""
    return "\n".join(" | ".join(c for c in r) for r in [*header, *rows])


def _con(db: Path) -> sqlite3.Connection:
    con = sqlite3.connect(f"file:{db}?mode=ro&immutable=1", uri=True)
    con.row_factory = sqlite3.Row
    return con


def search(query: str, years: tuple[int, int] | None = None, limit: int = 8, *, db: Path,
           exclude_works: frozenset[str] = frozenset()) -> list[dict]:
    """Tables matching all query terms (topped up with any-term matches), best first; each hit shows the caption,
    header and the first rows (use `table <table_id>` for all rows)."""
    con = _con(db)
    out, seen = [], set()
    for q, label in ((fts_query(query), "all terms"), (fts_query_any(query), "any term")):
        if not q or len(out) >= limit:
            continue
        sql = ("SELECT t.*, bm25(tables_fts) AS score FROM tables_fts JOIN tables t ON t.table_id = tables_fts.rowid "
               "WHERE tables_fts MATCH ?" + (" AND t.year BETWEEN ? AND ?" if years else "") +
               " ORDER BY score LIMIT ?")
        args = [q, *(years or ()), limit * 2]
        for r in con.execute(sql, args):
            if r["table_id"] in seen or len(out) >= limit or r["work_id"] in exclude_works:
                continue
            seen.add(r["table_id"])
            rows = json.loads(r["rows_json"])
            out.append({"table_id": r["table_id"], "work_id": r["work_id"], "doi": r["doi"], "title": r["title"],
                        "year": r["year"], "venue": r["venue"], "table": r["table_no"], "page": r["page"],
                        "caption": r["caption"], "match": label,
                        "preview": render(json.loads(r["header_json"]), rows[:MAX_ROWS_IN_HIT]),
                        "rows_total": len(rows)})
    return out


def get(table_id: int, *, db: Path) -> dict:
    r = _con(db).execute("SELECT * FROM tables WHERE table_id = ?", (table_id,)).fetchone()
    if r is None:
        return {"error": f"no table {table_id}"}
    return {"table_id": r["table_id"], "work_id": r["work_id"], "doi": r["doi"], "title": r["title"],
            "year": r["year"], "venue": r["venue"], "table": r["table_no"], "page": r["page"],
            "caption": r["caption"], "table_text": render(json.loads(r["header_json"]), json.loads(r["rows_json"])),
            "note": "Table reconstructed from the PDF layout; cells separated by ' | '. Exponents written as ^{…}."}
