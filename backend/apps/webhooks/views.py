from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import Role
from apps.apikeys.throttles import ApiKeyRateThrottle
from apps.common.permissions import TenantAccess
from apps.common.viewsets import TenantModelViewSet

from .models import InboundEndpoint, WebhookDelivery, WebhookEndpoint
from .serializers import (
    InboundEndpointSerializer,
    WebhookDeliverySerializer,
    WebhookEndpointSerializer,
)
from .tasks import deliver


class WebhookEndpointViewSet(TenantModelViewSet):
    """Manage webhook subscriptions (11.5). Admin to mutate."""

    queryset = WebhookEndpoint.all_objects.all()
    serializer_class = WebhookEndpointSerializer
    write_role = Role.ADMIN
    delete_role = Role.ADMIN

    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.tenant, secret=WebhookEndpoint.new_secret()
        )


class WebhookDeliveryViewSet(viewsets.ReadOnlyModelViewSet):
    """Delivery logs (11.4), read-only, with a replay action."""

    serializer_class = WebhookDeliverySerializer
    permission_classes = [TenantAccess]
    throttle_classes = [ApiKeyRateThrottle]
    filterset_fields = ["status", "endpoint"]

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        qs = WebhookDelivery.all_objects.select_related("event", "endpoint")
        if tenant is None:
            return qs.none()
        return qs.filter(tenant=tenant)

    @action(detail=True, methods=["post"])
    def replay(self, request, pk=None):
        delivery = self.get_object()
        delivery.status = WebhookDelivery.Status.PENDING
        delivery.error = ""
        delivery.save(update_fields=["status", "error"])
        deliver.delay(delivery.id)
        return Response(self.get_serializer(delivery).data)


class InboundEndpointViewSet(TenantModelViewSet):
    """Manage inbound (partner -> us) endpoints (11.6). Admin to mutate."""

    queryset = InboundEndpoint.all_objects.all()
    serializer_class = InboundEndpointSerializer
    write_role = Role.ADMIN
    delete_role = Role.ADMIN

    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.tenant,
            token=InboundEndpoint.new_token(),
            secret=InboundEndpoint.new_secret(),
        )
