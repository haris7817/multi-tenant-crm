from django.contrib import admin

from .models import Deal, Lead, Stage, Task


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
