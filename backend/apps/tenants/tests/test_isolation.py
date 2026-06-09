"""
The core promise of the whole project: one tenant can never see another's rows.

These tests exercise ``TenantManager`` + the thread-local context directly,
using the ``DemoRecord`` tenant-scoped model.
"""
import pytest

from apps.tenants.context import get_current_tenant, tenant_context
from apps.tenants.models import DemoRecord

pytestmark = pytest.mark.django_db


def test_manager_autofilters_by_current_tenant(acme, globex):
    DemoRecord.all_objects.create(tenant=acme, text="acme-1")
    DemoRecord.all_objects.create(tenant=acme, text="acme-2")
    DemoRecord.all_objects.create(tenant=globex, text="globex-1")

    with tenant_context(acme):
        texts = set(DemoRecord.objects.values_list("text", flat=True))
    assert texts == {"acme-1", "acme-2"}

    with tenant_context(globex):
        texts = set(DemoRecord.objects.values_list("text", flat=True))
    assert texts == {"globex-1"}


def test_tenant_a_cannot_read_tenant_b(acme, globex):
    DemoRecord.all_objects.create(tenant=globex, text="secret")
    with tenant_context(acme):
        assert DemoRecord.objects.filter(text="secret").count() == 0


def test_save_defaults_tenant_from_context(acme):
    with tenant_context(acme):
        rec = DemoRecord(text="no-tenant-passed")
        rec.save()  # tenant should be filled from context, not required up front
    assert rec.tenant_id == acme.id


def test_no_context_returns_all_rows(acme, globex):
    DemoRecord.all_objects.create(tenant=acme, text="a")
    DemoRecord.all_objects.create(tenant=globex, text="b")
    # Outside any request/context (e.g. shell), the scoped manager is unfiltered.
    assert get_current_tenant() is None
    assert DemoRecord.objects.count() == 2
