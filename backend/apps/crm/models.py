"""
Core CRM domain: Leads, a configurable Deal pipeline (Stage), Deals, and Tasks.

Every model inherits ``TenantBaseModel`` so it carries a ``tenant`` FK and is
auto-scoped by ``TenantManager``. ``owner``/``assigned_to`` reference the global
User; they're expected to be members of the same tenant (kept simple here).
"""
from django.conf import settings
from django.db import models

from apps.tenants.models import TenantBaseModel


class Lead(TenantBaseModel):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        QUALIFIED = "qualified", "Qualified"
        UNQUALIFIED = "unqualified", "Unqualified"
        CONVERTED = "converted", "Converted"

    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    company = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NEW
    )
    notes = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_leads",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Stage(TenantBaseModel):
    """A column in the tenant's deal pipeline (e.g. Qualification → Won)."""

    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    is_won = models.BooleanField(default=False)
    is_lost = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class Deal(TenantBaseModel):
    title = models.CharField(max_length=255)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stage = models.ForeignKey(
        Stage, on_delete=models.PROTECT, related_name="deals"
    )
    lead = models.ForeignKey(
        Lead,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deals",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_deals",
    )
    expected_close_date = models.DateField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def is_closed(self):
        return self.stage.is_won or self.stage.is_lost


class Task(TenantBaseModel):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    is_done = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
    )
    lead = models.ForeignKey(
        Lead, null=True, blank=True, on_delete=models.CASCADE, related_name="tasks"
    )
    deal = models.ForeignKey(
        Deal, null=True, blank=True, on_delete=models.CASCADE, related_name="tasks"
    )

    class Meta:
        ordering = ["is_done", "due_date", "-created_at"]

    def __str__(self):
        return self.title
