"""A tiny served data directory: one CC BY paper, one CC BY-NC-SA paper, and a tables database."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fusion_corpus.index.normalize import normalise

BY, NC = "http://creativecommons.org/licenses/by/4.0/", "http://creativecommons.org/licenses/by-nc-sa/3.0/"
SENT = "The H98 factor of the EAST type-II ELMy H-mode reached 1.1 with EC and NBI heating. "
AUTHORS = json.dumps([{"given": n, "family": f, "sequence": "additional"}
                      for n, f in (("A.", "Alpha"), ("B.", "Beta"), ("C.", "Gamma"), ("D.", "Delta"))])
WORKS = (("doi:10.1/by", "10.1/by", "Open paper on H98", BY, "cby"),
         ("doi:10.1/nc", "10.1/nc", "Noncommercial paper on H98", NC, "cnc"))


SCHEMA = """
CREATE TABLE works (work_id TEXT PRIMARY KEY, doi TEXT UNIQUE, title TEXT NOT NULL, abstract TEXT, venue TEXT,
    volume TEXT, issue TEXT, issn TEXT, published TEXT, year INTEGER, is_research INTEGER NOT NULL DEFAULT 1,
    authors_json TEXT NOT NULL DEFAULT '[]', licences_json TEXT NOT NULL DEFAULT '[]', abstract_src TEXT,
    abstract_licence TEXT);
CREATE VIRTUAL TABLE works_fts USING fts5(title, abstract, content='works', content_rowid='rowid');
CREATE TRIGGER works_fts_ai AFTER INSERT ON works BEGIN
    INSERT INTO works_fts(rowid, title, abstract) VALUES (new.rowid, new.title, new.abstract);
END;
CREATE TABLE citations (citing_work_id TEXT NOT NULL, cited_doi TEXT, cited_key TEXT NOT NULL);
CREATE TABLE copies (copy_id TEXT PRIMARY KEY, work_id TEXT NOT NULL, content_version TEXT NOT NULL, pages INTEGER,
    licence_url TEXT NOT NULL, copy_class TEXT NOT NULL, sharing TEXT NOT NULL, acquisition_route TEXT NOT NULL,
    canonical INTEGER NOT NULL DEFAULT 0);
CREATE TABLE text_layers (layer_id TEXT PRIMARY KEY, copy_id TEXT NOT NULL, stats_json TEXT NOT NULL,
    current INTEGER NOT NULL DEFAULT 1);
CREATE TABLE chunks (chunk_id INTEGER PRIMARY KEY AUTOINCREMENT, layer_id TEXT NOT NULL, work_id TEXT NOT NULL,
    seq INTEGER NOT NULL, section TEXT, page_start INTEGER NOT NULL, page_end INTEGER NOT NULL,
    char_start INTEGER NOT NULL, char_end INTEGER NOT NULL, text TEXT NOT NULL, norm_text TEXT NOT NULL);
CREATE VIRTUAL TABLE chunks_fts USING fts5(norm_text, content='chunks', content_rowid='chunk_id');
"""


def build(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(root / "catalog.sqlite")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    for work_id, doi, title, lic, copy_id in WORKS:
        conn.execute("INSERT INTO works (work_id, doi, title, abstract, venue, year, authors_json) "
                     "VALUES (?,?,?,?,?,?,?)",
                     (work_id, doi, title, f"{title} abstract", "Nuclear Fusion", 2020, AUTHORS))
        conn.execute("INSERT INTO copies VALUES (?,?, 'vor',1,?, 'A','shareable_fulltext','manual',1)",
                     (copy_id, work_id, lic))
        layer = f"{copy_id}:t"
        conn.execute("INSERT INTO text_layers VALUES (?,?,'{}',1)", (layer, copy_id))
        body = SENT * 3
        cur = conn.execute("INSERT INTO chunks (layer_id, work_id, seq, section, page_start, page_end, char_start, "
                           "char_end, text, norm_text) VALUES (?,?,0,'Results',1,1,0,?,?,?)",
                           (layer, work_id, len(body), body, normalise(body)))
        conn.execute("INSERT INTO chunks_fts (rowid, norm_text) VALUES (?,?)", (cur.lastrowid, normalise(body)))
    conn.commit()
    conn.close()
    _tables(root / "tables.sqlite")
    return root


def _tables(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript("""
        CREATE TABLE tables (table_id INTEGER PRIMARY KEY, work_id TEXT, doi TEXT, title TEXT, year INTEGER,
                             venue TEXT, table_no INTEGER, page INTEGER, caption TEXT, header_json TEXT,
                             rows_json TEXT, n_rows INTEGER, n_cols INTEGER, text TEXT);
        CREATE VIRTUAL TABLE tables_fts USING fts5(norm, content='');
    """)
    for i, (work_id, doi, title, _, _) in enumerate(WORKS, 1):
        header, rows = [["Shot", "H98"]], [["1", "1.1"], ["2", "1.2"]]
        con.execute("INSERT INTO tables VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (i, work_id, doi, title, 2020, "Nuclear Fusion", 1, 3, "H98 factor per shot",
                     json.dumps(header), json.dumps(rows), 2, 2, "H98"))
        con.execute("INSERT INTO tables_fts (rowid, norm) VALUES (?, ?)", (i, normalise("H98 factor per shot")))
    con.commit()
    con.close()
