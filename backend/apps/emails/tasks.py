"""
Celery tasks for transactional email.

Tasks take primitive ids (not model instances) so they serialize cleanly onto
the broker. Enqueue them with ``transaction.on_commit`` so a rolled-back request
never sends mail (see accounts.serializers / crm.views).
"""
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string

from apps.tenants.models import Tenant

User = get_user_model()


@shared_task
def send_welcome_email(user_id, tenant_id):
    """Welcome a newly added member to a workspace."""
    user = User.objects.filter(pk=user_id).first()
    tenant = Tenant.objects.filter(pk=tenant_id).first()
    if not user or not tenant:
        return None
    body = render_to_string("emails/welcome.txt", {"user": user, "tenant": tenant})
    send_mail(
        subject=f"Welcome to {tenant.name}",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
    return user.email


@shared_task
def send_deal_won_email(deal_id):
    """Notify a deal's owner that it was marked Won."""
    # Imported here to avoid a crm <-> emails import at module load.
    from apps.crm.models import Deal

    deal = Deal.all_objects.select_related("owner", "tenant").filter(pk=deal_id).first()
    if not deal or not deal.owner:
        return None
    body = render_to_string("emails/deal_won.txt", {"deal": deal})
    send_mail(
        subject=f"🎉 Deal won: {deal.title}",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[deal.owner.email],
    )
    return deal.owner.email
