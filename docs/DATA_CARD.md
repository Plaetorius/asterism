---
license: cc-by-4.0
language:
- en
pretty_name: fusion-corpus (Nuclear Fusion and PPCF)
size_categories:
- 100K<n<1M
task_categories:
- question-answering
- text-retrieval
tags:
- fusion
- plasma-physics
- scientific-literature
- rag
- mcp
---

# fusion-corpus v1.0.0

A searchable, citable corpus of the fusion-plasma literature: **24,101 works** from *Nuclear Fusion* and *Plasma
Physics and Controlled Fusion* (1960 to 2026), with **full text, 165,951 passages and 3,893 reconstructed tables**
for the **3,494 articles** that carry a Creative Commons licence on the version of record. Every record traces to a
DOI. No PDFs are distributed. Code and the MCP server: https://github.com/Plaetorius/fusion-corpus

## Use

```bash
uv tool install git+https://github.com/Plaetorius/fusion-corpus
fusion-corpus download          # these archives, checksum-verified, into ~/.fusion-corpus/
claude mcp add fusion-corpus -- fusion-corpus mcp
```

## Files

| Archive | Contents |
|---|---|
| `fusion-corpus-db-v1.0.0.tar.zst` | `catalog.sqlite` (metadata, passages, FTS index), `tables.sqlite`, `LICENSES.md`, `DATASHEET.md`, `MANIFEST.sha256` |
| `fusion-corpus-jsonl-v1.0.0.tar.zst` | `works`, `citations` (776,000 reference links), `fulltext`, `passages`, `tables` as JSONL (CC BY material only) |
| `fusion-corpus-nc-sa-v1.0.0.tar.zst` | the 3 CC BY-NC-SA 3.0 papers (full text, passages, table). Not for commercial use |

`SHA256SUMS` lists the archive checksums; `MANIFEST.sha256` inside the db and JSONL archives lists every file.

## Composition

- **Metadata layer:** 24,101 works (all Crossref records of the two journals); 23,439 classified as research
  articles. Sources: Crossref (metadata facts) and OpenAlex (CC0).
- **Full-text layer:** 3,494 articles, 92 % from 2020 or later: do not count trends on it; use the metadata layer
  with its coverage fields.
- **Abstracts:** released for 3,495 works whose article is CC licensed; withheld (null) for the other 18,195.

## Licences

The selection, structure, cleaning and table reconstruction are offered under **CC BY 4.0**. Each article stays
under its own licence: 3,146 CC BY 4.0, 345 CC BY 3.0 and 3 CC BY-NC-SA 3.0. Every record carries its DOI and
licence URL, and full-text records an `attribution` string. Reuse requires attribution and a statement of changes
(see `LICENSES.md` in the archive). No endorsement by the authors, IOP Publishing or the IAEA is implied.

## Collection

Metadata was harvested from the Crossref and OpenAlex APIs on 2026-10-02. Full texts were obtained from the
publisher under an arrangement with the publisher; to build your own corpus, obtain PDFs or JATS under your
publisher's text-and-data-mining terms or from open repositories, then ingest them locally with the code
repository.

## Known defects

- Table coverage is about 88 % of detected captions. Without ruling lines, adjacent columns can merge, and
  multi-line cells can appear as extra rows. Check values against the article.
- Equations are flattened to linear text; sub/superscripts are heuristic. Two-column reading order is usually right
  but figure captions and side boxes can interrupt paragraphs.
- Abstracts are present for only 3,495 of 24,101 works.

## Intended use

Retrieval and question answering with citations, text mining of open fusion literature, table lookup (verify
values), bibliometrics on the metadata layer. Not suitable: commercial use of the NC-SA subset; whole-field claims
from the full-text layer alone; using reconstructed table values unchecked.

## Evidence that it helps

Pre-registered, audited studies (same model, Claude Opus 5.5, in every setup; "web search" is the assistant's
built-in search and fetch): exact facts from recent papers, corpus 93 % vs web search 74 % (129 questions); values
printed in tables, 99 % vs 57 % (69 questions); papers public only after the model's training cutoff, 98 % vs 48 %
(124 fact questions). On open-ended questions and broad evidence gathering there was no significant difference.
Protocols and results: https://github.com/Plaetorius/fusion-corpus-evals

## Privacy

Every released text value was scanned for the publisher's per-download stamps, cover-page residue, the
maintainer's personal details, local paths and IP addresses: 0 must-not-ship hits (see `DATASHEET.md`). The
articles' own author names, affiliations and correspondence addresses are published as printed in the articles.
Take-down and error reports: https://github.com/Plaetorius/fusion-corpus/issues

## Citation

See `CITATION.cff` in the code repository (a Zenodo DOI is added at release).
