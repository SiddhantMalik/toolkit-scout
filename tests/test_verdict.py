"""The verdict rubric is the part reviewers argue about, so its rules are pinned down here."""
from verdict import verdict

BASE = dict(entity_status="resolved", api_styles=["rest"], mcp_type="official_remote",
            access_dev="self_free", access_prod="same_as_dev", api_breadth="broad", tenancy="global")


def make(**overrides):
    return {**BASE, **overrides}


def test_clean_self_serve_app_is_easy():
    assert verdict(make())[0] == "easy"


def test_unresolved_entity_is_unknown_first():
    assert verdict(make(entity_status="ambiguous")) == ("unknown", "R0", ["ENTITY_UNRESOLVED"])


def test_cli_only_without_mcp_is_no():
    assert verdict(make(api_styles=["cli_only"], mcp_type="none"))[0] == "no"


def test_gated_dev_access_is_hard_when_mcp_exemption_off():
    r = make(access_dev="customer_only")
    assert verdict(r, fixed=True)[0] == "hard"


def test_v1_lets_an_official_mcp_excuse_gated_access():
    # the logic hole found by the second audit: kept as v1 so the original numbers stay reproducible
    r = make(access_dev="customer_only")
    assert verdict(r, fixed=False)[0] == "caveat"


def test_paid_production_plan_is_friction_only_in_v3():
    r = make(access_prod="paid_plan")
    assert verdict(r, fixed=False)[0] == "easy"
    assert verdict(r, fixed=True) == ("caveat", "R3", ["PAID_PLAN"])


def test_unknown_access_is_unknown_in_v3_not_easy():
    r = make(access_dev="unknown")
    assert verdict(r, fixed=True)[0] == "unknown"


def test_friction_flags_collect_blocker_codes():
    r = make(admin_only_credential=True, tenancy="per_region", api_breadth="narrow", api_beta=True)
    label, rule, blockers = verdict(r)
    assert (label, rule) == ("caveat", "R3")
    assert set(blockers) == {"ADMIN_ONLY_CREDENTIAL", "PER_REGION_HOST", "NARROW_SURFACE", "BETA_OR_UNSTABLE"}
