import pytest
from rest_framework.test import APIClient

from apps.accounts.models import Membership, Role, User
from apps.crm.pipeline import create_default_pipeline
from apps.tenants.models import Domain, Tenant


@pytest.fixture
def make_tenant(db):
    def _make(slug):
        tenant = Tenant.objects.create(name=slug.title(), slug=slug)
        Domain.objects.create(tenant=tenant, domain=f"{slug}.crm.local")
        create_default_pipeline(tenant)
        return tenant

    return _make


@pytest.fixture
def make_member(db):
    def _make(tenant, role=Role.SALES_REP, email=None):
        email = email or f"{role}@{tenant.slug}.crm.local"
        user, created = User.objects.get_or_create(email=email)
        if created:
            user.set_password("password123")
            user.save()
        Membership.objects.get_or_create(user=user, tenant=tenant, defaults={"role": role})
        return user

    return _make


@pytest.fixture
def client_for(db, make_member):
    def _make(tenant, role=Role.SALES_REP):
        make_member(tenant, role=role)
        api = APIClient()
        resp = api.post(
            "/api/auth/login/",
            {"email": f"{role}@{tenant.slug}.crm.local", "password": "password123"},
            HTTP_HOST=f"{tenant.slug}.crm.local",
        )
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {resp.json()['access']}")
        api.defaults["HTTP_HOST"] = f"{tenant.slug}.crm.local"
        return api

    return _make
