# Worked examples

These answers were produced by running the server's own functions (through the `asterism-mcp` CLI) against the v1.0.0 data.
Each answer was then checked by hand against the source text; numbers appear in the quoted passage or the command output.
An LLM assistant would phrase them differently, but it would get the same passages, citations and caveats.

Setup: `asterism-mcp download` (data in `~/.asterism/`). The commands below use the CLI; the MCP tools behave the same.

## 1. Exact value in the text

**Question:** What H98 factor did EAST report for type-II ELMy H-mode with EC+NBI heating?

**Commands:**
```
asterism-mcp search "H98 factor type-II ELMy H-mode EC NBI heating EAST" --limit 3
asterism-mcp passage 79003 --context 0
asterism-mcp passage 79017 --context 1
```

**Answer:** EAST reported H98 up to **1.1** in type-II ELMy H-mode, for both EC+NBI and EC+LHW heating (abstract, page 2). In the body (pages 5-6), type-II discharges heated with 3 MW EC and 1.4 MW NBI reached H98 close to 1 even at the small separatrix-W-limiter gap of about 4 cm; for comparison, type-I discharges (3 MW EC, 1.7 MW NBI) rose from 0.8 to 1 when the gap went from about 4 to 8 cm. The 1.1 is a peak across the type-II regime, not the value of one discharge.

**Source:** Jia, Loarte, Sun et al., Impact of tungsten plasma facing components on H-mode operational space in EAST in support of ITER new baseline, Nuclear Fusion 2026, doi:10.1088/1741-4326/ae81c8, CC BY 4.0. DOI 10.1088/1741-4326/ae81c8, pages 5-6 (chunk 79017).

> "The normalized H-mode energy confinement can reach H_98 factors up to 1.1 for both EC+NBI and EC+LHW power combination in the type-II ELMy H-mode regime." (abstract, chunk 79003)
>
> "the type-II ELMy H-mode can maintain a higher energy confinement, reaching H_98 close to 1, even with smaller ∆_r." (chunk 79017)

**Checked:** both quotes compared with the full passage text; they match. (The search hit reports pages 6-6 for chunk 79017, the passage call reports 5-6; the latter is used.)

## 2. A value printed in a table

**Question:** How much did energy confinement time improve between attached and pronounced-detached states on HL-2A?

**Commands:**
```
asterism-mcp tables "energy confinement time H98 scaling table"
asterism-mcp table 2418
asterism-mcp search "pronounced detachment HL-2A energy confinement time increased stored energy" --years 2025 2025 --limit 4
asterism-mcp passage 73265 --context 0
```

**Answer:** Table 1 lists tau_E of 27 ±1.3 ms in the attached state and 33.6 ±1.6 ms in the pronounced-detached state, an increment of about 24.4%. Stored energy rose from 13.9 ±0.2 kJ to 16 ±0.4 kJ (about 15.1%). Tables are reconstructed from the PDF layout and may merge columns, so the table values were cross-checked against the running text rather than trusted alone.

**Source:** Wu, Xu, Wang et al., Compatibility of pronounced detachment with improved confinement on HL-2A tokamak, Nuclear Fusion 2025, doi:10.1088/1741-4326/ad9e04, CC BY 4.0. DOI 10.1088/1741-4326/ad9e04, pages 4-4 (text, chunk 73265); the table is on page 6 (table 2418).

> "energy confinement time τ_E increases from 27 ms to 33.6 ms"

**Checked:** table cells and passage agree on 27 ms, 33.6 ms and 24.4%; the ± uncertainties appear only in the table. The first `tables` hit was chosen from a list of loosely related tables; always read the caption.

## 3. What exists (titles, including paywalled papers)

**Question:** What has been published on negative triangularity tokamaks?

**Command:**
```
asterism-mcp works "negative triangularity tokamak" --limit 5
```

**Answer:** The first five matches are: Medvedev et al. 2015 (stability limits and prospects as a fusion energy system, Nuclear Fusion), Kikuchi et al. 2019 (L-mode-edge negative triangularity reactor), Nelson, Paz-Soldan and Saarelma 2022 (H-mode inhibition in reactor plasmas), Abate et al. 2020 (RFX-mod2 equilibria, PPCF), and Lvovskiy et al. 2026 (first robust negative triangularity control in a spherical tokamak, PPCF). `works` searches titles and abstracts and lists paywalled papers too, but full text is open only for a subset: all five of these show `has_fulltext: 0`, so the corpus can name them but not quote them.

**Source:** Lvovskiy, Vincent, Anand et al., First experimental realization of robust negative triangularity plasma control in a spherical tokamak, Plasma Physics and Controlled Fusion 2026, doi:10.1088/1361-6587/ae92b1, https://publishingsupport.iopscience.iop.org/iop-standard/v1. DOI 10.1088/1361-6587/ae92b1, pages: none (metadata only).

> No quote available: this paper's licence does not allow text in the corpus (`has_abstract: 0`, `has_fulltext: 0`).

**Checked:** titles, years and venues compared with the command output; they match. No claim about the papers' findings is made.

## 4. Publication trend

**Question:** Is negative triangularity research growing?

**Command:**
```
asterism-mcp count "negative triangularity"
```

**Answer:** The output has two rows: n = 8 matching works in the 2010s and n = 114 in the 2020s (decade still running). The caveat is large: abstract coverage (`frac_abstract`) is 0.125 in the 2010s versus about 0.80 in the 2020s, so the 2010s count is mostly title matches and is certainly too low. The data support "many more matches in the 2020s", not a growth rate.

**Source:** `count` output (no passage; counts are not citable text). Fields: frac_abstract 0.125 and 0.7982456140350878, frac_cc_vor 0.125 and 0.7982456140350878. DOI and pages: not applicable.

> "Counts match title + abstract text, so they depend on abstract coverage (see frac_abstract per period) and on wording."

**Checked:** every number above is copied from the JSON; the caveat text is the tool's own.

## 5. A recent (2025-2026) fact

**Question:** How effective was a lithium vapor box divertor module at reducing heat flux, according to 2026 work?

**Commands:**
```
asterism-mcp search "lithium vapor box divertor detachment 2026" --years 2025 2026 --limit 5
asterism-mcp passage 2049 --context 0
```

**Answer:** The Magnum-PSI paper on an open vapor box module reports simulated heat-flux reductions toward the target of up to 81% in low-flux scenarios and 75% in high-flux scenarios. These are simulation results quoted in the paper's conclusions, not a measurement of the plasma-facing heat load.

**Source:** Romano, Tanke, Schwartz et al., Experimental evaluation of the vapor box divertor concept with an open vapor box module in Magnum-PSI, Nuclear Fusion 2026, doi:10.1088/1741-4326/ae2d71, CC BY 4.0. DOI 10.1088/1741-4326/ae2d71, pages 6-6 (chunk 2049).

> "Simulations calculate reductions of up to 81% in low-flux scenarios and 75% in high-flux scenarios"

**Checked:** compared with the passage; matches. Plausible-sounding answers such as "the experiment measured an 81% reduction" are NOT supported: the passage says simulations.

## 6. What the corpus cannot answer

**Question:** What is the measured cross-section for muon-catalyzed fusion?

**Commands:**
```
asterism-mcp search "muon-catalyzed fusion cross section measurement" --limit 3
asterism-mcp works "muon-catalyzed fusion"
asterism-mcp count "muon-catalyzed fusion"
asterism-mcp passage 41046 --context 0
```

**Answer:** The corpus cannot give a number. `count` finds a single matching work (1980s, `frac_abstract` 0.0). `works` lists two 1987 papers on muon catalysis, but both show `has_abstract: 0` and `has_fulltext: 0`, so only titles exist. The only open-text hit is a 2024 IAEA conference summary that mentions a muon-catalyzed fusion hybrid proposal and contains no cross-section. The right next step is the paywalled 1987 papers, via their DOIs.

**Source:** Litaudon, Mazon, Summary of the 29th IAEA fusion energy conference under the topics magnetic fusion experiments (EX) and innovative & alternative concepts (IAC), Nuclear Fusion 2024, doi:10.1088/1741-4326/ad5365, CC BY 4.0. DOI 10.1088/1741-4326/ad5365, pages 12-12 (chunk 41046). Metadata-only paper: Eliezer, Tajima, Rosenbluth, Muon catalysed fusion-fission reactor driven by a recirculating beam, Nuclear Fusion 1987, doi:10.1088/0029-5515/27/4/001.

> "An original fusion-fission hybrid development to amplify the small power of muon-catalyzed fusion was also proposed by [142]"

**Checked:** read the passage; the word "cross" does not appear in it, so it does not answer the question. A low `count` here is not evidence the topic is unstudied.

## Transcript from a real Claude Code session

Run on a clean machine: the wheel installed in a fresh virtual environment, data fetched with `asterism-mcp download`,
and the server added to Claude Code with `--mcp-config`. Question and answer, unedited (Sonnet 5.5, three tools allowed:
`search`, `get_passage`, `paper`):

> **Q:** What H98 factor did EAST report for type-II ELMy H-mode with EC+NBI heating? Use the Asterism tools, cite the DOI, page and licence.
>
> **A:** EAST reported H98 factors **up to 1.1** for type-II ELMy H-mode with EC+NBI heating.
>
> **Source:** Jia, Loarte, Sun et al., "Impact of tungsten plasma facing components on H-mode operational space in EAST in support of ITER new baseline", *Nuclear Fusion* 2026, doi:10.1088/1741-4326/ae81c8. Licence: CC BY 4.0.
>
> - **Headline value (page 2, abstract):** "The normalized H-mode energy confinement can reach H_98 factors up to 1.1 for both EC+NBI and EC+LHW power combination in the type-II ELMy H-mode regime." The total auxiliary power was 3-5 MW, at q95 ≈ 6.0.
> - **Typical range (pp. 7-8, section 2.4.2):** "H_98 0.9-1.1 could be achieved by type-II ELMs", compared with only about 0.8 for the few type-I ELMy H-modes sustained at a plasma-limiter distance of about 4 cm.
> - **Matched pair (p. 7, section 2.4.1):** In a direct type-II vs type-I comparison, discharge 140 902 (type-II) had H98 ≈ 0.95 and 140 893 (type-I) had ≈ 0.85. Both used 2 MW EC, 1.5 MW LHW and 0.6 MW NBI, so that pair is not EC+NBI-only.
>
> The 1.1 figure is a peak for the EC+NBI combination, not a single-discharge value tied to one specific power level.

The assistant found the abstract value (1.1) that the first search page did not show; the H98 values and quotes in the three
bullets were checked against passages 79003, 79023 and 79021 (the heating-power and q95 details were not rechecked). The data directory was byte-identical before and after the session.
