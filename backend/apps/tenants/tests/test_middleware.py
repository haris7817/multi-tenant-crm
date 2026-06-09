"""The middleware must resolve the tenant from the subdomain — and only then."""
import pytest

pytestmark = pytest.mark.django_db


def test_resolves_tenant_from_subdomain(api_client, acme):
    resp = api_client.get("/api/tenant/", HTTP_HOST="acme.crm.local")
    assert resp.status_code == 200
    assert resp.json()["slug"] == "acme"


def test_unknown_subdomain_is_404(api_client, acme):
    resp = api_client.get("/api/tenant/", HTTP_HOST="nope.crm.local")
    assert resp.status_code == 404


def test_bare_host_has_no_tenant(api_client, acme):
    resp = api_client.get("/api/tenant/", HTTP_HOST="crm.local")
    assert resp.status_code == 404


def test_inactive_tenant_is_404(api_client, acme):
    acme.is_active = False
    acme.save()
    resp = api_client.get("/api/tenant/", HTTP_HOST="acme.crm.local")
    assert resp.status_code == 404
