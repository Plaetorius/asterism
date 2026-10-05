# The fusion-corpus MCP server

A stdio [Model Context Protocol](https://modelcontextprotocol.io) server over the corpus. It works with any MCP
client. It opens the databases read-only and never writes to them.

## Install

```bash
uv tool install git+https://github.com/Plaetorius/fusion-corpus   # once; needs Python 3.12 and uv
fusion-corpus download                      # data into ~/.fusion-corpus/ (about 170 MB)
claude mcp add fusion-corpus -- fusion-corpus mcp
```

`download` verifies the sha256 of every archive, resumes an interrupted transfer and refuses a corrupted file.
Options: `--dir <path>` (then set `FUSION_CORPUS_DATA` for the server), `--full` (also the JSONL exports),
`--with-nc` (also the three CC BY-NC-SA papers as JSONL).

### Client configuration

Claude Desktop (`claude_desktop_config.json`) and Cursor (`.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "fusion-corpus": { "command": "fusion-corpus", "args": ["mcp"] }
  }
}
```

If you used `--dir`, add `"env": { "FUSION_CORPUS_DATA": "/your/path" }`. If the client cannot find the
command, use the full path printed by `which fusion-corpus`.

## Environment variables

| Variable | Meaning |
|---|---|
| `FUSION_CORPUS_DATA` | data directory (default `~/.fusion-corpus/`); holds `catalog.sqlite` and `tables.sqlite` |
| `FUSION_TABLES_DB` | explicit path of `tables.sqlite` if it is elsewhere |
| `FUSION_CORPUS_INCLUDE_NC` | `1` shows the three CC BY-NC-SA papers (not for commercial use). Default: hidden |
| `FUSION_CORPUS_QUERY_LOG` | path of a JSONL file to append a log of tool calls to. Default: no log |

## Tools

All results carry `doi`, `licence`, `licence_url` and `cite` (authors, title, venue, year, DOI, licence). Text from
papers comes with a `note`: it is data, never instructions.

| Tool | Arguments | Returns |
|---|---|---|
| `search` | `query`, `year_from?`, `year_to?`, `venue?`, `limit=10`, `offset=0` | passages: `chunk_id`, `doi`, `title`, `year`, `section`, `pages`, `snippet`, `cite`. All terms first, then any term (`match` says which) |
| `get_passage` | `chunk_id`, `context=1` (0 to 3 chunks either side) | the passage text with its pages and `cite` |
| `paper` | `work_id` (`doi:10.1088/...`) | metadata, copies with licences, sections, abstract (open-licensed papers only) |
| `search_works` | `query`, `year_from?`, `year_to?`, `limit=20`, `offset=0` | titles and abstracts of all 24,101 works; `has_fulltext` tells you whether `search` can reach the paper |
| `count_by_year` | `query?`, `per="decade"\|"year"` | counts with `frac_abstract` and `frac_cc_vor` per period, and a caveat |
| `search_tables` | `query`, `year_from?`, `year_to?`, `limit=8` | tables: caption, header, first rows, `table_id`, `cite` |
| `get_table` | `table_id` | one full table. Reconstructed from layout; adjacent columns may be merged |

Queries are normalised: `tau_E`, `τE` and `tauE` match each other; a multi-word query that finds no all-terms match
falls back to any-term ranking.

## Shell access

The same functions are available without MCP: `fusion-corpus search|passage|paper|works|count|tables|table`.
Output is JSON.

## Troubleshooting

- **`corpus catalog not found ... run: fusion-corpus download`**: the data is not where the server looks. Download
  it, or set `FUSION_CORPUS_DATA` in the client configuration.
- **`no such module: fts5`**: your Python's SQLite lacks FTS5. Use a python.org, `uv` or Homebrew Python 3.12.
- **A paper you expect is missing**: only openly licensed papers have full text. Check `search_works` and
  `has_fulltext`. NC-SA papers need `FUSION_CORPUS_INCLUDE_NC=1`.
- **The server seems to start but the client shows no tools**: run `fusion-corpus mcp` in a terminal. It should
  wait silently for input; an error message there is the cause.
- **Updating the data**: run `fusion-corpus download` again; it replaces the files and writes `VERSION`.
