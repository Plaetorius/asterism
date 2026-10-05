"""`fusion-corpus download`: fetch the data archives, verify their checksums, unpack to ~/.fusion-corpus/.

URLs, sizes and sha256 are pinned in `sources.json` (or passed with `--sources`). Downloads resume after an
interruption, retry on network errors, and are refused on a checksum mismatch. Nothing outside the target
directory is written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tarfile
import time
import urllib.error
import urllib.request
from pathlib import Path

import zstandard

from fusion_corpus.serve import data

SOURCES = Path(__file__).with_name("sources.json")
CHUNK = 1 << 20
RETRIES = 4
BACKOFF_SECONDS = 1.0


class DownloadError(RuntimeError):
    pass


def load_sources(location: str | None = None) -> dict:
    text = (Path(location) if location and "://" not in location else None)
    if text is not None:
        return json.loads(text.read_text())
    if location:
        with urllib.request.urlopen(location, timeout=30) as r:
            return json.loads(r.read())
    return json.loads(SOURCES.read_text())


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while block := f.read(CHUNK):
            h.update(block)
    return h.hexdigest()


def _progress(done: int, total: int, label: str) -> None:
    pct = f"{100 * done / total:5.1f}%" if total else "  ?  "
    print(f"\r{label}: {done / 1e6:8.1f} MB {pct}", end="", file=sys.stderr, flush=True)


def fetch(url: str, dest: Path, size: int, label: str) -> None:
    """Download `url` to `dest` + '.part' (resuming from its current length), then rename on completion."""
    part = dest.with_name(dest.name + ".part")
    last: Exception | None = None
    for attempt in range(RETRIES):
        have = part.stat().st_size if part.exists() else 0
        if size and have >= size:
            break
        req = urllib.request.Request(url, headers={"Range": f"bytes={have}-"} if have else {})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                if have and r.status != 206:      # server ignored the range: start over
                    have = 0
                with open(part, "ab" if have else "wb") as f:
                    while block := r.read(CHUNK):
                        f.write(block)
                        have += len(block)
                        _progress(have, size, label)
        except (urllib.error.URLError, OSError, ConnectionError) as exc:
            last = exc
            time.sleep(BACKOFF_SECONDS * (attempt + 1))
            continue
        if not size or have >= size:
            break
    else:
        raise DownloadError(f"{label}: download failed after {RETRIES} attempts ({last})")
    print(file=sys.stderr)
    part.replace(dest)


def verify(path: Path, sha256: str, label: str) -> None:
    got = sha256_of(path)
    if got != sha256:
        path.unlink(missing_ok=True)
        raise DownloadError(f"{label}: checksum mismatch (expected {sha256[:12]}…, got {got[:12]}…); file removed")


def unpack(archive: Path, target: Path) -> list[str]:
    """Extract a .tar.zst, refusing anything but plain files and directories inside `target`."""
    names: list[str] = []
    root = target.resolve()
    with open(archive, "rb") as raw, zstandard.ZstdDecompressor().stream_reader(raw) as stream, \
            tarfile.open(fileobj=stream, mode="r|") as tar:
        for member in tar:
            dest = (target / member.name).resolve()
            if not (member.isfile() or member.isdir()) or root not in (dest, *dest.parents):
                raise DownloadError(f"unsafe archive member {member.name!r}")
            tar.extract(member, target, filter="data")
            if member.isfile():
                names.append(member.name)
    return names


def selected(sources: dict, full: bool, with_nc: bool) -> list[str]:
    return ["db", *(["jsonl"] if full else []), *(["nc-sa"] if with_nc else [])]


def run(target: Path, sources: dict, full: bool = False, with_nc: bool = False) -> list[str]:
    target.mkdir(parents=True, exist_ok=True)
    unpacked: list[str] = []
    for key in selected(sources, full, with_nc):
        spec = sources["archives"][key]
        if not spec.get("url"):
            raise DownloadError(f"{key}: no download URL is pinned yet in sources.json (data not published)")
        archive = target / Path(spec["url"]).name
        fetch(spec["url"], archive, spec["size"], key)
        verify(archive, spec["sha256"], key)
        unpacked += unpack(archive, target)
        archive.unlink()
    (target / "VERSION").write_text(sources["version"] + "\n")
    return unpacked


def client_config(target: Path) -> str:
    env = {} if target == data.DEFAULT_DIR else {"FUSION_CORPUS_DATA": str(target)}
    server = {"command": "fusion-corpus", "args": ["mcp"], **({"env": env} if env else {})}
    add_env = "".join(f" -e FUSION_CORPUS_DATA={target}" for _ in env)
    return "\n".join([
        "Data ready. Add the server to your AI client:", "",
        "Claude Code:", f"  claude mcp add fusion-corpus{add_env} -- fusion-corpus mcp", "",
        "Claude Desktop (claude_desktop_config.json) and Cursor (.cursor/mcp.json):",
        json.dumps({"mcpServers": {"fusion-corpus": server}}, indent=2)])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="fusion-corpus download", description=__doc__.split("\n\n")[0])
    ap.add_argument("--dir", type=Path, default=data.data_dir(), help="target directory (default ~/.fusion-corpus)")
    ap.add_argument("--full", action="store_true", help="also fetch the JSONL exports")
    ap.add_argument("--with-nc", action="store_true", help="also fetch the 3 CC BY-NC-SA papers")
    ap.add_argument("--sources", help="alternative sources.json (path or URL)")
    a = ap.parse_args(argv)
    try:
        run(a.dir, load_sources(a.sources), a.full, a.with_nc)
    except DownloadError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(client_config(a.dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
