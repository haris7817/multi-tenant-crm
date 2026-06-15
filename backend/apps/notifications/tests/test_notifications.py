"""Phase 9.1/9.3/9.4/9.5 — feed, assignment, reminders, digests."""
from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from apps.accounts.models import Role
from apps.crm.models import Lead, Task
from apps.notifications.models import Notification
from apps.notifications.services import notify
from apps.notifications.tasks import remind_due_tasks, send_daily_digests

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme(make_tenant, make_member):
    tenant = make_tenant("acme")
    for role in (Role.SALES_REP, Role.MANAGER):
        make_member(tenant, role=role)
    return tenant


# --- 9.5 Assignment ----------------------------------------------------------

def test_assigning_lead_notifies_new_owner(client_for, acme, make_member):
    mgr = make_member(acme, role=Role.MANAGER)
    api = client_for(acme, role=Role.SALES_REP)
    api.post("/api/leads/", {"name": "Jane", "owner": mgr.id})
    assert Notification.all_objects.filter(
        tenant=acme, recipient=mgr, type=Notification.Type.ASSIGNED
    ).exists()


def test_no_notification_when_owner_unchanged(client_for, acme, make_member):
    mgr = make_member(acme, role=Role.MANAGER)
    lead = Lead.all_objects.create(tenant=acme, name="X", owner=mgr)
    Notification.all_objects.all().delete()
    # Saving again without changing owner must not re-notify.
    lead.name = "X2"
    lead.save()
    assert Notification.all_objects.filter(recipient=mgr).count() == 0


# --- 9.1 Feed ----------------------------------------------------------------

def test_feed_is_scoped_to_user(client_for, acme, make_member):
    rep = make_member(acme, role=Role.SALES_REP)
    mgr = make_member(acme, role=Role.MANAGER)
    notify(tenant=acme, recipient=rep, type=Notification.Type.SYSTEM, message="for rep")
    notify(tenant=acme, recipient=mgr, type=Notification.Type.SYSTEM, message="for mgr")

    api = client_for(acme, role=Role.SALES_REP)
    rows = api.get("/api/notifications/").json()["results"]
    assert [n["message"] for n in rows] == ["for rep"]


def test_unread_count_and_mark_read(client_for, acme, make_member):
    rep = make_member(acme, role=Role.SALES_REP)
    n1 = notify(tenant=acme, recipient=rep, type=Notification.Type.SYSTEM, message="a")
    notify(tenant=acme, recipient=rep, type=Notification.Type.SYSTEM, message="b")
    api = client_for(acme, role=Role.SALES_REP)

    assert api.get("/api/notifications/unread_count/").json()["unread"] == 2
    api.post(f"/api/notifications/{n1.id}/mark_read/")
    assert api.get("/api/notifications/unread_count/").json()["unread"] == 1
    api.post("/api/notifications/mark_all_read/")
    assert api.get("/api/notifications/unread_count/").json()["unread"] == 0


# --- 9.4 Task reminders ------------------------------------------------------

def test_remind_due_tasks_notifies_once(acme, make_member):
    rep = make_member(acme, role=Role.SALES_REP)
    yesterday = timezone.localdate() - timedelta(days=1)
    Task.all_objects.create(
        tenant=acme, title="Overdue", assigned_to=rep, due_date=yesterday
    )
    assert remind_due_tasks() == 1
    assert remind_due_tasks() == 0  # deduped same day
    assert Notification.all_objects.filter(
        recipient=rep, type=Notification.Type.TASK_DUE
    ).count() == 1


# --- 9.3 Daily digest --------------------------------------------------------

def test_daily_digest_emails_users_with_work(acme, make_member):
    rep = make_member(acme, role=Role.SALES_REP)
    Lead.all_objects.create(tenant=acme, name="Cold", owner=rep, is_stale=True)
    sent = send_daily_digests()
    assert sent >= 1
    assert any(rep.email in m.to for m in mail.outbox)
