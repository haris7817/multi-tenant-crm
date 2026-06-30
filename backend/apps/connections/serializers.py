from rest_framework import serializers

from .models import Connection


class ConnectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Connection
        # Tokens are NEVER exposed over the API.
        fields = [
            "id", "provider", "status", "account_email", "scopes",
            "expires_at", "created_at",
        ]
        read_only_fields = fields


class AuthorizeSerializer(serializers.Serializer):
    provider = serializers.CharField()
    redirect_uri = serializers.URLField()


class CallbackSerializer(serializers.Serializer):
    state = serializers.CharField()
    code = serializers.CharField()
