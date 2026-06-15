from rest_framework import serializers

from .models import ApiKey, Scope


class ApiKeySerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(read_only=True)
    created_by_email = serializers.EmailField(
        source="created_by.email", read_only=True, default=None
    )

    class Meta:
        model = ApiKey
        fields = [
            "id", "name", "prefix", "scopes", "is_active",
            "created_by_email", "created_at", "last_used_at", "revoked_at",
        ]
        read_only_fields = fields


class ApiKeyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    scopes = serializers.ListField(
        child=serializers.ChoiceField(choices=Scope.choices),
        allow_empty=False,
        default=[Scope.READ],
    )

    def validate_scopes(self, scopes):
        # de-dupe and keep stable order
        return [s for s in (Scope.READ, Scope.WRITE) if s in scopes]
