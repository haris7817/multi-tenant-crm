from django.db import transaction
from rest_framework import serializers

from apps.tenants.models import Domain, Tenant

from .models import Membership, Role, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "full_name", "date_joined"]
        read_only_fields = fields


class MembershipSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    full_name = serializers.CharField(source="user.full_name", read_only=True)

    class Meta:
        model = Membership
        fields = ["id", "email", "full_name", "role", "created_at"]
        read_only_fields = ["id", "email", "full_name", "created_at"]


class RegisterSerializer(serializers.Serializer):
    """
    Public onboarding: create a brand-new tenant plus its first Owner user and
    the ``<slug>.crm.local`` subdomain. Runs on a tenant-less (base) host.
    """

    tenant_name = serializers.CharField(max_length=255)
    slug = serializers.SlugField()
    email = serializers.EmailField()
    full_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8)
    base_domain = serializers.CharField(default="crm.local")

    def validate_slug(self, value):
        if Tenant.objects.filter(slug=value).exists():
            raise serializers.ValidationError("That workspace slug is taken.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("That email already has an account.")
        return value

    @transaction.atomic
    def create(self, validated):
        tenant = Tenant.objects.create(
            name=validated["tenant_name"], slug=validated["slug"]
        )
        Domain.objects.create(
            tenant=tenant, domain=f"{validated['slug']}.{validated['base_domain']}"
        )
        user = User.objects.create_user(
            email=validated["email"],
            password=validated["password"],
            full_name=validated.get("full_name", ""),
        )
        Membership.objects.create(user=user, tenant=tenant, role=Role.OWNER)
        return {"tenant": tenant, "user": user}


class InviteSerializer(serializers.Serializer):
    """Add a member to the CURRENT tenant (creating the user if needed)."""

    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=Role.choices, default=Role.VIEWER)
    full_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=8, required=False)

    def validate_role(self, value):
        # Only an Owner may grant the Owner role.
        if value == Role.OWNER and self.context["request"].role != Role.OWNER:
            raise serializers.ValidationError("Only an Owner can grant the Owner role.")
        return value

    @transaction.atomic
    def create(self, validated):
        tenant = self.context["request"].tenant
        user, created = User.objects.get_or_create(
            email=validated["email"].lower(),
            defaults={"full_name": validated.get("full_name", "")},
        )
        if created:
            if validated.get("password"):
                user.set_password(validated["password"])
            else:
                user.set_unusable_password()
            user.save()
        membership, m_created = Membership.objects.get_or_create(
            user=user, tenant=tenant, defaults={"role": validated["role"]}
        )
        if not m_created:
            raise serializers.ValidationError("User is already a member.")
        return membership


class RoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Membership
        fields = ["role"]

    def validate_role(self, value):
        if value == Role.OWNER and self.context["request"].role != Role.OWNER:
            raise serializers.ValidationError("Only an Owner can grant the Owner role.")
        return value
