"""Phase 13.2/13.3/13.6 — Slack, lead enrichment, inbound email→note."""
import hashlib
import hmac
import json

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Role
from apps.connections.models import Connection
from apps.connectors import slack
from apps.crm.models import Deal, Lead, Note, Stage
from apps.webhooks.models import InboundEndpoint

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme(make_tenant):
    return make_tenant("acme")


# --- 13.3 Slack --------------------------------------------------------------

def test_winning_deal_posts_to_slack_when_connected(
    jwt_client, acme, monkeypatch, django_capture_on_commit_callbacks
):
    Connection.all_objects.create(
        tenant=acme, provider="slack", status="connected",
        access_token="xoxb-token", metadata={"channel": "#wins"},
    )
    posted = {}
    monkeypatch.setattr(
        slack, "_slack_post",
        lambda token, channel, text: posted.update(channel=channel, text=text, token=token) or True,
    )
    new = Stage.all_objects.get(tenant=acme, name="New")
    won = Stage.all_objects.get(tenant=acme, name="Won")
    deal = Deal.all_objects.create(tenant=acme, title="BigCo", value=5000, stage=new)

    api = jwt_client(acme, role=Role.SALES_REP)
    with django_capture_on_commit_callbacks(execute=True):
        api.post(f"/api/deals/{deal.id}/move/", {"stage": won.id})

    assert posted["channel"] == "#wins"
    assert "BigCo" in posted["text"]
    assert posted["token"] == "xoxb-token"


def test_no_slack_no_post(jwt_client, acme, monkeypatch, django_capture_on_commit_callbacks):
    calls = []
    monkeypatch.setattr(slack, "_slack_post", lambda *a, **k: calls.append(a))
    new = Stage.all_objects.get(tenant=acme, name="New")
    won = Stage.all_objects.get(tenant=acme, name="Won")
    deal = Deal.all_objects.create(tenant=acme, title="X", stage=new)
    api = jwt_client(acme, role=Role.SALES_REP)
    with django_capture_on_commit_callbacks(execute=True):
        api.post(f"/api/deals/{deal.id}/move/", {"stage": won.id})
    assert calls == []  # no Slack connection -> no message


# --- 13.6 Enrichment ---------------------------------------------------------

def test_enrich_fills_company_from_domain(jwt_client, acme):
    lead = Lead.all_objects.create(tenant=acme, name="Jane", email="jane@buyco-inc.com")
    api = jwt_client(acme, role=Role.SALES_REP)
    resp = api.post(f"/api/leads/{lead.id}/enrich/")
    assert resp.status_code == 200
    body = resp.json()
    assert body["company"] == "Buyco Inc"
    assert body["custom"]["enriched"] is True


def test_enrich_skips_free_email(jwt_client, acme):
    lead = Lead.all_objects.create(tenant=acme, name="Jane", email="jane@gmail.com")
    api = jwt_client(acme, role=Role.SALES_REP)
    resp = api.post(f"/api/leads/{lead.id}/enrich/")
    assert resp.json()["company"] == ""  # free providers aren't enriched


# --- 13.2 Inbound email -> note ----------------------------------------------

def test_inbound_email_logged_as_note(acme):
    ep = InboundEndpoint.all_objects.create(
        tenant=acme, token="t" * 32, secret="s" * 64, action="log_email"
    )
    lead = Lead.all_objects.create(tenant=acme, name="Jane", email="jane@buyco.com")
    body = json.dumps(
        {"from": "jane@buyco.com", "subject": "Re: proposal", "body": "Looks good!"}
    ).encode()
    sig = "sha256=" + hmac.new(ep.secret.encode(), body, hashlib.sha256).hexdigest()
    resp = APIClient().post(
        f"/api/v1/inbound/{ep.token}/", data=body,
        content_type="application/json", HTTP_X_SIGNATURE=sig,
    )
    assert resp.status_code == 201
    note = Note.all_objects.get(tenant=acme, target_id=lead.id)
    assert "Re: proposal" in note.body and "Looks good!" in note.body


def test_inbound_email_no_matching_lead_404(acme):
    ep = InboundEndpoint.all_objects.create(
        tenant=acme, token="t" * 32, secret="s" * 64, action="log_email"
    )
    body = json.dumps({"from": "nobody@x.com", "subject": "hi", "body": "x"}).encode()
    sig = "sha256=" + hmac.new(ep.secret.encode(), body, hashlib.sha256).hexdigest()
    resp = APIClient().post(
        f"/api/v1/inbound/{ep.token}/", data=body,
        content_type="application/json", HTTP_X_SIGNATURE=sig,
    )
    assert resp.status_code == 404
