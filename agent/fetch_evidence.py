"""Stage 1 (retrieval). Deterministic, no LLM.
For each app: fetch docs page(s) + llms.txt + up to 4 one-hop links (auth/pricing/mcp/getting-started),
detect JS-shells/challenges, and cut keyword-in-context snippets per field.
Snippets (not regex counts) are what Stage 2 is allowed to quote from.
Usage: python agent/fetch_evidence.py [--ids 1,2]
"""
import re, sys, json, urllib.parse as up, concurrent.futures as cf, requests
from common import load_seed, ROOT

UA = {"User-Agent": "Mozilla/5.0 (compatible; toolkit-scout/0.2; research)"}
OUT = ROOT/"data"/"evidence"; OUT.mkdir(parents=True, exist_ok=True)
OVR = json.loads((ROOT/"data"/"url_overrides.json").read_text()) if (ROOT/"data"/"url_overrides.json").exists() else {}
HOP = re.compile(r"auth|oauth|token|api-?key|credential|pricing|plans?|mcp|getting-?started|quick-?start|rate-?limit|access", re.I)
PAT = {
 "auth":   r"Bearer|OAuth ?2(\.\d)?|OAuth|API[ -]?keys?|API[ -]token|personal access token|access token|Basic auth\w*|client[ _]credentials|X-API-Key|Authorization:|JWT|service account",
 "access": r"free (plan|trial|tier|account|to use)|all plans|paid plans?|available (on|for|to)|Enterprise|contact (our )?(sales|us|the team|support)|request access|apply for|approval|approved by|app review|partner program|admin(istrator)?s? can|only admin|sandbox|developer (account|edition|program|token)|pricing|upgrade to|requires? (a|an) (paid|premium|business)",
 "mcp":    r"\bMCP\b|Model Context Protocol",
 "api":    r"GraphQL|REST(ful)? API|SOAP|OpenAPI|endpoints?\b",
}
def clean(html):
    html = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", html)
    t = re.sub(r"(?s)<[^>]+>", " ", html); t = re.sub(r"&[a-z#0-9]+;", " ", t)
    return re.sub(r"\s+", " ", t).strip()
def get(u):
    try:
        r = requests.get(u, headers=UA, timeout=20)
        return r.status_code, r.url, r.text, r.headers.get("content-type","")
    except Exception as e: return 0, u, "", type(e).__name__
def links(html, base):
    out=[]
    for m in re.finditer(r'(?is)<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', html):
        h, label = m.group(1), clean(m.group(2))
        full = up.urljoin(base, h)
        if up.urlparse(full).netloc.split(".")[-2:] == up.urlparse(base).netloc.split(".")[-2:] and HOP.search(h+" "+label):
            if full not in out: out.append(full)
    return out[:4]
def kwic(text, url):
    res = {}
    for f, pat in PAT.items():
        seen=[]; items=[]
        for m in re.finditer(pat, text, re.I):
            s = max(0, m.start()-130); e = min(len(text), m.end()+170)
            if any(abs(s-x) < 200 for x in seen): continue
            seen.append(s); items.append({"url": url, "text": text[s:e]})
            if len(items) >= 5: break
        res[f] = items
    return res
def one(app):
    rec = {"id": app["id"], "name": app["name"], "pages": [], "snippets": {k: [] for k in PAT}}
    urls = OVR.get(str(app["id"]), app["docs"])[:2]
    queue = list(urls)
    for u in urls:
        p = up.urlparse(u); queue.append(f"{p.scheme}://{p.netloc}/llms.txt")
    done = set(); total = ""
    while queue and len(done) < 9:
        u = queue.pop(0)
        if u in done: continue
        done.add(u)
        s, final, raw, ct = get(u)
        txt = clean(raw) if s == 200 and ("html" in ct or "text" in ct) else ""
        shell = 0 < len(txt) < 1500 or bool(re.search(r"Just a moment|Enable JavaScript|cf-chl", raw[:4000]))
        rec["pages"].append({"url": u, "final": final, "status": s, "chars": len(txt), "js_shell_or_challenge": shell})
        if txt and not u.endswith("llms.txt") and len(done) <= 3 and s == 200:
            for l in links(raw, final):
                if l not in done and l not in queue: queue.append(l)
        if txt and not shell:
            total += txt[:150000]
            for f, items in kwic(txt[:150000], final).items(): rec["snippets"][f] += items
    for f in rec["snippets"]: rec["snippets"][f] = rec["snippets"][f][:8]
    rec["usable_chars"] = len(total)
    rec["usable"] = len(total) >= 3000
    (OUT/f"{app['id']}.txt").write_text(total)
    return rec
if __name__ == "__main__":
    apps = load_seed()
    if "--ids" in sys.argv:
        keep = {int(x) for x in sys.argv[sys.argv.index("--ids")+1].split(",")}; apps = [a for a in apps if a["id"] in keep]
    with cf.ThreadPoolExecutor(10) as ex: res = list(ex.map(one, apps))
    (ROOT/"data"/"evidence_index.json").write_text(json.dumps(res, indent=1))
    print(f"usable text (>=3000 chars, not shell): {sum(r['usable'] for r in res)}/{len(res)}")
    for r in res:
        if not r["usable"]: print("WEAK", r["id"], r["name"], r["usable_chars"], [p["status"] for p in r["pages"][:3]])
