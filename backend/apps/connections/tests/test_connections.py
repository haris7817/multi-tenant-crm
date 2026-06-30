"""Phase 12 — encrypted credentials + OAuth connection framework."""
import pytest
from django.db import connection as db_conn

from apps.accounts.models import Role
from apps.connections import services
from apps.connections.crypto import decrypt
from apps.connections.models import Connection, OAuthState

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme(make_tenant):
    return make_tenant("acme")


@pytest.fixture
def globex(make_tenant):
    return make_tenant("globex")


@pytest.fixture
def configured_google(settings):
    settings.OAUTH_PROVIDERS = {
        "google": {"client_id": "cid", "client_secret": "csecret"},
        "slack": {"client_id": "", "client_secret": ""},
    }


# --- 12.3 Encryption at rest -------------------------------------------------

def test_tokens_encrypted_in_db(acme):
    conn = Connection.all_objects.create(
        tenant=acme, provider="google", access_token="super-secret-token"
    )
    # The Python value is plaintext...
    conn.refresh_from_db()
    assert conn.access_token == "super-secret-token"
    # ...but the raw DB column is ciphertext (not the plaintext).
    with db_conn.cursor() as c:
        c.execute(
            "SELECT access_token FROM connections_connection WHERE id = %s", [conn.id]
        )
        raw = c.fetchone()[0]
    assert raw != "super-secret-token"
    assert decrypt(raw) == "super-secret-token"


# --- 12.4 OAuth flow ---------------------------------------------------------

def test_authorize_returns_url(jwt_client, acme, configured_google):
    api = jwt_client(acme, role=Role.ADMIN)
    resp = api.post(
        "/api/connections/authorize/",
        {"provider": "google", "redirect_uri": "https://acme.crm.local/oauth/callback"},
        format="json",
    )
    assert resp.status_code == 200
    assert resp.json()["authorize_url"].startswith(
        "https://accounts.google.com/o/oauth2/v2/auth?"
    )
    assert OAuthState.objects.filter(tenant=acme, provider="google").exists()


def test_unconfigured_provider_rejected(jwt_client, acme, configured_google):
    api = jwt_client(acme, role=Role.ADMIN)
    resp = api.post(
        "/api/connections/authorize/",
        {"provider": "slack", "redirect_uri": "https://acme.crm.local/cb"},
        format="json",
    )
    assert resp.status_code == 400


def test_callback_exchanges_code(jwt_client, acme, configured_google, monkeypatch):
    monkeypatch.setattr(
        services, "_token_request",
        lambda url, data: {
            "access_token": "at-123", "refresh_token": "rt-456",
            "expires_in": 3600, "scope": "email", "account_email": "u@acme.com",
        },
    )
    api = jwt_client(acme, role=Role.ADMIN)
    st = OAuthState.objects.create(
        tenant=acme, provider="google", state="xyz",
        redirect_uri="https://acme.crm.local/cb",
    )
    resp = api.post(
        "/api/connections/callback/", {"state": st.state, "code": "auth-code"},
        format="json",
    )
    assert resp.status_code == 201
    conn = Connection.all_objects.get(tenant=acme, provider="google")
    assert conn.status == "connected"
    assert conn.access_token == "at-123"  # decrypted on read
    assert "access_token" not in resp.json()  # token never returned over API


def test_refresh_connection(acme, configured_google, monkeypatch):
    conn = Connection.all_objects.create(
        tenant=acme, provider="google", refresh_token="rt-old",
        access_token="at-old", status="connected",
    )
    monkeypatch.setattr(
        services, "_token_request",
        lambda url, data: {"access_token": "at-new", "expires_in": 3600},
    )
    services.refresh_connection(conn)
    conn.refresh_from_db()
    assert conn.access_token == "at-new"


def test_used_state_cannot_be_replayed(jwt_client, acme, configured_google, monkeypatch):
    monkeypatch.setattr(
        services, "_token_request",
        lambda url, data: {"access_token": "at", "refresh_token": "rt"},
    )
    api = jwt_client(acme, role=Role.ADMIN)
    st = OAuthState.objects.create(
        tenant=acme, provider="google", state="once", redirect_uri="https://x/cb"
    )
    first = api.post("/api/connections/callback/", {"state": "once", "code": "c"}, format="json")
    assert first.status_code == 201
    replay = api.post("/api/connections/callback/", {"state": "once", "code": "c"}, format="json")
    assert replay.status_code == 400  # state already used


def test_connections_tenant_scoped(jwt_client, acme, globex):
    Connection.all_objects.create(tenant=globex, provider="google", status="connected")
    api = jwt_client(acme, role=Role.ADMIN)
    assert api.get("/api/connections/").json()["count"] == 0


def test_member_cannot_authorize(jwt_client, acme, configured_google):
    api = jwt_client(acme, role=Role.VIEWER)
    resp = api.post(
        "/api/connections/authorize/",
        {"provider": "google", "redirect_uri": "https://x/cb"},
        format="json",
    )
    assert resp.status_code == 403
