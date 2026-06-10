from rest_framework import viewsets

from apps.accounts.permissions import IsTenantMember

from .filters import AuditLogFilter
from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only activity feed for the current tenant. Audit rows are written by
    the system (see common.viewsets), never created via the API.

    Filter a single record's history with ?target_model=lead&target_id=<id>.
    """

    serializer_class = AuditLogSerializer
    permission_classes = [IsTenantMember]
    filterset_class = AuditLogFilter
    ordering_fields = ["created_at"]

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        qs = AuditLog.objects.select_related("actor", "target_type")
        if tenant is None:
            return qs.none()
        return qs.filter(tenant=tenant)
