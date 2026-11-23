"""Collapse any vocabulary (pass-1 seed, pass-2 schema, gold) into comparable fields."""
from verdict import verdict
def auth_set(xs):
    m = {"oauth2":"oauth2","apikey":"key","api_key":"key","token":"key","bearer_token":"key","basic":"basic","jwt":"jwt","none":"none","other":"other"}
    return sorted({m[x] for x in xs if x in m})
def access_cls(v):
    return {"self":"self","trial":"self","self_free":"self","self_trial":"self","paid":"paid","paid_plan":"paid","gated":"gated",
            "sales_contact":"gated","customer_only":"gated","partner_review":"gated","enterprise_license":"gated","kyc_verification":"gated"}.get(v)
def from_pass1(a):
    return {"auth": auth_set(a["auth"]), "access": access_cls(a["access"]), "mcp_official": a["mcp"]=="official", "verdict": a["verdict"]}
def from_pass2(r, exempt=True):
    v = verdict(r, mcp_exempt=exempt)[0]
    mo = None if r.get("mcp_type") in (None,"unknown") else r["mcp_type"] in ("official_remote","official_local")
    return {"auth": auth_set(r.get("auth") or []), "access": access_cls(r.get("access_dev")), "mcp_official": mo, "verdict": v}
def from_goldB(g):
    return {"auth": auth_set(g.get("auth") or []), "access": access_cls(g.get("access_dev")),
            "mcp_official": None if g.get("mcp_type") in (None,"unknown") else g["mcp_type"] in ("official_remote","official_local"),
            "verdict": g.get("verdict")}
