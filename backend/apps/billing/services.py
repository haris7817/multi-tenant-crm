"""
Stripe integration (13.1).

Stripe calls are wrapped here so tests can mock them. ``apply_event`` updates the
local Subscription from a verified Stripe webhook event (the source of truth for
subscription state). ``stripe`` is imported lazily so the module loads without it.
"""
from datetime import datetime, timezone

from django.conf import settings
from rest_framework.exceptions import ValidationError

from .models import Subscription
from .plans import get_plan


def _stripe():
    import stripe

    stripe.api_key = settings.STRIPE_SECRET_KEY
    return stripe


def ensure_customer(tenant, sub: Subscription) -> str:
    if sub.stripe_customer_id:
        return sub.stripe_customer_id
    customer = _stripe().Customer.create(
        name=tenant.name, metadata={"tenant_id": tenant.id, "slug": tenant.slug}
    )
    sub.stripe_customer_id = customer.id
    sub.save(update_fields=["stripe_customer_id"])
    return customer.id


def create_checkout_session(*, tenant, plan_key, success_url, cancel_url) -> str:
    plan = get_plan(plan_key)
    if not plan or not plan["stripe_price_id"]:
        raise ValidationError({"plan": "Plan is not purchasable."})
    sub = Subscription.for_tenant(tenant)
    customer = ensure_customer(tenant, sub)
    session = _stripe().checkout.Session.create(
        customer=customer,
        mode="subscription",
        line_items=[{"price": plan["stripe_price_id"], "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"tenant_id": tenant.id, "plan": plan_key},
    )
    return session.url


def construct_event(payload: bytes, sig_header: str):
    """Verify a Stripe webhook signature and return the event."""
    return _stripe().Webhook.construct_event(
        payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
    )


def _find_subscription(*, customer_id=None, tenant_id=None):
    if tenant_id:
        sub = Subscription.objects.filter(tenant_id=tenant_id).first()
        if sub:
            return sub
    if customer_id:
        return Subscription.objects.filter(stripe_customer_id=customer_id).first()
    return None


def apply_event(event: dict) -> bool:
    """Update the local Subscription from a Stripe event. Returns True if handled."""
    etype = event["type"]
    obj = event["data"]["object"]

    if etype == "checkout.session.completed":
        sub = _find_subscription(
            customer_id=obj.get("customer"),
            tenant_id=(obj.get("metadata") or {}).get("tenant_id"),
        )
        if not sub:
            return False
        sub.plan = (obj.get("metadata") or {}).get("plan", sub.plan)
        sub.status = Subscription.Status.ACTIVE
        sub.stripe_subscription_id = obj.get("subscription", "")
        if obj.get("customer"):
            sub.stripe_customer_id = obj["customer"]
        sub.save()
        return True

    if etype in ("customer.subscription.updated", "customer.subscription.deleted"):
        sub = _find_subscription(customer_id=obj.get("customer"))
        if not sub:
            return False
        if etype.endswith("deleted"):
            sub.status = Subscription.Status.CANCELED
            sub.plan = "free"
        else:
            sub.status = obj.get("status", sub.status)
            if obj.get("current_period_end"):
                sub.current_period_end = datetime.fromtimestamp(
                    obj["current_period_end"], tz=timezone.utc
                )
        sub.save()
        return True

    return False
