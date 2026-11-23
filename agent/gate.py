"""Stage 3: verification gate.

  pass2a   raw extractor output, merged from data/pass2/raw_*.jsonl
  check    every quote is looked for in the page text saved for its app (check_quotes.py); quotes that came through a
           web tool are checked against the Composio copy of the cited page when stage 3b saved one
  gate     a field whose quotes ALL fail is reset to 'unknown' (abstain)          -> pass2b_strict.jsonl
  requote  failed quotes replaced by text taken from the cited page (requote.jsonl), then everything is checked
           again; values never change, and a replacement only counts if it is found verbatim  -> pass2b.jsonl
  correct  logged audit corrections (corrections.json), never counted as agent accuracy  -> pass2c.jsonl
  browser  the 5 apps the pipeline could not settle, resolved with the brief's hints, a browser and web search
           (browser_loop.jsonl); not scored, because 4 of them are gold apps and I had seen gold  -> pass2d.jsonl (published)

python agent/gate.py   (also writes quote_check*.json and human_queue.json)
"""
import copy
import glob
import json
import subprocess
import sys

from common import ROOT

P2 = ROOT / "data/pass2"
FIELD_KEYS = {"auth": ["auth"], "access": ["access_dev", "access_prod"],
              "mcp": ["mcp_type", "mcp_url"], "api": ["api_styles", "api_breadth"]}
RESET = {"auth": [], "access_dev": "unknown", "access_prod": "unknown", "mcp_type": "unknown",
         "mcp_url": None, "api_styles": [], "api_breadth": "unknown"}


def write_jsonl(path, rows):
    path.write_text("".join(json.dumps(rows[i]) + "\n" for i in sorted(rows)))


def load_raw():
    rows = {}
    for path in sorted(glob.glob(str(P2 / "raw_*.jsonl"))):
        for line in filter(str.strip, open(path)):
            record = json.loads(line)
            rows[record["id"]] = record
    missing = set(range(1, 101)) - set(rows)
    assert not missing, f"apps missing from raw output: {sorted(missing)}"
    return rows


def check(path, out_name):
    """Run check_quotes.py on a JSONL file; save its report; return {app id: [quote statuses]} and the summary."""
    out = subprocess.run([sys.executable, str(ROOT / "agent/check_quotes.py"), str(path)],
                         capture_output=True, text=True, check=True).stdout
    (P2 / out_name).write_text(out)
    report = json.loads(out)
    return {r["id"]: r["quotes"] for r in report["rows"]}, report["summary"]


def apply_gate(rows, status):
    """Reset every field whose quotes all failed; return (gated rows, list of resets)."""
    gated, resets = {}, []
    for app_id, record in rows.items():
        out = copy.deepcopy(record)
        for field, keys in FIELD_KEYS.items():
            statuses = [q["status"] for q in status[app_id] if q["field"] == field]
            if statuses and all(s == "unverified" for s in statuses):
                for key in keys:
                    out[key] = copy.deepcopy(RESET[key])
                resets.append({"id": app_id, "name": record["name"], "field": field})
        gated[app_id] = out
    return gated, resets


def apply_requotes(rows):
    requoted = copy.deepcopy(rows)
    for line in filter(str.strip, open(P2 / "requote.jsonl")):
        fix = json.loads(line)
        for evidence in requoted[fix["id"]]["evidence"]:
            if evidence["field"] == fix["field"] and evidence["quote"] == fix["old_quote"]:
                evidence["quote"], evidence["requoted_from"] = fix["new_quote"], fix["old_quote"]
    return requoted


def human_queue(rows):
    return [{"id": i, "name": r["name"], "entity_status": r.get("entity_status"),
             "confidence": r.get("confidence"), "question": r.get("needs_human")}
            for i, r in rows.items()
            if r.get("needs_human") or r.get("entity_status") in ("ambiguous", "not_found", "renamed")
            or r.get("confidence") == "low"]


def main():
    rows = load_raw()
    write_jsonl(P2 / "pass2a.jsonl", rows)

    status, summary = check(P2 / "pass2a.jsonl", "quote_check.json")
    strict, strict_resets = apply_gate(rows, status)
    write_jsonl(P2 / "pass2b_strict.jsonl", strict)

    requoted = apply_requotes(rows)
    write_jsonl(P2 / "pass2a_requoted.jsonl", requoted)
    status_rq, summary_rq = check(P2 / "pass2a_requoted.jsonl", "quote_check_requoted.json")
    gated, resets = apply_gate(requoted, status_rq)
    write_jsonl(P2 / "pass2b.jsonl", gated)

    corrected = copy.deepcopy(gated)
    for fix in json.load(open(P2 / "corrections.json"))["fixes"]:
        corrected[fix["id"]].update(fix["set"])
        corrected[fix["id"]]["provenance"] = "audit_correction: " + fix["reason"]
    write_jsonl(P2 / "pass2c.jsonl", corrected)

    published = copy.deepcopy(corrected)
    for line in filter(str.strip, open(P2 / "browser_loop.jsonl")):
        fix = json.loads(line)
        published[fix["id"]].update(fix["set"])
        published[fix["id"]]["evidence"] = published[fix["id"]].get("evidence", []) + fix["evidence"]
        published[fix["id"]]["provenance"] = "browser_loop: " + fix["method"]
    write_jsonl(P2 / "pass2d.jsonl", published)

    (P2 / "human_queue.json").write_text(json.dumps(
        {"resets_by_strict_gate": strict_resets, "resets_by_gate": resets, "queue": human_queue(rows)}, indent=1))
    print("quotes:", summary, "-> after re-quote:", summary_rq)
    print("strict gate resets:", [(r["name"], r["field"]) for r in strict_resets])
    print("final gate resets: ", [(r["name"], r["field"]) for r in resets])


if __name__ == "__main__":
    main()
