"""
Plan catalog (13.1). Limits of ``None`` mean unlimited. Stripe price ids come
from env so real checkout works once configured; the free plan needs no Stripe.
"""
from django.conf import settings


def _price(key: str) -> str:
    return settings.STRIPE_PRICES.get(key, "")


def get_plans() -> dict:
    return {
        "free": {
            "key": "free", "name": "Free", "price_cents": 0,
            "stripe_price_id": "", "max_leads": 200, "max_members": 3,
        },
        "pro": {
            "key": "pro", "name": "Pro", "price_cents": 2900,
            "stripe_price_id": _price("pro"), "max_leads": None, "max_members": None,
        },
    }


def get_plan(key: str) -> dict | None:
    return get_plans().get(key)
