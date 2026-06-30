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
from .tokens import TenantTokenObtainPairSerializer, issue_tenant_tokens


class LoginView(TokenObtainPairView):
    """POST email+password on a tenant subdomain → tenant-scoped JWT."""

    serializer_class = TenantTokenObtainPairSerializer
    permission_classes = [AllowAny]


class GoogleLoginView(APIView):
    """
    SSO (12.1): exchange a Google ID token for our tenant-scoped JWT.

    The tenant comes from the subdomain; the Google email must already belong to
    a member of that tenant (no silent auto-provisioning).
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        from .google_auth import verify_google_token

        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return Response({"detail": "Unknown tenant."}, status=400)
        credential = request.data.get("credential")
        if not credential:
            return Response({"detail": "Missing 'credential'."}, status=400)

        try:
            info = verify_google_token(credential)
        except Exception:
            return Response({"detail": "Invalid Google token."}, status=401)

        email = (info.get("email") or "").lower()
        if not email or info.get("email_verified") is False:
            return Response({"detail": "Email not verified."}, status=401)

        from .models import User

        user = User.objects.filter(email__iexact=email).first()
        membership = (
            Membership.objects.filter(user=user, tenant=tenant).first()
            if user
            else None
        )
        if not user or not membership:
            return Response(
                {"detail": "No account for this email in this workspace."}, status=403
            )
        return Response(issue_tenant_tokens(user, tenant, membership))


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
        from apps.billing.quota import check_quota

        check_quota(request.tenant, "members")  # plan limit (402 if exceeded)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membership = serializer.save()
        return Response(
            MembershipSerializer(membership).data, status=status.HTTP_201_CREATED
        )
