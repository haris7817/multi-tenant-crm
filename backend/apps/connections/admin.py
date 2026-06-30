from django.contrib import admin

from .models import Connection, OAuthState


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    list_display = ["provider", "status", "tenant", "account_email", "expires_at"]
    list_filter = ["tenant", "provider", "status"]
    # Never show encrypted token values in admin.
    exclude = ["access_token", "refresh_token"]


@admin.register(OAuthState)
class OAuthStateAdmin(admin.ModelAdmin):
    list_display = ["provider", "tenant", "used", "created_at"]
    list_filter = ["tenant", "provider", "used"]
