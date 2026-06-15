from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsTenantMember

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """The current user's notification feed (tenant-scoped)."""

    serializer_class = NotificationSerializer
    permission_classes = [IsTenantMember]

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        qs = Notification.all_objects.select_related("target_type")
        if tenant is None:
            return qs.none()
        return qs.filter(tenant=tenant, recipient=self.request.user)

    @action(detail=False)
    def unread_count(self, request):
        return Response({"unread": self.get_queryset().filter(is_read=False).count()})

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        n = self.get_object()
        n.is_read = True
        n.save(update_fields=["is_read"])
        return Response(self.get_serializer(n).data)

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"marked": updated})
