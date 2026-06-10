from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ["created_at", "tenant", "actor", "action", "target_repr"]
    list_filter = ["tenant", "action", "target_type"]
    search_fields = ["target_repr", "actor__email"]
    readonly_fields = [f.name for f in AuditLog._meta.fields] + ["target"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
