"""
Per-tenant API keys (10.2) for programmatic access by external apps.

The secret is shown ONCE at creation; we store only its SHA-256 hash. Lookup is
by the public ``prefix`` (also shown in the dashboard), then a constant-time
hash compare. The key carries scopes (``read`` / ``write``) checked per request.
"""
import hashlib
import hmac
import secrets

from django.conf import settings
from django.db import models

from apps.tenants.models import Tenant


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class Scope(models.TextChoices):
    READ = "read", "Read"
    WRITE = "write", "Write"


class ApiKey(models.Model):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="api_keys"
    )
    name = models.CharField(max_length=100)
    prefix = models.CharField(max_length=12, unique=True, db_index=True)
    hashed_key = models.CharField(max_length=64)
    scopes = models.JSONField(default=list)  # e.g. ["read"] or ["read", "write"]
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="api_keys",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.prefix})"

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None

    @classmethod
    def generate(cls, *, tenant, name, scopes, created_by=None):
        """Create a key and return (instance, raw_secret). Raw is shown once."""
        prefix = secrets.token_hex(4)  # 8 chars
        secret = secrets.token_urlsafe(24)
        raw = f"crm_{prefix}_{secret}"
        instance = cls.objects.create(
            tenant=tenant,
            name=name,
            prefix=prefix,
            hashed_key=_hash(raw),
            scopes=scopes,
            created_by=created_by,
        )
        return instance, raw

    def matches(self, raw: str) -> bool:
        return hmac.compare_digest(self.hashed_key, _hash(raw))
