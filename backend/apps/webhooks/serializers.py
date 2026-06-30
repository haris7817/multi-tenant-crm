from rest_framework import serializers

from .events import ALL, is_valid
from .models import InboundEndpoint, WebhookDelivery, WebhookEndpoint


class WebhookEndpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookEndpoint
        fields = [
            "id", "url", "events", "description", "is_active",
            "secret", "created_at",
        ]
        # secret is generated server-side and shown so the receiver can verify
        # signatures; never set by the client.
        read_only_fields = ["id", "secret", "created_at"]

    def validate_events(self, events):
        bad = [e for e in events if not is_valid(e)]
        if bad:
            raise serializers.ValidationError(f"Unknown event(s): {bad}")
        return events


class WebhookDeliverySerializer(serializers.ModelSerializer):
    event_type = serializers.CharField(source="event.event_type", read_only=True)

    class Meta:
        model = WebhookDelivery
        fields = [
            "id", "endpoint", "event", "event_type", "status", "attempts",
            "response_status", "error", "last_attempt_at", "created_at",
        ]
        read_only_fields = fields


class InboundEndpointSerializer(serializers.ModelSerializer):
    # The receiver URL the partner should POST to.
    receive_url = serializers.SerializerMethodField()

    class Meta:
        model = InboundEndpoint
        fields = [
            "id", "source", "action", "is_active",
            "token", "secret", "receive_url", "created_at",
        ]
        # token + secret are generated server-side; shown so the partner can
        # configure their sender (URL + signing).
        read_only_fields = ["id", "token", "secret", "receive_url", "created_at"]

    def get_receive_url(self, obj):
        return f"/api/v1/inbound/{obj.token}/"
