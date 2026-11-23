"""Turn data/final.json + data/scores.json + gold + audit files into the values the page template needs.

Every number shown on the page is produced here from data; nothing is typed into the template by hand.
`build_context()` returns {token_name: string}; build_site.py substitutes them into site/template.html.
"""
import html
import json

from common import ROOT
from norm import access_cls

CATEGORY_ORDER = None   # filled from data, keeps the seed order


def _jsonl(path):
    return [json.loads(line) for line in (ROOT / path).read_text().splitlines() if line.strip()]


def _table(rows, headers, css="t"):
    head = "".join(f"<th>{h}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f'<div class=scroll><table class={css}><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def _frac(scores, run, gold, field):
    s = scores[run][gold][field]
    return f'{s["correct"]}/{s["n"]}'


def _cell(score):
    return f'{score["correct"]}/{score["n"]} <small>({score["acc"]}%, CI {score["ci95"][0]}–{score["ci95"][1]})</small>'


RUNS = [("pass1_memory", "Pass 1: memory only"),
        ("pass2a", "Pass 2a: agent + evidence + quotes"),
        ("pass2b_strict", "Pass 2b strict: Composio-checked quote gate, before re-quote"),
        ("pass2b", "Pass 2b: after quote gate + re-quote (verdict rubric v1)"),
        ("pass2b_v3", "Pass 2b: verdict rubric v3 (post-hoc fix)")]


def _score_table(scores, gold):
    rows = []
    for run, label in RUNS:
        s = scores[run][gold]
        rows.append([label, _cell(s["mcp_official"]), _cell(s["access"]),
                     f'{_cell(s["auth"])}<br><small>Jaccard {s["auth_jaccard_mean"]}</small>',
                     f'{_cell(s["verdict"])}<br><small>within one step: {s["verdict_within_one"]["correct"]}/{s["verdict_within_one"]["n"]}</small>'])
    return _table(rows, ["Run", "Official MCP?", "Dev access class", "Auth methods", "Verdict"])


def _misses(apps_by_id, gold_a, gold_b):
    """Field-level disagreements between final pass-2 rows and gold."""
    out = []
    for name, gold in (("A", gold_a), ("B", gold_b)):
        for app_id, g in gold.items():
            app = apps_by_id[app_id]
            is_official = app["mcp_type"] in ("official_remote", "official_local")
            gold_mcp = g.get("mcp_official") if name == "A" else (
                None if g.get("mcp_type") in (None, "unknown") else g["mcp_type"] in ("official_remote", "official_local"))
            if gold_mcp is not None and gold_mcp != is_official:
                out.append((name, app["name"], "official MCP", str(gold_mcp), str(is_official)))
            gold_access = g.get("access") if name == "A" else access_cls(g.get("access_dev"))
            if gold_access and gold_access != access_cls(app["access_dev"]):
                out.append((name, app["name"], "dev access", gold_access, str(access_cls(app["access_dev"]))))
            if g.get("verdict") and g["verdict"] != app["verdict"]:
                out.append((name, app["name"], "verdict (rubric v3)", g["verdict"], app["verdict"]))
    return out


def _audit(crosscheck, evidence40):
    def agree(field):
        rows = [r for r in crosscheck if r["field"] == field]
        return sum(r["verdict"] == "agree" for r in rows), len(rows)
    agreement = {f: agree(f) for f in ("access", "auth", "mcp", "evidence")}
    support = [str(r["supports_value"]).lower() for r in evidence40]
    return agreement, {
        "present": sum(str(r["present_today"]).lower().startswith("yes") for r in evidence40),
        "clean": support.count("yes"), "weak": sum(s.startswith("yes(") for s in support),
        "partial": support.count("partial"), "no": support.count("no"), "n": len(evidence40)}


def _composio_loop(scores):
    """Numbers for the Composio verification loop (stage 3b/3d)."""
    run = json.loads((ROOT / "data/composio_run.json").read_text())
    pages = run["pages"].values()
    raw = {r["id"]: r for r in _jsonl("data/pass2/pass2a.jsonl")}
    before = json.loads((ROOT / "data/pass2/quote_check.json").read_text())["rows"]
    after = json.loads((ROOT / "data/pass2/quote_check_requoted.json").read_text())["rows"]
    def web_statuses(report):
        out = []
        for row in report:
            for evidence, quote in zip(raw[row["id"]]["evidence"], row["quotes"]):
                if evidence.get("src") == "web":
                    out.append(quote["status"])
        return out
    web_before, web_after = web_statuses(before), web_statuses(after)
    requotes = list(_jsonl("data/pass2/requote.jsonl"))
    A = "goldA_hard_cases"
    return {
        "cx_pages_ok": sum(p["ok"] for p in pages), "cx_pages": len(run["pages"]),
        "cx_web": len(web_before), "cx_verified": web_before.count("verified"),
        "cx_failed": web_before.count("unverified"), "cx_unchecked": web_before.count("unchecked_web"),
        "cx_requoted": len(requotes), "cx_failed_after": web_after.count("unverified"),
        "cx_requote_names": ", ".join(sorted({r["app"] for r in requotes})),
        "cx_a_mcp_strict": _frac(scores, "pass2b_strict", A, "mcp_official"),
        "cx_a_mcp_final": _frac(scores, "pass2b", A, "mcp_official"),
        "cx_session_runs": len(run["runs"]),
    }


def build_context():
    final = json.loads((ROOT / "data/final.json").read_text())
    summary, apps = final["summary"], final["apps"]
    scores = json.loads((ROOT / "data/scores.json").read_text())
    queue = json.loads((ROOT / "data/pass2/human_queue.json").read_text())["queue"]
    human_ids = json.loads((ROOT / "data/human_check_ids.json").read_text())["ids"]
    gold_a = {g["id"]: g for g in _jsonl("gold/gold_A.jsonl")}
    gold_b = {g["id"]: g for g in _jsonl("gold/gold_B.jsonl")}
    by_id = {a["id"]: a for a in apps}
    n, nr = summary["n_total"], summary["n_reliable"]
    cat = summary["by_category"]
    verdicts = summary["verdict"]
    quotes = summary["quotes"]
    drift = summary["drift_vs_pass1"]
    blockers = summary["blockers"]
    audit_agree, audit_ev = _audit(_jsonl("audit/crosscheck.jsonl"), _jsonl("audit/evidence40.jsonl"))
    misses = _misses(by_id, gold_a, gold_b)
    names = lambda label: ", ".join(a["name"] for a in apps if a["verdict"] == label)   # noqa: E731
    B, A = "goldB_random_heldout", "goldA_hard_cases"
    sc = lambda run, g, f: scores[run][g][f]   # noqa: E731

    category_rows = [[c, v["n"], v["self"], v["paid"] + v["gated"], v["official_mcp"],
                      f'<span class=e>{v["easy"]}</span>', f'<span class=c>{v["caveat"]}</span>', f'<span class=h>{v["hard"]}</span>']
                     for c, v in cat.items()]
    top = list(blockers.items())[:6]
    blocker_bars = "".join(
        f'<div class=bar><span>{k.replace("_", " ").title()}</span><i style="width:{round(100 * v / max(blockers.values()))}%"></i><b>{v}</b></div>'
        for k, v in top)
    human_rows = [[f'{a["id"]}. {html.escape(a["name"])}', html.escape(", ".join(a["auth"])),
                   f'{a["access_dev"]} → {a.get("access_prod")}', a["mcp_type"],
                   f'<a href="{html.escape(a["docs_url"])}">docs</a>', "☐ auth &nbsp;☐ access &nbsp;☐ MCP"]
                  for a in (by_id[i] for i in human_ids)]

    ctx = {
        **_composio_loop(scores),
        "retrieved": summary["retrieved"], "n": n, "nr": nr,
        "mcp_official": summary["mcp_official"], "mcp_remote": summary["mcp"].get("official_remote", 0),
        "mcp_local": summary["mcp"].get("official_local", 0), "mcp_flipped": drift["mcp_none_to_official"],
        "self_dev": summary["access_dev"].get("self", 0), "gated_dev": summary["access_dev"].get("gated", 0),
        "paid_dev": summary["access_dev"].get("paid", 0), "self_serve_n": summary["self_serve_n"],
        "prod_friction": summary["prod_friction"],
        "oauth2": summary["auth"]["oauth2"], "key": summary["auth"]["key"], "basic": summary["auth"]["basic"],
        "jwt": summary["auth"]["jwt"], "key_only": summary["auth_only_key"],
        "q_verified": quotes["verified"], "q_web": quotes["web_only"], "q_failed": quotes["failed"],
        "q_total": sum(quotes.values()),
        "v_easy": verdicts.get("easy", 0), "v_caveat": verdicts.get("caveat", 0), "v_hard": verdicts.get("hard", 0),
        "v_no": verdicts.get("no", 0), "v_unknown": verdicts.get("unknown", 0),
        "hard_names": names("hard"), "no_names": names("no"), "unknown_names": names("unknown"),
        "easy_prod": f'{cat["Productivity and Project Management"]["easy"]}/{cat["Productivity and Project Management"]["n"]}',
        "easy_data": f'{cat["Data, SEO and Scraping"]["easy"]}/{cat["Data, SEO and Scraping"]["n"]}',
        "easy_fin": f'{cat["Finance and Fintech"]["easy"]}/{cat["Finance and Fintech"]["n"]}',
        "easy_eco": f'{cat["Ecommerce"]["easy"]}/{cat["Ecommerce"]["n"]}',
        "easy_sup": f'{cat["Support and Helpdesk"]["easy"]}/{cat["Support and Helpdesk"]["n"]}',
        "blocker_bars": blocker_bars, "category_table": _table(category_rows,
            ["Category", "n", "Free/trial dev access", "Paid/gated dev access", "Official MCP", "Easy", "Caveat", "Hard"]),
        # accuracy: random held-out sample (gold B), the number to trust
        "b_mcp_p1": _frac(scores, "pass1_memory", B, "mcp_official"), "b_mcp_p2": _frac(scores, "pass2b", B, "mcp_official"),
        "b_acc_p1": _frac(scores, "pass1_memory", B, "access"), "b_acc_p2": _frac(scores, "pass2b", B, "access"),
        "b_ver_p1": sc("pass1_memory", B, "verdict")["acc"], "b_ver_v1": sc("pass2b", B, "verdict")["acc"],
        "b_ver_v3": sc("pass2b_v3", B, "verdict")["acc"],
        "a_ver_p1": sc("pass1_memory", A, "verdict")["acc"], "a_ver_v1": sc("pass2b", A, "verdict")["acc"],
        "a_ver_v3": sc("pass2b_v3", A, "verdict")["acc"],
        "a_auth_p1": sc("pass1_memory", A, "auth")["acc"], "a_auth_p2": sc("pass2b", A, "auth")["acc"],
        "a_mcp_p1": _frac(scores, "pass1_memory", A, "mcp_official"), "a_mcp_p2": _frac(scores, "pass2b", A, "mcp_official"),
        "score_table_b": _score_table(scores, B), "score_table_a": _score_table(scores, A),
        "drift_mcp": drift["mcp_changed"], "drift_access": drift["access_changed"], "drift_auth": drift["auth_changed"],
        "drift_verdict": drift["verdict_changed"],
        "miss_count": len(misses),
        "miss_table": _table([[g, html.escape(a), f, x, y] for g, a, f, x, y in misses], ["Gold", "App", "Field", "Gold says", "Pass 2 says"]),
        "audit_table": _table([["Dev access class", "{}/{}".format(*audit_agree["access"])],
                               ["Auth methods (strict)", "{}/{}".format(*audit_agree["auth"])],
                               ["Official MCP", "{}/{}".format(*audit_agree["mcp"])],
                               ["Cited quote + URL fully support the values", "{}/{}".format(*audit_agree["evidence"])]],
                              ["Field", "Auditor agrees with pipeline (30 fresh apps)"]),
        "audit_ev_bad": audit_agree["evidence"][1] - audit_agree["evidence"][0], "audit_n": audit_agree["evidence"][1],
        "e40_present": audit_ev["present"], "e40_n": audit_ev["n"], "e40_clean": audit_ev["clean"],
        "e40_weak": audit_ev["weak"], "e40_part": audit_ev["partial"], "e40_no": audit_ev["no"],
        "queue_n": len(queue), "human_rows": _table(human_rows, ["App", "Auth", "Dev → prod access", "MCP", "Docs", "Check"]),
        "web_only_apps": sum(1 for r in _jsonl("data/pass2/pass2a.jsonl") if any(e.get("src") == "web" for e in r["evidence"])),
    }
    keep = ("id", "name", "category", "description", "auth", "access_dev", "access_prod", "min_plan", "admin_only_credential",
            "api_styles", "api_breadth", "api_beta", "tenancy", "mcp_type", "mcp_url", "docs_url", "evidence", "confidence",
            "needs_human", "entity_status", "entity_note", "verdict", "rule", "blockers", "quotes_verified", "quotes_web_only", "quotes_failed")
    rows = []
    for a in apps:
        row = {k: a.get(k) for k in keep}
        for list_field in ("auth", "api_styles", "blockers", "evidence"):   # extractors sometimes wrote "unknown" instead of []
            if not isinstance(row[list_field], list):
                row[list_field] = [] if row[list_field] in (None, "unknown") else [row[list_field]]
        rows.append(row)
    ctx["app_data_json"] = json.dumps(rows, ensure_ascii=False).replace("</", "<\\/")
    return {k: str(v) for k, v in ctx.items()}
