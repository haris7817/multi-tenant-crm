"""
Audit log: an immutable record of who did what to which object, when.

One row per create/update/delete of a tenant resource. ``changes`` holds a
field-level diff for updates. Rows are written by ``activity.services.record``
(called from the viewset base) and are read-only over the API.
"""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.tenants.models import Tenant


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATED = "created", "Created"
        UPDATED = "updated", "Updated"
        DELETED = "deleted", "Deleted"

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="audit_logs"
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=10, choices=Action.choices)

    # Generic pointer to the affected object (Lead, Deal, Task, ...).
    target_type = models.ForeignKey(
        ContentType, null=True, on_delete=models.SET_NULL
    )
    target_id = models.PositiveBigIntegerField(null=True)
    target = GenericForeignKey("target_type", "target_id")
    target_repr = models.CharField(max_length=255, blank=True)

    # {field: [old, new]} for updates; empty for create/delete.
    changes = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "target_type", "target_id"]),
            models.Index(fields=["tenant", "-created_at"]),
        ]

    def __str__(self):
        who = self.actor.email if self.actor else "system"
        return f"{who} {self.action} {self.target_repr}"
