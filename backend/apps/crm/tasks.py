"""Scheduled CRM background jobs (run by Celery Beat)."""
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import Lead


@shared_task
def flag_stale_leads(days=14):
    """
    Mark open leads that have had no update in ``days`` as stale.

    This is a SYSTEM job that runs across all tenants, so it uses the unscoped
    ``all_objects`` manager (there is no request/tenant context in a beat task).
    Returns the number of leads newly flagged.
    """
    cutoff = timezone.now() - timedelta(days=days)
    open_statuses = [Lead.Status.NEW, Lead.Status.CONTACTED, Lead.Status.QUALIFIED]
    return (
        Lead.all_objects.filter(
            updated_at__lt=cutoff, is_stale=False, status__in=open_statuses
        ).update(is_stale=True)
    )
