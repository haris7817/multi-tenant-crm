from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import TenantSerializer


@extend_schema(
    responses=TenantSerializer,
    description="Return the tenant resolved from the request subdomain, or 404.",
)
@api_view(["GET"])
@permission_classes([AllowAny])
def current_tenant(request):
    """
    Lets a client (and our tests) confirm which tenant a subdomain resolves to.
    Unknown / inactive subdomains return 404 — proving the middleware refuses to
    serve a request as a non-existent tenant.
    """
    if getattr(request, "tenant", None) is None:
        raise Http404("No tenant for this host.")
    return Response(TenantSerializer(request.tenant).data)
