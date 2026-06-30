"""Scheduled notification jobs (Celery Beat): task reminders + daily digests."""
from celery import shared_task
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from apps.accounts.models import Membership
from apps.crm.models import Lead, Task

from .models import Notification
from .services import notify


@shared_task
def remind_due_tasks():
    """9.4 — notify assignees of tasks that are due today or overdue (once/day)."""
    today = timezone.localdate()
    ct = ContentType.objects.get_for_model(Task)
    due = Task.all_objects.filter(
        is_done=False, assigned_to__isnull=False, due_date__lte=today
    ).select_related("assigned_to", "tenant")

    created = 0
    for task in due:
        already = Notification.all_objects.filter(
            recipient=task.assigned_to,
            target_type=ct,
            target_id=task.id,
            type=Notification.Type.TASK_DUE,
            created_at__date=today,
        ).exists()
        if already:
            continue
        notify(
            tenant=task.tenant,
            recipient=task.assigned_to,
            type=Notification.Type.TASK_DUE,
            message=f"Task “{task.title}” is due.",
            target=task,
        )
        created += 1
    return created


@shared_task
def send_daily_digests():
    """9.3 — email each member a digest of their stale leads + due tasks."""
    today = timezone.localdate()
    sent = 0
    for membership in Membership.objects.select_related("user", "tenant"):
        user, tenant = membership.user, membership.tenant
        stale = Lead.all_objects.filter(
            tenant=tenant, owner=user, is_stale=True
        ).count()
        due = Task.all_objects.filter(
            tenant=tenant, assigned_to=user, is_done=False, due_date__lte=today
        ).count()
        if not (stale or due):
            continue
        body = render_to_string(
            "emails/digest.txt",
            {"user": user, "tenant": tenant, "stale": stale, "due": due},
        )
        send_mail(
            subject=f"Your {tenant.name} daily digest",
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )
        sent += 1
    return sent
