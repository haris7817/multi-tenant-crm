from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.tenants.serializers import TenantSerializer

from .models import Membership, Role
from .permissions import HasTenantRole, IsTenantMember
from .serializers import (
    InviteSerializer,
    MembershipSerializer,
    RegisterSerializer,
    RoleUpdateSerializer,
    UserSerializer,
)
from .tokens import TenantTokenObtainPairSerializer


class LoginView(TokenObtainPairView):
    """POST email+password on a tenant subdomain → tenant-scoped JWT."""

    serializer_class = TenantTokenObtainPairSerializer
    permission_classes = [AllowAny]


class RegisterView(APIView):
    """Public: create a new workspace (tenant) + its Owner. Base host, no auth."""

    permission_classes = [AllowAny]

    @extend_schema(request=RegisterSerializer, responses=TenantSerializer)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(
            {
                "tenant": TenantSerializer(result["tenant"]).data,
                "owner": UserSerializer(result["user"]).data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(responses=UserSerializer)
@api_view(["GET"])
@permission_classes([IsTenantMember])
def me(request):
    """Current user, their role, and the active tenant."""
    return Response(
        {
            "user": UserSerializer(request.user).data,
            "role": request.role,
            "tenant": TenantSerializer(request.tenant).data,
        }
    )


class MemberViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Manage members of the current tenant. Admins+ can view/manage; granting the
    Owner role is restricted to Owners (enforced in the serializers).
    """

    def get_queryset(self):
        # Memberships of the active tenant only.
        return Membership.objects.filter(
            tenant=self.request.tenant
        ).select_related("user")

    def get_serializer_class(self):
        if self.action == "create":
            return InviteSerializer
        if self.action in ("update", "partial_update"):
            return RoleUpdateSerializer
        return MembershipSerializer

    def get_permissions(self):
        if self.action == "list":
            return [IsTenantMember()]
        return [HasTenantRole(Role.ADMIN)()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        return Response(
            MembershipSerializer(membership).data, status=status.HTTP_201_CREATED
        )
