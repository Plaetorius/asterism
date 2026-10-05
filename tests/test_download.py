import hashlib
import io
import tarfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import zstandard

from asterism_mcp.release import download as D


def _archive(files: dict[str, bytes], extra: list[tarfile.TarInfo] | None = None) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tar:
        for name, body in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(body)
            tar.addfile(info, io.BytesIO(body))
        for info in extra or []:
            tar.addfile(info)
    return zstandard.ZstdCompressor().compress(buf.getvalue())


class Server:
    """Serves one blob with Range support; `cut_first` makes the first full response stop halfway."""

    def __init__(self, blob: bytes, cut_first: bool = False):
        outer = self
        self.cut_first, self.requests = cut_first, []

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                rng = self.headers.get("Range")
                start = int(rng.split("=")[1].rstrip("-")) if rng else 0
                outer.requests.append(start)
                body = blob[start:]
                self.send_response(206 if rng else 200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                if outer.cut_first and start == 0:
                    outer.cut_first = False
                    self.wfile.write(body[: len(body) // 2])
                    self.wfile.flush()
                    self.connection.close()
                    return
                self.wfile.write(body)

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}/fusion-corpus-db-v1.0.0.tar.zst"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self):
        self.httpd.shutdown()


def _sources(url: str, blob: bytes, sha: str | None = None) -> dict:
    spec = {"url": url, "size": len(blob), "sha256": sha or hashlib.sha256(blob).hexdigest()}
    return {"version": "v1.0.0", "archives": {"db": spec}}


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(D, "BACKOFF_SECONDS", 0)


def test_good_download_unpacks_and_writes_version(tmp_path):
    blob = _archive({"catalog.sqlite": b"cat", "tables.sqlite": b"tab"})
    srv = Server(blob)
    try:
        names = D.run(tmp_path / "d", _sources(srv.url, blob))
    finally:
        srv.close()
    assert sorted(names) == ["catalog.sqlite", "tables.sqlite"]
    assert (tmp_path / "d" / "catalog.sqlite").read_bytes() == b"cat"
    assert (tmp_path / "d" / "VERSION").read_text() == "v1.0.0\n"
    assert not list((tmp_path / "d").glob("*.zst*"))


def test_corrupted_download_is_refused_and_removed(tmp_path):
    blob = _archive({"catalog.sqlite": b"cat"})
    srv = Server(blob)
    try:
        with pytest.raises(D.DownloadError, match="checksum mismatch"):
            D.run(tmp_path / "d", _sources(srv.url, blob, sha="0" * 64))
    finally:
        srv.close()
    assert not (tmp_path / "d" / "catalog.sqlite").exists()
    assert not list((tmp_path / "d").glob("*.zst*")) and not (tmp_path / "d" / "VERSION").exists()


def test_interrupted_download_resumes_with_a_range_request(tmp_path):
    blob = _archive({"catalog.sqlite": b"x" * 200_000})
    srv = Server(blob, cut_first=True)
    try:
        D.run(tmp_path / "d", _sources(srv.url, blob))
    finally:
        srv.close()
    assert (tmp_path / "d" / "catalog.sqlite").read_bytes() == b"x" * 200_000
    assert srv.requests[0] == 0 and srv.requests[-1] > 0


def test_unpack_refuses_path_traversal(tmp_path):
    blob = _archive({"../evil.txt": b"no"})
    archive = tmp_path / "a.tar.zst"
    archive.write_bytes(blob)
    with pytest.raises(D.DownloadError, match="unsafe"):
        D.unpack(archive, tmp_path / "d")
    assert not (tmp_path / "evil.txt").exists()


def test_unpublished_data_is_reported(tmp_path):
    with pytest.raises(D.DownloadError, match="not published"):
        D.run(tmp_path / "d", {"version": "v1", "archives": {"db": {"url": "", "size": 0, "sha256": ""}}})


def test_selection_and_config_snippets(tmp_path):
    assert D.selected({}, False, False) == ["db"]
    assert D.selected({}, True, True) == ["db", "jsonl", "nc-sa"]
    text = D.client_config(tmp_path)
    assert "claude mcp add asterism" in text and "mcpServers" in text and str(tmp_path) in text
