"""
OAuth2 provider registry (12.4).

Client id/secret come from env so real credentials stay out of the code. A
provider with no client_id is "unconfigured" (the connect button is disabled in
the UI), but the flow + tests work end-to-end against a mocked token endpoint.
"""
from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True)
class Provider:
    key: str
    label: str
    authorize_url: str
    token_url: str
    scope: str
    client_id: str
    client_secret: str

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)


def _p(key, label, authorize_url, token_url, scope):
    return Provider(
        key=key,
        label=label,
        authorize_url=authorize_url,
        token_url=token_url,
        scope=scope,
        client_id=settings.OAUTH_PROVIDERS.get(key, {}).get("client_id", ""),
        client_secret=settings.OAUTH_PROVIDERS.get(key, {}).get("client_secret", ""),
    )


def get_registry():
    return {
        "google": _p(
            "google", "Google",
            "https://accounts.google.com/o/oauth2/v2/auth",
            "https://oauth2.googleapis.com/token",
            "openid email profile https://www.googleapis.com/auth/calendar.readonly",
        ),
        "slack": _p(
            "slack", "Slack",
            "https://slack.com/oauth/v2/authorize",
            "https://slack.com/api/oauth.v2.access",
            "chat:write,channels:read",
        ),
    }


def get_provider(key: str) -> Provider | None:
    return get_registry().get(key)
