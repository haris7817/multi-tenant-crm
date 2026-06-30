"""Phase 11.6 — inbound signature-verified receiver."""
import hashlib
import hmac
import json

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.crm.models import Lead
from apps.webhooks.models import InboundEndpoint, InboundEvent

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme(make_tenant):
    return make_tenant("acme")


def _sign(secret, body: bytes):
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def _post_raw(token, body: bytes, signature):
    # Anonymous client (no auth) — partners don't have JWT/keys.
    return APIClient().post(
        f"/api/v1/inbound/{token}/",
        data=body,
        content_type="application/json",
        HTTP_X_SIGNATURE=signature,
    )


# --- Management --------------------------------------------------------------

def test_admin_creates_inbound_endpoint(jwt_client, acme):
    api = jwt_client(acme, role=Role.ADMIN)
    resp = api.post(
        "/api/inbound-endpoints/",
        {"source": "typeform", "action": "create_lead"},
        format="json",
    )
    assert resp.status_code == 201
    body = resp.json()
    assert len(body["token"]) == 32 and len(body["secret"]) == 64
    assert body["receive_url"] == f"/api/v1/inbound/{body['token']}/"


# --- Receiver ----------------------------------------------------------------

def test_valid_signature_creates_lead(acme):
    ep = InboundEndpoint.all_objects.create(
        tenant=acme, token="t" * 32, secret="s" * 64, source="typeform"
    )
    body = json.dumps({"name": "Inbound Jane", "email": "j@x.com"}).encode()
    resp = _post_raw(ep.token, body, _sign(ep.secret, body))
    assert resp.status_code == 201
    lead = Lead.all_objects.get(tenant=acme, name="Inbound Jane")
    assert lead.source == "typeform"
    assert InboundEvent.all_objects.filter(endpoint=ep, status="processed").exists()


def test_invalid_signature_rejected(acme):
    ep = InboundEndpoint.all_objects.create(
        tenant=acme, token="t" * 32, secret="s" * 64
    )
    body = json.dumps({"name": "Nope"}).encode()
    resp = _post_raw(ep.token, body, "sha256=wrong")
    assert resp.status_code == 401
    assert not Lead.all_objects.filter(tenant=acme, name="Nope").exists()
    assert InboundEvent.all_objects.filter(endpoint=ep, status="rejected").exists()


def test_unknown_token_404(acme):
    body = b"{}"
    resp = _post_raw("z" * 32, body, _sign("whatever", body))
    assert resp.status_code == 404


def test_missing_name_400(acme):
    ep = InboundEndpoint.all_objects.create(
        tenant=acme, token="t" * 32, secret="s" * 64
    )
    body = json.dumps({"email": "no-name@x.com"}).encode()
    resp = _post_raw(ep.token, body, _sign(ep.secret, body))
    assert resp.status_code == 400
