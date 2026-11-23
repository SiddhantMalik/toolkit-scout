"""Score predictions against frozen gold. python agent/score.py <pass1|pass2 file label>...  -> data/scores.json"""
import json, math, sys, pathlib
from common import ROOT, load_seed
from norm import from_pass1, from_pass2, from_goldB
def wilson(k, n, z=1.96):
    if n == 0: return (0,0)
    p=k/n; d=1+z*z/n; c=p+z*z/(2*n); h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))
    return (round(100*(c-h)/d), round(100*(c+h)/d))
def load_gold():
    A = {}; B = {}
    for l in (ROOT/"gold/gold_A.jsonl").read_text().splitlines():
        g=json.loads(l); A[g["id"]] = {k:v for k,v in g.items() if k in ("auth","access","mcp_official","verdict")}
    p = ROOT/"gold/gold_B.jsonl"
    if p.exists():
        for l in p.read_text().splitlines():
            if l.strip(): g=json.loads(l); B[g["id"]] = from_goldB(g)
    return A, B
ORD = {"easy":0,"caveat":1,"hard":2,"no":3}
def score(pred, gold):
    out = {}
    # extra metrics: auth set-Jaccard (gold labels list primary methods only) and verdict within-one-step
    js=[]; w1=[]; wn=0
    for i,g in gold.items():
        p = pred.get(i)
        if g.get("auth") and p and p.get("auth") is not None:
            a,b=set(g["auth"]),set(p["auth"]); js.append(len(a&b)/len(a|b))
        if g.get("verdict") in ORD and p and p.get("verdict") in ORD:
            wn+=1; w1.append(abs(ORD[g["verdict"]]-ORD[p["verdict"]])<=1)
    out["auth_jaccard_mean"] = round(sum(js)/len(js),2) if js else None
    out["verdict_within_one"] = {"n":wn,"correct":sum(w1)}
    for f in ("auth","access","mcp_official","verdict"):
        n=k=ab=0
        for i,g in gold.items():
            if f not in g or g[f] in (None,[]) and f!="auth": continue
            if f=="auth" and not g[f]: continue
            p = pred.get(i, {}).get(f)
            if p in (None,"unknown") and f!="auth" or (f=="auth" and p is None):
                ab += 1; n += 1; continue          # abstention counts as not-correct, reported separately
            n += 1; k += (p == g[f])
        out[f] = {"n":n,"correct":k,"abstained":ab,"acc":round(100*k/n) if n else None,"ci95":wilson(k,n)}
    return out
def pass1_preds(): return {a["id"]: from_pass1(a) for a in load_seed()}
def pass2_preds(path, exempt=True):
    P={}
    for l in pathlib.Path(path).read_text().splitlines():
        if l.strip(): r=json.loads(l); P[r["id"]] = from_pass2(r, exempt)
    return P
if __name__=="__main__":
    A,B = load_gold(); res={}
    runs = {"pass1_memory": pass1_preds()}
    for lab,path in [x.split("=") for x in sys.argv[1:]]: runs[lab] = pass2_preds(path, exempt=not lab.endswith("_v2"))
    for lab,P in runs.items(): res[lab] = {"goldA_hard_cases": score(P,A), "goldB_random_heldout": score(P,B) if B else None}
    (ROOT/"data/scores.json").write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
