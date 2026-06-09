"""
Per-request "current tenant" stored in a thread-local.

The middleware writes the resolved tenant here at the start of each request and
clears it at the end. Model managers read it to auto-scope queries. This is the
mechanism that makes ``Lead.objects.all()`` return only the active tenant's rows
without every caller remembering to filter.
"""
import threading
from contextlib import contextmanager

_state = threading.local()


def set_current_tenant(tenant):
    _state.tenant = tenant


def get_current_tenant():
    return getattr(_state, "tenant", None)


def clear_current_tenant():
    _state.tenant = None


@contextmanager
def tenant_context(tenant):
    """Temporarily run a block as a given tenant (handy in tasks/tests/shell)."""
    previous = get_current_tenant()
    set_current_tenant(tenant)
    try:
        yield
    finally:
        set_current_tenant(previous)
