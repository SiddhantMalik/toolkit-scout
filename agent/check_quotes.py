"""Stage 3 (deterministic verifier): every evidence quote must appear (whitespace/case-normalised)
in the saved page text for that app (data/evidence/<id>.txt or data/evidence_extra/<id>_*.txt).
Fields whose quotes fail are flagged 'quote_unverified'. src='web' quotes can't be machine-checked -> 'unchecked'.
python agent/check_quotes.py data/pass2/raw_*.jsonl > data/pass2/quote_check.json"""
import json, re, sys, glob
from common import ROOT
def norm(s): return re.sub(r"[\W_]+"," ",s.lower()).strip()
def corpus(i):
    t = ""
    for p in [ROOT/f"data/evidence/{i}.txt", *sorted(glob.glob(str(ROOT/f"data/evidence_extra/{i}_*.txt")))]:
        try: t += " " + open(p, errors="ignore").read()
        except FileNotFoundError: pass
    return norm(t)
rows = []; summary = {"verified":0,"unverified":0,"unchecked_web":0}
for path in sys.argv[1:]:
    for l in open(path):
        if not l.strip(): continue
        r = json.loads(l); c = corpus(r["id"]); res = []
        for e in r.get("evidence", []):
            q = norm(e.get("quote",""))
            if len(q) < 12: st = "unverified"
            elif q in c: st = "verified"
            elif e.get("src") == "web": st = "unchecked_web"
            else: st = "unverified"
            summary[{"verified":"verified","unverified":"unverified","unchecked_web":"unchecked_web"}[st]] += 1
            res.append({"field":e.get("field"),"url":e.get("url"),"status":st})
        rows.append({"id":r["id"],"name":r["name"],"quotes":res})
print(json.dumps({"summary":summary,"rows":rows}, indent=1))
