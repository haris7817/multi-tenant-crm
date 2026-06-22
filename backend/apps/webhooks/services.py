"""Emit domain events into the outbox and schedule dispatch (11.2)."""
from django.db import transaction

from .models import WebhookEvent


def emit_event(*, tenant, event_type, payload):
    """
    Write an event to the outbox in the CURRENT transaction, then schedule
    fan-out after commit. If the surrounding transaction rolls back, the event
    is never recorded or sent.
    """
    event = WebhookEvent.objects.create(
        tenant=tenant, event_type=event_type, payload=payload
    )
    # Imported lazily to avoid app-load import cycles.
    from .tasks import dispatch_event

    transaction.on_commit(lambda: dispatch_event.delay(event.id))
    return event
