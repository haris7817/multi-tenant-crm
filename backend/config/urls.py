"""Root URL configuration."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from django.views.decorators.csrf import csrf_exempt

from apps.webhooks.inbound import inbound_receiver
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


@csrf_exempt
def healthcheck(_request):
    """Liveness probe (also a handy csrf-exempt POST target for webhook demos)."""
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", healthcheck, name="health"),
    # OpenAPI schema + Swagger UI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("api/", include("apps.tenants.urls")),
    path("api/", include("apps.accounts.urls")),
    path("api/", include("apps.crm.urls")),
    path("api/", include("apps.activity.urls")),
    path("api/", include("apps.analytics.urls")),
    path("api/", include("apps.notifications.urls")),
    path("api/", include("apps.apikeys.urls")),
    path("api/", include("apps.webhooks.urls")),
    path("api/", include("apps.connections.urls")),
    path("api/", include("apps.billing.urls")),
    # Versioned public API surface (Phase 10). Same viewsets; accepts a user JWT
    # or an API key. External apps should target /api/v1/.
    path("api/v1/", include("apps.crm.urls")),
    # Inbound webhook receiver (11.6): signature-verified, token in the URL.
    path(
        "api/v1/inbound/<str:token>/",
        inbound_receiver,
        name="inbound-webhook",
    ),
]

if settings.DEBUG:
    # Serve user-uploaded attachments in dev (use S3/CDN in production).
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
