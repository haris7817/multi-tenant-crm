"""OAuth2 authorization-code flow + token refresh (12.4)."""
import json
import secrets
import urllib.parse
import urllib.request
from datetime import timedelta

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import Connection, OAuthState
from .providers import get_provider


def _token_request(token_url: str, data: dict) -> dict:
    """POST form-encoded to a token endpoint; return parsed JSON (mocked in tests)."""
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        token_url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def start_oauth(*, tenant, provider_key, redirect_uri):
    """Create state and return the provider's authorize URL to redirect the user to."""
    provider = get_provider(provider_key)
    if provider is None:
        raise ValidationError({"provider": "Unknown provider."})
    if not provider.configured:
        raise ValidationError({"provider": f"{provider.label} is not configured."})

    state = secrets.token_urlsafe(24)
    OAuthState.objects.create(
        tenant=tenant, provider=provider_key, state=state, redirect_uri=redirect_uri
    )
    params = {
        "client_id": provider.client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": provider.scope,
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{provider.authorize_url}?{urllib.parse.urlencode(params)}"


def complete_oauth(*, tenant, state, code, user=None):
    """Validate state, exchange the code for tokens, and store the connection."""
    try:
        st = OAuthState.objects.get(tenant=tenant, state=state, used=False)
    except OAuthState.DoesNotExist:
        raise ValidationError({"state": "Invalid or expired state."})

    provider = get_provider(st.provider)
    tokens = _token_request(
        provider.token_url,
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": st.redirect_uri,
            "client_id": provider.client_id,
            "client_secret": provider.client_secret,
        },
    )

    expires_at = None
    if tokens.get("expires_in"):
        expires_at = timezone.now() + timedelta(seconds=int(tokens["expires_in"]))

    conn, _ = Connection.objects.update_or_create(
        tenant=tenant,
        provider=st.provider,
        defaults={
            "status": Connection.Status.CONNECTED,
            "access_token": tokens.get("access_token", ""),
            "refresh_token": tokens.get("refresh_token", ""),
            "expires_at": expires_at,
            "scopes": tokens.get("scope", provider.scope),
            "account_email": tokens.get("account_email", ""),
            "connected_by": user if getattr(user, "is_authenticated", False) else None,
            "metadata": {k: v for k, v in tokens.items() if k not in {
                "access_token", "refresh_token", "expires_in"}},
        },
    )
    st.used = True
    st.save(update_fields=["used"])
    return conn


def refresh_connection(conn: Connection) -> Connection:
    """Use the refresh token to obtain a new access token."""
    provider = get_provider(conn.provider)
    if not conn.refresh_token or provider is None:
        raise ValidationError({"detail": "No refresh token available."})
    tokens = _token_request(
        provider.token_url,
        {
            "grant_type": "refresh_token",
            "refresh_token": conn.refresh_token,
            "client_id": provider.client_id,
            "client_secret": provider.client_secret,
        },
    )
    conn.access_token = tokens.get("access_token", conn.access_token)
    if tokens.get("refresh_token"):
        conn.refresh_token = tokens["refresh_token"]
    if tokens.get("expires_in"):
        conn.expires_at = timezone.now() + timedelta(seconds=int(tokens["expires_in"]))
    conn.status = Connection.Status.CONNECTED
    conn.save()
    return conn
