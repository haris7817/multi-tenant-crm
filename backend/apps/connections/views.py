from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import Role
from apps.accounts.permissions import HasTenantRole, IsTenantMember

from .models import Connection
from .providers import get_registry
from .serializers import (
    AuthorizeSerializer,
    CallbackSerializer,
    ConnectionSerializer,
)
from .services import complete_oauth, start_oauth


class ConnectionViewSet(
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """Per-tenant external connections. Management actions require Admin."""

    serializer_class = ConnectionSerializer

    def get_permissions(self):
        if self.action in ("list", "providers"):
            return [IsTenantMember()]
        return [HasTenantRole(Role.ADMIN)()]

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        qs = Connection.all_objects.all()
        return qs.filter(tenant=tenant) if tenant else qs.none()

    @action(detail=False)
    def providers(self, request):
        """Catalog of providers with configured + connected status."""
        connected = set(
            self.get_queryset()
            .filter(status=Connection.Status.CONNECTED)
            .values_list("provider", flat=True)
        )
        data = [
            {
                "key": p.key,
                "label": p.label,
                "configured": p.configured,
                "connected": p.key in connected,
            }
            for p in get_registry().values()
        ]
        return Response(data)

    @action(detail=False, methods=["post"])
    def authorize(self, request):
        """Return the provider authorize URL to redirect the user to (Admin)."""
        serializer = AuthorizeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        url = start_oauth(
            tenant=request.tenant,
            provider_key=serializer.validated_data["provider"],
            redirect_uri=serializer.validated_data["redirect_uri"],
        )
        return Response({"authorize_url": url})

    @action(detail=False, methods=["post"])
    def callback(self, request):
        """Exchange the authorization code for tokens and store the connection."""
        serializer = CallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conn = complete_oauth(
            tenant=request.tenant,
            state=serializer.validated_data["state"],
            code=serializer.validated_data["code"],
            user=request.user,
        )
        return Response(ConnectionSerializer(conn).data, status=201)
