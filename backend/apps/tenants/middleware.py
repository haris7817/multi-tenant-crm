"""Resolve the tenant from the request host and expose it for the request."""
from .context import clear_current_tenant, set_current_tenant
from .models import Domain


class TenantMiddleware:
    """
    Look up the tenant by the request's host (full subdomain match) and attach
    it as ``request.tenant`` while also storing it in the thread-local context
    that model managers read.

    ``request.tenant`` is ``None`` for hosts that don't map to a tenant
    (e.g. ``localhost``, ``crm.local``, the admin host). Views/permissions decide
    whether a missing tenant is an error for a given route.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()
        request.tenant = self._resolve(host)
        set_current_tenant(request.tenant)
        try:
            return self.get_response(request)
        finally:
            # Never leak tenant state across requests on a reused thread.
            clear_current_tenant()

    @staticmethod
    def _resolve(host):
        try:
            domain = Domain.objects.select_related("tenant").get(domain=host)
        except Domain.DoesNotExist:
            return None
        tenant = domain.tenant
        return tenant if tenant.is_active else None
