from django.contrib import admin

from .models import ApiKey


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    list_display = ["name", "prefix", "tenant", "scopes", "is_active", "last_used_at"]
    list_filter = ["tenant"]
    search_fields = ["name", "prefix"]
    readonly_fields = ["prefix", "hashed_key", "created_at", "last_used_at"]
