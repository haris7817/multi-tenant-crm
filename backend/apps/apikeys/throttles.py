"""Per-key rate limiting (10.4). Only applies to API-key requests."""
from rest_framework.throttling import SimpleRateThrottle

from .models import ApiKey


class ApiKeyRateThrottle(SimpleRateThrottle):
    scope = "apikey"

    def get_cache_key(self, request, view):
        key = getattr(request, "auth", None)
        if isinstance(key, ApiKey):
            return f"throttle_apikey_{key.prefix}"
        return None  # not an API-key request -> not throttled here
