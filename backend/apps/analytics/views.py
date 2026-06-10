"""
Tenant-scoped analytics endpoints.

Every query is filtered by ``request.tenant`` so a tenant only ever aggregates
its own data. The expensive ``summary`` rollup is cached in Redis per tenant
with a short TTL.
"""
from datetime import timedelta
from decimal import Decimal

from django.core.cache import cache
from django.db.models import Count, DecimalField, Sum, Value
from django.db.models.functions import Coalesce, TruncDate, TruncMonth
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from apps.accounts.permissions import IsTenantMember
from apps.crm.models import Deal, Lead, Stage

SUMMARY_TTL = 60  # seconds


def _money(qs):
    """Sum a queryset's ``value`` as a float (0.0 when empty)."""
    total = qs.aggregate(
        s=Coalesce(Sum("value"), Value(0), output_field=DecimalField())
    )["s"]
    return float(total or Decimal(0))


def _deals(tenant):
    return Deal.all_objects.filter(tenant=tenant)


def _leads(tenant):
    return Lead.all_objects.filter(tenant=tenant)


def _build_summary(tenant):
    deals = _deals(tenant)
    won = deals.filter(stage__is_won=True)
    lost = deals.filter(stage__is_lost=True)
    open_deals = deals.filter(stage__is_won=False, stage__is_lost=False)

    won_count, lost_count = won.count(), lost.count()
    closed = won_count + lost_count
    leads = _leads(tenant)

    return {
        "leads_total": leads.count(),
        "leads_stale": leads.filter(is_stale=True).count(),
        "open_deals": open_deals.count(),
        "open_pipeline_value": _money(open_deals),
        "won_deals": won_count,
        "won_value": _money(won),
        "win_rate": round(won_count / closed, 3) if closed else 0.0,
    }


@extend_schema(description="High-level KPIs for the current tenant (cached ~60s).")
@api_view(["GET"])
@permission_classes([IsTenantMember])
def summary(request):
    key = f"analytics:summary:{request.tenant.id}"
    data = cache.get(key)
    if data is None:
        data = _build_summary(request.tenant)
        cache.set(key, data, SUMMARY_TTL)
    return Response(data)


@extend_schema(description="Deal count and total value per pipeline stage (kanban totals).")
@api_view(["GET"])
@permission_classes([IsTenantMember])
def deals_by_stage(request):
    tenant = request.tenant
    rows = {
        r["stage"]: r
        for r in _deals(tenant)
        .values("stage")
        .annotate(
            count=Count("id"),
            value=Coalesce(Sum("value"), Value(0), output_field=DecimalField()),
        )
    }
    data = []
    for stage in Stage.all_objects.filter(tenant=tenant).order_by("order"):
        r = rows.get(stage.id)
        data.append(
            {
                "stage": stage.name,
                "is_won": stage.is_won,
                "is_lost": stage.is_lost,
                "count": r["count"] if r else 0,
                "value": float(r["value"]) if r else 0.0,
            }
        )
    return Response(data)


@extend_schema(description="Lead count grouped by status.")
@api_view(["GET"])
@permission_classes([IsTenantMember])
def leads_by_status(request):
    rows = (
        _leads(request.tenant)
        .values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )
    return Response(list(rows))


@extend_schema(description="Leads created per day over the last N days (default 30).")
@api_view(["GET"])
@permission_classes([IsTenantMember])
def leads_over_time(request):
    days = int(request.query_params.get("days", 30))
    since = timezone.now() - timedelta(days=days)
    rows = (
        _leads(request.tenant)
        .filter(created_at__gte=since)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    return Response(list(rows))


@extend_schema(description="Open pipeline value grouped by expected-close month.")
@api_view(["GET"])
@permission_classes([IsTenantMember])
def revenue_forecast(request):
    open_deals = _deals(request.tenant).filter(
        stage__is_won=False, stage__is_lost=False, expected_close_date__isnull=False
    )
    rows = (
        open_deals.annotate(month=TruncMonth("expected_close_date"))
        .values("month")
        .annotate(
            value=Coalesce(Sum("value"), Value(0), output_field=DecimalField())
        )
        .order_by("month")
    )
    return Response([{"month": r["month"], "value": float(r["value"])} for r in rows])
