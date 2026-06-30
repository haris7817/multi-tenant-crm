"""Webhook delivery (11.3): fan-out, HMAC signing, retries with backoff."""
import hashlib
import hmac
import json
import urllib.error
import urllib.request

from celery import shared_task
from django.utils import timezone

from .models import WebhookDelivery, WebhookEndpoint, WebhookEvent


def _post(url, data, headers, timeout=10):
    """Thin HTTP POST wrapper (kept separate so tests can mock it)."""
    req = urllib.request.Request(url, data=data, method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status


@shared_task
def dispatch_event(event_id):
    """Fan an outbox event out to every subscribed, active endpoint."""
    event = WebhookEvent.all_objects.select_related("tenant").filter(pk=event_id).first()
    if not event:
        return 0
    endpoints = WebhookEndpoint.all_objects.filter(tenant=event.tenant, is_active=True)
    count = 0
    for endpoint in endpoints:
        if not endpoint.subscribes_to(event.event_type):
            continue
        delivery = WebhookDelivery.objects.create(
            tenant=event.tenant, endpoint=endpoint, event=event
        )
        deliver.delay(delivery.id)
        count += 1
    event.dispatched = True
    event.save(update_fields=["dispatched"])
    return count


@shared_task(bind=True, max_retries=5)
def deliver(self, delivery_id):
    """Deliver one signed payload; retry with exponential backoff on 5xx/errors."""
    d = (
        WebhookDelivery.all_objects.select_related("endpoint", "event")
        .filter(pk=delivery_id)
        .first()
    )
    if not d:
        return
    endpoint, event = d.endpoint, d.event
    body = json.dumps(
        {"id": event.id, "event": event.event_type, "data": event.payload},
        default=str,
    ).encode()
    signature = hmac.new(endpoint.secret.encode(), body, hashlib.sha256).hexdigest()
    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Event": event.event_type,
        "X-Webhook-Signature": f"sha256={signature}",
        "X-Webhook-Delivery": str(d.id),
    }

    d.attempts += 1
    d.last_attempt_at = timezone.now()
    try:
        status = _post(endpoint.url, body, headers)
        d.response_status = status
        d.status = WebhookDelivery.Status.SUCCESS
        d.error = ""
        d.save()
    except urllib.error.HTTPError as exc:
        d.response_status = exc.code
        d.status = WebhookDelivery.Status.FAILED
        d.error = f"HTTP {exc.code}"
        d.save()
        if exc.code >= 500:
            raise self.retry(countdown=2 ** self.request.retries)
    except urllib.error.URLError as exc:
        d.status = WebhookDelivery.Status.FAILED
        d.error = str(exc.reason)
        d.save()
        raise self.retry(countdown=2 ** self.request.retries)


@shared_task
def sweep_undispatched_events():
    """Safety net for the outbox: dispatch any events that were missed."""
    pending = WebhookEvent.all_objects.filter(dispatched=False)[:500]
    for event in pending:
        dispatch_event.delay(event.id)
    return len(pending)
