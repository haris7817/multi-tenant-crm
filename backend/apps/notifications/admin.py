from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["type", "message", "recipient", "is_read", "tenant", "created_at"]
    list_filter = ["tenant", "type", "is_read"]
    search_fields = ["message", "recipient__email"]
