from rest_framework import serializers

from .models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True, default=None)
    target_model = serializers.CharField(source="target_type.model", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = [
            "id", "action", "actor", "actor_email",
            "target_model", "target_id", "target_repr",
            "changes", "created_at",
        ]
        read_only_fields = fields
