"""Analytics: correct aggregates, win rate, and strict tenant scoping."""
import pytest

from apps.accounts.models import Role
from apps.crm.models import Deal, Lead, Stage

pytestmark = pytest.mark.django_db


def _stage(tenant, name):
    return Stage.all_objects.get(tenant=tenant, name=name)


@pytest.fixture
def acme(make_tenant):
    """Acme with 3 leads and deals: 2 won (1000+2000), 1 lost (500), 1 open (3000)."""
    tenant = make_tenant("acme")
    for i in range(3):
        Lead.all_objects.create(tenant=tenant, name=f"Lead {i}", status=Lead.Status.NEW)
    Deal.all_objects.create(tenant=tenant, title="W1", value=1000, stage=_stage(tenant, "Won"))
    Deal.all_objects.create(tenant=tenant, title="W2", value=2000, stage=_stage(tenant, "Won"))
    Deal.all_objects.create(tenant=tenant, title="L1", value=500, stage=_stage(tenant, "Lost"))
    Deal.all_objects.create(tenant=tenant, title="O1", value=3000, stage=_stage(tenant, "New"))
    return tenant


@pytest.fixture
def globex(make_tenant):
    tenant = make_tenant("globex")
    Lead.all_objects.create(tenant=tenant, name="G Lead", status=Lead.Status.NEW)
    Deal.all_objects.create(tenant=tenant, title="G", value=9999, stage=_stage(tenant, "Won"))
    return tenant


def test_summary_kpis(client_for, acme):
    api = client_for(acme)
    data = api.get("/api/analytics/summary/").json()
    assert data["leads_total"] == 3
    assert data["won_deals"] == 2
    assert data["won_value"] == 3000.0
    assert data["open_deals"] == 1
    assert data["open_pipeline_value"] == 3000.0
    # win rate = won / (won + lost) = 2 / 3
    assert data["win_rate"] == round(2 / 3, 3)


def test_summary_is_tenant_scoped(client_for, acme, globex):
    api = client_for(acme)
    data = api.get("/api/analytics/summary/").json()
    assert data["won_value"] == 3000.0  # Globex's 9999 never counted


def test_deals_by_stage_includes_empty_stages(client_for, acme):
    api = client_for(acme)
    rows = {r["stage"]: r for r in api.get("/api/analytics/deals-by-stage/").json()}
    assert rows["New"]["count"] == 1
    assert rows["Won"]["count"] == 2
    assert rows["Won"]["value"] == 3000.0
    assert rows["Proposal"]["count"] == 0   # empty stages still listed
    assert rows["Won"]["is_won"] is True


def test_leads_by_status(client_for, acme):
    api = client_for(acme)
    rows = {r["status"]: r["count"] for r in api.get("/api/analytics/leads-by-status/").json()}
    assert rows["new"] == 3


def test_leads_over_time_counts_recent(client_for, acme):
    api = client_for(acme)
    rows = api.get("/api/analytics/leads-over-time/").json()
    assert sum(r["count"] for r in rows) == 3


def test_requires_membership(client_for, acme, globex):
    # Acme member querying analytics on the Globex subdomain is rejected.
    api = client_for(acme)
    api.defaults["HTTP_HOST"] = "globex.crm.local"
    assert api.get("/api/analytics/summary/").status_code == 403


def test_summary_is_cached_per_tenant(client_for, acme):
    api = client_for(acme)
    first = api.get("/api/analytics/summary/").json()
    # Add a won deal AFTER the first (now-cached) call.
    Deal.all_objects.create(tenant=acme, title="W3", value=5000, stage=_stage(acme, "Won"))
    cached = api.get("/api/analytics/summary/").json()
    assert cached == first  # served from cache, new deal not yet reflected
