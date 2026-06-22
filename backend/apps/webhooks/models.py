"""
Webhooks (Phase 11).

* ``WebhookEndpoint`` — a tenant's subscription: a URL + signing secret + the
  events it wants.
* ``WebhookEvent`` — the transactional **outbox** (11.2): a row written in the
  same DB transaction as the business change, so the event exists iff the change
  commits. A dispatcher fans it out to matching endpoints.
* ``WebhookDelivery`` — one delivery attempt-record per (event, endpoint), for
  logs + replay (11.4).
"""
import secrets

from django.db import models

from apps.tenants.models import TenantBaseModel

from .events import ALL


class WebhookEndpoint(TenantBaseModel):
    url = models.URLField()
    secret = models.CharField(max_length=64)  # used to HMAC-sign deliveries
    events = models.JSONField(default=list)   # subscribed types; [] or ["*"] = all
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.url

    @staticmethod
    def new_secret() -> str:
        return secrets.token_hex(32)

    def subscribes_to(self, event_type: str) -> bool:
        return not self.events or ALL in self.events or event_type in self.events


class WebhookEvent(TenantBaseModel):
    """Transactional outbox row."""

    event_type = models.CharField(max_length=50)
    payload = models.JSONField(default=dict)
    dispatched = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["dispatched", "created_at"])]

    def __str__(self):
        return f"{self.event_type} ({self.id})"


class WebhookDelivery(TenantBaseModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    endpoint = models.ForeignKey(
        WebhookEndpoint, on_delete=models.CASCADE, related_name="deliveries"
    )
    event = models.ForeignKey(
        WebhookEvent, on_delete=models.CASCADE, related_name="deliveries"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING
    )
    attempts = models.PositiveIntegerField(default=0)
    response_status = models.IntegerField(null=True, blank=True)
    error = models.TextField(blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event.event_type} -> {self.endpoint.url} [{self.status}]"


# --- 11.6 Inbound webhooks --------------------------------------------------


class InboundEndpoint(TenantBaseModel):
    """A signature-verified URL partners POST into (e.g. a lead-capture form)."""

    class Action(models.TextChoices):
        CREATE_LEAD = "create_lead", "Create lead"

    token = models.CharField(max_length=32, unique=True, db_index=True)
    secret = models.CharField(max_length=64)
    source = models.CharField(max_length=50, blank=True)
    action = models.CharField(
        max_length=20, choices=Action.choices, default=Action.CREATE_LEAD
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"inbound:{self.source or self.action} ({self.token})"

    @staticmethod
    def new_token() -> str:
        return secrets.token_hex(16)

    @staticmethod
    def new_secret() -> str:
        return secrets.token_hex(32)


class InboundEvent(TenantBaseModel):
    class Status(models.TextChoices):
        PROCESSED = "processed", "Processed"
        REJECTED = "rejected", "Rejected"
        ERROR = "error", "Error"

    endpoint = models.ForeignKey(
        InboundEndpoint, on_delete=models.CASCADE, related_name="events"
    )
    status = models.CharField(max_length=10, choices=Status.choices)
    payload = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"inbound {self.status} ({self.id})"
