"""Phase 0 smoke tests — prove the project boots and serves."""
import pytest


@pytest.mark.django_db
def test_healthcheck(api_client):
    resp = api_client.get("/api/health/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.django_db
def test_openapi_schema_available(api_client):
    resp = api_client.get("/api/schema/")
    assert resp.status_code == 200
