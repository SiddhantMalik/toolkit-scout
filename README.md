# Toolkit Scout

**Live case study:** https://sidmalik.dev/toolkit-scout/ · by [Siddhant Malik](https://sidmalik.dev)

Researches 100 apps (auth, self-serve vs gated, API surface, MCP, buildability verdict) with an agent pipeline, then checks its own accuracy against frozen gold sets. Output: `site/index.html` (single-page case study) and `data/final.json` (machine-readable).

## Layout
| Path | What |
|---|---|
| `data/pass1_seed.txt` | The 100 apps + **pass 1** (memory-only baseline, written before any docs were opened) |
| `agent/fetch_evidence.py` | Stage 1: fetch docs, `llms.txt`, one hop to auth/pricing/MCP pages; saves page text to `data/evidence/` |
| `agent/mcp_probe.py` | Stage 1b: MCP Registry leads (hints only) |
| `agent/prompts/extract.md` | Stage 2: the extraction prompt/schema. Every field needs a verbatim quote + URL, else `unknown` |
| `data/pass2/raw_*.jsonl` | Stage 2 output (10 extractor agents; 40 apps Sonnet, 60 Opus) |
| `agent/check_quotes.py`, `agent/gate.py` | Stage 3: verify each quote appears in saved page text; reset fields whose quotes all fail |
| `agent/composio_mcp.py`, `agent/composio_fetch.py` | Stage 3b: a small Composio Connect MCP client; asks `COMPOSIO_SEARCH_TOOLS` for a page fetcher and re-fetches, via `COMPOSIO_MULTI_EXECUTE_TOOL`, every cited page behind a quote the shell could not check. Saves to `data/evidence_composio/`, logs `data/composio_run.json` |
| `data/pass2/requote.jsonl` | Stage 3d: paraphrased quotes replaced with text from the fetched page (values unchanged), then re-checked. Done by the orchestrating agent, logged |
| `agent/verdict.py` | Deterministic buildability rubric (v1 original; v3 = post-hoc fix via `fixed=True`, see page) |
| `gold/gold_A.jsonl`, `gold/gold_B.jsonl` | Frozen gold: A = 27 hard cases (reviewer-picked), B = 20 seeded-random apps, blind labels. Labelled by Opus agents, **not humans** |
| `agent/score.py` | Per-field accuracy, Wilson 95% CI, Jaccard (auth), within-one (verdict) |
| `agent/analyze.py`, `agent/build_site.py` | Compute every page number from data; render the page |

## Reproduce (offline, from committed data, ~5 s)
```bash
pip install -r requirements.txt
python agent/run_all.py          # gate -> score -> analyze -> build site/index.html
python -m pytest -q tests        # rubric, scorer and quote-checker tests
```
`agent/report.py` turns `data/*.json` into page text; `site/template.html`, `style.css` and `app.js` hold markup, styling and the table script, so no prose lives in Python. The build fails if a template token has no value.

## Re-run the research (needs network + an LLM)
```bash
python agent/run_all.py --research        # stage 1 (network) then the offline steps; or run fetch_evidence.py / mcp_probe.py alone
# stage 2: for each app id, give agent/prompts/extract.md to your LLM agent (web + shell tools),
# have it append one JSON line per app to data/pass2/raw_<k>.jsonl
python agent/gate.py                                              # stage 3
```
Stage 2 here ran as Claude subagents. Composio is used in stage 3b (see below).

## Composio stage (3b)
```bash
export COMPOSIO_CONSUMER_KEY=ck_...      # Composio Connect consumer key (x-consumer-api-key); never written to disk
python agent/composio_fetch.py            # default fetcher: KEENABLE_FETCH_URL_PUBLIC (free, shared hourly quota)
python agent/composio_fetch.py --tool TAVILY_EXTRACT   # metered alternative (renders JavaScript)
python agent/run_all.py                   # re-check quotes against the fetched pages and rebuild
```
Result on this run: 20 of 21 cited pages fetched; 33 web-tool quotes checked against the page they cite: 27 match, 5 did not (mostly paraphrases), 1 cited URL is a 404. The strict gate turned two correct gold-A MCP answers into abstentions (22/24 to 20/24); re-quoting 3 quotes from the fetched pages restored 22/24. Both stages are scored (`pass2b_strict`, `pass2b`).

## Known limits
Five apps the pipeline could not settle were settled in a final browser-and-search loop (`data/pass2/browser_loop.jsonl`, not scored). The author checked 10 random apps by hand against the docs (auth, access, MCP): 30/30 agree (`data/human_check.json`); one checker, so treat it as a spot-check. The verdict column is not validated. Gold sets are model-labelled; gold B is n=20 (CI roughly ±20 pts). Some pages were unreadable by script (JS-only or bot-blocked); their pages were re-fetched through Composio, and 1 web-tool quote (a 404 PitchBook URL) is still unchecked. Quotes from script-saved pages are matched against all text saved for the app, not the exact cited URL. Facts are dated 2026-11-23.


## Notes
`data/evidence*/` hold cached text of public developer-docs pages, kept so the quote checker can be re-run offline. The single-file page is `site/index.html` (mirrored to `docs/` for GitHub Pages).
