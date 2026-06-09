"""
Auth identities and tenant membership.

A ``User`` is a GLOBAL identity (one person, one login) that can belong to many
tenants. ``Membership`` is the join row that grants a user a ``Role`` within a
specific tenant — this is the backbone of RBAC.
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models

from apps.tenants.models import Tenant

from .managers import UserManager


class Role(models.TextChoices):
    OWNER = "owner", "Owner"
    ADMIN = "admin", "Admin"
    MANAGER = "manager", "Manager"
    SALES_REP = "sales_rep", "Sales Rep"
    VIEWER = "viewer", "Viewer"


# Privilege ordering for hierarchical checks: a higher level implies all lower
# permissions. Used by HasTenantRole(min_role).
ROLE_LEVEL = {
    Role.OWNER: 4,
    Role.ADMIN: 3,
    Role.MANAGER: 2,
    Role.SALES_REP: 1,
    Role.VIEWER: 0,
}


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class Membership(models.Model):
    """Grants ``user`` a ``role`` inside ``tenant``."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="memberships"
    )
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(
        max_length=20, choices=Role.choices, default=Role.VIEWER
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "tenant")
        ordering = ["tenant", "role"]

    def __str__(self):
        return f"{self.user.email} @ {self.tenant.slug} ({self.role})"

    @property
    def level(self):
        return ROLE_LEVEL.get(self.role, -1)
