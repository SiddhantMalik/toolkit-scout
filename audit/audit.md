# Audit of toolkit-scout (2026-11-23)

Auditor: independent skeptical review (a Claude Opus agent, so **not** independent of the model family that produced pass 2 and both gold sets; read every "agree" below with that in mind). Nothing under `/home/claude/toolkit-scout` was modified. Work copy: `/tmp/review2/repo`.

Files: `audit.md` (this), `crosscheck.jsonl` (30 apps × 4 fields), `evidence40.jsonl` (40 evidence entries), `sample30.json` (sampled ids), `res30.jsonl`/`res40.jsonl` (raw fetch + quote-presence results), `tools/` (scripts used), `fetch/` (page cache).

## 0. Reproduction

Re-ran `gate.py`, `score.py pass2a=… pass2b=… pass2b_v2=…`, `analyze.py`, `build_site.py` in the copy. **Byte-identical** `scores.json`, `final.json`, `pass2b.jsonl`, `quote_check.json` and `site/index.html`. Gold hashes match the page (`4552cb48…`, `133239ac…`). Every number on the page does follow from the committed data. The problems are in what the code counts and what the prose says about it, not in arithmetic.

## 1. Code bugs and metric problems (ranked by impact on reported numbers)

1. **Rubric v2 was tuned on the test set, and it's the row the page leans on.** (`agent/verdict.py:4,11`; `agent/score.py:51`). Switching `mcp_exempt` to False flips exactly two gold‑B apps (49 Amazon SP‑API, 90 PitchBook), which is the whole of the 55% → 65% verdict gain on gold B. The v1 rule isn't a stray logic error either. It's the rubric written in the gold‑A reviewer notes (§3.3, R3: "the only self‑serve path is MCP while REST is gated → caveat"), and gold A's Brex = caveat was labelled with it. So v2 moves toward gold B and away from the rubric gold A was labelled under. On top of that, `verdict.py`, `score.py` and `norm.py` were first committed in `6224fee`, the same commit as the pass‑2 results and `scores.json`, with the v2 switch already in. Git doesn't back the claim that v1 was pre‑registered as code (the rubric text in the review notes was). The honest verdict number is v1: **gold B 11/20 = 55% (CI 34–74)**, below pass 1's 65%.
2. **Gold "unknown" verdicts can never be matched** (`agent/score.py:37‑38`). When the prediction is `unknown` and gold is `unknown`, the row is filed as an abstention and scored wrong. Gold A #84 Paygent: both sides say unknown. Pass‑2 gold‑A verdict should be **10/17 (59%)**, not 9/17 (53%). Within‑one (`score.py:27`) also drops every gold‑unknown row, so the page's "every disagreement is within one step" leaves out #50 fanbasis (gold unknown, pass 2 easy).
3. **Production paid plans never count as friction** (`agent/verdict.py:17`). Only `HARD ∪ {app_review}` triggers a prod blocker. Twilio, Vonage, SendGrid and Xero have `access_prod=paid_plan` and still come out **easy**, so they're in the page's "easy wins". Meanwhile `analyze.py:27` counts the same four as having "a stricter gate for production". This bug is also why the rubric run on gold B's own fields says easy where the gold labeller wrote caveat (Copper, Gorgias, DataForSEO, SE Ranking: all `prod=paid_plan`). The page blames that disagreement on the labeller.
4. **Unknown or missing fields default to "easy"** (`verdict.py:10‑24`). `dev=unknown` with any API style skips R0, and `tenancy/admin_only=None` add no blocker. Cloudflare's access was **reset to unknown by the gate** and is still verdict easy and listed in "easy wins". 36 apps have `admin_only_credential=None`, 14 of them easy.
5. **The top blockers rest on fields that need no evidence and are never gated** (`gate.py:15‑23`, `extract.md` schema). `tenancy`, `admin_only_credential`, `api_breadth`, `api_beta` and `min_plan` have no evidence category, and the gate only resets a field when it **has** quotes and all of them fail. Fields with zero quotes go through untouched: in pass2b, 48 apps have `api_styles` set with no api quote, 3 have auth, 1 access and 4 mcp with no quote. PER_TENANT_HOST (12), ADMIN_ONLY (11), PER_REGION (8) and NARROW (7) are the page's "most common blockers", and none of them is evidence‑checked. The page itself admits WhatsApp's admin‑only flag has no quote.
6. **The quote checker doesn't bind a quote to its URL and doesn't check meaning** (`check_quotes.py:8‑23`). It searches the concatenation of all saved text for the app, ignoring `e["url"]`, and the `evidence_extra` files are written by the extractors themselves. 127 of 308 have no `URL:` provenance header. Some are 404 pages (`60_mcp-in-clay.txt`), and one is a docs AI‑assistant answer, not docs text (`47_4.txt`, an Ecwid `?ask=` response). 10 "verified" quotes appear only in files whose header URL differs from the cited URL. The ≥12‑character floor lets trivial quotes through ("linkedin ads mcp", "mermaid mcp server"). Apps whose quotes are all `src=web` bypass the gate completely (Salesforce 4/4, PitchBook 5/5, Otter 4/4). "540 machine‑verified verbatim" really means "appears somewhere in text the agent saved".
7. **Gold B's verdict isn't produced by the same code** (`norm.py:15‑18` uses `g["verdict"]`). The docstring at `verdict.py:1` says "same code scores agent output and gold‑derived fields". That's false. Gold B is labeller judgement, its schema has no tenancy or admin fields, and running the rubric on gold‑B fields disagrees with gold‑B verdicts on 7/20 apps under v1 and 5/20 under v2.
8. **`prod_friction` KPI** (`analyze.py:27`). It counts any prod ≠ dev, including dev already gated or paid (8 of the 34). The page's "{77} … but 34 **of them** add a second gate" is wrong: 26 of the 77 self‑serve apps do.
9. Minor or latent:
   - `verdict.py:12`: an empty `api_styles` is a subset of `{cli_only,none,sdk_only}`, so an api‑field gate reset would make an app "no API". Not triggered now.
   - `verdict.py:16` (v1 only) labels customer_only/partner/KYC as `SALES_CONTACT`.
   - `score.py:37`: auth reset to `[]` scores as wrong rather than abstained, unlike the other fields.
   - `score.py:6`: `wilson(0,0)` returns (0,0).
   - The Wilson formula itself is correct. Jaccard is correct, but only over rows where both sides are present.
   - `__pycache__/*.pyc` was committed despite `.gitignore`.
   - `pass2a_partial.jsonl` differs from `pass2a.jsonl` in 2 rows, undocumented.
10. **Leakage and independence, not code.** The orchestrator read the gold‑A review notes, which name the gold‑A MCP answers app by app (DealCloud, Meta Ads, Brex, Consensus, Otter…), before writing the extraction prompt and running the extractors. Gold‑A pass‑2 MCP (92%) is contaminated, and the page discloses only part of this. Gold B, the extractors and this audit are all Claude models with the same schema and vocabulary, so their agreement is partly shared bias. File mtimes show extractor evidence being written (`evidence_extra/11_1.txt` 09:53:18) before gold B was committed (09:53:36). The page's "labelled blind before any pass‑2 output existed" is therefore not strictly true, though nothing shows the labeller saw any of it.

### Corrected headline metrics (my recomputation)
| Metric | Page | Corrected / honest |
|---|---|---|
| Gold B verdict, pass 2 | 65% (v2) shown as "the number to trust" | **55% (v1, pre‑specified)**. The 65% is post‑hoc on the same 20 apps. Pass 1 = 65%. |
| Gold A verdict, pass 2 | 9/17 = 53% | **10/17 = 59%** (unknown = unknown bug). Pass 1 = 12/17 = 71%, so it still gets worse |
| Gold A auth, pass 2 | 53% | Unchanged, but it **fell** from pass 1's 88% and Jaccard fell 0.91 → 0.76. The page doesn't say this |
| Easy count | 39 | 35 if a prod paid plan counts as friction (Twilio, Vonage, SendGrid, Xero), 34 without Cloudflare (access unknown) |
| Official MCP | 81/95 | At least 80 (Pinterest isn't launched). 8 more are beta, EAP or dev preview (Podio, Zendesk, Lark, WhatsApp, WooCommerce, BigCommerce, fanbasis, plus Pinterest) |

## 2. Page claims vs data
| # | Page claim | Status | Detail |
|---|---|---|---|
| P1 | "77 of 95 … but 34 **of them** add a second gate" | **Wrong** | 26 of the 77. The 34 includes 8 apps whose dev access is already paid or gated |
| P2 | "34/95 add a stricter gate for production" (KPI) | Overstated / inconsistent | Includes 4 apps the rubric calls easy (prod paid_plan) and pairs like customer_only→partner_review |
| P3 | Pattern 3 caveat: "Mailchimp's, Magento's and Shopify's dev MCPs search docs" | **Misleading** | All three are recorded `docs_only` and **are not** in the 81, so they can't be caveats on that number. Pinterest (not launched) *is* in the 81 |
| P4 | "memory-only first pass missed it for 40 of 100" | Overstated | That's drift against pass 2, not error against truth. It includes p1 "community" and a pass‑2 false positive (Pinterest) |
| P5 | Pattern 4: non‑paywall blockers "outnumber paid‑plan gates several times over" | Weakly supported | Each code is about 2× PAID_PLAN (6), and PAID_PLAN is undercounted (bug 3). The large codes come from unevidenced fields (bug 5) |
| P6 | Pattern 5: easy wins cluster in "data, productivity **and developer tools**" | Overstated | Dev tools 5/10 easy, against CRM 4/10 and Comms 4/10. With about 10 per category, 1–2 apps is noise. Fintech 1/8, Ecommerce 2/10, Support 2/9 is directionally right but n is tiny |
| P7 | "Seven of the ten first‑launch Sonnet runs died (529)…; 40 Sonnet / 60 Opus" | **Unverifiable** | No logs, model tags or run records in the repo. Raw files are 10×10 ids with no model field. The numbers are internally consistent (3+1 Sonnet files, 6 Opus) |
| P8 | "Human involvement: none yet … The 5 that most need a person: [7 names]" | **Wrong count** | Lists 7 apps. "No human" can't be verified either way |
| P9 | Blocked‑site list "…Gumroad, Consensus and the Amazon and Google docs", placed beside the web‑only quote count | Inconsistent | Those four have 0 web‑only quotes (all file‑verified). Maybe true of stage‑1 fetch, but the sentence ties it to web‑only quotes |
| P10 | "Pass 1 … committed to git before anything else" | **False as written** | The first commit (62eebbd) also contains gold A and review notes that critique `data/evidence` fetch results, so retrieval had already run |
| P11 | "v1 (pre‑registered)" / "fixed it after seeing gold, and now show both. Version v2 is used in the table above" | Misleading | Not pre‑registered as code (bug 1). The table shows four rows, and v2 is the only row that ties pass 1 on gold B |
| P12 | "Exact agreement did not improve over memory" | **Understated** | Gold A: 71% → 53% (59% after bug 2), so it got worse. Gold B v1: 65% → 55%, also worse |
| P13 | "every disagreement is within one step" | Overstated | Gold‑unknown rows are excluded (fanbasis). Within‑one on a 4‑step scale where nearly everything is easy or caveat is close to vacuous |
| P14 | "gold labeller … called Lark, Sentry and Grain easy despite regional hosts or partner‑gated production" | **Wrong diagnosis** | Gold's own fields for those apps (prod same_as_dev, no tenancy field) do give easy under the rubric. The labeller disagreed on **facts**, not rubric application. Where gold departs from the rubric it runs the other way (Copper, Gorgias, Aircall, DataForSEO, SE Ranking = caveat), which exposes bug 3 |
| P15 | "Auth scoring is lenient on purpose" | **Wrong word** | Exact‑set match is the strict metric. Jaccard is the lenient one. Gold B lists all methods, so "gold lists the primary one" is true of gold A only |
| P16 | "Memory → evidence did the work" (MCP 80 → 100 on B, 33 → 92 on A) | Partly supported | The MCP gain is real (and my cross‑check agrees). Gold‑A MCP is contaminated by the orchestrator having read the reviewer notes, and the same paragraph says nothing about auth getting worse on gold A |
| P17 | "Gold B labelled blind before any pass‑2 output existed" | Not strictly true | mtimes, see bug 10 |
| P18 | "540 quotes machine‑verified verbatim" | Overstated | Checked against agent‑saved text, not against the cited URL (bug 6). My re‑fetch: 39/40 present today, 32/40 support the value |
| P19 | KPIs 100/95, 81/95, 77/95; auth 76/72/13/5, key‑only 13; gated 11, paid 6; verdict counts; 79 open questions; hashes; "reset one field (Cloudflare)" | Correct vs data | Reproduced. "Most apps offer both" holds: 56/95 |
| P20 | "Gold B … n=20 means ±20 points" | Correct | e.g. 65% → [43, 82] |

## 3. Fresh cross‑check of pass 2 (30 apps)
Sample: ids not in gold_A.jsonl or gold_B.jsonl (53 eligible). Stratified 3 per category, `random.Random(424242)`, categories in seed order, ids sorted within category. Ids: 3, 5, 7, 14, 17, 18, 21, 22, 26, 34, 38, 39, 44, 45, 48, 55, 56, 58, 65, 68, 69, 71, 72, 74, 83, 85, 89, 93, 98, 99. Method: re‑fetched every auth/access/MCP evidence URL (148 entries) with curl and normalised substring checks. Blocked pages (GitHub, developer.salesforce.com, binance, airtable, slack root) went through WebFetch. Targeted vendor checks for Pipedrive, GoHighLevel, Threads, iPayX, Gumroad and Pinterest. Access is compared at class level (self = free or trial / paid / gated).

| Field | n | agree | partial | disagree | strict agreement (Wilson 95%) |
|---|---|---|---|---|---|
| Dev access class | 30 | 29 | 0 | 1 (iPayX: API plans from $99/mo, pipeline says self_free) | 97% (83–99) |
| Auth methods | 30 | 27 | 2 (Firecrawl OAuth only for MCP; Ramp "basic" is token‑endpoint client auth) | 1 (Magento: cited quote says OAuth **1.0a**, labelled oauth2) | 90% (74–97); 97% lenient |
| Official MCP | 30 | 29 | 0 | 1 (Pinterest: page says "Be the first to know when it launches") | 97% (83–99) |
| Evidence actually supports value | 30 | 17 | 10 | 3 (Pinterest, Magento, iPayX: the pipeline's own quote contradicts its value) | 57% (39–73); 90% incl. partial |

CI width: with n=30, a 97% point estimate has a lower bound of about 83%, so the plausible error rate is anywhere from about 1% to 17%. This is consistent with gold B's 90–100% on these fields and doesn't narrow it much. Caveat: the auditor is the same model family, and class‑level access matching is forgiving (trial and free both count as "self").

| id | app | dev access (pipeline → auditor) | auth | official MCP | evidence supports? |
|---|---|---|---|---|---|
| 3 | Pipedrive | agree (self_free (self) -> same_as_dev) | agree (oauth2,api_key) | agree (official_remote) | partial: quotes present; access quote does not itself show free access |
| 5 | Twenty | agree (self_free (self) -> same_as_dev) | agree (oauth2,api_key,bearer_token) | agree (official_remote) | agree: all quotes present and supportive |
| 7 | Zoho CRM | agree (self_free (self) -> same_as_dev) | agree (oauth2) | agree (official_remote) | agree: all present, supportive |
| 14 | Front | agree (self_free (self) -> partner_review) | agree (oauth2,bearer_token) | agree (official_remote) | partial: present; access quote is a truncated fragment |
| 17 | Plain | agree (self_trial (self) -> same_as_dev) | agree (api_key,oauth2,bearer_token) | agree (official_remote) | agree: present, supportive |
| 18 | Help Scout | agree (self_trial (self) -> same_as_dev) | agree (oauth2) | agree (official_remote) | agree: present, supportive |
| 21 | Slack | agree (self_free (self) -> same_as_dev) | agree (oauth2,bearer_token) | agree (official_remote) | agree: present (root page needed WebFetch) |
| 22 | Twilio | agree (self_trial (self) -> paid_plan) | agree (basic,api_key) | agree (official_local) | agree: present (GitHub via WebFetch); alpha status not reflected |
| 26 | Discord | agree (self_free (self) -> app_review) | agree (oauth2,bearer_token,other) | agree (docs_only) | agree: present, supportive |
| 34 | GoHighLevel | agree (self_free (self) -> app_review) | agree (oauth2,bearer_token) | agree (official_remote) | agree: present, supportive |
| 38 | Pinterest | agree (partner_review (gated) -> app_review) | agree (oauth2) | disagree: official_remote → NOT launched: page is a launch sign-up ('Be the first to know when it launches') -> not an available official MCP | disagree: pipeline's own MCP quote contradicts official_remote |
| 39 | Threads (Meta) | agree (self_free (self) -> app_review) | agree (oauth2) | agree (official_remote) | partial: present (llms.txt index only; no endpoint URL captured) |
| 44 | Salesforce Commerce Cloud | agree (customer_only (gated) -> enterprise_license) | agree (oauth2,jwt) | agree (official_local) | partial: web quotes present today (WebFetch); 'customer_only' is inferred, not stated |
| 45 | Magento (Adobe Commerce) | agree (self_free (self) -> same_as_dev) | disagree: oauth2,bearer_token,other → OAuth 1.0a + bearer token (+admin session); NOT OAuth 2 in the cited docs | agree (docs_only) | disagree: auth quote contradicts 'oauth2' label; access quotes don't show self_free |
| 48 | Gumroad | agree (self_free (self) -> same_as_dev) | agree (oauth2,bearer_token) | agree (official_remote) | partial: auth quotes (with JSX artefact {" "}) not findable today |
| 55 | Apify | agree (self_free (self) -> same_as_dev) | agree (bearer_token,oauth2) | agree (official_remote) | agree: present |
| 56 | Firecrawl | agree (self_free (self) -> same_as_dev) | partial: bearer_token,oauth2 → API key bearer; OAuth only for MCP connections | agree (official_remote) | agree: present |
| 58 | Sherlock | agree (self_free (self) -> same_as_dev) | agree (none) | agree (community) | partial: MCP evidence is an aggregator (glama.ai), which the prompt forbids as evidence |
| 65 | Supabase | agree (self_free (self) -> same_as_dev) | agree (bearer_token,oauth2) | agree (official_remote) | agree: present |
| 68 | MongoDB Atlas | agree (self_free (self) -> same_as_dev) | agree (oauth2,other) | agree (official_remote) | agree: present |
| 69 | Datadog | agree (self_trial (self) -> customer_only) | agree (api_key,oauth2) | agree (official_remote) | partial: present; access quote is nav chrome; prod=customer_only has no quote |
| 71 | Notion | agree (self_free (self) -> self_free) | agree (oauth2,bearer_token) | agree (official_remote) | agree: present |
| 72 | Airtable | agree (self_free (self) -> self_free) | agree (oauth2,bearer_token) | agree (official_remote) | agree: present (web quotes confirmed via WebFetch) |
| 74 | Jira | agree (self_free (self) -> self_free) | agree (oauth2,basic,jwt) | agree (official_remote) | partial: present; access quotes weak (page title, distribution toggle) |
| 83 | Binance | agree (kyc_verification (gated) -> same_as_dev) | agree (api_key) | agree (official_remote) | agree: web quotes present today (WebFetch) |
| 85 | iPayX | disagree: self_free (self) -> paid_plan → API key plans paid (from $99/mo); only 3 free public audits/IP/month without a key -> paid | agree (api_key,bearer_token) | agree (official_remote) | disagree: access quotes contradict self_free |
| 89 | Ramp | agree (customer_only (gated) -> unknown) | partial: oauth2,basic → oauth2 (client creds/auth code); 'basic' is only token-endpoint client auth | agree (official_remote) | agree: present |
| 93 | Fathom | agree (self_free (self) -> self_free) | agree (api_key,oauth2) | agree (official_remote) | agree: present |
| 98 | Mermaid CLI | agree (self_free (self) -> same_as_dev) | agree (none) | agree (community) | partial: MCP quote 'mermaid mcp server' is a 3-word package slug; trivially 'verifiable' |
| 99 | YouTube Transcript | agree (self_free (self) -> same_as_dev) | agree (api_key,bearer_token,oauth2) | agree (official_remote) | partial: present; conditional on entity choice |

## 4. Evidence integrity (40 random evidence entries)
Sample: `random.Random(4040)`, 30 drawn from src=file and 10 from src=web, any app and any field. Each URL was re‑fetched with curl, and WebFetch was used where curl got 403 or JS. Results are in `evidence40.jsonl`.

- **Quote present on the cited page today: 39/40.** The one miss is Monday.com: the page says "For *building* and testing…" and the quote says "For *developing* and testing…". The pipeline's own checker had already flagged that one as unverified.
- **Quote supports the recorded value: 32/40 yes** (several weak or trivial), **3 partial, 5 no**. The no cases: Paygent api (Japanese marketing copy), Vonage access (a 10DLC sentence), Zendesk api, Smartsheet auth (a sentence about Gov/EU tokens), and Otter access (value is unknown).
- Web‑sourced quotes: 10/10 present via WebFetch. Two are 3‑word package slugs ("linkedin ads mcp", "mermaid mcp server") and one cites an aggregator (glama.ai), which the prompt forbids as evidence.
- My own curl check gave a false positive on npm's 403 page (the URL slug matched the quote). The pipeline's ≥12‑char normalised substring check has the same weakness.

| id | app | field | src | present today | supports | note |
|---|---|---|---|---|---|---|
| 15 | Pylon | mcp | file | yes | yes(weak) | on vendor MCP page; quote is about auth not existence |
| 64 | Cloudflare | mcp | file | yes(WebFetch) | yes | GitHub blocked to curl; WebFetch confirms |
| 68 | MongoDB Atlas | access | file | yes | yes |  |
| 84 | Paygent Connect | api | file | yes | no | Japanese marketing text (dev effort 3-5 weeks); says nothing about API style |
| 76 | Monday.com | access | file | no (paraphrase: page says 'For building and testing') | yes(meaning) | pipeline also flagged this quote unverified; gate kept field via 2nd quote |
| 4 | Attio | access | file | yes | yes |  |
| 14 | Front | auth | file | yes | yes |  |
| 72 | Airtable | access | file | yes | yes |  |
| 30 | Vonage | access | file | yes | no | 10DLC registration sentence; does not support self_trial or prod=paid_plan |
| 27 | Telegram | auth | file | yes | yes |  |
| 67 | Snowflake | auth | file | yes | yes |  |
| 96 | Devin | mcp | file | yes | yes |  |
| 25 | Pumble | mcp | file | yes | yes |  |
| 71 | Notion | auth | file | yes | yes |  |
| 46 | Squarespace | access | file | yes | yes |  |
| 13 | Freshdesk | auth | file | yes | yes |  |
| 86 | QuickBooks | access | file | yes | partial | Premium APIs partner-only; core API not gated |
| 53 | Ahrefs | auth | file | yes | yes |  |
| 31 | Google Ads | mcp | file | yes | yes |  |
| 11 | Zendesk | api | file | yes | no | 'Most of our APIs are organized by product capabilities' does not support rest/sdk_only |
| 99 | YouTube Transcript | mcp | file | yes | yes |  |
| 65 | Supabase | auth | file | yes | yes |  |
| 14 | Front | mcp | file | yes | yes |  |
| 99 | YouTube Transcript | api | file | yes | yes(weak) |  |
| 87 | Xero | auth | file | yes | yes | from Xero's MCP repo README, not API docs |
| 9 | Copper | access | file | yes | yes |  |
| 96 | Devin | mcp | file | yes | yes |  |
| 56 | Firecrawl | mcp | file | yes | yes |  |
| 79 | Smartsheet | auth | file | yes | no | about Gov/EU separate tokens; does not show oauth2/bearer |
| 43 | BigCommerce | api | file | yes | yes |  |
| 44 | Salesforce Commerce Cloud | access | web | yes(WebFetch) | partial | 'correct permissions' does not establish customer_only |
| 83 | Binance | access | web | yes(WebFetch) | yes |  |
| 72 | Airtable | access | web | yes(WebFetch, clause) | partial | about privacy/ToS URLs before sharing; not about dev access class |
| 92 | Otter AI | access | web | yes(WebFetch) | no | field value is unknown; quote is about Claude workspace admin |
| 33 | LinkedIn Ads | mcp | web | yes(WebFetch) | yes(trivial) | 3-word quote 'linkedin ads mcp'; page itself says no official LinkedIn MCP |
| 1 | Salesforce | auth | web | yes(WebFetch) | yes |  |
| 58 | Sherlock | mcp | web | yes | yes(aggregator) | glama.ai aggregator; prompt forbids aggregators as evidence |
| 91 | NotebookLM | mcp | web | yes | yes |  |
| 98 | Mermaid CLI | mcp | web | yes(WebFetch) | yes(trivial) | package slug; publisher myxvisual, not mermaid-js |
| 56 | Firecrawl | mcp | web | yes | yes |  |

## 5. Overall assessment

**The pass‑2 facts are mostly right. The accuracy story on the page is not.**

- Field‑level facts hold up. Dev access class, auth and official MCP agree with an independent re‑check at about 90–97% on 30 fresh apps, and the quotes are overwhelmingly real (39/40 present today). The "MCP is now the norm" finding is real: about 80 of 95, not 81, and roughly a tenth of those are beta, EAP or preview.
- The **verdict** column and everything built on it (easy‑win list, blocker chart, category easy counts, outreach list) is the weak part. It rests on a rubric with a prod‑paid‑plan hole and unknown‑means‑easy defaults, it was tuned on gold B after scoring, and its blocker inputs are fields no evidence or gate ever checks.
- **Headline numbers that are wrong or misleading:** gold‑B verdict 65% (pre‑specified rubric gives 55%, below memory); gold‑A verdict 53% (bug, should be 59%, still below memory's 71%); "34 of them"; "the 5 that most need a person" (lists 7); the Mailchimp/Magento/Shopify caveat on the 81; "did not improve" (it got worse); the Lark/Sentry/Grain explanation; "lenient" auth scoring; "committed before anything else"; and the Sonnet/Opus/529 account, which has no artefact behind it.

### What should change
1. Report gold‑B verdict under v1 (55%) as the primary number. Show v2 only as an explicitly post‑hoc sensitivity row. Say plainly that verdict accuracy fell versus memory on both gold sets.
2. Fix `score.py` (unknown = unknown counts as correct, and within‑one should report excluded rows). Fix `verdict.py` (prod `paid_plan` → PAID_PLAN; `dev=unknown` → unknown or caveat, never easy). Then regenerate.
3. Make the gate reset any decision‑driving field that has **no** quote, and add evidence categories for tenancy and admin_only, or drop those blockers from the headline chart.
4. Bind each quote to its URL (store a URL plus fetch hash per saved file and check the quote in *that* file), raise the minimum quote length, and treat aggregator or third‑party pages as non‑evidence for "official" claims.
5. Change Pinterest to not launched or announced. Fix Magento auth (OAuth 1.0a), iPayX access (paid) and Cloudflare access. Add a beta/preview flag next to "official".
6. Fix the page text items P1, P3, P8, P10–P15. Either add run logs for the Sonnet/Opus claim or drop it.
7. Get a real human to label a fresh random sample. Every current "check" is a Claude model checking Claude.
