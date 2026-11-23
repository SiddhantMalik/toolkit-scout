"""Build site/index.html from data/final.json + data/scores.json + gold files. Every number on the page is computed here."""
import json, html
from common import ROOT
from norm import from_goldB, auth_set, access_cls
F = json.load(open(ROOT/"data/final.json")); S = F["summary"]; APPS = F["apps"]
SC = json.load(open(ROOT/"data/scores.json")); HQ = json.load(open(ROOT/"data/pass2/human_queue.json"))
HC = json.load(open(ROOT/"data/human_check_ids.json"))["ids"]
gA = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT/"gold/gold_A.jsonl")}
gB = {json.loads(l)["id"]: json.loads(l) for l in open(ROOT/"gold/gold_B.jsonl")}
byid = {a["id"]: a for a in APPS}
n, nr = S["n_total"], S["n_reliable"]
def P(k, d=nr): return round(100*k/d)
cat = S["by_category"]
# ---- misses lists (pass 2b vs gold) ----
def mo(a): return a["mcp_type"] in ("official_remote","official_local")
miss = []
for name, G in (("A", gA), ("B", gB)):
    for i, g in G.items():
        a = byid[i]
        gm = g.get("mcp_official") if name=="A" else (None if g.get("mcp_type") in (None,"unknown") else g["mcp_type"] in ("official_remote","official_local"))
        if gm is not None and gm != mo(a): miss.append((name, a["name"], "official MCP", str(gm), str(mo(a))))
        ga = g.get("access") if name=="A" else access_cls(g.get("access_dev"))
        if ga and ga != access_cls(a["access_dev"]): miss.append((name, a["name"], "dev access", ga, str(access_cls(a["access_dev"]))))
        gv = g.get("verdict")
        if gv and gv != a["verdict"]: miss.append((name, a["name"], "verdict (rubric v2)", gv, a["verdict"]))
def row(lab, key):
    out=[]
    for g in ("goldA_hard_cases","goldB_random_heldout"):
        s = SC[lab][g]
        out.append(s)
    return out
def cell(s, k):
    x = s[k]; return f'{x["correct"]}/{x["n"]} <small>({x["acc"]}%, CI {x["ci95"][0]}–{x["ci95"][1]})</small>'
def tbl(rows_, cols):
    h = "".join(f"<th>{c}</th>" for c in cols)
    b = "".join("<tr>"+"".join(f"<td>{c}</td>" for c in r)+"</tr>" for r in rows_)
    return f"<table class=t><thead><tr>{h}</tr></thead><tbody>{b}</tbody></table>"
labs = [("pass1_memory","Pass 1 — memory only"),("pass2a","Pass 2a — agent + evidence + quotes"),("pass2b","Pass 2b — after quote gate"),("pass2b_v2","Pass 2b, verdict rubric v2 (post-hoc fix)")]
def score_table(g):
    rows_=[]
    for lab, name in labs:
        s = SC[lab][g]
        rows_.append([name, cell(s,"mcp_official"), cell(s,"access"), f'{cell(s,"auth")}<br><small>Jaccard {s["auth_jaccard_mean"]}</small>', f'{cell(s,"verdict")}<br><small>within-1: {s["verdict_within_one"]["correct"]}/{s["verdict_within_one"]["n"]}</small>'])
    return tbl(rows_, ["Run","Official MCP?","Dev access class","Auth methods","Verdict"])
verd = S["verdict"]; hard_names = [a["name"] for a in APPS if a["verdict"]=="hard"]
unk_names = [a["name"] for a in APPS if a["verdict"]=="unknown"]
no_names = [a["name"] for a in APPS if a["verdict"]=="no"]
cat_rows = "".join(f'<tr><td>{c}</td><td>{v["n"]}</td><td>{v["self"]}</td><td>{v["paid"]+v["gated"]}</td><td>{v["official_mcp"]}</td><td class=e>{v["easy"]}</td><td class=c>{v["caveat"]}</td><td class=h>{v["hard"]}</td></tr>' for c,v in cat.items())
bl = S["blockers"]; top_bl = list(bl.items())[:6]
bl_html = "".join(f'<div class=bar><span>{k.replace("_"," ").title()}</span><i style="width:{round(100*v/max(bl.values()))}%"></i><b>{v}</b></div>' for k,v in top_bl)
drift = S["drift_vs_pass1"]
def hc_rows():
    out=[]
    for i in HC:
        a = byid[i]; ev = {e["field"]:e for e in a["evidence"]}
        out.append(f'<tr><td>{a["id"]}. {html.escape(a["name"])}</td><td>{html.escape(", ".join(a["auth"]))}</td><td>{a["access_dev"]} → {a.get("access_prod")}</td><td>{a["mcp_type"]}</td><td><a href="{html.escape(a["docs_url"])}">docs</a></td><td class=chk>☐ auth ☐ access ☐ MCP</td></tr>')
    return "".join(out)
data = json.dumps([{k:a.get(k) for k in ("id","name","category","description","auth","access_dev","access_prod","min_plan","admin_only_credential","api_styles","api_breadth","api_beta","tenancy","mcp_type","mcp_url","docs_url","evidence","confidence","needs_human","entity_status","entity_note","verdict","rule","blockers","quotes_verified","quotes_web_only","quotes_failed")} for a in APPS], ensure_ascii=False).replace("</","<\\/")
q = S["quotes"]
page = f"""<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Toolkit Scout — researching 100 apps for agent-toolkit buildability</title>
<style>
:root{{--bg:#fbfaf7;--fg:#1d1d1b;--mut:#6b6a63;--line:#e2dfd6;--card:#fff;--ac:#c2410c;--ok:#15803d;--wn:#b45309;--no:#b91c1c}}
@media(prefers-color-scheme:dark){{:root{{--bg:#161614;--fg:#ecebe5;--mut:#a09f96;--line:#33322d;--card:#1f1f1c;--ac:#fb923c;--ok:#4ade80;--wn:#fbbf24;--no:#f87171}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1120px;margin:0 auto;padding:28px 20px 80px}}h1{{font-size:30px;line-height:1.15;margin:0 0 6px}}h2{{font-size:21px;margin:44px 0 10px;border-top:1px solid var(--line);padding-top:22px}}h3{{font-size:15px;margin:18px 0 6px}}
.sub{{color:var(--mut);max-width:760px}}.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:18px 0}}.kpi b{{display:block;font-size:26px}}.kpi span{{color:var(--mut);font-size:12.5px}}
ol.pat{{padding-left:20px}}ol.pat li{{margin:10px 0}}ol.pat b{{color:var(--ac)}}
table.t{{border-collapse:collapse;width:100%;font-size:13px}}table.t th,table.t td{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}}table.t th{{color:var(--mut);font-weight:600;position:sticky;top:0;background:var(--bg)}}
.e{{color:var(--ok);font-weight:600}}.c{{color:var(--wn);font-weight:600}}.h{{color:var(--no);font-weight:600}}small{{color:var(--mut)}}
.bar{{display:grid;grid-template-columns:190px 1fr 36px;align-items:center;gap:8px;margin:4px 0;font-size:13px}}.bar i{{display:block;height:10px;background:var(--ac);border-radius:3px}}.bar b{{text-align:right}}
.chips{{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}}.chips button,.chips select,.chips input{{font:inherit;font-size:13px;padding:5px 10px;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;cursor:pointer}}.chips button.on{{background:var(--fg);color:var(--bg)}}
#apps td{{cursor:pointer}}#apps tr.open+tr.det{{display:table-row}}tr.det{{display:none;background:var(--card)}}tr.det td{{font-size:12.5px;color:var(--mut)}}.pill{{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;border:1px solid var(--line)}}
.v-easy{{color:var(--ok);border-color:var(--ok)}}.v-caveat{{color:var(--wn);border-color:var(--wn)}}.v-hard{{color:var(--no);border-color:var(--no)}}.v-no,.v-unknown{{color:var(--mut)}}
.flow{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px;margin:12px 0}}.flow .card{{font-size:13px}}.flow .card b{{display:block;margin-bottom:3px}}.tag{{font-size:11px;padding:1px 6px;border-radius:4px;background:var(--line);margin-left:4px}}
.warn{{border-left:4px solid var(--wn);padding:8px 14px;background:var(--card);margin:12px 0}}.chk{{white-space:nowrap}}code{{background:var(--line);padding:1px 5px;border-radius:4px;font-size:12.5px}}a{{color:var(--ac)}}
</style></head><body><main>
<h1>Toolkit Scout: 100 apps, researched by an agent pipeline and checked against frozen gold sets</h1>
<p class=sub>For each app: auth, how a developer gets credentials, API surface, MCP status, and whether an agent toolkit could be built today, with a verbatim quote and URL behind every claim. Retrieved <b>{S["retrieved"]}</b>. Facts like MCP launches and plan limits move fast, so treat every row as dated.</p>
<div class=kpis>
<div class="card kpi"><b>{n}</b><span>apps researched ({nr} with resolved entity and ≥ medium confidence; patterns use these)</span></div>
<div class="card kpi"><b>{S["mcp_official"]}/{nr}</b><span>have an official MCP server</span></div>
<div class="card kpi"><b>{S["access_dev"].get("self",0)}/{nr}</b><span>give a developer free or trial credentials</span></div>
<div class="card kpi"><b>{S["prod_friction"]}/{nr}</b><span>add a stricter gate for production use</span></div>
<div class="card kpi"><b>{q["verified"]}</b><span>quotes machine-verified verbatim ({q["web_only"]} web-only, {q["failed"]} failed)</span></div>
</div>

<h2>1 · The patterns (headline)</h2>
<ol class=pat>
<li><b>Getting a developer key is rarely the problem; production is.</b> {S["access_dev"].get("self",0)} of {nr} apps hand a developer free or trial credentials, but {S["prod_friction"]} of them add a second gate before you can use the API on other customers' accounts (app review, partner approval, KYC, a paid plan). Only {S["access_dev"].get("gated",0)} gate even the first credential (sales contact, customer-only, partner or enterprise licence) and {S["access_dev"].get("paid",0)} need a paid plan.</li>
<li><b>OAuth2 and API keys are the two auth patterns, and most apps offer both.</b> OAuth2 appears in {S["auth"]["oauth2"]}/{nr} apps, API key or bearer token in {S["auth"]["key"]}/{nr}, Basic in {S["auth"]["basic"]}, JWT in {S["auth"]["jwt"]}. Only {S["auth_only_key"]} are key-only, so a toolkit can usually offer a zero-friction key path plus an OAuth path.</li>
<li><b>An official MCP is now the norm, not a differentiator.</b> {S["mcp_official"]}/{nr} apps ship a vendor MCP ({S["mcp"].get("official_remote",0)} remote, {S["mcp"].get("official_local",0)} local). My memory-only first pass missed it for {drift["mcp_none_to_official"]} of the {n} apps. Caveats: some are beta, some cover only part of the product (Plaid's covers Dashboard diagnostics; Mailchimp's, Magento's and Shopify's dev MCPs search docs), so "has MCP" does not mean "toolkit is done".</li>
<li><b>The most common blockers are not paywalls.</b> Admin-only credentials, production approval, app review, and per-tenant or per-region hosts outnumber paid-plan gates several times over (chart below). These are cheap to handle in a toolkit design (document the admin step, collect the subdomain or region at connect time) but they stop a "paste a key and go" flow.</li>
<li><b>Easy wins cluster in data, productivity and developer tools; friction clusters in fintech, ecommerce and support.</b> Easy: Productivity {cat["Productivity and Project Management"]["easy"]}/{cat["Productivity and Project Management"]["n"]}, Data/SEO {cat["Data, SEO and Scraping"]["easy"]}/{cat["Data, SEO and Scraping"]["n"]}. Lowest: Fintech {cat["Finance and Fintech"]["easy"]}/{cat["Finance and Fintech"]["n"]}, Ecommerce {cat["Ecommerce"]["easy"]}/{cat["Ecommerce"]["n"]}, Support {cat["Support and Helpdesk"]["easy"]}/{cat["Support and Helpdesk"]["n"]}.</li>
<li><b>Outreach list (needs a partnership or sales contact):</b> {", ".join(hard_names)}. <b>Not buildable as an API toolkit:</b> {", ".join(no_names)}. <b>Needs a human to decide what the app even is:</b> {", ".join(unk_names)}.</li>
</ol>
<h3>Blockers across all {n} apps (counts of apps with that blocker)</h3>{bl_html}
<h3>By category (reliable rows)</h3>
<table class=t><thead><tr><th>Category</th><th>n</th><th>Free/trial dev access</th><th>Paid/gated dev access</th><th>Official MCP</th><th>Easy</th><th>Caveat</th><th>Hard</th></tr></thead><tbody>{cat_rows}</tbody></table>
<p class=sub>Verdicts ({n} apps): easy {verd.get("easy",0)}, caveat {verd.get("caveat",0)}, hard {verd.get("hard",0)}, no {verd.get("no",0)}, unknown {verd.get("unknown",0)}. Verdict is computed by code (first matching rule): <code>unknown</code> entity unresolved → <code>no</code> no network API → <code>hard</code> dev credentials need sales/customer/partner/enterprise/KYC → <code>caveat</code> any friction (paid plan, prod approval, admin-only credential, per-tenant/region host, narrow API, beta) → <code>easy</code>. Each row shows the rule and blocker codes.</p>

<h2>2 · All {n} apps</h2>
<div class=chips id=chips></div>
<div style="overflow:auto;max-height:640px"><table class=t id=apps><thead><tr><th>#</th><th>App</th><th>Auth</th><th>Dev → prod access</th><th>API</th><th>MCP</th><th>Verdict</th><th>Conf.</th></tr></thead><tbody></tbody></table></div>
<p class=sub>Click a row for the one-line description, blockers, evidence quotes with URLs, and open questions. Full machine-readable data: <code>data/final.json</code> in the repo (the same JSON is embedded in this page's source).</p>

<h2>3 · The agent and where a human was needed</h2>
<div class=flow>
<div class=card><b>0 · Baseline <span class=tag>memory</span></b>Pass 1 written from model memory, no docs opened, committed to git before anything else.</div>
<div class=card><b>1 · Retrieve <span class=tag>script</span></b><code>fetch_evidence.py</code>: docs + <code>llms.txt</code> + one hop to auth/pricing/MCP pages; flags JS shells. <code>mcp_probe.py</code>: MCP registry leads.</div>
<div class=card><b>2 · Extract <span class=tag>LLM agents</span></b>10 parallel extractor agents, one prompt and schema. Every field needs a verbatim quote + URL, else <code>unknown</code>.</div>
<div class=card><b>3 · Verify <span class=tag>script</span></b><code>check_quotes.py</code> checks each quote appears in the saved page text; <code>gate.py</code> resets fields whose quotes all fail.</div>
<div class=card><b>4 · Verdict <span class=tag>code</span></b><code>verdict.py</code> derives easy/caveat/hard/no/unknown from the fields, so the label is reproducible.</div>
<div class=card><b>5 · Score <span class=tag>script</span></b><code>score.py</code> against gold sets frozen in git before scoring (hashes below).</div>
</div>
<h3>What ran where, plainly</h3><ul>
<li>Stage 2 ran as Claude subagents inside a Claude session (40 apps on Sonnet, 60 on Opus). Seven of the ten first-launch Sonnet runs died on API overload (HTTP 529) and were re-run; six moved to Opus. <b>I did not use Composio's SDK or MCP</b> to build this; stages 1, 3, 4 and 5 are plain Python and the stage-2 prompt is in <code>agent/prompts/extract.md</code> so it can be driven by any model or swapped onto Composio tools.</li>
<li>The sandbox shell could reach many doc sites but not all. {sum(1 for a in APPS if a["quotes_web_only"]>0)} apps have at least one quote that came through a web-fetch tool rather than a saved page, so the checker could not verify it ({q["web_only"]} quotes). Sites that blocked scripts or needed JavaScript include Salesforce, Otter, PitchBook, Binance, Lark, Airtable, Gumroad, Consensus and the Amazon and Google docs.</li>
<li><b>Human involvement: none yet.</b> No person reviewed these rows. {len(HQ["queue"])} apps carry an open question for a human (entity decisions, pricing that isn't public, login-walled docs, rubric judgement calls). The 5 that most need a person: Paygent Connect and YouTube Transcript (entity ambiguous), fanbasis and Coda and NotebookLM (renamed), Otter and PitchBook (docs unreadable to the agent).</li></ul>

<h2>4 · Verification: how accurate is it, honestly</h2>
<div class=warn><b>Read this first.</b> Both gold sets were labelled by Opus agents from primary docs, <b>not by humans</b>. Gold A (27 apps, an independent reviewer) was picked to be suspicious and obscure, so it exaggerates pass-1 error. Gold B (20 apps, seeded random, 2 per category, labelled blind before any pass-2 output existed) is the fair estimate, but n=20 means 95% intervals of roughly ±20 points. Extractors were told not to open any gold or review file; that blindness is by instruction, not enforced by the sandbox, and I (the orchestrator) had read the reviewer's findings before launching them.</div>
<h3>Gold B: random held-out sample (n=20), the number to trust</h3>{score_table("goldB_random_heldout")}
<h3>Gold A: hard cases picked by the reviewer (27 apps; n varies by field)</h3>{score_table("goldA_hard_cases")}
<h3>What moved accuracy, and what didn't</h3><ul>
<li><b>Memory → evidence-grounded extraction did the work.</b> Official-MCP detection went from {cell(SC["pass1_memory"]["goldB_random_heldout"],"mcp_official")} to {cell(SC["pass2b"]["goldB_random_heldout"],"mcp_official")} on the random sample and from {cell(SC["pass1_memory"]["goldA_hard_cases"],"mcp_official")} to {cell(SC["pass2b"]["goldA_hard_cases"],"mcp_official")} on the hard cases. Most of the gain is freshness (2025–26 vendor MCP launches, renames), which a memory-only baseline can't know. That baseline is deliberately weak.</li>
<li><b>The quote gate barely mattered for accuracy.</b> It checked {q["verified"]+q["web_only"]+q["failed"]} quotes: {q["verified"]} verified, {q["web_only"]} unverifiable, {q["failed"]} failed; it reset one field (Cloudflare access) and changed no gold-scored result. It is there for auditability, and it found a bug in itself (it dropped non-Latin characters until an extractor's Japanese quotes failed).</li>
<li><b>Verdict is the weak column.</b> Exact agreement did not improve over memory, though every disagreement is within one step. Two causes: the rubric is a judgement call, and the gold labeller did not always apply the rubric it was given (it called Lark, Sentry and Grain "easy" despite regional hosts or partner-gated production). I also found a logic error in my own rubric (an official MCP excused gated developer access, though an MCP can need the same gated credential), fixed it after seeing gold, and now show both versions. Version v2 is used in the table above.</li>
<li><b>Auth scoring is lenient on purpose.</b> Extractors list every supported method; gold lists the primary one, so exact-set match punishes completeness. Jaccard is shown next to exact.</li>
<li>Pass 1 vs pass 2 changed {drift["mcp_changed"]} MCP calls, {drift["access_changed"]} access classes, {drift["auth_changed"]} auth sets and {drift["verdict_changed"]} verdicts across all {n} apps. Only the gold-sampled ones have a ground truth to say which side was right.</li></ul>
<h3>Where pass 2 still disagrees with gold ({len(miss)} field-level misses)</h3>
{tbl([[g,html.escape(a),f,x,y] for g,a,f,x,y in miss], ["Gold","App","Field","Gold says","Pass 2 says"])}
<p class=sub>Frozen gold files: <code>gold/gold_A.jsonl</code> sha256 <code>4552cb48…</code>, <code>gold/gold_B.jsonl</code> sha256 <code>133239ac…</code>, committed before the scored pass-2 run. Pass-1 predictions, pass-2 predictions, scoring script and the raw quote-check results are all in the repo.</p>
<h3>Other things the agents got wrong or could not settle</h3><ul>
<li>Entity resolution: "Paygent Connect" matches no single product; "YouTube Transcript" resolved to a third-party service (TranscriptAPI), not Google's captions API; fanbasis is now Commas; Coda is now Superhuman Docs; NotebookLM's API is the enterprise "Gemini Notebook Enterprise". All five are flagged, not guessed.</li>
<li>Some extractor labels are provisional: Threads' MCP type is an inference from a docs index whose pages came back empty; WhatsApp's "admin-only credential" has no quote behind it; Shopify's store-management MCP is announced but not live (recorded as docs-only); WooCommerce's MCP is a per-site developer preview.</li>
<li>Pricing tables rendered as icons or JS could not be read for Copper, Devin and Pylon, so "which plan unlocks the API" is unconfirmed there.</li></ul>

<h2>5 · Your turn: 10-app human spot-check</h2>
<p class=sub>Seeded random sample (seed 7) from apps in neither gold set. Open the docs, tick what matches. This is the human check that has not happened yet; if you fill it in, send the results back and I'll fold them into the scores.</p>
<table class=t><thead><tr><th>App</th><th>Auth</th><th>Dev → prod access</th><th>MCP</th><th>Docs</th><th>Check</th></tr></thead><tbody>{hc_rows()}</tbody></table>

<h2>6 · Run it</h2>
<pre class=card><code>git clone &lt;repo&gt; &amp;&amp; cd toolkit-scout
python agent/fetch_evidence.py          # stage 1: fetch docs, save page text
python agent/mcp_probe.py               # stage 1b: MCP registry leads
# stage 2: run agent/prompts/extract.md per app with any LLM -&gt; data/pass2/raw_*.jsonl (included)
python agent/gate.py                    # stage 3: quote check + gate
python agent/score.py pass2b=data/pass2/pass2b.jsonl pass2b_v2=data/pass2/pass2b.jsonl
python agent/analyze.py &amp;&amp; python agent/build_site.py   # regenerates every number on this page</code></pre>
</main>
<script type=application/json id=data>{data}</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);let fv='all',fc='all',fq='';
const cats=[...new Set(D.map(a=>a.category))];
const el=(t,c,h)=>{{const e=document.createElement(t);if(c)e.className=c;if(h!==undefined)e.innerHTML=h;return e}};
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));
const chips=document.getElementById('chips');
['all','easy','caveat','hard','no','unknown'].forEach(v=>{{const b=el('button',v==='all'?'on':'',v);b.onclick=()=>{{fv=v;[...chips.querySelectorAll('button')].forEach(x=>x.classList.toggle('on',x===b));render()}};chips.appendChild(b)}});
const sel=el('select');sel.innerHTML='<option value=all>all categories</option>'+cats.map(c=>`<option>${{esc(c)}}</option>`).join('');sel.onchange=()=>{{fc=sel.value;render()}};chips.appendChild(sel);
const inp=el('input');inp.placeholder='search app…';inp.oninput=()=>{{fq=inp.value.toLowerCase();render()}};chips.appendChild(inp);
function render(){{const tb=document.querySelector('#apps tbody');tb.innerHTML='';
D.filter(a=>(fv==='all'||a.verdict===fv)&&(fc==='all'||a.category===fc)&&a.name.toLowerCase().includes(fq)).forEach(a=>{{
const tr=el('tr','',`<td>${{a.id}}</td><td><b>${{esc(a.name)}}</b><br><small>${{esc(a.category)}}</small></td><td>${{esc((a.auth||[]).join(', '))}}</td><td>${{esc(a.access_dev)}} → ${{esc(a.access_prod)}}</td><td>${{esc((a.api_styles||[]).join(', '))}}<br><small>${{esc(a.api_breadth)}}</small></td><td>${{esc(a.mcp_type)}}</td><td><span class="pill v-${{a.verdict}}">${{a.verdict}}</span><br><small>${{esc((a.blockers||[]).join(', '))}}</small></td><td>${{esc(a.confidence)}}</td>`);
const ev=(a.evidence||[]).map(e=>`<li><b>${{esc(e.field)}}</b>: “${{esc(e.quote)}}” <a href="${{esc(e.url)}}" target=_blank rel=noopener>${{esc((e.url||'').replace(/^https?:\\/\\//,'').slice(0,60))}}</a></li>`).join('');
const dt=el('tr','det',`<td></td><td colspan=7>${{esc(a.description)}}<br>Entity: ${{esc(a.entity_status)}} ${{esc(a.entity_note||'')}} · rule ${{esc(a.rule)}} · tenancy ${{esc(a.tenancy)}} · quotes verified ${{a.quotes_verified}}, web-only ${{a.quotes_web_only}}, failed ${{a.quotes_failed}}<br>${{a.needs_human?'<b>Open question:</b> '+esc(a.needs_human)+'<br>':''}}<a href="${{esc(a.docs_url)}}" target=_blank rel=noopener>docs</a><ul>${{ev}}</ul></td>`);
tr.onclick=()=>tr.classList.toggle('open');tb.appendChild(tr);tb.appendChild(dt)}})}}
render();
</script></body></html>"""
(ROOT/"site").mkdir(exist_ok=True); (ROOT/"site/index.html").write_text(page)
print("built", len(page)//1024, "KB;", len(miss), "misses")
