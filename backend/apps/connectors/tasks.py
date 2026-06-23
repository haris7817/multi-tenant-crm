"""Celery tasks for connectors (13.3 Slack)."""
from celery import shared_task

from apps.connections.models import Connection
from apps.crm.models import Deal


@shared_task
def post_deal_won_to_slack(deal_id):
    """If the tenant has Slack connected, announce a won deal in their channel."""
    deal = Deal.all_objects.select_related("tenant").filter(pk=deal_id).first()
    if not deal:
        return "no deal"
    conn = Connection.all_objects.filter(
        tenant=deal.tenant, provider="slack", status=Connection.Status.CONNECTED
    ).first()
    if not conn or not conn.access_token:
        return "no slack"

    from .slack import _slack_post, channel_for

    text = f":tada: Deal won: *{deal.title}* — ${deal.value}"
    _slack_post(conn.access_token, channel_for(conn), text)
    return "sent"
