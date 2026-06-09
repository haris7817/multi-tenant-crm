"""
RBAC permission classes.

The JWT carries ``tenant_id`` and ``role`` claims (set at login). On every
request we verify the token's tenant matches the subdomain's tenant — so an
Acme token can never be replayed against Globex — and then check the role.
"""
from rest_framework.permissions import BasePermission

from .models import ROLE_LEVEL


class IsTenantMember(BasePermission):
    """Authenticated, and the token's tenant matches the request's subdomain."""

    message = "You are not a member of this tenant."

    def has_permission(self, request, view):
        tenant = getattr(request, "tenant", None)
        user = getattr(request, "user", None)
        token = getattr(request, "auth", None)
        if tenant is None or not (user and user.is_authenticated) or token is None:
            return False
        if token.get("tenant_id") != tenant.id:
            return False
        # Expose the caller's role for downstream checks / views.
        request.role = token.get("role")
        return True


def HasTenantRole(min_role):
    """
    Permission factory: caller must be a tenant member with at least ``min_role``
    (by the ROLE_LEVEL hierarchy). Usage: ``permission_classes = [HasTenantRole(Role.MANAGER)]``.
    """
    required_level = ROLE_LEVEL[min_role]

    class _HasTenantRole(IsTenantMember):
        message = f"Requires '{min_role}' role or higher."

        def has_permission(self, request, view):
            if not super().has_permission(request, view):
                return False
            return ROLE_LEVEL.get(request.role, -1) >= required_level

    return _HasTenantRole
