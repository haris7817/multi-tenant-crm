"""
WebSocket layer for real-time notifications (9.2).

Auth: browsers can't set headers on a WebSocket, so the client passes the JWT in
the query string (?token=...). The tenant comes from the token's ``tenant_id``
claim (not the Host), so each socket joins exactly one tenant+user group.
"""
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.urls import path
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


def group_name(tenant_id, user_id):
    return f"notify_{tenant_id}_{user_id}"


@database_sync_to_async
def _load_user(user_id):
    return User.objects.filter(pk=user_id, is_active=True).first()


class JWTAuthMiddleware(BaseMiddleware):
    """Populate scope['user'] and scope['tenant_id'] from a ?token= JWT."""

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        token = (query.get("token") or [None])[0]
        scope = dict(scope)
        scope["user"] = None
        scope["tenant_id"] = None
        if token:
            try:
                access = AccessToken(token)
                scope["tenant_id"] = access.get("tenant_id")
                scope["user"] = await _load_user(access.get("user_id"))
            except TokenError:
                pass
        return await super().__call__(scope, receive, send)


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        tenant_id = self.scope.get("tenant_id")
        if not user or not tenant_id:
            await self.close()
            return
        self.group = group_name(tenant_id, user.id)
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)

    # Receives messages sent via group_send(type="notify.message").
    async def notify_message(self, event):
        await self.send_json(event["data"])


websocket_urlpatterns = [
    path("ws/notifications/", NotificationConsumer.as_asgi()),
]
