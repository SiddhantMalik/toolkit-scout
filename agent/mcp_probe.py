"""Stage 1b: query the official MCP Registry for each app; keep candidates whose reverse-DNS namespace
or repo owner matches the vendor token. Output is a LEAD list for Stage 2, not a verdict."""
import re, json, urllib.parse as up, requests, concurrent.futures as cf
from common import load_seed, ROOT
def tokens(a):
    host = up.urlparse(a["docs"][0]).netloc.split(".")
    t = {re.sub(r"[^a-z0-9]","",a["name"].lower().split(" (")[0].split(" ")[0])}
    t.add(host[-2] if len(host)>1 else host[0])
    return {x for x in t if len(x)>2}
def probe(a):
    toks = tokens(a); out=[]
    try:
        r = requests.get("https://registry.modelcontextprotocol.io/v0/servers", params={"search": a["name"].split(" (")[0], "limit": 30}, timeout=20).json()
    except Exception as e: return {"id":a["id"],"error":type(e).__name__,"cands":[]}
    for s in r.get("servers", []):
        sv = s["server"]; ns = sv["name"].split("/")[0].lower(); repo = (sv.get("repository") or {}).get("url","").lower()
        owner = repo.split("github.com/")[-1].split("/")[0] if "github.com" in repo else ""
        hit = any(t in ns.replace("-","").replace(".","") or t == owner.replace("-","") for t in toks)
        if hit: out.append({"name": sv["name"], "remote": [x.get("url") for x in sv.get("remotes",[])][:1], "repo": repo, "desc": sv.get("description","")[:90]})
    uniq = {c["name"]: c for c in out}
    return {"id": a["id"], "name": a["name"], "cands": list(uniq.values())[:3]}
if __name__ == "__main__":
    apps = load_seed()
    with cf.ThreadPoolExecutor(6) as ex: res = list(ex.map(probe, apps))
    (ROOT/"data"/"mcp_leads.json").write_text(json.dumps(res, indent=1))
    print(sum(1 for r in res if r["cands"]), "of", len(res), "apps have registry candidates")
