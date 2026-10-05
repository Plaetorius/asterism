"""Counts from the M layer, always with their coverage (D6, PLAN §8 `count_by_year` / `coverage`).

Per year: n works, n research works, and — over the *research* works of that year — the fraction with an
abstract (any source, and Crossref alone), with a deposited reference list, and with an active CC licence on
the VoR. A fraction is None when the year has no research work, never a silent 0.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime

from asterism_mcp.metadata import licence as lic

DECADE = 10


@dataclass(frozen=True)
class YearCoverage:
    year: int
    n: int
    n_research: int
    n_abstract: int  # research works with an abstract (any source)
    n_abstract_crossref: int  # research works whose abstract came from Crossref
    n_refs: int  # research works with ≥ 1 deposited reference
    n_cc_vor: int  # research works with an active CC licence on the VoR

    def _frac(self, k: int) -> float | None:
        return k / self.n_research if self.n_research else None

    @property
    def frac_abstract(self) -> float | None:
        return self._frac(self.n_abstract)

    @property
    def frac_abstract_crossref(self) -> float | None:
        return self._frac(self.n_abstract_crossref)

    @property
    def frac_refs(self) -> float | None:
        return self._frac(self.n_refs)

    @property
    def frac_cc_vor(self) -> float | None:
        return self._frac(self.n_cc_vor)


def fts_query(text: str) -> str:
    """Plain words → an FTS5 AND of quoted terms (so '-', ':' or '(' in user text can't break the syntax).
    A query already using FTS syntax (quotes, AND/OR/NOT, NEAR, *) is passed through unchanged."""
    if re.search(r'["*]|\b(AND|OR|NOT|NEAR)\b', text):
        return text
    terms = [t for t in re.split(r"\s+", text.strip()) if t]
    return " ".join('"' + t.replace('"', '""') + '"' for t in terms)


def _rows(conn: sqlite3.Connection, query: str | None, venue: str | None) -> list[sqlite3.Row]:
    where, params = ["w.year IS NOT NULL"], []
    if venue:
        where.append("(w.venue = ? OR w.issn = ?)")
        params += [venue, venue]
    if query:
        where.append("w.rowid IN (SELECT rowid FROM works_fts WHERE works_fts MATCH ?)")
        params.append(fts_query(query))
    sql = f"""
        SELECT w.year, w.is_research, w.abstract IS NOT NULL AS has_abstract, w.abstract_src, w.licences_json,
               EXISTS (SELECT 1 FROM citations c WHERE c.citing_work_id = w.work_id) AS has_refs
        FROM works w WHERE {' AND '.join(where)}
    """
    return conn.execute(sql, params).fetchall()


def count_by_year(conn: sqlite3.Connection, query: str | None = None, venue: str | None = None,
                  today: date | None = None) -> list[YearCoverage]:
    """Per-year counts and coverage, optionally restricted to a title+abstract FTS query and a venue
    (name or key ISSN). Years with no matching work are omitted."""
    today = today or datetime.now(UTC).date()
    acc: dict[int, list[int]] = defaultdict(lambda: [0] * 6)
    for r in _rows(conn, query, venue):
        a = acc[r["year"]]
        a[0] += 1
        if not r["is_research"]:
            continue
        a[1] += 1
        a[2] += bool(r["has_abstract"])
        a[3] += r["abstract_src"] == "crossref"
        a[4] += bool(r["has_refs"])
        licences = lic.from_json(json.loads(r["licences_json"] or "[]"))
        a[5] += lic.cc_on_version(licences, "vor", today) is not None
    return [YearCoverage(y, *acc[y]) for y in sorted(acc)]


def by_decade(years: list[YearCoverage]) -> list[YearCoverage]:
    """Sum yearly rows into decades (the `year` field holds the decade start)."""
    acc: dict[int, list[int]] = defaultdict(lambda: [0] * 6)
    for y in years:
        a = acc[y.year - y.year % DECADE]
        for i, v in enumerate((y.n, y.n_research, y.n_abstract, y.n_abstract_crossref, y.n_refs, y.n_cc_vor)):
            a[i] += v
    return [YearCoverage(d, *acc[d]) for d in sorted(acc)]
