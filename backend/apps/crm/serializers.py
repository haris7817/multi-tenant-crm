from rest_framework import serializers

from .models import (
    Attachment,
    CustomFieldDefinition,
    Deal,
    Lead,
    Note,
    SavedView,
    Stage,
    Tag,
    Task,
)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "color"]
        read_only_fields = ["id"]


class LeadSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, required=False, queryset=Tag.all_objects.all()
    )
    tags_detail = TagSerializer(source="tags", many=True, read_only=True)

    class Meta:
        model = Lead
        fields = [
            "id", "name", "email", "phone", "company", "source",
            "status", "notes", "owner", "owner_email", "is_stale",
            "tags", "tags_detail", "custom",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "owner_email", "is_stale"]

    def validate_tags(self, tags):
        return _validate_tenant_tags(self, tags)


def _validate_tenant_tags(serializer, tags):
    tenant = serializer.context["request"].tenant
    for tag in tags:
        if tag.tenant_id != tenant.id:
            raise serializers.ValidationError("Tag does not belong to this tenant.")
    return tags


class StageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stage
        fields = ["id", "name", "order", "is_won", "is_lost"]
        read_only_fields = ["id"]


class DealSerializer(serializers.ModelSerializer):
    stage_name = serializers.CharField(source="stage.name", read_only=True)
    is_closed = serializers.BooleanField(read_only=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, required=False, queryset=Tag.all_objects.all()
    )
    tags_detail = TagSerializer(source="tags", many=True, read_only=True)

    class Meta:
        model = Deal
        fields = [
            "id", "title", "value", "stage", "stage_name", "lead", "owner",
            "expected_close_date", "closed_at", "is_closed",
            "tags", "tags_detail", "custom",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "closed_at", "created_at", "updated_at", "stage_name", "is_closed"]

    def validate_stage(self, stage):
        # Defense in depth: a client must not reference another tenant's stage.
        tenant = self.context["request"].tenant
        if stage.tenant_id != tenant.id:
            raise serializers.ValidationError("Stage does not belong to this tenant.")
        return stage

    def validate_tags(self, tags):
        return _validate_tenant_tags(self, tags)


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


# --- Phase 8 ----------------------------------------------------------------


class NoteSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True, default=None)
    target_model = serializers.CharField(source="target_type.model", read_only=True)

    class Meta:
        model = Note
        fields = [
            "id", "body", "author", "author_email",
            "target_model", "target_id", "created_at",
        ]
        # target is supplied as query/body params and resolved in the view.
        read_only_fields = [
            "id", "author", "author_email", "target_model", "target_id", "created_at",
        ]


class AttachmentSerializer(serializers.ModelSerializer):
    target_model = serializers.CharField(source="target_type.model", read_only=True)
    file = serializers.FileField(write_only=True)
    # Relative URL (e.g. /media/...) so it works through the dev proxy.
    url = serializers.SerializerMethodField()

    class Meta:
        model = Attachment
        fields = [
            "id", "file", "url", "filename", "uploaded_by",
            "target_model", "target_id", "created_at",
        ]
        read_only_fields = [
            "id", "url", "filename", "uploaded_by", "target_model", "target_id", "created_at",
        ]

    def get_url(self, obj):
        return obj.file.url if obj.file else None


class CustomFieldDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomFieldDefinition
        fields = ["id", "entity", "key", "label", "field_type", "options"]
        read_only_fields = ["id"]


class SavedViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedView
        fields = ["id", "entity", "name", "params", "created_at"]
        read_only_fields = ["id", "created_at"]


class BulkActionSerializer(serializers.Serializer):
    """Apply one action to many leads at once (8.5)."""

    ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    action = serializers.ChoiceField(
        choices=["set_status", "set_owner", "add_tag", "delete"]
    )
    status = serializers.ChoiceField(choices=Lead.Status.choices, required=False)
    owner = serializers.IntegerField(required=False, allow_null=True)
    tag = serializers.IntegerField(required=False)


class LeadImportSerializer(serializers.Serializer):
    """CSV upload for bulk lead import (8.4)."""

    file = serializers.FileField()
