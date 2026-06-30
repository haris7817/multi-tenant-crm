from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.accounts.models import Membership, Role
from apps.accounts.permissions import HasTenantRole, IsTenantMember

from .models import Subscription
from .plans import get_plan, get_plans
from .services import apply_event, construct_event, create_checkout_session


@api_view(["GET"])
@permission_classes([IsTenantMember])
def billing_status(request):
    from apps.crm.models import Lead

    sub = Subscription.for_tenant(request.tenant)
    plan = get_plan(sub.plan) or get_plan("free")
    return Response(
        {
            "plan": sub.plan,
            "plan_name": plan["name"],
            "status": sub.status,
            "current_period_end": sub.current_period_end,
            "usage": {
                "leads": Lead.all_objects.filter(tenant=request.tenant).count(),
                "members": Membership.objects.filter(tenant=request.tenant).count(),
            },
            "limits": {"leads": plan["max_leads"], "members": plan["max_members"]},
        }
    )


@api_view(["GET"])
@permission_classes([IsTenantMember])
def plans_view(request):
    return Response(
        [{k: v for k, v in p.items() if k != "stripe_price_id"} for p in get_plans().values()]
    )


@api_view(["POST"])
@permission_classes([HasTenantRole(Role.ADMIN)])
def checkout(request):
    base = f"http://{request.tenant.slug}.crm.local:5173/billing"
    url = create_checkout_session(
        tenant=request.tenant,
        plan_key=request.data.get("plan"),
        success_url=request.data.get("success_url", f"{base}?status=success"),
        cancel_url=request.data.get("cancel_url", f"{base}?status=cancel"),
    )
    return Response({"checkout_url": url})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def stripe_webhook(request):
    """Stripe -> us. Signature-verified; updates the local Subscription."""
    try:
        event = construct_event(request.body, request.headers.get("Stripe-Signature", ""))
    except Exception:
        return Response({"detail": "Invalid signature."}, status=400)
    apply_event(event)
    return Response({"received": True})
