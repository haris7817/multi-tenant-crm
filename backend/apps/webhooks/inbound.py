"""
Inbound webhook receiver (11.6).

Partners POST to ``/api/v1/inbound/<token>/``. The ``token`` (public, in the URL)
identifies the tenant + integration; the ``X-Signature`` header (HMAC-SHA256 of
the raw body using the shared secret) proves authenticity. No JWT/API key needed.
"""
import hashlib
import hmac
import json

from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.crm.models import Lead
from apps.tenants.context import set_current_tenant

from .events import LEAD_CREATED
from .models import InboundEndpoint, InboundEvent
from .services import emit_event


def _valid_signature(secret: str, raw: bytes, header: str) -> bool:
    expected = "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header or "")


def _safe_payload(raw: bytes):
    try:
        return json.loads(raw or b"{}")
    except ValueError:
        return {"_raw": raw.decode(errors="replace")[:1000]}


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def inbound_receiver(request, token):
    endpoint = (
        InboundEndpoint.all_objects.select_related("tenant")
        .filter(token=token, is_active=True)
        .first()
    )
    if not endpoint:
        return Response({"detail": "Unknown endpoint."}, status=404)

    raw = request.body  # read raw bytes BEFORE parsing for an exact signature match
    if not _valid_signature(endpoint.secret, raw, request.headers.get("X-Signature")):
        InboundEvent.all_objects.create(
            tenant=endpoint.tenant,
            endpoint=endpoint,
            status=InboundEvent.Status.REJECTED,
            payload=_safe_payload(raw),
            error="Invalid signature",
        )
        return Response({"detail": "Invalid signature."}, status=401)

    data = request.data if isinstance(request.data, dict) else {}
    set_current_tenant(endpoint.tenant)

    if endpoint.action == InboundEndpoint.Action.CREATE_LEAD:
        name = (data.get("name") or data.get("full_name") or "").strip()
        if not name:
            InboundEvent.all_objects.create(
                tenant=endpoint.tenant, endpoint=endpoint,
                status=InboundEvent.Status.ERROR, payload=data, error="Missing name",
            )
            return Response({"detail": "Payload missing 'name'."}, status=400)

        lead = Lead.all_objects.create(
            tenant=endpoint.tenant,
            name=name,
            email=(data.get("email") or "").strip(),
            company=(data.get("company") or "").strip(),
            source=endpoint.source or "inbound",
        )
        # Inbound creation fans out to outbound subscribers too.
        emit_event(
            tenant=endpoint.tenant,
            event_type=LEAD_CREATED,
            payload={"id": lead.id, "name": lead.name, "via": "inbound"},
        )
        InboundEvent.all_objects.create(
            tenant=endpoint.tenant, endpoint=endpoint,
            status=InboundEvent.Status.PROCESSED, payload=data,
        )
        return Response({"status": "ok", "lead_id": lead.id}, status=201)

    if endpoint.action == InboundEndpoint.Action.LOG_EMAIL:
        # 13.2 — an email provider's inbound-parse posts {from, subject, body};
        # we attach it as a note on the matching lead.
        from django.contrib.contenttypes.models import ContentType

        from apps.crm.models import Note

        sender = (data.get("from") or "").strip().lower()
        lead = Lead.all_objects.filter(tenant=endpoint.tenant, email__iexact=sender).first()
        if not lead:
            InboundEvent.all_objects.create(
                tenant=endpoint.tenant, endpoint=endpoint,
                status=InboundEvent.Status.ERROR, payload=data,
                error=f"No lead with email {sender}",
            )
            return Response({"detail": "No matching lead."}, status=404)

        body = f"📧 {data.get('subject', '(no subject)')}\n\n{data.get('body', '')}"
        Note.all_objects.create(
            tenant=endpoint.tenant,
            target_type=ContentType.objects.get_for_model(Lead),
            target_id=lead.id,
            body=body,
        )
        InboundEvent.all_objects.create(
            tenant=endpoint.tenant, endpoint=endpoint,
            status=InboundEvent.Status.PROCESSED, payload=data,
        )
        return Response({"status": "ok", "lead_id": lead.id}, status=201)

    return Response({"detail": "Unsupported action."}, status=400)
