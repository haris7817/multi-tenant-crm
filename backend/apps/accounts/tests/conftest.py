import pytest

from apps.accounts.models import Membership, Role, User
from apps.tenants.models import Domain, Tenant


@pytest.fixture
def make_tenant(db):
    def _make(slug, name=None):
        tenant = Tenant.objects.create(name=name or slug.title(), slug=slug)
        Domain.objects.create(tenant=tenant, domain=f"{slug}.crm.local")
        return tenant

    return _make


@pytest.fixture
def make_member(db):
    def _make(tenant, email, role=Role.VIEWER, password="password123"):
        user = User.objects.create_user(email=email, password=password)
        Membership.objects.create(user=user, tenant=tenant, role=role)
        return user

    return _make


@pytest.fixture
def acme(make_tenant):
    return make_tenant("acme")


@pytest.fixture
def globex(make_tenant):
    return make_tenant("globex")


def login(api_client, host, email, password="password123"):
    """Helper: obtain an access token via the tenant subdomain."""
    resp = api_client.post(
        "/api/auth/login/",
        {"email": email, "password": password},
        HTTP_HOST=host,
    )
    return resp


@pytest.fixture
def auth_client():
    """Return a factory that builds an authed APIClient for a given token+host."""
    from rest_framework.test import APIClient

    def _make(token, host):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        client.defaults["HTTP_HOST"] = host
        return client

    return _make
