"""Deterministic buildability rubric (first match wins). Same code scores agent output and gold-derived fields."""
HARD = {"sales_contact","customer_only","partner_review","enterprise_license","kyc_verification"}
def verdict(r, fixed=False):
    # v1 (original, as written in the reviewer notes): an official MCP excuses gated dev access from 'hard'; prod paid plan ignored; unknown access defaults to easy.
    # v3 (fixed=True, post-hoc after audit): no MCP exemption; gated/paid PRODUCTION access counts as friction; unknown access -> 'unknown'.
    """returns (label, rule, blocker_codes)"""
    b = []
    if r.get("entity_status") in ("ambiguous","not_found"): return "unknown","R0",["ENTITY_UNRESOLVED"]
    styles = set(r.get("api_styles") or []); mcp = r.get("mcp_type")
    dev = r.get("access_dev"); prod = r.get("access_prod","same_as_dev")
    if dev == "unknown" and not styles: return "unknown","R0",["DOCS_NOT_PUBLIC"]
    selfserve_mcp = (not fixed) and mcp in ("official_remote","official_local")
    if styles <= {"cli_only","none","sdk_only"} and mcp not in ("official_remote","official_local"):
        return "no","R1",["NO_API"]
    if dev in HARD and not selfserve_mcp: return "hard","R2",[{"sales_contact":"SALES_CONTACT","customer_only":"CUSTOMER_ONLY","partner_review":"PARTNER_PROGRAM","enterprise_license":"ENTERPRISE_ONLY","kyc_verification":"KYC_OR_BUSINESS_VERIFICATION"}[dev]]
    if fixed and dev == "unknown": return "unknown","R0b",["DOCS_NOT_PUBLIC"]
    if dev == "paid_plan" or (fixed and prod == "paid_plan"): b.append("PAID_PLAN")
    if dev in HARD: b.append("ENTERPRISE_ONLY" if dev=="enterprise_license" else "SALES_CONTACT")
    if prod not in ("same_as_dev", dev, None, "unknown") and prod in HARD|{"app_review"}: b.append("APP_REVIEW" if prod=="app_review" else "PROD_APPROVAL")
    if r.get("admin_only_credential"): b.append("ADMIN_ONLY_CREDENTIAL")
    if r.get("tenancy") in ("per_subdomain","self_hosted"): b.append("PER_TENANT_HOST")
    if r.get("tenancy") == "per_region": b.append("PER_REGION_HOST")
    if r.get("api_breadth") == "narrow": b.append("NARROW_SURFACE")
    if r.get("api_beta"): b.append("BETA_OR_UNSTABLE")
    if b: return "caveat","R3",b
    return "easy","R4",["NONE"]
