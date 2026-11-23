"""Score predictions against the frozen gold sets and write data/scores.json.

Usage:  python agent/score.py LABEL=predictions.jsonl [LABEL=predictions.jsonl ...]

A label ending in "_v3" uses the post-hoc verdict rubric (verdict.py, fixed=True).
The pass-1 memory baseline is always scored too.

Metrics per field: correct / n, abstentions (counted as not-correct), Wilson 95% CI.
Extras: mean Jaccard overlap for auth sets, and verdict agreement within one step.
"""
import json
import math
import sys

from common import ROOT, load_seed
from norm import from_goldB, from_pass1, from_pass2

FIELDS = ("auth", "access", "mcp_official", "verdict")
VERDICT_ORDER = {"easy": 0, "caveat": 1, "hard": 2, "no": 3}


def wilson(k, n, z=1.96):
    """95% Wilson score interval for k successes out of n, as whole percentages."""
    if n == 0:
        return (0, 0)
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round(100 * (centre - half) / denom), round(100 * (centre + half) / denom))


def _read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def load_gold():
    """Return (gold_A, gold_B) as {app_id: collapsed fields}. Gold A is partial: only reviewer-judged fields."""
    gold_a = {g["id"]: {k: v for k, v in g.items() if k in FIELDS} for g in _read_jsonl(ROOT / "gold/gold_A.jsonl")}
    path_b = ROOT / "gold/gold_B.jsonl"
    gold_b = {g["id"]: from_goldB(g) for g in _read_jsonl(path_b)} if path_b.exists() else {}
    return gold_a, gold_b


def _gold_value(gold_fields, field):
    """The gold label for a field, or None when gold gives no usable label."""
    if field not in gold_fields:
        return None
    value = gold_fields[field]
    if field == "auth":
        return value or None
    return None if value in (None, []) else value


def _score_field(pred, gold, field):
    n = correct = abstained = 0
    for app_id, gold_fields in gold.items():
        expected = _gold_value(gold_fields, field)
        if expected is None:
            continue
        n += 1
        got = pred.get(app_id, {}).get(field)
        if got is not None and got == expected:        # exact match, including a correct "unknown"
            correct += 1
        elif got is None or (got == "unknown" and field != "auth"):
            abstained += 1
    return {"n": n, "correct": correct, "abstained": abstained,
            "acc": round(100 * correct / n) if n else None, "ci95": wilson(correct, n)}


def _extras(pred, gold):
    """Auth Jaccard (gold labels list primary methods only) and verdict within-one-step agreement."""
    jaccards, within_one = [], []
    for app_id, gold_fields in gold.items():
        got = pred.get(app_id)
        if not got:
            continue
        if gold_fields.get("auth") and got.get("auth") is not None:
            a, b = set(gold_fields["auth"]), set(got["auth"])
            jaccards.append(len(a & b) / len(a | b))
        if gold_fields.get("verdict") in VERDICT_ORDER and got.get("verdict") in VERDICT_ORDER:
            within_one.append(abs(VERDICT_ORDER[gold_fields["verdict"]] - VERDICT_ORDER[got["verdict"]]) <= 1)
    return {"auth_jaccard_mean": round(sum(jaccards) / len(jaccards), 2) if jaccards else None,
            "verdict_within_one": {"n": len(within_one), "correct": sum(within_one)}}


def score(pred, gold):
    return {**_extras(pred, gold), **{f: _score_field(pred, gold, f) for f in FIELDS}}


def pass1_preds():
    return {a["id"]: from_pass1(a) for a in load_seed()}


def pass2_preds(path, fixed=False):
    return {r["id"]: from_pass2(r, fixed) for r in _read_jsonl(path if hasattr(path, "read_text") else ROOT / path)}


def main(argv):
    gold_a, gold_b = load_gold()
    runs = {"pass1_memory": pass1_preds()}
    for spec in argv:
        label, path = spec.split("=")
        runs[label] = pass2_preds(path, fixed=label.endswith("_v3"))
    results = {label: {"goldA_hard_cases": score(preds, gold_a),
                       "goldB_random_heldout": score(preds, gold_b) if gold_b else None}
               for label, preds in runs.items()}
    (ROOT / "data/scores.json").write_text(json.dumps(results, indent=1))
    return results


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1:]), indent=1))
