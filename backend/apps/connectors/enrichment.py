"""
Lead enrichment (13.6).

Default provider derives company from the email domain (deterministic, works with
no external account). Swap ``_lookup`` for Clearbit/Apollo in production.
"""


def _lookup(email: str) -> dict:
    """Return enrichment data for an email. Replace with a real provider."""
    domain = email.split("@")[-1] if "@" in (email or "") else ""
    if not domain or domain in {"gmail.com", "outlook.com", "yahoo.com"}:
        return {}
    name = domain.rsplit(".", 1)[0].replace("-", " ").title()
    return {"company": name, "domain": domain, "enriched": True}


def enrich_lead(lead) -> dict:
    """Fill company + custom fields on a lead from the enrichment provider."""
    data = _lookup(lead.email)
    if not data:
        return {}
    if data.get("company") and not lead.company:
        lead.company = data["company"]
    lead.custom = {**(lead.custom or {}), **{k: v for k, v in data.items() if k != "company"}}
    lead.save()
    return data
