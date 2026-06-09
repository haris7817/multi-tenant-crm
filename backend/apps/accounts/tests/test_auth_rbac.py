"""Auth + RBAC: tenant-scoped login, role gating, and cross-tenant token rejection."""
import pytest

from apps.accounts.models import Membership, Role
from apps.accounts.tests.conftest import login

pytestmark = pytest.mark.django_db


def test_login_returns_tenant_scoped_token(api_client, acme, make_member):
    make_member(acme, "owner@acme.crm.local", role=Role.OWNER)
    resp = login(api_client, "acme.crm.local", "owner@acme.crm.local")
    assert resp.status_code == 200
    assert resp.json()["role"] == Role.OWNER
    assert resp.json()["tenant"] == "acme"


def test_login_rejected_for_non_member(api_client, acme, globex, make_member):
    # User belongs to acme, tries to log in on globex subdomain.
    make_member(acme, "owner@acme.crm.local", role=Role.OWNER)
    resp = login(api_client, "globex.crm.local", "owner@acme.crm.local")
    assert resp.status_code == 400


def test_me_returns_role_and_tenant(api_client, auth_client, acme, make_member):
    make_member(acme, "mgr@acme.crm.local", role=Role.MANAGER)
    token = login(api_client, "acme.crm.local", "mgr@acme.crm.local").json()["access"]
    client = auth_client(token, "acme.crm.local")
    resp = client.get("/api/auth/me/")
    assert resp.status_code == 200
    assert resp.json()["role"] == Role.MANAGER
    assert resp.json()["tenant"]["slug"] == "acme"


def test_viewer_cannot_invite_members(api_client, auth_client, acme, make_member):
    make_member(acme, "viewer@acme.crm.local", role=Role.VIEWER)
    token = login(api_client, "acme.crm.local", "viewer@acme.crm.local").json()["access"]
    client = auth_client(token, "acme.crm.local")
    resp = client.post("/api/members/", {"email": "new@acme.crm.local", "role": "viewer"})
    assert resp.status_code == 403


def test_admin_can_invite_members(api_client, auth_client, acme, make_member):
    make_member(acme, "admin@acme.crm.local", role=Role.ADMIN)
    token = login(api_client, "acme.crm.local", "admin@acme.crm.local").json()["access"]
    client = auth_client(token, "acme.crm.local")
    resp = client.post(
        "/api/members/",
        {"email": "new@acme.crm.local", "role": "sales_rep", "password": "password123"},
    )
    assert resp.status_code == 201
    assert Membership.objects.filter(
        tenant=acme, user__email="new@acme.crm.local"
    ).exists()


def test_cross_tenant_token_is_rejected(api_client, auth_client, acme, globex, make_member):
    """An Acme token must not work against the Globex subdomain."""
    make_member(acme, "owner@acme.crm.local", role=Role.OWNER)
    token = login(api_client, "acme.crm.local", "owner@acme.crm.local").json()["access"]
    client = auth_client(token, "globex.crm.local")
    resp = client.get("/api/auth/me/")
    assert resp.status_code == 403


def test_members_list_scoped_to_tenant(api_client, auth_client, acme, globex, make_member):
    make_member(acme, "a-admin@acme.crm.local", role=Role.ADMIN)
    make_member(acme, "a-rep@acme.crm.local", role=Role.SALES_REP)
    make_member(globex, "g-owner@globex.crm.local", role=Role.OWNER)
    token = login(api_client, "acme.crm.local", "a-admin@acme.crm.local").json()["access"]
    client = auth_client(token, "acme.crm.local")
    resp = client.get("/api/members/")
    assert resp.status_code == 200
    emails = {m["email"] for m in resp.json()["results"]}
    assert emails == {"a-admin@acme.crm.local", "a-rep@acme.crm.local"}


def test_register_creates_tenant_and_owner(api_client):
    resp = api_client.post(
        "/api/auth/register/",
        {
            "tenant_name": "New Co",
            "slug": "newco",
            "email": "founder@newco.crm.local",
            "password": "password123",
        },
        HTTP_HOST="crm.local",
    )
    assert resp.status_code == 201
    assert resp.json()["tenant"]["slug"] == "newco"
    # And the founder can immediately log in on their new subdomain as Owner.
    login_resp = login(api_client, "newco.crm.local", "founder@newco.crm.local")
    assert login_resp.status_code == 200
    assert login_resp.json()["role"] == Role.OWNER
