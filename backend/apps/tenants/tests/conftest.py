import pytest

from apps.tenants.models import Domain, Tenant


@pytest.fixture
def acme(db):
    tenant = Tenant.objects.create(name="Acme Inc", slug="acme")
    Domain.objects.create(tenant=tenant, domain="acme.crm.local")
    return tenant


@pytest.fixture
def globex(db):
    tenant = Tenant.objects.create(name="Globex Corp", slug="globex")
    Domain.objects.create(tenant=tenant, domain="globex.crm.local")
    return tenant
