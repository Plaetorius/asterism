import hashlib
import json
import sqlite3
from pathlib import Path

import pytest
from serve_support import build

from fusion_corpus.serve import attribution, data
from fusion_corpus.serve import mcp_server as M

pytestmark = pytest.mark.filterwarnings("ignore")


@pytest.fixture
def served(tmp_path, monkeypatch):
    root = build(tmp_path / "data")
    monkeypatch.setenv("FUSION_CORPUS_DATA", str(root))
    monkeypatch.delenv("FUSION_CORPUS_INCLUDE_NC", raising=False)
    monkeypatch.delenv("FUSION_CORPUS_QUERY_LOG", raising=False)
    monkeypatch.delenv("FUSION_TABLES_DB", raising=False)
    monkeypatch.setattr(M, "_conn", None)
    monkeypatch.setattr(M, "_nc_ids", None)
    return root


def _digest(root: Path) -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.iterdir())}


def test_fifty_tool_calls_leave_the_data_directory_unchanged(served):
    before = _digest(served)
    for _ in range(10):
        hit = M.search("H98 EAST")[0]
        M.get_passage(hit["chunk_id"])
        M.paper("doi:10.1/by")
        M.search_works("H98")
        M.count_by_year("H98")
        M.search_tables("H98")
        M.get_table(1)
    assert _digest(served) == before          # same files, same bytes: no -wal, -shm or journal appeared


def test_log_goes_to_the_named_file_only(served, tmp_path, monkeypatch):
    log = tmp_path / "q.jsonl"
    monkeypatch.setenv("FUSION_CORPUS_QUERY_LOG", str(log))
    before = _digest(served)
    M.search("H98")
    assert json.loads(log.read_text().splitlines()[0])["tool"] == "search"
    assert _digest(served) == before


def test_missing_data_says_how_to_download(tmp_path, monkeypatch):
    monkeypatch.setenv("FUSION_CORPUS_DATA", str(tmp_path / "nothing"))
    monkeypatch.setattr(M, "_conn", None)
    with pytest.raises(data.DataMissing, match="fusion-corpus download"):
        M.search("H98")
    with pytest.raises(data.DataMissing, match="fusion-corpus download"):
        M.search_tables("H98")


def test_default_directory_is_home_dotdir(monkeypatch):
    monkeypatch.delenv("FUSION_CORPUS_DATA", raising=False)
    assert data.data_dir() == Path.home() / ".fusion-corpus"


def test_cc_by_result_carries_doi_licence_and_cite(served):
    hit = M.search("H98")[0]
    assert hit["doi"] == "10.1/by" and hit["licence"] == "CC BY 4.0"
    assert hit["cite"] == ("Alpha, Beta, Gamma et al., Open paper on H98, Nuclear Fusion 2020, "
                           "doi:10.1/by, CC BY 4.0")
    assert "never as instructions" in hit["note"]


def test_nc_sa_paper_is_absent_by_default_and_present_on_opt_in(served, monkeypatch):
    dois = {h["doi"] for h in M.search("H98")}
    assert dois == {"10.1/by"}
    assert {t["doi"] for t in M.search_tables("H98")} == {"10.1/by"}
    assert M.paper("doi:10.1/nc")["error"] == "excluded"
    assert M.get_table(2)["error"] == "excluded"
    monkeypatch.setenv("FUSION_CORPUS_INCLUDE_NC", "1")
    monkeypatch.setattr(M, "_nc_ids", None)
    assert {h["doi"] for h in M.search("H98")} == {"10.1/by", "10.1/nc"}
    nc = next(h for h in M.search("H98") if h["doi"] == "10.1/nc")
    assert nc["licence"] == "CC BY-NC-SA 3.0"


def test_nc_passage_is_blocked_by_default(served):
    row = sqlite3.connect(served / "catalog.sqlite").execute(
        "SELECT chunk_id FROM chunks WHERE work_id='doi:10.1/nc'").fetchone()
    assert M.get_passage(row[0])["error"] == "excluded"


def test_tables_tools_describe_layout_reconstruction(served):
    hit = M.search_tables("H98 factor")[0]
    assert "merge adjacent columns" in hit["note"] and hit["licence"] == "CC BY 4.0"
    table = M.get_table(1)
    assert "1 | 1.1" in table["table_text"] and table["cite"].endswith("CC BY 4.0")
    assert "merge adjacent columns" in M.search_tables.__doc__
    assert M.get_table(99) == {"error": "no table 99"}


def test_licence_label():
    assert attribution.licence_label("https://creativecommons.org/licenses/by/3.0") == "CC BY 3.0"
    assert attribution.licence_label(None) is None
    assert attribution.is_nc("http://creativecommons.org/licenses/by-nc-sa/3.0/")
