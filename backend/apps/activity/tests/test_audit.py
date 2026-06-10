"""Audit logging: writes are recorded with actor + diff, reads are tenant-scoped."""
import pytest

from apps.accounts.models import Role
from apps.activity.models import AuditLog

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme(make_tenant):
    return make_tenant("acme")


@pytest.fixture
def globex(make_tenant):
    return make_tenant("globex")


def test_creating_a_lead_records_an_audit_entry(client_for, acme):
    api = client_for(acme, role=Role.SALES_REP)
    resp = api.post("/api/leads/", {"name": "Jane", "company": "BuyCo"})
    assert resp.status_code == 201

    log = AuditLog.objects.get(tenant=acme, action="created")
    assert log.target_repr == "Jane"
    assert log.target_type.model == "lead"
    assert log.actor.email == f"{Role.SALES_REP}@acme.crm.local"


def test_updating_a_lead_records_a_field_diff(client_for, acme):
    api = client_for(acme, role=Role.SALES_REP)
    lead_id = api.post("/api/leads/", {"name": "Jane", "status": "new"}).json()["id"]

    api.patch(f"/api/leads/{lead_id}/", {"status": "qualified"}, format="json")

    log = AuditLog.objects.filter(tenant=acme, action="updated").latest("created_at")
    assert log.changes["status"] == ["new", "qualified"]


def test_deleting_records_an_entry(client_for, acme):
    rep = client_for(acme, role=Role.SALES_REP)
    lead_id = rep.post("/api/leads/", {"name": "Doomed"}).json()["id"]
    mgr = client_for(acme, role=Role.MANAGER)
    assert mgr.delete(f"/api/leads/{lead_id}/").status_code == 204

    assert AuditLog.objects.filter(
        tenant=acme, action="deleted", target_repr="Doomed"
    ).exists()


def test_activity_feed_is_tenant_scoped(client_for, acme, globex):
    a = client_for(acme, role=Role.SALES_REP)
    a.post("/api/leads/", {"name": "Acme Lead"})
    g = client_for(globex, role=Role.SALES_REP)
    g.post("/api/leads/", {"name": "Globex Lead"})

    resp = a.get("/api/activity/")
    assert resp.status_code == 200
    reprs = {row["target_repr"] for row in resp.json()["results"]}
    assert reprs == {"Acme Lead"}          # never sees Globex's activity


def test_activity_feed_filters_by_record(client_for, acme):
    api = client_for(acme, role=Role.SALES_REP)
    l1 = api.post("/api/leads/", {"name": "Lead One"}).json()["id"]
    api.post("/api/leads/", {"name": "Lead Two"})
    api.patch(f"/api/leads/{l1}/", {"status": "contacted"}, format="json")

    resp = api.get(f"/api/activity/?target_model=lead&target_id={l1}")
    assert resp.status_code == 200
    actions = sorted(row["action"] for row in resp.json()["results"])
    assert actions == ["created", "updated"]   # only Lead One's history


def test_activity_is_read_only(client_for, acme):
    api = client_for(acme, role=Role.MANAGER)
    assert api.post("/api/activity/", {"action": "created"}).status_code == 405
