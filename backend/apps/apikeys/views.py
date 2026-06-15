from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.accounts.models import Role
from apps.accounts.permissions import HasTenantRole

from .models import ApiKey
from .serializers import ApiKeyCreateSerializer, ApiKeySerializer


class ApiKeyViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Manage a tenant's API keys from the dashboard. JWT + Admin only (you can't
    manage keys with a key). The raw secret is returned ONCE on create.
    """

    # Force JWT here so an API key can't be used to mint/revoke keys.
    authentication_classes = [JWTAuthentication]
    permission_classes = [HasTenantRole(Role.ADMIN)]

    def get_serializer_class(self):
        if self.action == "create":
            return ApiKeyCreateSerializer
        return ApiKeySerializer

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        if tenant is None:
            return ApiKey.objects.none()
        return ApiKey.objects.filter(tenant=tenant).select_related("created_by")

    def create(self, request, *args, **kwargs):
        serializer = ApiKeyCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key, raw = ApiKey.generate(
            tenant=request.tenant,
            name=serializer.validated_data["name"],
            scopes=serializer.validated_data["scopes"],
            created_by=request.user,
        )
        data = ApiKeySerializer(key).data
        data["key"] = raw  # shown once — store it now!
        return Response(data, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        # Soft-revoke so the audit/usage history is preserved.
        instance.revoked_at = timezone.now()
        instance.save(update_fields=["revoked_at"])
