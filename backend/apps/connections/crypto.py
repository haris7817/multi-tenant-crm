"""
Field-level encryption for secrets at rest (12.3).

Uses Fernet (AES-128-CBC + HMAC). The key comes from FIELD_ENCRYPTION_KEY, or is
derived from SECRET_KEY for dev. ``EncryptedTextField`` transparently encrypts on
write and decrypts on read, so tokens are ciphertext in the database.
"""
import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.db import models


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    key = getattr(settings, "FIELD_ENCRYPTION_KEY", "") or ""
    if not key:
        # Derive a stable 32-byte urlsafe key from SECRET_KEY (dev convenience).
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(digest).decode()
    return Fernet(key if isinstance(key, bytes) else key.encode())


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode()).decode()


class EncryptedTextField(models.TextField):
    """A TextField whose value is stored encrypted at rest."""

    def from_db_value(self, value, expression, connection):
        if value is None or value == "":
            return value
        try:
            return decrypt(value)
        except InvalidToken:
            return value  # tolerate legacy/plaintext rows

    def get_prep_value(self, value):
        if value is None or value == "":
            return value
        return encrypt(str(value))
