from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    target_model = serializers.CharField(
        source="target_type.model", read_only=True, default=None
    )

    class Meta:
        model = Notification
        fields = [
            "id", "type", "message", "target_model", "target_id",
            "is_read", "created_at",
        ]
        read_only_fields = fields
