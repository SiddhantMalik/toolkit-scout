import json, sys, re
from common import ROOT
idx = {r["id"]: r for r in json.load(open(ROOT/"data"/"evidence_index.json"))}
mcp = {r["id"]: r for r in json.load(open(ROOT/"data"/"mcp_leads.json"))}
lo, hi = int(sys.argv[1]), int(sys.argv[2])
caps = {"auth": 2, "access": 3, "mcp": 2, "api": 1}
for i in range(lo, hi+1):
    r = idx[i]; print(f"\n##{i} {r['name']} usable={r['usable_chars']} pages={[(p['url'].split('//')[1][:40],p['status']) for p in r['pages'][:4]]}")
    print(" REG:", [(c['name'][:40], (c['remote'] or [''])[0][:40]) for c in mcp[i]['cands']] or "-")
    for f, n in caps.items():
        for s in r["snippets"][f][:n]:
            print(f" {f[:3]}[{s['url'].split('//')[1][:30]}]:", s["text"][:230])
