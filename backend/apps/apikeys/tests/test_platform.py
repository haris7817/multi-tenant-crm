"""Phase 10 iter 2 — error envelope (10.5) + idempotency keys (10.5)."""
import pytest

from apps.accounts.models import Role
from apps.crm.models import Lead

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme(make_tenant):
    return make_tenant("acme")


# --- Error envelope ----------------------------------------------------------

def test_envelope_validation_error(jwt_client, acme):
    api = jwt_client(acme, role=Role.SALES_REP)
    resp = api.post("/api/leads/", {}, format="json")  # missing name
    assert resp.status_code == 400
    err = resp.json()["error"]
    assert err["code"] == "validation_error"
    assert err["status"] == 400
    assert "name" in err["fields"]


def test_envelope_permission_denied(jwt_client, acme):
    api = jwt_client(acme, role=Role.VIEWER)
    resp = api.post("/api/leads/", {"name": "x"}, format="json")
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "permission_denied"


def test_envelope_not_found(jwt_client, acme):
    api = jwt_client(acme, role=Role.SALES_REP)
    resp = api.get("/api/leads/99999999/")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


# --- Idempotency -------------------------------------------------------------

def test_idempotency_key_prevents_duplicate(jwt_client, acme):
    api = jwt_client(acme, role=Role.SALES_REP)
    hdr = {"HTTP_IDEMPOTENCY_KEY": "create-lead-001"}
    r1 = api.post("/api/leads/", {"name": "Idem Lead"}, format="json", **hdr)
    r2 = api.post("/api/leads/", {"name": "Idem Lead"}, format="json", **hdr)

    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r2["X-Idempotent-Replay"] == "true"
    assert r1.json()["id"] == r2.json()["id"]
    assert Lead.all_objects.filter(tenant=acme, name="Idem Lead").count() == 1


def test_different_idempotency_keys_create_two(jwt_client, acme):
    api = jwt_client(acme, role=Role.SALES_REP)
    api.post("/api/leads/", {"name": "Dup"}, format="json", HTTP_IDEMPOTENCY_KEY="k1")
    api.post("/api/leads/", {"name": "Dup"}, format="json", HTTP_IDEMPOTENCY_KEY="k2")
    assert Lead.all_objects.filter(tenant=acme, name="Dup").count() == 2
