"""Phase 11 — outbox, dispatch, HMAC signing, scoping, retry, replay."""
import hashlib
import hmac
import json
import urllib.error

import pytest

from apps.accounts.models import Role
from apps.crm.models import Lead
from apps.webhooks import tasks as webhook_tasks
from apps.webhooks.models import WebhookDelivery, WebhookEndpoint, WebhookEvent

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme(make_tenant):
    return make_tenant("acme")


@pytest.fixture
def capture_posts(monkeypatch):
    """Record outbound HTTP posts instead of making real requests."""
    calls = []

    def fake_post(url, data, headers, timeout=10):
        calls.append({"url": url, "data": data, "headers": headers})
        return 200

    monkeypatch.setattr(webhook_tasks, "_post", fake_post)
    return calls


# --- 11.5 Management ---------------------------------------------------------

def test_admin_creates_endpoint_with_secret(jwt_client, acme):
    api = jwt_client(acme, role=Role.ADMIN)
    resp = api.post(
        "/api/webhooks/",
        {"url": "https://example.com/hook", "events": ["lead.created"]},
        format="json",
    )
    assert resp.status_code == 201
    assert len(resp.json()["secret"]) == 64  # generated signing secret


def test_sales_rep_cannot_create_endpoint(jwt_client, acme):
    api = jwt_client(acme, role=Role.SALES_REP)
    resp = api.post("/api/webhooks/", {"url": "https://x.com/h"}, format="json")
    assert resp.status_code == 403


def test_invalid_event_rejected(jwt_client, acme):
    api = jwt_client(acme, role=Role.ADMIN)
    resp = api.post(
        "/api/webhooks/",
        {"url": "https://x.com/h", "events": ["not.real"]},
        format="json",
    )
    assert resp.status_code == 400


# --- 11.2/11.3 Outbox -> dispatch -> signed delivery -------------------------

def test_lead_created_delivers_signed_payload(
    jwt_client, acme, capture_posts, django_capture_on_commit_callbacks
):
    endpoint = WebhookEndpoint.all_objects.create(
        tenant=acme, url="https://example.com/hook",
        secret="s" * 64, events=["lead.created"],
    )
    api = jwt_client(acme, role=Role.SALES_REP)

    with django_capture_on_commit_callbacks(execute=True):
        resp = api.post("/api/leads/", {"name": "Hook Lead"}, format="json")
    assert resp.status_code == 201

    # An outbox row exists and a delivery succeeded.
    assert WebhookEvent.all_objects.filter(
        tenant=acme, event_type="lead.created", dispatched=True
    ).exists()
    delivery = WebhookDelivery.all_objects.get(endpoint=endpoint)
    assert delivery.status == "success"
    assert delivery.attempts == 1

    # The payload was HMAC-signed with the endpoint secret.
    assert len(capture_posts) == 1
    call = capture_posts[0]
    expected = hmac.new(b"s" * 64, call["data"], hashlib.sha256).hexdigest()
    assert call["headers"]["X-Webhook-Signature"] == f"sha256={expected}"
    body = json.loads(call["data"])
    assert body["event"] == "lead.created"
    assert body["data"]["name"] == "Hook Lead"


def test_endpoint_only_gets_subscribed_events(
    jwt_client, acme, capture_posts, django_capture_on_commit_callbacks
):
    # Subscribed to deal.won only — should NOT receive lead.created.
    WebhookEndpoint.all_objects.create(
        tenant=acme, url="https://example.com/hook",
        secret="x" * 64, events=["deal.won"],
    )
    api = jwt_client(acme, role=Role.SALES_REP)
    with django_capture_on_commit_callbacks(execute=True):
        api.post("/api/leads/", {"name": "No Hook"}, format="json")
    assert capture_posts == []


def test_delivery_is_tenant_scoped(
    jwt_client, make_tenant, capture_posts, django_capture_on_commit_callbacks
):
    acme = make_tenant("acme")
    globex = make_tenant("globex")
    WebhookEndpoint.all_objects.create(
        tenant=globex, url="https://globex.example/hook",
        secret="g" * 64, events=["*"],
    )
    api = jwt_client(acme, role=Role.SALES_REP)
    with django_capture_on_commit_callbacks(execute=True):
        api.post("/api/leads/", {"name": "Acme only"}, format="json")
    # Globex endpoint must not receive Acme's event.
    assert capture_posts == []


# --- 11.3 Failure handling ---------------------------------------------------

def test_4xx_marks_failed_without_retry(acme, monkeypatch):
    endpoint = WebhookEndpoint.all_objects.create(
        tenant=acme, url="https://example.com/hook", secret="s" * 64, events=["*"]
    )
    event = WebhookEvent.all_objects.create(tenant=acme, event_type="lead.created")
    delivery = WebhookDelivery.all_objects.create(
        tenant=acme, endpoint=endpoint, event=event
    )

    def boom(url, data, headers, timeout=10):
        raise urllib.error.HTTPError(url, 400, "Bad Request", {}, None)

    monkeypatch.setattr(webhook_tasks, "_post", boom)
    webhook_tasks.deliver(delivery.id)

    delivery.refresh_from_db()
    assert delivery.status == "failed"
    assert delivery.response_status == 400
    assert delivery.attempts == 1


# --- 11.4 Replay -------------------------------------------------------------

def test_replay_redelivers(jwt_client, acme, capture_posts):
    endpoint = WebhookEndpoint.all_objects.create(
        tenant=acme, url="https://example.com/hook", secret="s" * 64, events=["*"]
    )
    event = WebhookEvent.all_objects.create(tenant=acme, event_type="lead.created")
    delivery = WebhookDelivery.all_objects.create(
        tenant=acme, endpoint=endpoint, event=event,
        status=WebhookDelivery.Status.FAILED,
    )
    api = jwt_client(acme, role=Role.MANAGER)
    resp = api.post(f"/api/webhook-deliveries/{delivery.id}/replay/")
    assert resp.status_code == 200
    delivery.refresh_from_db()
    assert delivery.status == "success"   # redelivered via mocked _post
    assert len(capture_posts) == 1
