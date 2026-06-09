"""
Multi-tenancy core models and the shared-schema isolation mechanism.

Isolation has three cooperating pieces:
  * ``TenantManager``  — auto-filters every queryset by the current tenant.
  * ``TenantBaseModel`` — abstract base that adds the ``tenant`` FK + timestamps
    and wires in the manager. All business models inherit it.
  * ``TenantMiddleware`` (see middleware.py) — sets the current tenant per request.
"""
from django.db import models

from .context import get_current_tenant


class Tenant(models.Model):
    """A customer organization. The unit of data isolation."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, help_text="Subdomain label, e.g. 'acme'.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Domain(models.Model):
    """A host that maps to a tenant, e.g. ``acme.crm.local``."""

    tenant = models.ForeignKey(
        Tenant, related_name="domains", on_delete=models.CASCADE
    )
    domain = models.CharField(max_length=255, unique=True)
    is_primary = models.BooleanField(default=True)

    def __str__(self):
        return self.domain


class TenantManager(models.Manager):
    """
    Manager that scopes every query to the current tenant.

    When a tenant is active in the request context, ``get_queryset`` filters by
    it automatically. When there is no active tenant (migrations, shell, system
    tasks), it returns the unfiltered queryset — use ``all_objects`` for explicit
    cross-tenant access from code.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant is not None:
            return qs.filter(tenant=tenant)
        return qs


class TenantBaseModel(models.Model):
    """Abstract base for every tenant-owned model."""

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="%(class)ss"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantManager()           # tenant-scoped (default)
    all_objects = models.Manager()      # unscoped escape hatch

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Default the tenant from the request context so callers can't forget it
        # (and can't spoof another tenant — it's never taken from client input).
        if self.tenant_id is None:
            current = get_current_tenant()
            if current is not None:
                self.tenant = current
        super().save(*args, **kwargs)


class DemoRecord(TenantBaseModel):
    """
    A throwaway tenant-scoped model that exists only to prove isolation in
    Phase 1 (before real CRM models exist). Safe to delete once Leads/Deals land.
    """

    text = models.CharField(max_length=255)

    def __str__(self):
        return self.text
