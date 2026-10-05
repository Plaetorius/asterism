# Changelog

## v1.0.0

First public release (2026-10-05).

- Corpus: 24,101 works from *Nuclear Fusion* and *Plasma Physics and Controlled Fusion* (1960 to 2026); full text,
  165,951 passages and 3,893 reconstructed tables for 3,494 openly licensed articles. No PDFs.
- MCP server (`asterism-mcp mcp`): `search`, `get_passage`, `paper`, `search_works`, `count_by_year`,
  `search_tables`, `get_table`. Read-only; every result carries DOI, licence and a citation string; CC BY-NC-SA
  papers hidden unless `ASTERISM_INCLUDE_NC=1`.
- `asterism-mcp download`: pinned, checksum-verified, resumable data download with client configuration.
- Slim install: core dependencies are `mcp`, `pydantic` and `zstandard`; `build` and `eval` extras for the rest.
- Pre-registered studies live in the separate asterism-evals repository.
