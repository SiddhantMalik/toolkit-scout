"""Compute every number shown on the page from data (pass2b rows + pass-1 seed + scores). -> data/final.json"""
import json, collections as C
from common import ROOT, load_seed
from verdict import verdict
from norm import auth_set, access_cls, from_pass1
seed = {a["id"]: a for a in load_seed()}
rows = [json.loads(l) for l in open(ROOT/"data/pass2/pass2d.jsonl")]
qc = {r["id"]: r["quotes"] for r in json.load(open(ROOT/"data/pass2/quote_check_requoted.json"))["rows"]}
final = []
for r in rows:
    v, rule, blockers = verdict(r, fixed=True)
    q = qc[r["id"]]
    final.append({**r, "category": seed[r["id"]]["category"], "verdict": v, "rule": rule, "blockers": blockers,
                  "quotes_verified": sum(x["status"]=="verified" for x in q), "quotes_web_only": sum(x["status"]=="unchecked_web" for x in q),
                  "quotes_failed": sum(x["status"]=="unverified" for x in q),
                  "pass1": seed[r["id"]]})
cats = list(dict.fromkeys(a["category"] for a in seed.values()))
def rel(r): return r.get("entity_status") in ("resolved","renamed") and r.get("confidence") in ("high","medium")
R = [r for r in final if rel(r)]
def pct(k,n): return round(100*k/n) if n else None
out = {"n_total": len(final), "n_reliable": len(R), "retrieved": "2026-11-23"}
out["auth"] = {m: sum(1 for r in R if m in auth_set(r["auth"])) for m in ("oauth2","key","basic","jwt")}
out["auth_only_key"] = sum(1 for r in R if auth_set(r["auth"]) == ["key"])
out["auth_oauth_any"] = out["auth"]["oauth2"]
out["access_dev"] = dict(C.Counter(access_cls(r["access_dev"]) or "unknown" for r in R))
out["access_dev_raw"] = dict(C.Counter(r["access_dev"] for r in R))
SS = [r for r in R if access_cls(r["access_dev"]) == "self"]
out["self_serve_n"] = len(SS)
out["prod_friction"] = sum(1 for r in SS if r.get("access_prod") not in ("same_as_dev", r["access_dev"], "unknown", None))
out["mcp"] = dict(C.Counter(r["mcp_type"] for r in R))
out["mcp_official"] = sum(1 for r in R if r["mcp_type"] in ("official_remote","official_local"))
out["verdict"] = dict(C.Counter(r["verdict"] for r in final)); out["verdict_reliable"] = dict(C.Counter(r["verdict"] for r in R))
out["blockers"] = dict(C.Counter(b for r in final for b in r["blockers"] if b!="NONE").most_common())
out["tenancy"] = dict(C.Counter(r.get("tenancy") for r in R))
out["by_category"] = {}
for c in cats:
    rc = [r for r in R if r["category"]==c]
    out["by_category"][c] = {"n": len(rc), "self": sum(access_cls(r["access_dev"])=="self" for r in rc), "paid": sum(access_cls(r["access_dev"])=="paid" for r in rc),
        "gated": sum(access_cls(r["access_dev"])=="gated" for r in rc), "official_mcp": sum(r["mcp_type"] in ("official_remote","official_local") for r in rc),
        "easy": sum(r["verdict"]=="easy" for r in rc), "caveat": sum(r["verdict"]=="caveat" for r in rc), "hard": sum(r["verdict"]=="hard" for r in rc), "no": sum(r["verdict"]=="no" for r in rc)}
# pass-1 drift on all 100 (not accuracy: no gold)
drift = {"mcp_changed": 0, "mcp_none_to_official": 0, "access_changed": 0, "verdict_changed": 0, "auth_changed": 0}
for r in final:
    p1 = from_pass1(seed[r["id"]]); mo = r["mcp_type"] in ("official_remote","official_local")
    drift["mcp_changed"] += p1["mcp_official"] != mo; drift["mcp_none_to_official"] += (not p1["mcp_official"]) and mo
    drift["access_changed"] += (access_cls(r["access_dev"]) not in (None, p1["access"])) 
    drift["verdict_changed"] += r["verdict"] != p1["verdict"]; drift["auth_changed"] += auth_set(r["auth"]) != p1["auth"]
out["drift_vs_pass1"] = drift
out["easy_wins"] = [r["name"] for r in R if r["verdict"]=="easy"]
out["outreach"] = [{"name": r["name"], "why": r["blockers"]} for r in final if r["verdict"] in ("hard","unknown")]
out["quotes"] = {"verified": sum(r["quotes_verified"] for r in final), "web_only": sum(r["quotes_web_only"] for r in final), "failed": sum(r["quotes_failed"] for r in final)}
out["conf"] = dict(C.Counter(r["confidence"] for r in final)); out["entity"] = dict(C.Counter(r["entity_status"] for r in final))
(ROOT/"data/final.json").write_text(json.dumps({"summary": out, "apps": final}, indent=1))
print(json.dumps(out, indent=1)[:5500])
