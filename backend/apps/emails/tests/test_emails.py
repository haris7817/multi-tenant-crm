"""Email tasks fire (eagerly) on the right events and go to the right person."""
import pytest
from django.core import mail

from apps.accounts.models import Role
from apps.crm.models import Deal, Stage
from apps.emails.tasks import send_welcome_email

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme(make_tenant):
    return make_tenant("acme")


def test_welcome_task_emails_the_user(acme, make_member):
    user = make_member(acme, role=Role.OWNER, email="owner@acme.crm.local")
    send_welcome_email(user.id, acme.id)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["owner@acme.crm.local"]
    assert "Acme" in mail.outbox[0].subject


def test_register_sends_welcome_email(api_client, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        resp = api_client.post(
            "/api/auth/register/",
            {
                "tenant_name": "New Co",
                "slug": "newco",
                "email": "founder@newco.crm.local",
                "password": "password123",
            },
            HTTP_HOST="crm.local",
        )
    assert resp.status_code == 201
    assert any(m.to == ["founder@newco.crm.local"] for m in mail.outbox)


def test_winning_a_deal_emails_the_owner(
    client_for, acme, make_member, django_capture_on_commit_callbacks
):
    owner = make_member(acme, role=Role.SALES_REP)
    api = client_for(acme, role=Role.SALES_REP)  # same user
    new = Stage.all_objects.get(tenant=acme, name="New")
    won = Stage.all_objects.get(tenant=acme, name="Won")
    deal = Deal.all_objects.create(tenant=acme, title="Big Deal", stage=new, owner=owner)

    with django_capture_on_commit_callbacks(execute=True):
        resp = api.post(f"/api/deals/{deal.id}/move/", {"stage": won.id})

    assert resp.status_code == 200
    assert any("Deal won" in m.subject for m in mail.outbox)
    assert mail.outbox[-1].to == [owner.email]


def test_moving_to_a_non_won_stage_sends_no_email(
    client_for, acme, make_member, django_capture_on_commit_callbacks
):
    owner = make_member(acme, role=Role.SALES_REP)
    api = client_for(acme, role=Role.SALES_REP)
    new = Stage.all_objects.get(tenant=acme, name="New")
    qualified = Stage.all_objects.get(tenant=acme, name="Qualified")
    deal = Deal.all_objects.create(tenant=acme, title="Open", stage=new, owner=owner)

    with django_capture_on_commit_callbacks(execute=True):
        api.post(f"/api/deals/{deal.id}/move/", {"stage": qualified.id})

    assert mail.outbox == []
