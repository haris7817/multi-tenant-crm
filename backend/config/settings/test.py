"""Test settings — fast, isolated, Celery runs eagerly."""
from .base import *  # noqa: F401,F403

DEBUG = False

# A 32+ byte key keeps SimpleJWT's HMAC from warning during tests.
SECRET_KEY = "test-secret-key-that-is-long-enough-for-hmac-sha256"

ALLOWED_HOSTS = ["*"]

# Run Celery tasks synchronously in-process during tests.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Faster password hashing in tests.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
