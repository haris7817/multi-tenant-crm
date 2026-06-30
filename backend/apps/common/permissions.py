"""
Unified authorization for tenant resources (Phase 10).

A request may be authenticated two ways:
  * **User JWT** (the SPA) — gated by RBAC role (read/write/delete by method).
  * **API key** (external apps) — gated by the key's scopes (read/write); the
    tenant is already bound from the key by ApiKeyAuthentication.

``TenantAccess`` accepts either, so the same viewsets serve both audiences.
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.models import ROLE_LEVEL, Role
from apps.accounts.permissions import IsTenantMember
from apps.apikeys.models import ApiKey, Scope


class TenantAccess(BasePermission):
    def __init__(self, write_role=Role.SALES_REP, delete_role=Role.MANAGER):
        self.write_role = write_role
        self.delete_role = delete_role

    def has_permission(self, request, view):
        key = getattr(request, "auth", None)

        # --- API-key path: authorize by scope ---
        if isinstance(key, ApiKey):
            if request.method in SAFE_METHODS:
                return Scope.READ in key.scopes
            return Scope.WRITE in key.scopes

        # --- User JWT path: authorize by role ---
        if not IsTenantMember().has_permission(request, view):
            return False
        if request.method in SAFE_METHODS:
            return True
        required = self.delete_role if request.method == "DELETE" else self.write_role
        return ROLE_LEVEL.get(getattr(request, "role", None), -1) >= ROLE_LEVEL[required]
