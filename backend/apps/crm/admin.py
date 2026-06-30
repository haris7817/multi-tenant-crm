from django.contrib import admin

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


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ["name", "company", "status", "tenant", "owner", "created_at"]
    list_filter = ["tenant", "status"]
    search_fields = ["name", "email", "company"]


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ["name", "order", "is_won", "is_lost", "tenant"]
    list_filter = ["tenant"]
    ordering = ["tenant", "order"]


@admin.register(Deal)
class DealAdmin(admin.ModelAdmin):
    list_display = ["title", "value", "stage", "tenant", "owner", "closed_at"]
    list_filter = ["tenant", "stage"]
    search_fields = ["title"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "priority", "is_done", "due_date", "tenant", "assigned_to"]
    list_filter = ["tenant", "priority", "is_done"]
    search_fields = ["title"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "color", "tenant"]
    list_filter = ["tenant"]


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ["__str__", "author", "tenant", "created_at"]
    list_filter = ["tenant"]


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ["filename", "uploaded_by", "tenant", "created_at"]
    list_filter = ["tenant"]


@admin.register(CustomFieldDefinition)
class CustomFieldDefinitionAdmin(admin.ModelAdmin):
    list_display = ["label", "entity", "key", "field_type", "tenant"]
    list_filter = ["tenant", "entity"]


@admin.register(SavedView)
class SavedViewAdmin(admin.ModelAdmin):
    list_display = ["name", "entity", "user", "tenant"]
    list_filter = ["tenant", "entity"]
