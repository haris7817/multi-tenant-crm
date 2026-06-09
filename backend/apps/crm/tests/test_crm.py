"""CRM CRUD, tenant scoping, role gating, and the pipeline move action."""
import pytest

from apps.accounts.models import Role
from apps.crm.models import Deal, Lead, Stage

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme(make_tenant, make_member):
    tenant = make_tenant("acme")
    for role in (Role.VIEWER, Role.SALES_REP, Role.MANAGER):
        make_member(tenant, role=role)
    return tenant


@pytest.fixture
def globex(make_tenant, make_member):
    tenant = make_tenant("globex")
    make_member(tenant, role=Role.SALES_REP)
    return tenant


# --- CRUD + ownership ---------------------------------------------------------

def test_sales_rep_creates_lead_with_auto_tenant_and_owner(client_for, acme):
    api = client_for(acme, role=Role.SALES_REP)
    resp = api.post("/api/leads/", {"name": "Jane Buyer", "company": "BuyCo"})
    assert resp.status_code == 201
    lead = Lead.all_objects.get(name="Jane Buyer")
    assert lead.tenant_id == acme.id          # tenant stamped from request
    assert lead.owner.email == f"{Role.SALES_REP}@acme.crm.local"  # owner defaulted


def test_list_leads_is_tenant_scoped(client_for, acme, globex):
    Lead.all_objects.create(tenant=acme, name="Acme Lead")
    Lead.all_objects.create(tenant=globex, name="Globex Lead")
    api = client_for(acme, role=Role.SALES_REP)
    resp = api.get("/api/leads/")
    names = {r["name"] for r in resp.json()["results"]}
    assert names == {"Acme Lead"}


def test_cannot_retrieve_other_tenants_lead(client_for, acme, globex):
    other = Lead.all_objects.create(tenant=globex, name="Globex Lead")
    api = client_for(acme, role=Role.SALES_REP)
    resp = api.get(f"/api/leads/{other.id}/")
    assert resp.status_code == 404   # scoped queryset hides it entirely


# --- RBAC gating --------------------------------------------------------------

def test_viewer_cannot_create_lead(client_for, acme):
    api = client_for(acme, role=Role.VIEWER)
    resp = api.post("/api/leads/", {"name": "Nope"})
    assert resp.status_code == 403


def test_viewer_can_list_leads(client_for, acme):
    Lead.all_objects.create(tenant=acme, name="Visible")
    api = client_for(acme, role=Role.VIEWER)
    assert api.get("/api/leads/").status_code == 200


def test_sales_rep_cannot_delete_but_manager_can(client_for, acme):
    lead = Lead.all_objects.create(tenant=acme, name="Doomed")
    rep = client_for(acme, role=Role.SALES_REP)
    assert rep.delete(f"/api/leads/{lead.id}/").status_code == 403
    mgr = client_for(acme, role=Role.MANAGER)
    assert mgr.delete(f"/api/leads/{lead.id}/").status_code == 204


def test_only_manager_can_create_stage(client_for, acme):
    rep = client_for(acme, role=Role.SALES_REP)
    assert rep.post("/api/stages/", {"name": "Extra", "order": 9}).status_code == 403
    mgr = client_for(acme, role=Role.MANAGER)
    assert mgr.post("/api/stages/", {"name": "Extra", "order": 9}).status_code == 201


# --- Deal pipeline ------------------------------------------------------------

def test_move_deal_to_won_sets_closed_at(client_for, acme):
    new = Stage.all_objects.get(tenant=acme, name="New")
    won = Stage.all_objects.get(tenant=acme, name="Won")
    deal = Deal.all_objects.create(tenant=acme, title="Big Deal", value=5000, stage=new)
    api = client_for(acme, role=Role.SALES_REP)
    resp = api.post(f"/api/deals/{deal.id}/move/", {"stage": won.id})
    assert resp.status_code == 200
    deal.refresh_from_db()
    assert deal.stage_id == won.id
    assert deal.closed_at is not None


def test_cannot_move_deal_to_foreign_stage(client_for, acme, globex):
    new = Stage.all_objects.get(tenant=acme, name="New")
    foreign = Stage.all_objects.get(tenant=globex, name="Won")
    deal = Deal.all_objects.create(tenant=acme, title="Deal", stage=new)
    api = client_for(acme, role=Role.SALES_REP)
    resp = api.post(f"/api/deals/{deal.id}/move/", {"stage": foreign.id})
    assert resp.status_code == 400


def test_pipeline_endpoint_groups_deals_by_stage(client_for, acme):
    new = Stage.all_objects.get(tenant=acme, name="New")
    Deal.all_objects.create(tenant=acme, title="D1", stage=new)
    Deal.all_objects.create(tenant=acme, title="D2", stage=new)
    api = client_for(acme, role=Role.VIEWER)
    resp = api.get("/api/deals/pipeline/")
    assert resp.status_code == 200
    board = {col["stage"]["name"]: len(col["deals"]) for col in resp.json()}
    assert board["New"] == 2
    assert board["Won"] == 0
