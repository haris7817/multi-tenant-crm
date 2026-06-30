"""Per-tenant connections to external services (12.4) with encrypted tokens."""
from django.conf import settings
from django.db import models

from apps.tenants.models import TenantBaseModel

from .crypto import EncryptedTextField


class Connection(TenantBaseModel):
    class Status(models.TextChoices):
        CONNECTED = "connected", "Connected"
        DISCONNECTED = "disconnected", "Disconnected"
        ERROR = "error", "Error"

    provider = models.CharField(max_length=50)
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.DISCONNECTED
    )
    account_email = models.CharField(max_length=255, blank=True)
    scopes = models.CharField(max_length=500, blank=True)

    access_token = EncryptedTextField(blank=True, default="")
    refresh_token = EncryptedTextField(blank=True, default="")
    expires_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    connected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="connections",
    )

    class Meta:
        ordering = ["provider"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "provider"], name="uniq_connection_per_tenant"
            )
        ]

    def __str__(self):
        return f"{self.provider} [{self.status}]"


class OAuthState(TenantBaseModel):
    """Short-lived CSRF/state token tying an OAuth callback to its start."""

    provider = models.CharField(max_length=50)
    state = models.CharField(max_length=64, unique=True, db_index=True)
    redirect_uri = models.CharField(max_length=500)
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"state:{self.provider}"
