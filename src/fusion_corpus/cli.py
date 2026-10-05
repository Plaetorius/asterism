"""`fusion-corpus` command: start the MCP server, download the data, or query from the shell.

  fusion-corpus mcp                       start the stdio MCP server
  fusion-corpus download [--full] [--with-nc] [--dir D]
  fusion-corpus search|passage|paper|works|count|tables|table ...    (see `fusion-corpus search --help`)
"""

from __future__ import annotations

import sys

QUERY_COMMANDS = {"search", "passage", "paper", "works", "count", "tables", "table"}


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    cmd = args[0] if args else ""
    if cmd == "mcp":
        from fusion_corpus.serve.mcp_server import server
        server.run("stdio")
    elif cmd == "download":
        from fusion_corpus.release import download
        raise SystemExit(download.main(args[1:]))
    elif cmd in QUERY_COMMANDS:
        from fusion_corpus.serve import cli
        sys.argv = ["fusion-corpus", *args]
        cli._safe_main()
    else:
        print(__doc__.strip())
        raise SystemExit(0 if cmd in ("-h", "--help") else 2)
