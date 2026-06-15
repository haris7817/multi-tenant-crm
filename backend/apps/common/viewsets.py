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

from apps.accounts.models import Role
from apps.activity.models import AuditLog
from apps.activity.services import diff, record
from apps.apikeys.throttles import ApiKeyRateThrottle
from apps.common.permissions import TenantAccess


class TenantModelViewSet(viewsets.ModelViewSet):
    # Role required to mutate. Override per-resource if needed.
    write_role = Role.SALES_REP
    delete_role = Role.MANAGER

    # Per-key rate limiting (no-op for user-JWT requests).
    throttle_classes = [ApiKeyRateThrottle]

    # Set False on a viewset to skip audit logging for its writes.
    audit = True

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
        # One permission accepts EITHER a user JWT (role-gated) OR an API key
        # (scope-gated). Gating is by HTTP method, so custom GET actions are
        # reads and custom POST actions are writes — no per-action wiring.
        return [TenantAccess(write_role=self.write_role, delete_role=self.delete_role)]

    # --- writes (each also records an audit entry) ---------------------------

    def perform_create(self, serializer):
        # Tenant comes from the request, never from client input. ``owner`` is
        # only defaulted if the model has that field and the client omitted it.
        extra = {"tenant": self.request.tenant}
        model = serializer.Meta.model
        user = self.request.user
        # Default owner only for a real user (API keys may have no/anon user).
        if (
            _has_field(model, "owner")
            and not serializer.validated_data.get("owner")
            and getattr(user, "is_authenticated", False)
        ):
            extra["owner"] = user
        serializer.save(**extra)
        self._audit(AuditLog.Action.CREATED, serializer.instance)

    def perform_update(self, serializer):
        # Snapshot the fields being written so we can diff old vs new.
        instance = serializer.instance
        before = {f: getattr(instance, f) for f in serializer.validated_data}
        serializer.save()
        after = {f: getattr(serializer.instance, f) for f in before}
        self._audit(
            AuditLog.Action.UPDATED, serializer.instance, changes=diff(before, after)
        )

    def perform_destroy(self, instance):
        # Record before deleting so target_repr/pk are still available.
        self._audit(AuditLog.Action.DELETED, instance)
        instance.delete()

    def _audit(self, action, instance, changes=None):
        if not self.audit:
            return
        record(
            tenant=self.request.tenant,
            actor=self.request.user,
            action=action,
            instance=instance,
            changes=changes,
        )


def _has_field(model, name):
    return any(f.name == name for f in model._meta.get_fields())
