# Toolkit Scout

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
Stage 2 here ran as Claude subagents; Composio's SDK/MCP was **not** used (no API key was available); that step is still open. The prompt is model-agnostic and can be driven through Composio tools (search + fetch) instead.

## Known limits
No human has reviewed the rows yet (10-app checklist is on the page). Gold sets are model-labelled; gold B is n=20 (CI roughly ±20 pts). Some pages were unreadable by script (JS-only or bot-blocked); 31 quotes are web-fetch only and cannot be machine-checked. Facts are dated 2026-11-23.
