"""Stage 3b: verification gate. A field whose evidence quotes ALL fail the verbatim-presence check is reset to
'unknown' (abstain) and queued for a human. src='web' quotes can't be machine-checked: kept, but flagged 'web_only'.
python agent/gate.py  -> data/pass2/pass2a.jsonl, pass2b.jsonl, quote_check.json, human_queue.json"""
import json, glob, subprocess, sys
from common import ROOT
rows = {}
for p in sorted(glob.glob(str(ROOT/"data/pass2/raw_*.jsonl"))):
    for l in open(p):
        if l.strip(): r = json.loads(l); rows[r["id"]] = r
assert sorted(rows)==list(range(1,101)), sorted(set(range(1,101))-set(rows))
(ROOT/"data/pass2/pass2a.jsonl").write_text("".join(json.dumps(rows[i])+"\n" for i in sorted(rows)))
out = subprocess.run([sys.executable, str(ROOT/"agent/check_quotes.py"), str(ROOT/"data/pass2/pass2a.jsonl")], capture_output=True, text=True).stdout
qc = json.loads(out); (ROOT/"data/pass2/quote_check.json").write_text(out)
status = {r["id"]: r["quotes"] for r in qc["rows"]}
FIELD_KEYS = {"auth":["auth"],"access":["access_dev","access_prod"],"mcp":["mcp_type","mcp_url"],"api":["api_styles","api_breadth"]}
RESET = {"auth":[], "access_dev":"unknown","access_prod":"unknown","mcp_type":"unknown","mcp_url":None,"api_styles":[],"api_breadth":"unknown"}
b = {}; queue = []; resets = []
for i, r in rows.items():
    r2 = json.loads(json.dumps(r)); qs = status[i]
    for f, keys in FIELD_KEYS.items():
        fq = [q["status"] for q in qs if q["field"] == f]
        if fq and all(s == "unverified" for s in fq):
            for k in keys: r2[k] = RESET[k]
            resets.append({"id": i, "name": r["name"], "field": f}); 
    b[i] = r2
    if r.get("needs_human") or r.get("entity_status") in ("ambiguous","not_found","renamed") or r.get("confidence")=="low":
        queue.append({"id": i, "name": r["name"], "entity_status": r.get("entity_status"), "confidence": r.get("confidence"), "question": r.get("needs_human")})
(ROOT/"data/pass2/pass2b.jsonl").write_text("".join(json.dumps(b[i])+"\n" for i in sorted(b)))
(ROOT/"data/pass2/human_queue.json").write_text(json.dumps({"resets_by_gate": resets, "queue": queue}, indent=1))
print(qc["summary"], "| gate resets:", resets, "| human queue:", len(queue))
