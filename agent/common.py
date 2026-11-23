"""Shared loaders. Seed format documented in data/pass1_seed.txt."""
import json, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
FIELDS = ["id","name","category","docs","auth","access","api","mcp","verdict","blocker"]

def load_seed(path=ROOT/"data"/"pass1_seed.txt"):
    apps = []
    for line in path.read_text().splitlines():
        if not line.strip() or line.startswith("#"): continue
        p = line.split("|")
        d = dict(zip(FIELDS, p))
        d["id"] = int(d["id"]); d["docs"] = d["docs"].split()
        d["auth"] = [a for a in d["auth"].split(",") if a]
        apps.append(d)
    return apps
