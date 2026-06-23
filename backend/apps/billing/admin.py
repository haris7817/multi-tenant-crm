from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ["tenant", "plan", "status", "current_period_end", "updated_at"]
    list_filter = ["plan", "status"]
    search_fields = ["tenant__slug", "stripe_customer_id"]
