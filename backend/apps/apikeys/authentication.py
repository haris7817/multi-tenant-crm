"""
DRF authentication for API keys (10.3).

Clients send ``Authorization: Api-Key crm_<prefix>_<secret>``. On success we bind
the tenant FROM THE KEY (not the subdomain), so external apps can call the API on
any host without knowing the tenant's subdomain. ``request.auth`` is the ApiKey.
"""
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from rest_framework.authentication import (
    BaseAuthentication,
    get_authorization_header,
)
from rest_framework.exceptions import AuthenticationFailed

from apps.tenants.context import set_current_tenant

from .models import ApiKey


class ApiKeyAuthentication(BaseAuthentication):
    keyword = b"api-key"

    def authenticate(self, request):
        header = get_authorization_header(request).split()
        if not header or header[0].lower() != self.keyword:
            return None  # let other authenticators (JWT) try
        if len(header) != 2:
            raise AuthenticationFailed("Invalid Api-Key header.")

        raw = header[1].decode()
        parts = raw.split("_")
        if len(parts) < 3 or parts[0] != "crm":
            raise AuthenticationFailed("Malformed API key.")

        try:
            key = ApiKey.objects.select_related("tenant", "created_by").get(
                prefix=parts[1], revoked_at__isnull=True
            )
        except ApiKey.DoesNotExist:
            raise AuthenticationFailed("Invalid API key.")
        if not key.matches(raw):
            raise AuthenticationFailed("Invalid API key.")

        # Bind the tenant from the key (overrides any subdomain resolution).
        request.tenant = key.tenant
        set_current_tenant(key.tenant)
        ApiKey.objects.filter(pk=key.pk).update(last_used_at=timezone.now())

        return (key.created_by or AnonymousUser(), key)

    def authenticate_header(self, request):
        return "Api-Key"
