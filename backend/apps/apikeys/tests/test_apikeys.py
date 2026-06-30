"""Phase 10 — API key management, key auth, scopes, tenant-from-key isolation."""
import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.apikeys.models import ApiKey, Scope
from apps.crm.models import Lead

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme(make_tenant):
    return make_tenant("acme")


@pytest.fixture
def globex(make_tenant):
    return make_tenant("globex")


# --- 10.2 Management ---------------------------------------------------------

def test_admin_creates_key_and_secret_shown_once(jwt_client, acme):
    api = jwt_client(acme, role=Role.ADMIN)
    resp = api.post(
        "/api/api-keys/", {"name": "Zapier", "scopes": ["read", "write"]}, format="json"
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["key"].startswith("crm_")          # raw secret returned once
    assert body["prefix"] in body["key"]
    # Listing never exposes the secret again.
    listed = api.get("/api/api-keys/").json()["results"][0]
    assert "key" not in listed


def test_sales_rep_cannot_manage_keys(jwt_client, acme):
    api = jwt_client(acme, role=Role.SALES_REP)
    assert api.post("/api/api-keys/", {"name": "x"}, format="json").status_code == 403


def test_revoke_key_disables_it(jwt_client, api_key_client, acme):
    api, key, raw = api_key_client(acme, scopes=[Scope.READ])
    admin = jwt_client(acme, role=Role.ADMIN)
    assert admin.delete(f"/api/api-keys/{key.id}/").status_code == 204
    key.refresh_from_db()
    assert key.revoked_at is not None
    # The revoked key no longer authenticates.
    assert api.get("/api/v1/leads/").status_code == 401


# --- 10.3 Key auth + scopes --------------------------------------------------

def test_read_key_can_list_but_not_write(api_key_client, acme):
    Lead.all_objects.create(tenant=acme, name="Acme Lead")
    api, _key, _raw = api_key_client(acme, scopes=[Scope.READ])
    assert api.get("/api/v1/leads/").status_code == 200
    assert api.post("/api/v1/leads/", {"name": "New"}, format="json").status_code == 403


def test_write_key_can_create(api_key_client, acme):
    api, _key, _raw = api_key_client(acme, scopes=[Scope.READ, Scope.WRITE])
    resp = api.post("/api/v1/leads/", {"name": "Via API"}, format="json")
    assert resp.status_code == 201
    assert Lead.all_objects.filter(tenant=acme, name="Via API").exists()


def test_bad_key_is_rejected():
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION="Api-Key crm_deadbeef_nope")
    assert api.get("/api/v1/leads/").status_code == 401


# --- Tenant binding from the key (no subdomain needed) -----------------------

def test_key_binds_tenant_regardless_of_host(api_key_client, acme, globex):
    Lead.all_objects.create(tenant=acme, name="Acme Lead")
    Lead.all_objects.create(tenant=globex, name="Globex Lead")
    api, _key, _raw = api_key_client(acme, scopes=[Scope.READ])
    # No tenant subdomain in the Host — tenant comes purely from the key.
    resp = api.get("/api/v1/leads/", HTTP_HOST="testserver")
    names = {r["name"] for r in resp.json()["results"]}
    assert names == {"Acme Lead"}


def test_jwt_still_works_on_v1(jwt_client, acme):
    Lead.all_objects.create(tenant=acme, name="Acme Lead")
    api = jwt_client(acme, role=Role.VIEWER)
    assert api.get("/api/v1/leads/").status_code == 200
