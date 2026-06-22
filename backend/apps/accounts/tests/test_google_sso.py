"""Phase 12.1 — Sign in with Google (verifier mocked)."""
import pytest

from apps.accounts import google_auth
from apps.accounts.models import Role

pytestmark = pytest.mark.django_db


def _mock_verify(monkeypatch, email, verified=True):
    monkeypatch.setattr(
        google_auth,
        "verify_google_token",
        lambda credential: {"email": email, "email_verified": verified},
    )


def test_member_can_sign_in_with_google(api_client, make_tenant, make_member, monkeypatch):
    tenant = make_tenant("acme")
    make_member(tenant, role=Role.MANAGER, email="boss@acme.crm.local")
    _mock_verify(monkeypatch, "boss@acme.crm.local")

    resp = api_client.post(
        "/api/auth/google/", {"credential": "g-token"}, HTTP_HOST="acme.crm.local"
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == Role.MANAGER
    assert resp.json()["tenant"] == "acme"
    assert resp.json()["access"]


def test_non_member_email_rejected(api_client, make_tenant, monkeypatch):
    make_tenant("acme")
    _mock_verify(monkeypatch, "stranger@elsewhere.com")
    resp = api_client.post(
        "/api/auth/google/", {"credential": "g-token"}, HTTP_HOST="acme.crm.local"
    )
    assert resp.status_code == 403


def test_unverified_email_rejected(api_client, make_tenant, make_member, monkeypatch):
    tenant = make_tenant("acme")
    make_member(tenant, role=Role.VIEWER, email="v@acme.crm.local")
    _mock_verify(monkeypatch, "v@acme.crm.local", verified=False)
    resp = api_client.post(
        "/api/auth/google/", {"credential": "g-token"}, HTTP_HOST="acme.crm.local"
    )
    assert resp.status_code == 401


def test_invalid_token_rejected(api_client, make_tenant, monkeypatch):
    make_tenant("acme")

    def boom(credential):
        raise ValueError("bad token")

    monkeypatch.setattr(google_auth, "verify_google_token", boom)
    resp = api_client.post(
        "/api/auth/google/", {"credential": "x"}, HTTP_HOST="acme.crm.local"
    )
    assert resp.status_code == 401


def test_missing_credential_400(api_client, make_tenant):
    make_tenant("acme")
    resp = api_client.post("/api/auth/google/", {}, HTTP_HOST="acme.crm.local")
    assert resp.status_code == 400
