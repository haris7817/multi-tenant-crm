from rest_framework import serializers

from .models import Deal, Lead, Stage, Task


class LeadSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)

    class Meta:
        model = Lead
        fields = [
            "id", "name", "email", "phone", "company", "source",
            "status", "notes", "owner", "owner_email",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "owner_email"]


class StageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stage
        fields = ["id", "name", "order", "is_won", "is_lost"]
        read_only_fields = ["id"]


class DealSerializer(serializers.ModelSerializer):
    stage_name = serializers.CharField(source="stage.name", read_only=True)
    is_closed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Deal
        fields = [
            "id", "title", "value", "stage", "stage_name", "lead", "owner",
            "expected_close_date", "closed_at", "is_closed",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "closed_at", "created_at", "updated_at", "stage_name", "is_closed"]

    def validate_stage(self, stage):
        # Defense in depth: a client must not reference another tenant's stage.
        tenant = self.context["request"].tenant
        if stage.tenant_id != tenant.id:
            raise serializers.ValidationError("Stage does not belong to this tenant.")
        return stage


class DealMoveSerializer(serializers.Serializer):
    """Payload for the 'move deal to a stage' pipeline action."""

    # Unscoped manager (safe to snapshot); the view validates the stage's tenant.
    stage = serializers.PrimaryKeyRelatedField(queryset=Stage.all_objects.all())


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            "id", "title", "description", "due_date", "is_done", "priority",
            "assigned_to", "lead", "deal", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
