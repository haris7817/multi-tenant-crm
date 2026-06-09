"""Helpers to record audit entries and compute field-level diffs."""
import datetime
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.db.models import Model

from .models import AuditLog


def _jsonable(value):
    """Coerce a model field value into something JSON-serializable for ``changes``."""
    if isinstance(value, Model):
        return value.pk
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value


def diff(before: dict, after: dict) -> dict:
    """Return {field: [old, new]} for keys whose value changed."""
    changes = {}
    for field in before:
        old, new = before[field], after.get(field)
        if old != new:
            changes[field] = [_jsonable(old), _jsonable(new)]
    return changes


def record(*, tenant, actor, action, instance, changes=None):
    """Write one audit row. ``actor`` may be an unauthenticated user or None."""
    actor = actor if (actor and getattr(actor, "is_authenticated", False)) else None
    return AuditLog.objects.create(
        tenant=tenant,
        actor=actor,
        action=action,
        target_type=ContentType.objects.get_for_model(instance.__class__),
        target_id=instance.pk,
        target_repr=str(instance)[:255],
        changes=changes or {},
    )
