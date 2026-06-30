"""In-app notifications (9.1) — one row per thing a user should be told about."""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.tenants.models import TenantBaseModel


class Notification(TenantBaseModel):
    class Type(models.TextChoices):
        ASSIGNED = "assigned", "Assigned"
        TASK_DUE = "task_due", "Task due"
        DEAL_WON = "deal_won", "Deal won"
        MENTION = "mention", "Mention"
        SYSTEM = "system", "System"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.SYSTEM)
    message = models.CharField(max_length=255)

    # Optional pointer to the related record (Lead/Deal/Task).
    target_type = models.ForeignKey(
        ContentType, null=True, blank=True, on_delete=models.SET_NULL
    )
    target_id = models.PositiveBigIntegerField(null=True, blank=True)
    target = GenericForeignKey("target_type", "target_id")

    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "recipient", "is_read"]),
        ]

    def __str__(self):
        return f"[{self.type}] {self.message}"
