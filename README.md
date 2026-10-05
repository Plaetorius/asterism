# Asterism

**An open literature corpus for fusion science, and an MCP server that lets any AI assistant search it with
citations.** It covers every paper ever published in *Nuclear Fusion* and *Plasma Physics and Controlled Fusion*
(24,101 works, 1960 to 2026), with the full text, passages and tables of the 3,494 openly licensed ones. Every
result carries a DOI, a page and the licence.

## Quick start

You need Python 3.12 and [`uv`](https://docs.astral.sh/uv/). Download the data once (about 170 MB, checksum
verified, into `~/.asterism/`), then add the server to your AI client:

```bash
uv tool install git+https://github.com/Plaetorius/asterism   # once; needs Python 3.12 and uv
asterism-mcp download
claude mcp add asterism -- asterism-mcp mcp   # Claude Code
```

`download` also prints the snippet for Claude Desktop and Cursor (any MCP client works). Then ask, for example:
*"What H98 factor did EAST report for type-II ELMy H-mode with EC+NBI heating?"* The assistant answers with the DOI,
the page and the licence, and nothing is written to your disk except the downloaded data. The server opens the
databases read-only. Details, tools and troubleshooting: [docs/MCP.md](docs/MCP.md). Worked examples:
[docs/EXAMPLES.md](docs/EXAMPLES.md).

Update later with `uv tool upgrade asterism-mcp`. The package is not on PyPI yet.

## Does it help? (headline results)

All arms use the same model (Claude Opus 5.5). "Web search" means the assistant's built-in web search and fetch.

- **Exact facts from recent papers:** corpus 93 % vs web search 74 % (129 questions).
- **Values printed in tables:** 99 % vs 57 % (69 questions).
- **Papers public only after the model's training cutoff:** 98 % vs 48 % (124 fact questions).
- **Where it does not help:** on open-ended research questions and broad evidence gathering we found no
  significant difference. Those results are inconclusive, which is not the same as "as good as".

The studies were pre-registered and audited. Protocols, frozen inputs and results: [asterism-evals](https://github.com/Plaetorius/asterism-evals). A replication with Gemini is still running and is not cited here.

## MCP tools

| Tool | What it does |
|---|---|
| `search` | BM25 over full-text passages (`tau_E`, `τE` and `tauE` all match) |
| `get_passage` | one passage with neighbouring context |
| `paper` | metadata, licence, sections and abstract of a work |
| `search_works` | titles and abstracts of all 24,101 works, including paywalled ones |
| `count_by_year` | publication trends, with abstract and open-text coverage per period |
| `search_tables`, `get_table` | values printed in tables (reconstructed from layout; may merge adjacent columns) |

Every result has `doi`, `licence` and a ready-made `cite` string. Text from papers is returned as data with a note;
tool descriptions tell the assistant never to follow instructions found in it. Three papers licensed CC BY-NC-SA
are hidden unless you set `ASTERISM_INCLUDE_NC=1`.

## Limitations

- Two journals only. Full text exists only for the openly licensed papers, about 3,500 of 24,100, and 92 % of them
  date from 2020 or later: use `search_works` and `count_by_year` (with their coverage fields) for trends.
- Retrieval is keyword (BM25) only, with no embeddings. Tables are reconstructed from PDF layout and can be wrong:
  check values against the paper.
- One arm model per study. Question writers and judges were LLM agents, not practising researchers.
  The meta-analysis study is small (6 tasks).

## Citation and licences

Cite via [CITATION.cff](CITATION.cff). Code: MIT. The data compilation (selection, structure, cleaning, table
reconstruction): CC BY 4.0. Each article stays under its own licence, shown in its record and in `LICENSES.md`
inside the data archive; reuse requires attribution (the `cite` field). No PDFs are distributed.

## Data

The data lives on Hugging Face: [Plaetorius/asterism-fusion-corpus](https://huggingface.co/datasets/Plaetorius/asterism-fusion-corpus)
(SQLite databases, JSONL exports, datasheet). `asterism-mcp download` fetches and verifies it for you.

## Development

```bash
uv sync
uv run pytest -q && uv run ruff check .
```

Issues and take-down requests: [SECURITY.md](SECURITY.md). Changes: [CHANGELOG.md](CHANGELOG.md).
