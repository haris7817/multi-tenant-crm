from django.contrib import admin

from .models import (
    InboundEndpoint,
    InboundEvent,
    WebhookDelivery,
    WebhookEndpoint,
    WebhookEvent,
)


@admin.register(InboundEndpoint)
class InboundEndpointAdmin(admin.ModelAdmin):
    list_display = ["source", "action", "token", "tenant", "is_active"]
    list_filter = ["tenant", "action", "is_active"]


@admin.register(InboundEvent)
class InboundEventAdmin(admin.ModelAdmin):
    list_display = ["endpoint", "status", "tenant", "created_at"]
    list_filter = ["tenant", "status"]


@admin.register(WebhookEndpoint)
class WebhookEndpointAdmin(admin.ModelAdmin):
    list_display = ["url", "tenant", "is_active", "created_at"]
    list_filter = ["tenant", "is_active"]


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ["event_type", "tenant", "dispatched", "created_at"]
    list_filter = ["tenant", "dispatched", "event_type"]


@admin.register(WebhookDelivery)
class WebhookDeliveryAdmin(admin.ModelAdmin):
    list_display = ["event", "endpoint", "status", "attempts", "response_status"]
    list_filter = ["tenant", "status"]
