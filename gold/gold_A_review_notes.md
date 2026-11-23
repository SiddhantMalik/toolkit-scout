# Independent review: toolkit-scout (Composio take-home)

Reviewer scope: design critique, fact-check of pass-1 (`data/pass1_seed.txt`), schema/rubric proposal, and deliverable risks. Checked 2026-11-23 against live docs. Nothing under `/home/claude/toolkit-scout` was edited.

---

## 0. Headline

1. **The MCP column is the weakest part of pass 1.** I checked the MCP field for 26 apps and pass 1 was wrong on 19 of them, almost always by saying `none`/`community` where there is now an official server. Pass 1 was written from memory, and the 2025-26 wave of vendor MCP launches (Salesforce, Netlify, Zoho Cliq, Pylon, DealCloud, Brex, Squarespace, systeme.io, Clay, Consensus, Higgsfield, Meta Ads, Close, Reducto, MrScraper, WooCommerce) isn't in it.
2. **Three verdicts flip outright.** Consensus, Clay and Otter are marked "no public API / hard", but all three have a public API and an official MCP. Consensus is wrong in all 5 fields.
3. **Entity resolution is a silent failure mode.** `Paygent Connect` points at a Japanese PSP (paygent.co.jp). There are at least two other "Paygent"s, and none of them has a product called "Connect". `fanbasis` has been renamed Commas, and every docs subdomain redirects to a marketing page. `YouTube Transcript` points at a third-party service (transcriptapi.com). These need a human decision, so the agent should abstain on them.
4. **"90/100 fetched" overstates coverage.** 10 of the 90 "ok" fetches are JS shells or challenge pages under 1,000 chars (Gumroad is 3 chars, Xero 40, iPayX 59, Consensus 74). Another 21 of the 90 produced *zero* signals of any kind, HubSpot included. Real usable coverage is about 70.
5. **Regex counts work for routing and are unsound for determinations.** The concrete false positives are in §1.1. Gating and access are semantic, conditional claims. Treat them as extraction targets with quoted evidence, not as keyword frequencies.

My sample was **deliberately biased toward suspicious and obscure apps**, so the error rate below is not an estimate of pass-1 accuracy on all 100. Don't quote it as one.

---

## 1. Design critique

### 1.1 Is regex signal counting a sound basis for auth/gating?

No. It's useful as a cheap *retrieval and routing* layer: it tells you which pages and sentences to read. It's unsound as the *decision* layer. Here's what it gets wrong in the current evidence:

| Failure class | Concrete example from `data/evidence` |
|---|---|
| Endpoint and data names match auth/gating patterns | Gladly `jwt=8` comes from the endpoint "Create a User Identity JWT", and the API is actually Basic auth. Gladly `paid=4` comes from "upgrade my account" in *sample JSON payloads*. |
| Domain vocabulary collides | Telegram `gated=15` comes from "suggested post approved" and "need to be approved by supergroup administrators". The Bot API is fully self-serve. |
| Product names collide | Vercel `free=75` is the `/v2/sandboxes` endpoint family, not a free tier. |
| Nav chrome counted as content | MCP hits for Pylon, DealCloud, Brex and Squarespace come from the sidebar. That happens to be correct here, but the count says nothing about what the MCP does or who publishes it. |
| Docs-MCP vs product-MCP | BigCommerce's "MCP Server" lets you query the *developer docs*. Plaid's hit is a docs-bot MCP. Paygent's `_mcp/server` is a docs MCP. Regex counts all of these as `mcp`. |
| Absence ≠ negative | 21 of the 90 "ok" pages have zero signals (HubSpot, Zendesk, Help Scout, Snowflake, Airtable, Ramp...). An overview page that never says "OAuth" doesn't mean there's no OAuth. |
| JS-rendered / challenge pages | Lark 15 chars, Gumroad 3, Xero 40, QuickBooks 62, Binance 72, iPayX 59, Pinterest 113, Airtable 163. Consensus docs return a Cloudflare challenge. All of these are still flagged `ok=True` because `blob` is non-empty. |
| Wrong entity → confident wrong evidence | #84 fetched a Japanese PSP homepage. #50 fetched the Commas marketing page. #37, #59 and #97 fetched marketing homepages, not docs. |
| Length bias | Freshdesk is 611k chars (apikey=86) and Pumble is 1.7k. Raw counts aren't comparable across apps. |
| Over-broad patterns | `oauth2` matches `access_token`, which appears in almost any bearer-token API. `bearer` matches "private app". `gated` matches "approved", "approval" and "allowlist" (IP allowlists are a security feature, not a gate). `paid` matches "upgrade". |
| Conditions are invisible | The actual gating facts are sentences like "Only Admin users can create API tokens" (Pylon), "Available on all plans" (Pumble), "Contact the team for API access and pricing" (Waterfall), "Enterprise workspaces only" (Otter API), "require ... an active Gemini Notebook Enterprise license" (NotebookLM), or KYC before key creation (Binance). Regex can't tell the *subject* or the *scope* of the condition. |
| Two-stage access | Plaid, WhatsApp Cloud API, Meta Ads, Amazon SP-API and Pinterest all have a self-serve sandbox/dev tier plus a production approval step. A single `access` label loses that. |

**Recommendation.** Keep regex/keyword hits to *locate* candidate pages and sentences, and prefer `llms.txt` and `.md` page variants where they exist. Pylon, systeme.io, Waterfall, Consensus, Higgsfield, Paygent and Gladly all expose them, and they're cleaner than scraped HTML. Then run an LLM extraction pass where **every field must carry a verbatim quote plus a URL**, and check deterministically that the quote string actually appears in the fetched text. If the quote isn't found, the field becomes `unknown`. Also follow links one hop to auth, pricing and MCP pages, because the overview page rarely holds the gating facts.

### 1.2 Is the pass-1 → pass-2 accuracy framing honest?

It can be. As currently set up it's vulnerable in five ways:

- **What is ground truth?** If pass 2 gets scored against the documents pass 2 itself chose, or graded by the same model, the score is circular. Ground truth has to be a **gold set labelled by a human from primary docs**, with a quote and URL per field, **before** looking at pass-2 output.
- **Who is "the human"?** That's the candidate, who also built the pipeline, which creates confirmation bias. Mitigations:
  - Freeze the gold labels in a committed file (timestamp or hash) before the scored pass-2 run.
  - Label the verdict field against the written rubric (§3), not by gut feel.
  - If possible, double-label about 10 apps in a separate session and report agreement (Cohen's κ), especially for `verdict` and `access`.
- **Leakage and overfitting.** If prompts or regexes get tuned on the same 25 apps that are then scored, the pass-1 → pass-2 jump is partly training-set accuracy. Split into a **dev sample** (iterate freely) and a **held-out test sample** (scored once). Also disclose hand edits: any field a human fixed must be marked `source=human` and excluded from "agent accuracy".
- **Secondary sources as gold.** Aggregators (mcpservers.org, apitracker, Scalekit/Truto blogs, and **composio.dev/toolkits/***, which already lists Otter, Clay, Higgsfield, Copper and others) are fine as *leads*. They're not gold. Using Composio's own catalog as truth would also be awkward in front of Composio.
- **Strawman baseline.** Memory-only pass 1 is a weak baseline. Most of the gain will be *freshness* (MCP launches, renames), not reasoning. Say that plainly. If you can, add a fairer middle baseline such as "single web search, no verification loop".

Report the results honestly:

- **Per-field accuracy**, not just one aggregate number.
- **n and a 95% Wilson CI.** At n=25, ±15–20 pp is normal.
- **Coverage and abstention separately.** `unknown` is neither correct nor silently dropped.
- **The confusion pattern**, for example "pass 1 under-reports MCP".
- **The retrieval date**, because facts move. Ahrefs, for example, now sells API access on Lite and above, not just Enterprise.

### 1.3 A credible verification protocol

1. **Sample.** Draw 25–30 apps at random, stratified by the 10 categories × pass-1 verdict bucket, and fix the seed. Add any apps flagged ambiguous to a separate "hard cases" list rather than the random sample.
2. **Gold labelling.** A human opens the primary docs (auth page, pricing/plan page, MCP page). For each field, record the value from the controlled vocabulary (§3), a verbatim quote, the URL and the date. Mark `unverifiable` if the docs aren't public. Freeze the labels.
3. **Agent pass 2.** Extraction with mandatory quotes, then a quote-presence check, then a rubric-derived verdict.
4. **Verification loop.**
   - A second-model or second-prompt "skeptic" re-reads only the cited quote and asks whether it supports the value.
   - Disagreements trigger one more retrieval hop: the auth page, the pricing page, and a `<vendor> MCP` search restricted to the vendor's domain.
   - Anything still contested goes to the human queue.
   - Log each loop iteration's per-field accuracy against gold. That log is the "accuracy rising" chart.
5. **Score** the held-out set once and publish the gold file, the predictions file and the scoring script.
6. **Error analysis.** Pick 5 errors that remain after pass 2, explain why each happened, and say what would fix it.

---

## 2. Fact-check of pass 1 (28 apps, all 10 categories)

Legend: ✓ = pass-1 value supported; ✗ = wrong (corrected value given); ~ = partially right or needs a better vocabulary; ? = could not verify from public docs.

| # | App (category) | Pass-1 (auth / access / api / mcp / verdict) | Field-level findings | Evidence URL |
|---|---|---|---|---|
| 1 | Salesforce (CRM) | oauth2 / self / rest+graphql / community / easy | **mcp ✗ → official** (Salesforce Hosted MCP Servers, GA Apr 2026). Others ✓. The seed docs URL returns 403 to the fetcher. | https://developer.salesforce.com/blogs/2026/04/salesforce-hosted-mcp-servers-are-now-generally-available |
| 8 | Close (CRM) | apikey,oauth2 / trial / rest / community / easy | **mcp ✗ → official** (an "MCP Server" section in Close's dev platform). Others ✓. | https://developer.close.com/ |
| 10 | DealCloud (CRM) | oauth2 / gated / rest / none / hard | auth ✓ ("Requesting an OAuth2 Bearer Token" from API keys); access ✓ (customer tenant); **mcp ✗ → official** (/mcp: Getting Started, Authentication, Available Tools, Custom MCP Servers). | https://api.docs.dealcloud.com/mcp/getting-started |
| 15 | Pylon (Support) | token / paid / rest / none / caveat | auth ✓ (Bearer; "Only Admins can create and manage API tokens"; US/EU regional hosts); access ~ (no public self-serve signup, "Book a demo", so closer to `sales_contact` than `paid`); **mcp ✗ → official** (mcp.usepylon.com, OAuth 2.0 or API token). | https://docs.usepylon.com/pylon-docs/developer/api/authentication.md , https://docs.usepylon.com/pylon-docs/integrations/pylon-mcp.md |
| 20 | Gladly (Support) | basic / gated / rest / none / hard | All ✓. Basic auth is agent email + API token. I found no vendor MCP, only third-party ones (StackOne, Truto). The evidence regex wrongly reports `jwt=8` and `paid=4`. | https://developer.gladly.com/llms.txt , https://www.stackone.com/connectors/gladly/mcp/ |
| 23 | Zoho Cliq (Comms) | oauth2 / self / rest / none / easy | **mcp ✗ → official** (Zoho Cliq MCP Server). Others ✓. | https://www.zoho.com/cliq/help/platform/zoho-cliq-mcp.html |
| 25 | Pumble (Comms) | apikey / paid / rest / none / caveat | auth ✓; **access ✗ → self (free)**: "Available on all plans". The blocker "new API" is unsupported. The real caveat is a narrow action set via the API add-on (messages, replies, reactions, channels). Verdict should be easy or caveat for narrow scope. | https://pumble.com/help/integrations/add-pumble-apps/api-keys-integration |
| 32 | Meta Ads (Marketing) | oauth2 / gated / rest / none / hard | **mcp ✗ → official** ("Ads MCP Server: Overview, Get started, Available tools" in Meta's docs). Access and verdict ✓ (app review). | https://developers.facebook.com/documentation/ads-commerce/ (Ads MCP Server section) |
| 37 | systeme.io (Marketing) | apikey / paid / rest / none / caveat | auth ✓ (`X-API-Key`); **api ✗: broad, not "thin"** (contacts, tags, fields, funnels, communities, automations, booking calendar, webhooks); **mcp ✗ → official** (an MCP key from "MCP & API keys"); **verdict ✗ → easy**; access ? (the docs state no plan restriction, so `paid` is unsupported). The seed evidence URL is the marketing homepage. | https://developer.systeme.io/reference/api.md , https://developer.systeme.io/docs/mcp-server.md |
| 42 | WooCommerce (Ecom) | basic / self / rest / none / caveat | **auth ~ → api_key (consumer key/secret) sent via Basic or query**; **mcp ✗ → official** (WooCommerce MCP, beta from 10.x, abilities API). Verdict ✓ (per-store URL). | https://developer.woocommerce.com/docs/features/mcp/ |
| 43 | BigCommerce (Ecom) | oauth2,token / trial / rest / none / easy | api ~ (REST **and GraphQL**, per the docs "Complete REST and GraphQL API docs"); mcp ~ (a **docs-only** MCP exists, so the vocabulary needs a `docs_only` value). | https://docs.bigcommerce.com/developer/docs/overview/quick-start |
| 46 | Squarespace (Ecom) | oauth2,apikey / paid / rest / none / caveat | **mcp ✗ → official** ("MCP support for Claude and ChatGPT"). Others plausible. | https://developers.squarespace.com/ |
| 50 | fanbasis (Ecom) | apikey / paid / rest / none / caveat | **Entity drift: FanBasis has been renamed Commas.** docs., developers., apidocs. and api. all redirect to the commas.com marketing page. I found no public API docs, so auth/access/api are **?** (unsupported by evidence). The only hint is a customer quote saying "The API is clean". Should be `unknown`, needs a human. | https://commas.com/ (banner "FanBasis is now Commas!") |
| 53 | Ahrefs (Data/SEO) | apikey / paid / rest / official / caveat | All ✓. API units are included on Lite and above, with free test queries on any paid plan. | https://help.ahrefs.com/en/articles/6559232-about-api-v3 , https://docs.ahrefs.com/api/docs/free-test-queries.md |
| 54 | MrScraper (Data/SEO) | apikey / trial / rest / none / caveat | **mcp ✗ → official** (an "MCP Server" docs page). auth ~ ("API token"). The blocker is "-" while the verdict is caveat, which is inconsistent. | https://docs.mrscraper.com/docs/getting-started/overview |
| 59 | Waterfall.io (Data/SEO) | apikey / paid / rest / none / caveat | auth ✓ (`x-api-key`, master key plus sub-keys); api ✓ (broad async launcher/finder REST); **access ✗ → sales_contact**: "Contact the team for API access and pricing". Verdict should be caveat or hard depending on the rubric (sales-gated). The seed URL is the marketing homepage. | https://docs.waterfall.io/v1/authentication.md |
| 60 | Clay (Data/SEO) | apikey / paid / none / none / hard | **api ✗ → rest** (a Public API in beta with a `clay-api-key` header; table query is Enterprise-only); **mcp ✗ → official** (hosted and local, OAuth only; npm `@clayhq/clay-mcp`); **verdict ✗ → caveat**. *Source is secondary (Scalekit): confirm against Clay's own docs before publishing.* | https://www.scalekit.com/blog/clay-mcp-vs-api , https://npmjs.com/package/@clayhq/clay-mcp |
| 63 | Netlify (Dev) | token,oauth2 / self / rest / community / easy | **mcp ✗ → official** (netlify/netlify-mcp). The seed docs URL returns 404. | https://docs.netlify.com/welcome/build-with-ai/netlify-mcp-server , https://github.com/netlify/netlify-mcp |
| 79 | Smartsheet (Productivity) | oauth2,token / paid / rest / official / caveat | mcp ✓ (official, GA). **The seed docs URL is a 404**; the correct one is developers.smartsheet.com/api/smartsheet/introduction. | https://developers.smartsheet.com/api/smartsheet/ai-integration/mcp-server |
| 82 | Plaid (Fintech) | apikey / self / rest / official / caveat | auth/access/verdict ✓ (sandbox free, production approval). mcp ~: the evidence hit is a **docs-assistant MCP**, so the type should be recorded. | https://plaid.com/docs/ |
| 83 | Binance (Fintech) | apikey / self / rest / community / caveat | access ~: API key creation needs a verified (KYC) account and is region-restricted, so `self` hides that gate. The blocker "trading actions prohibited" is unexplained. Say whether it's a Composio policy choice or a vendor fact. | https://www.binance.com/en/support/faq/360002502072 |
| 84 | Paygent Connect (Fintech) | apikey / gated / rest / none / hard | **Entity unresolved.** The seed resolved to PAYGENT Co. (a Japanese PSP, merchant contract). Other candidates: Paygent (withpaygent.com: AI-agent billing, self-serve API key, SDKs, docs MCP) and a Solana "Paygent" storefront. **No product called "Paygent Connect" was found.** Every field is conditional on the entity, so this should go to the human queue. | https://www.paygent.co.jp/ , https://docs.withpaygent.com/llms.txt , https://paygent-solana.vercel.app/docs |
| 85 | iPayX (Fintech) | apikey / self / rest / none / caveat | **mcp ✗ → exists** (iPayX FX Audit MCP. Publisher attribution is ambiguous: hosted on workers.dev, Smithery account `ybolduc`). auth ~ (3 tools need no auth with an IP-based free cap; the forensic report needs a paid bearer key). The seed docs URL is a 59-char JS shell. | https://mcpservers.org/servers/ipayx-technologies/mcp-fx-audit |
| 88 | Brex (Fintech) | oauth2,token / gated / rest / none / caveat | **mcp ✗ → official** (developer.brex.com/docs/mcp). Others ✓. | https://developer.brex.com/llms.txt |
| 91 | NotebookLM (AI) | oauth2 / gated / rest / none / hard | Mostly ✓. The API exists only for NotebookLM (Gemini) Enterprise: you need a license, the `discoveryengine.notebookLmUser` role and GCP user OAuth. Access is better labelled `paid_enterprise_license` than `gated`. Consumer NotebookLM has no API. | https://docs.cloud.google.com/gemini/enterprise/notebooklm-enterprise/docs/api-notebooks |
| 92 | Otter AI (AI) | oauth2 / gated / none / official / hard (no public API) | mcp ✓ (official, OAuth 2.1, standard accounts); **api ✗ → rest** (bearer API key, **Enterprise workspaces only**); auth ~ (oauth2 for MCP, api_key for REST); **verdict ✗ → caveat** (the MCP path is self-serve; the blocker "no public API" is false). Secondary source; Otter's help centre returned 403. | https://www.scalekit.com/blog/otter-mcp-vs-api , https://claude.com/connectors/otter-ai |
| 94 | Consensus (AI) | none / gated / none / none / hard (no public API) | **All five fields ✗.** There's a public API (`GET /v1/search`, a "Create API key" CTA), so auth → api_key, api → rest, mcp → official ("Use Consensus in ChatGPT, Claude, Copilot, or with the API"), verdict → easy or caveat (pricing for API tiers not verified). | https://consensus.app/home/api/ , https://docs.consensus.app/llms.txt |
| 95 | Reducto (AI) | apikey / self / rest / none / easy | **mcp ✗ → official** ("Reducto MCP server" in the docs nav). | https://docs.reducto.ai/ |
| 97 | higgsfield (AI) | apikey / paid / rest / none / caveat | auth ~ (custom `Authorization: Key <id>:<secret>`; record the key-pair scheme); **mcp ✗ → official** (MCP in the product nav, plus a help-centre "connect Higgsfield to AI agent"); the blocker "unknown" should be replaced (credit-based paid usage). The seed URL is the marketing homepage; the docs are at docs.higgsfield.ai. | https://docs.higgsfield.ai/docs/authentication.md , https://higgsfield.ai/ |

**Tally on this (biased) sample:**

| Field | Checked | Pass-1 wrong |
|---|---|---|
| `mcp` | 26 | 19 |
| `api` | 28 | 4 (Clay, Otter, Consensus, systeme breadth) |
| `access` | 28 | 4 clear (Pumble, Waterfall, Consensus, Binance) plus 2 vocabulary issues |
| `auth` | 28 | 2 clear plus 4 partial |
| `verdict` | 28 | 5 (Consensus, Clay, Otter, systeme, Pumble) |
| Entity unresolved | — | 2 (Paygent Connect, fanbasis) |
| Broken or marketing-page evidence URLs | — | 9 |

Mainstream gated apps were right: Gladly, Ahrefs, NotebookLM and Smartsheet were essentially correct.

**Also flag for human review:** YouTube Transcript (#99) maps to a third-party product, transcriptapi.com, rather than YouTube's own captions API, which is OAuth and owner-only. Sherlock (#58) is assumed to be the OSINT CLI; confirm the intended entity. Mermaid CLI (#98) is CLI-only, but Mermaid Chart (the company) has a hosted API/MCP, so state which one you mean.

---

## 3. Recommended schema, vocabulary and rubric

### 3.1 Record schema (one per app)

```jsonc
{
  "id": 37, "name": "systeme.io", "category": "Marketing, Ads, Email and Social",
  "entity": {"resolved_name": "Systeme.io", "homepage": "...", "docs_root": "...",
             "status": "resolved|renamed|ambiguous|not_found", "notes": "..."},
  "description": "one line",
  "auth": [{"method": "api_key_header", "detail": "X-API-Key", "issuer": "any_user|admin_only|partner_app"}],
  "access": {"dev": "self_free|self_trial|paid_plan|sales_contact|customer_only|partner_review|kyc_verification|enterprise_license",
             "prod": "same enum or same_as_dev",
             "min_plan": "free|<plan name>|unknown"},
  "api": {"styles": ["rest","graphql","soap","grpc","websocket","cli_only","sdk_only","none"],
          "breadth": "narrow|moderate|broad", "write": true, "webhooks": true,
          "openapi_url": null, "tenancy": "global|per_subdomain|per_region|self_hosted"},
  "mcp": {"type": "official_remote|official_local|docs_only|community|aggregator_only|none",
          "url": null, "auth": "oauth|api_key|none"},
  "verdict": {"label": "easy|caveat|hard|no", "blocker_codes": ["PAID_PLAN","ADMIN_TOKEN"], "rule_fired": "R3"},
  "evidence": [{"field": "auth", "url": "...", "quote": "verbatim", "retrieved": "2026-11-23",
                "source_tier": "primary_docs|vendor_blog|secondary|memory"}],
  "confidence": "high|medium|low",
  "provenance": "agent|agent+verified|human",
  "last_checked": "2026-11-23"
}
```

Confidence rule: **high** means every key field has a primary-docs quote that passed the quote-presence check. **medium** means at least one field rests on a vendor blog or secondary source. **low** means memory, inference or an `unknown` field.

### 3.2 Blocker codes (controlled)

`NONE, PAID_PLAN, ENTERPRISE_ONLY, SALES_CONTACT, CUSTOMER_ONLY, PARTNER_PROGRAM, APP_REVIEW, PROD_APPROVAL, KYC_OR_BUSINESS_VERIFICATION, ADMIN_ONLY_CREDENTIAL, PER_TENANT_HOST, PER_REGION_HOST, NARROW_SURFACE, BETA_OR_UNSTABLE, NO_API, CLI_ONLY, ENTITY_UNRESOLVED, DOCS_NOT_PUBLIC, TOS_RESTRICTION`

### 3.3 Buildability rubric (first matching rule wins, so it's reproducible)

| Rule | Condition (all from evidence fields) | Verdict |
|---|---|---|
| R0 | `entity.status ∈ {ambiguous, not_found}` or every key field is `unknown` | **unknown** (human queue; never guessed) |
| R1 | No network API and no hosted MCP (`api.styles ⊆ {cli_only, none}` and `mcp.type ∈ {none, docs_only}`) | **no** |
| R2 | Dev credentials need `customer_only`, `sales_contact`, `partner_review`, `enterprise_license` or `kyc_verification` **and** there's no self-serve MCP or sandbox path | **hard** |
| R3 | Self-serve credentials exist, but at least one friction applies: `paid_plan`, `prod` stricter than `dev`, `admin_only` issuer, per-tenant/region host, `narrow` breadth, beta API, or the only self-serve path is MCP while REST is gated | **caveat** (list every applicable blocker code) |
| R4 | Self-serve free or trial creds, OAuth2 or key, global host, moderate or broad read+write REST/GraphQL | **easy** |

Applied to the corrections above: Consensus → R4 (or R3 if the API is paid). Otter → R3 (REST is enterprise-gated, MCP is self-serve). Clay → R3 (beta API, enterprise features). Waterfall → R2 (sales-contact). Pumble → R3 (`NARROW_SURFACE`) or R4. systeme.io → R4.

Accuracy scoring per field:

- `auth`: set Jaccard, plus exact-match rate.
- `access.dev`: exact.
- `api.styles`: set exact.
- `mcp.type`: exact, plus a collapsed binary "has vendor MCP".
- `verdict`: exact and within-one, with the confusion matrix.

---

## 4. Top risks for the final deliverable and what a Composio reviewer will probe

1. **Spot-checks on obscure apps.** A Composio engineer will open Consensus, Clay, Otter, Higgsfield, Paygent and fanbasis first, because those are where research agents hallucinate. Get those exactly right or mark them `unknown`.
2. **The MCP column.** Composio knows the MCP landscape intimately, and its own catalog already has toolkits for several of these apps (Otter, Clay, Higgsfield, Copper). Under-reporting official MCPs reads as "stale research". Distinguish official remote, official local, docs-only, and aggregator.
3. **Unreproducible accuracy claims.** Expect "Show me the gold file, the scoring script, n, and which apps were in the sample. Was the sample chosen before or after you saw results?" Publish `gold.jsonl`, `pred_pass1.jsonl`, `pred_pass2.jsonl` and `score.py`, and generate the HTML numbers from them, never by hand.
4. **Human-in-the-loop honesty.** Log every human intervention (entity decisions, URL fixes, overrides) with a reason. Fields fixed by hand must not count as agent accuracy. The assignment explicitly asks where a human was needed. Expected answers: entity resolution, JS-only or login-walled docs, sales-gated pricing, and verdict judgment calls.
5. **Evidence-URL quality.** 9 of the URLs I checked are 404/403, a JS shell, or a marketing homepage. A reviewer will click 5 links at random. Every evidence URL should be a docs page that contains the quoted sentence.
6. **Pattern claims built on noisy fields.** Cross-100 patterns ("X% need paid plans", "MCP adoption by category") inherit every labelling error. Compute them only from `confidence ≥ medium` rows, and report the denominator.
7. **Verdict subjectivity.** Without the rubric, "caveat vs hard" looks arbitrary. Show the rule that fired and the blocker codes for each app.
8. **Strawman baseline.** If pass 1 is memory-only and pass 2 has web access, a reviewer will say the improvement is obvious. Frame it as measuring *what verification catches*: MCP freshness, renames, entity errors, gating nuance.
9. **Time sensitivity.** Put a "retrieved on" date on every row and on the page. MCP and plan facts changed within months (Salesforce MCP went from beta in Oct 2025 to GA in Apr 2026).
10. **Scraping hygiene.** The fetcher gets 403s and Cloudflare challenges. Don't claim coverage you don't have. Report usable-text coverage (about 70–80), not HTTP-200 coverage (90).
11. **Confident wrongness vs abstention.** A reviewer will value "unknown, needs sales contact, here's why" far more than a guessed value. Make abstention a first-class output and count it in the metrics.
