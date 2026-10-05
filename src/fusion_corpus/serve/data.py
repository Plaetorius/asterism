"""Where the served data lives, and what to say when it is missing.

Order: `FUSION_CORPUS_DATA`, then `~/.fusion-corpus/`. The directory holds `catalog.sqlite` and `tables.sqlite`
(written by `fusion-corpus download`). Nothing here creates or writes anything.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DIR = Path.home() / ".fusion-corpus"
MISSING_HINT = "run: fusion-corpus download"


class DataMissing(RuntimeError):
    pass


def data_dir() -> Path:
    return Path(os.environ.get("FUSION_CORPUS_DATA") or DEFAULT_DIR)


def _require(path: Path, what: str) -> Path:
    if not path.is_file():
        raise DataMissing(f"{what} not found at {path}. {MISSING_HINT}")
    return path


def catalog_path() -> Path:
    return _require(data_dir() / "catalog.sqlite", "corpus catalog")


def tables_path() -> Path:
    explicit = os.environ.get("FUSION_TABLES_DB")
    if explicit:
        return _require(Path(explicit), "tables database")
    base = data_dir()
    nested = base / "tables" / "tables.sqlite"
    return _require(nested if nested.is_file() else base / "tables.sqlite", "tables database")


def include_nc() -> bool:
    """CC BY-NC-SA papers are hidden unless the user opts in."""
    return os.environ.get("FUSION_CORPUS_INCLUDE_NC") == "1"
