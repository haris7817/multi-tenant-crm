"""
Resolve a generic CRM target (a Lead or Deal) for notes/attachments.

Only these two models can be targeted, and the target must belong to the
current tenant — this is where we enforce that a note/file can't be attached to
another tenant's record.
"""
from django.contrib.contenttypes.models import ContentType
from rest_framework.exceptions import ValidationError

from .models import Deal, Lead

TARGET_MODELS = {"lead": Lead, "deal": Deal}


def resolve_target(tenant, model_name, target_id):
    """Return (ContentType, instance) for a tenant-owned Lead/Deal, or 400."""
    model = TARGET_MODELS.get((model_name or "").lower())
    if model is None:
        raise ValidationError({"target_model": "Must be 'lead' or 'deal'."})
    try:
        obj = model.all_objects.get(pk=target_id, tenant=tenant)
    except model.DoesNotExist:
        raise ValidationError({"target_id": "No such record in this tenant."})
    return ContentType.objects.get_for_model(model), obj
