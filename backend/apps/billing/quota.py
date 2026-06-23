"""Plan quota enforcement (13.1) — HTTP 402 when a tenant exceeds its plan."""
from rest_framework.exceptions import APIException

from .models import Subscription
from .plans import get_plan


class QuotaExceeded(APIException):
    status_code = 402  # Payment Required
    default_detail = "Plan limit reached — upgrade your plan."
    default_code = "quota_exceeded"


def _limit(plan: dict, resource: str):
    return plan.get("max_leads") if resource == "leads" else plan.get("max_members")


def _current(tenant, resource: str) -> int:
    if resource == "leads":
        from apps.crm.models import Lead
        return Lead.all_objects.filter(tenant=tenant).count()
    from apps.accounts.models import Membership
    return Membership.objects.filter(tenant=tenant).count()


def check_quota(tenant, resource: str):
    """Raise QuotaExceeded if adding one more ``resource`` would exceed the plan."""
    sub = Subscription.for_tenant(tenant)
    plan = get_plan(sub.plan) or get_plan("free")
    limit = _limit(plan, resource)
    if limit is None:  # unlimited
        return
    if _current(tenant, resource) >= limit:
        raise QuotaExceeded(
            f"Your {plan['name']} plan allows {limit} {resource}. Upgrade to add more."
        )
