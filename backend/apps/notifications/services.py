"""Create notifications and push them to the recipient's WebSocket (9.2)."""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.contenttypes.models import ContentType

from .models import Notification


def _serialize(n: Notification) -> dict:
    return {
        "id": n.id,
        "type": n.type,
        "message": n.message,
        "target_model": n.target_type.model if n.target_type_id else None,
        "target_id": n.target_id,
        "is_read": n.is_read,
        "created_at": n.created_at.isoformat(),
    }


def _push(n: Notification):
    """Send the new notification to the recipient's tenant+user group."""
    layer = get_channel_layer()
    if layer is None:
        return
    group = f"notify_{n.tenant_id}_{n.recipient_id}"
    async_to_sync(layer.group_send)(
        group, {"type": "notify.message", "data": _serialize(n)}
    )


def notify(*, tenant, recipient, type, message, target=None):
    """Create one notification for ``recipient`` (a User or id) and push it live."""
    kwargs = {"tenant": tenant, "type": type, "message": message}
    if hasattr(recipient, "pk"):
        kwargs["recipient"] = recipient
    else:
        kwargs["recipient_id"] = recipient
    if target is not None:
        kwargs["target_type"] = ContentType.objects.get_for_model(target.__class__)
        kwargs["target_id"] = target.pk
    notification = Notification.objects.create(**kwargs)
    _push(notification)
    return notification
