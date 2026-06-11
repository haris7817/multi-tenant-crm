"""Scheduled background jobs: flag_stale_leads + beat registration."""
from datetime import timedelta

import pytest
from django.conf import settings
from django.utils import timezone

from apps.crm.models import Lead
from apps.crm.tasks import flag_stale_leads

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme(make_tenant):
    return make_tenant("acme")


def _age(lead, days):
    # updated_at uses auto_now, so set it directly via .update (which skips it).
    past = timezone.now() - timedelta(days=days)
    Lead.all_objects.filter(pk=lead.pk).update(updated_at=past)


def test_old_open_lead_is_flagged_stale(acme):
    old = Lead.all_objects.create(tenant=acme, name="Cold", status=Lead.Status.NEW)
    fresh = Lead.all_objects.create(tenant=acme, name="Warm", status=Lead.Status.NEW)
    _age(old, 30)

    flagged = flag_stale_leads(days=14)

    old.refresh_from_db()
    fresh.refresh_from_db()
    assert flagged == 1
    assert old.is_stale is True
    assert fresh.is_stale is False


def test_closed_leads_are_not_flagged(acme):
    converted = Lead.all_objects.create(
        tenant=acme, name="Closed", status=Lead.Status.CONVERTED
    )
    _age(converted, 30)

    flag_stale_leads(days=14)

    converted.refresh_from_db()
    assert converted.is_stale is False


def test_task_runs_across_tenants(make_tenant):
    acme = make_tenant("acme")
    globex = make_tenant("globex")
    a = Lead.all_objects.create(tenant=acme, name="A", status=Lead.Status.NEW)
    g = Lead.all_objects.create(tenant=globex, name="G", status=Lead.Status.NEW)
    _age(a, 30)
    _age(g, 30)

    flagged = flag_stale_leads(days=14)
    assert flagged == 2  # system job spans all tenants


def test_beat_schedule_is_registered():
    schedule = settings.CELERY_BEAT_SCHEDULE
    assert "flag-stale-leads-daily" in schedule
    assert schedule["flag-stale-leads-daily"]["task"] == "apps.crm.tasks.flag_stale_leads"
