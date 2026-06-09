"""Development settings."""
from .base import *  # noqa: F401,F403
from .base import env

DEBUG = True

# Allow tenant subdomains like acme.crm.local during local dev.
ALLOWED_HOSTS = env(
    "DJANGO_ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1", ".crm.local"],
)

# Vite dev server origin(s) for CORS.
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
)
# Subdomains of crm.local on the Vite port are also fine in dev.
CORS_ALLOWED_ORIGIN_REGEXES = [r"^http://[a-z0-9-]+\.crm\.local:5173$"]
