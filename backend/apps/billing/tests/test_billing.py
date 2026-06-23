"""Phase 13.1 — Stripe billing: status, checkout, webhook, quotas."""
import pytest

from apps.accounts.models import Role
from apps.billing import quota, views
from apps.billing.models import Subscription

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme(make_tenant):
    return make_tenant("acme")


# --- Status / plans ----------------------------------------------------------

def test_billing_status_defaults_to_free(jwt_client, acme):
    api = jwt_client(acme, role=Role.ADMIN)
    data = api.get("/api/billing/").json()
    assert data["plan"] == "free"
    assert data["status"] == "active"
    assert data["limits"]["leads"] == 200
    assert "leads" in data["usage"]


def test_plans_listed_without_price_ids(jwt_client, acme):
    api = jwt_client(acme, role=Role.ADMIN)
    plans = api.get("/api/billing/plans/").json()
    keys = {p["key"] for p in plans}
    assert keys == {"free", "pro"}
    assert all("stripe_price_id" not in p for p in plans)


# --- Checkout ----------------------------------------------------------------

def test_admin_checkout_returns_url(jwt_client, acme, monkeypatch):
    monkeypatch.setattr(
        views, "create_checkout_session", lambda **kw: "https://checkout.stripe.test/abc"
    )
    api = jwt_client(acme, role=Role.ADMIN)
    resp = api.post("/api/billing/checkout/", {"plan": "pro"}, format="json")
    assert resp.status_code == 200
    assert resp.json()["checkout_url"].startswith("https://checkout.stripe.test/")


def test_member_cannot_checkout(jwt_client, acme):
    api = jwt_client(acme, role=Role.SALES_REP)
    assert api.post("/api/billing/checkout/", {"plan": "pro"}, format="json").status_code == 403


# --- Webhook (subscription state is driven by Stripe) ------------------------

def test_webhook_activates_pro_on_checkout_completed(jwt_client, acme, monkeypatch):
    Subscription.for_tenant(acme)  # ensure a row exists
    event = {
        "type": "checkout.session.completed",
        "data": {"object": {
            "customer": "cus_1", "subscription": "sub_1",
            "metadata": {"tenant_id": str(acme.id), "plan": "pro"},
        }},
    }
    monkeypatch.setattr(views, "construct_event", lambda payload, sig: event)
    api = jwt_client(acme, role=Role.ADMIN)
    resp = api.post("/api/billing/stripe/webhook/", {}, format="json")
    assert resp.status_code == 200
    sub = Subscription.objects.get(tenant=acme)
    assert sub.plan == "pro" and sub.status == "active"
    assert sub.stripe_subscription_id == "sub_1"


def test_webhook_cancel_reverts_to_free(acme, monkeypatch):
    Subscription.objects.create(
        tenant=acme, plan="pro", status="active", stripe_customer_id="cus_9"
    )
    event = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"customer": "cus_9", "status": "canceled"}},
    }
    monkeypatch.setattr(views, "construct_event", lambda payload, sig: event)
    from rest_framework.test import APIClient

    APIClient().post("/api/billing/stripe/webhook/", {}, format="json", HTTP_HOST="acme.crm.local")
    sub = Subscription.objects.get(tenant=acme)
    assert sub.status == "canceled" and sub.plan == "free"


def test_bad_signature_returns_400(acme, monkeypatch):
    def boom(payload, sig):
        raise ValueError("bad signature")

    monkeypatch.setattr(views, "construct_event", boom)
    from rest_framework.test import APIClient

    resp = APIClient().post(
        "/api/billing/stripe/webhook/", {}, format="json", HTTP_HOST="acme.crm.local"
    )
    assert resp.status_code == 400


# --- Quotas ------------------------------------------------------------------

def test_lead_quota_blocks_over_limit(jwt_client, acme, monkeypatch):
    monkeypatch.setattr(
        quota, "get_plan",
        lambda key: {"name": "Free", "max_leads": 1, "max_members": 99},
    )
    api = jwt_client(acme, role=Role.SALES_REP)
    assert api.post("/api/leads/", {"name": "One"}, format="json").status_code == 201
    resp = api.post("/api/leads/", {"name": "Two"}, format="json")
    assert resp.status_code == 402  # Payment Required
    assert resp.json()["error"]["code"] == "quota_exceeded"


def test_member_quota_blocks_invite(jwt_client, acme, monkeypatch):
    monkeypatch.setattr(
        quota, "get_plan",
        lambda key: {"name": "Free", "max_leads": 999, "max_members": 1},
    )
    api = jwt_client(acme, role=Role.ADMIN)  # admin already = 1 member, at limit
    resp = api.post(
        "/api/members/", {"email": "new@acme.crm.local", "role": "viewer"}, format="json"
    )
    assert resp.status_code == 402
