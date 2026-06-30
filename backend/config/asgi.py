"""ASGI config — HTTP via Django, WebSockets via Channels."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

# Initialize Django/apps before importing consumers (which import models).
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from apps.notifications.ws import (  # noqa: E402
    JWTAuthMiddleware,
    websocket_urlpatterns,
)

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
