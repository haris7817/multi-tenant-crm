"""One subscription per tenant (13.1)."""
from django.db import models

from apps.tenants.models import Tenant


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        TRIALING = "trialing", "Trialing"
        PAST_DUE = "past_due", "Past due"
        CANCELED = "canceled", "Canceled"

    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="subscription"
    )
    plan = models.CharField(max_length=20, default="free")
    status = models.CharField(
        max_length=15, choices=Status.choices, default=Status.ACTIVE
    )
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.tenant.slug}: {self.plan} ({self.status})"

    @classmethod
    def for_tenant(cls, tenant) -> "Subscription":
        sub, _ = cls.objects.get_or_create(tenant=tenant)
        return sub
