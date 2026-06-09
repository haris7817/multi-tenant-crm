"""
Shared DRF base classes for tenant-owned resources.

``TenantModelViewSet`` gives every CRM resource the same guarantees:
  * queries are scoped to the active tenant at REQUEST time,
  * new rows are stamped with the request's tenant and default owner,
  * role gating by HTTP method: read = any member, write = Sales Rep+,
    delete = Manager+.
Subclasses just set ``queryset`` and ``serializer_class``.
"""
from rest_framework import viewsets
from rest_framework.permissions import SAFE_METHODS

from apps.accounts.models import Role
from apps.accounts.permissions import HasTenantRole, IsTenantMember


class TenantModelViewSet(viewsets.ModelViewSet):
    # Role required to mutate. Override per-resource if needed.
    write_role = Role.SALES_REP
    delete_role = Role.MANAGER

    def get_queryset(self):
        # Scope to the active tenant HERE (per request). Subclasses declare
        # ``queryset`` using the UNSCOPED ``all_objects`` manager so the import-
        # time snapshot never bakes in a stale tenant filter (a TenantManager
        # snapshot would freeze to whichever tenant happened to be active when
        # the module was first imported).
        qs = super().get_queryset()
        tenant = getattr(self.request, "tenant", None)
        if tenant is None:
            return qs.none()
        return qs.filter(tenant=tenant)

    def get_permissions(self):
        # Gate by method so custom GET actions (e.g. /pipeline/) are reads and
        # custom POST actions (e.g. /move/) are writes — no per-action wiring.
        method = self.request.method
        if method in SAFE_METHODS:
            return [IsTenantMember()]
        if method == "DELETE":
            return [HasTenantRole(self.delete_role)()]
        return [HasTenantRole(self.write_role)()]

    def perform_create(self, serializer):
        # Tenant comes from the request, never from client input. ``owner`` is
        # only defaulted if the model has that field and the client omitted it.
        extra = {"tenant": self.request.tenant}
        model = serializer.Meta.model
        if _has_field(model, "owner") and not serializer.validated_data.get("owner"):
            extra["owner"] = self.request.user
        serializer.save(**extra)


def _has_field(model, name):
    return any(f.name == name for f in model._meta.get_fields())
