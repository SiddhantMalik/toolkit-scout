# Stage 2 extraction prompt (used verbatim by every extractor agent)

You research developer-API facts for apps so a team can decide whether an agent toolkit can be built. Date today: 2026-11-23.

For each assigned app id, produce ONE JSON line in the output file. Use ONLY primary vendor sources (their docs, pricing, help center, GitHub org). Aggregators (composio.dev, mcpservers.org, apitracker, review blogs) are leads only, never evidence.

Inputs available to you
- /home/claude/toolkit-scout/data/pass1_seed.txt  -> app name, category, starting docs URLs (column 4). IGNORE its other columns (auth/access/api/mcp/verdict): they are an unreliable memory baseline; do not copy them.
- /home/claude/toolkit-scout/data/evidence/<id>.txt -> cleaned text of pages already fetched for that app (may be empty/thin/nav-noise). /home/claude/toolkit-scout/data/evidence_index.json lists which URLs were fetched.
- Shell can fetch many doc sites (python requests). WebSearch / WebFetch for discovery. If you fetch extra pages, save the cleaned text to /home/claude/toolkit-scout/data/evidence_extra/<id>_<n>.txt so quotes can be verified.
- DO NOT read anything under /tmp/review, /tmp/gold, /home/claude/toolkit-scout/gold, or the *.md files in data/. Do not read data/mcp_leads.json except as a hint.

Rules
1. Every field you set needs evidence: {"field","url","quote"} where quote is a VERBATIM sentence/phrase (<=30 words) copied from a page text you saved/read. If it only came from WebFetch/WebSearch, still quote it but set "src":"web". If you cannot find a quote, set the field to "unknown". Never guess.
2. Open the auth page, the pricing/plan or access page, and look specifically for MCP (vendor docs, vendor GitHub org, vendor changelog). 'official' MCP = published by the vendor itself.
3. Resolve the entity first. If the named app is ambiguous, renamed, or you cannot find a product matching the hint, set entity_status to "ambiguous"/"renamed"/"not_found" and explain; still extract what you can for the best candidate but label it.
4. Two-stage access: record access_dev (what a developer needs to get working credentials) and access_prod (what is needed to use it on other customers' accounts / production), e.g. app review, partner approval, KYC.

Output schema (one line per app, JSON):
{"id":int,"name":str,
 "entity_status":"resolved|renamed|ambiguous|not_found","entity_note":str,
 "description":"one line what the app does",
 "auth":[subset of "oauth2","api_key","basic","bearer_token","jwt","other","none"],
 "access_dev":"self_free|self_trial|paid_plan|sales_contact|customer_only|partner_review|enterprise_license|kyc_verification|unknown",
 "access_prod":"same_as_dev|self_free|self_trial|paid_plan|sales_contact|customer_only|partner_review|enterprise_license|kyc_verification|app_review|unknown",
 "min_plan":str,
 "admin_only_credential":bool|null,
 "api_styles":[subset of "rest","graphql","soap","grpc","websocket","cli_only","sdk_only","none"],
 "api_breadth":"narrow|moderate|broad|unknown",
 "api_beta":bool|null,
 "tenancy":"global|per_subdomain|per_region|self_hosted",
 "mcp_type":"official_remote|official_local|docs_only|community|none|unknown",
 "mcp_url":str|null,
 "docs_url":"best primary docs/auth URL (must be a docs page, not a marketing home)",
 "evidence":[{"field":"auth|access|api|mcp|entity","url":str,"quote":str,"src":"file|web"}],
 "confidence":"high|medium|low",
 "needs_human":str|null}
Set confidence=high only if auth, access and mcp each have a quote from a primary page. Set needs_human with the specific question whenever you are unsure (entity, login-walled docs, pricing not public).
Write the file path you are given, one JSON object per line, valid JSON only. When done, reply with one line: the path and count.
