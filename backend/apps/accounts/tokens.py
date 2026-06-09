"""Tenant-aware JWT: embed tenant_id + role so each token is bound to a tenant."""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Membership


class TenantTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Authenticate against the subdomain's tenant. The user must have a membership
    in that tenant; the resulting tokens carry ``tenant_id`` and ``role`` claims.
    """

    def validate(self, attrs):
        # super().validate() authenticates email/password and sets self.user.
        super().validate(attrs)

        request = self.context["request"]
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            raise serializers.ValidationError("Unknown tenant subdomain.")

        try:
            membership = Membership.objects.get(user=self.user, tenant=tenant)
        except Membership.DoesNotExist:
            raise serializers.ValidationError(
                "You are not a member of this tenant."
            )

        refresh = self.get_token(self.user)
        refresh["tenant_id"] = tenant.id
        refresh["role"] = membership.role

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "role": membership.role,
            "tenant": tenant.slug,
            "email": self.user.email,
        }
