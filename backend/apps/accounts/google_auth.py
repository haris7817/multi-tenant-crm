"""
Verify a Google ID token (12.1).

Kept in its own module so tests can monkeypatch ``verify_google_token`` without
needing network or real Google credentials. Real verification uses google-auth.
"""
from django.conf import settings


def verify_google_token(credential: str) -> dict:
    """Validate a Google ID token and return its claims (email, name, ...)."""
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token

    client_id = settings.OAUTH_PROVIDERS.get("google", {}).get("client_id") or None
    return google_id_token.verify_oauth2_token(
        credential, google_requests.Request(), client_id
    )
