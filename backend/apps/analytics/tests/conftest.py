import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.accounts.models import Membership, Role, User
from apps.crm.pipeline import create_default_pipeline
from apps.tenants.models import Domain, Tenant


@pytest.fixture(autouse=True)
def _clear_cache():
    """Keep the (process-global) locmem cache from leaking across tests."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def make_tenant(db):
    def _make(slug):
        tenant = Tenant.objects.create(name=slug.title(), slug=slug)
        Domain.objects.create(tenant=tenant, domain=f"{slug}.crm.local")
        create_default_pipeline(tenant)
        return tenant

    return _make


@pytest.fixture
def client_for(db):
    def _make(tenant, role=Role.VIEWER):
        email = f"{role}@{tenant.slug}.crm.local"
        user, created = User.objects.get_or_create(email=email)
        if created:
            user.set_password("password123")
            user.save()
        Membership.objects.get_or_create(user=user, tenant=tenant, defaults={"role": role})
        api = APIClient()
        resp = api.post(
            "/api/auth/login/",
            {"email": email, "password": "password123"},
            HTTP_HOST=f"{tenant.slug}.crm.local",
        )
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['access']}")
        api.defaults["HTTP_HOST"] = f"{tenant.slug}.crm.local"
        return api

    return _make
