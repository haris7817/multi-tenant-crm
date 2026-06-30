"""
Idempotency-Key support (10.5).

A client retrying a POST with the same ``Idempotency-Key`` header gets the
original response back instead of creating a duplicate. We key the cache by the
credential (Authorization) + path + idempotency key, so it works for both JWT
and API-key callers without needing the resolved tenant.
"""
import hashlib

from django.core.cache import cache
from django.http import HttpResponse

IDEMPOTENCY_TTL = 60 * 60 * 24  # 24h


class IdempotencyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        idem = request.headers.get("Idempotency-Key")
        if request.method != "POST" or not idem:
            return self.get_response(request)

        auth = request.headers.get("Authorization", "")
        raw = f"{auth}|{request.path}|{idem}"
        cache_key = "idem:" + hashlib.sha256(raw.encode()).hexdigest()

        cached = cache.get(cache_key)
        if cached:
            resp = HttpResponse(
                cached["content"],
                status=cached["status"],
                content_type=cached["content_type"],
            )
            resp["X-Idempotent-Replay"] = "true"
            return resp

        response = self.get_response(request)
        # Ensure DRF responses are rendered before reading .content.
        if hasattr(response, "render") and not getattr(response, "is_rendered", True):
            response.render()
        if response.status_code < 500:
            cache.set(
                cache_key,
                {
                    "content": response.content,
                    "status": response.status_code,
                    "content_type": response.get("Content-Type", "application/json"),
                },
                IDEMPOTENCY_TTL,
            )
        return response
