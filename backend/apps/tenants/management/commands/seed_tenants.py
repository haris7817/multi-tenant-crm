"""
Seed demo tenants and users so the app is usable immediately in local dev.

Creates two tenants (acme, globex), each with one user per role. Every demo
user's password is ``password123``.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.accounts.models import Membership, Role
from apps.crm.models import Deal, Lead, Stage
from apps.crm.pipeline import create_default_pipeline
from apps.tenants.models import Domain, Tenant

User = get_user_model()

DEMO_TENANTS = [
    ("Acme Inc", "acme", "acme.crm.local"),
    ("Globex Corp", "globex", "globex.crm.local"),
]

DEMO_PASSWORD = "password123"


class Command(BaseCommand):
    help = "Create demo tenants (acme, globex) with one user per role."

    def handle(self, *args, **options):
        for name, slug, domain in DEMO_TENANTS:
            tenant, created = Tenant.objects.get_or_create(
                slug=slug, defaults={"name": name}
            )
            Domain.objects.get_or_create(
                domain=domain, defaults={"tenant": tenant, "is_primary": True}
            )
            self.stdout.write(f"{'Created' if created else 'Exists'}: {name} -> {domain}")

            for role in Role.values:
                email = f"{role}@{slug}.crm.local"
                user, u_created = User.objects.get_or_create(
                    email=email, defaults={"full_name": f"{role.title()} ({slug})"}
                )
                if u_created:
                    user.set_password(DEMO_PASSWORD)
                    user.save()
                Membership.objects.get_or_create(
                    user=user, tenant=tenant, defaults={"role": role}
                )
                self.stdout.write(f"  - {email} [{role}]")

            self._seed_crm(tenant, slug)

        self.stdout.write(
            self.style.SUCCESS(f"Demo data ready. All passwords: {DEMO_PASSWORD!r}")
        )

    def _seed_crm(self, tenant, slug):
        create_default_pipeline(tenant)
        owner = Membership.objects.get(tenant=tenant, role=Role.OWNER).user
        new_stage = Stage.all_objects.get(tenant=tenant, name="New")
        won_stage = Stage.all_objects.get(tenant=tenant, name="Won")

        for i in range(1, 4):
            lead, _ = Lead.all_objects.get_or_create(
                tenant=tenant,
                name=f"{slug.title()} Lead {i}",
                defaults={
                    "email": f"lead{i}@{slug}.example.com",
                    "company": f"{slug.title()} Prospect {i}",
                    "owner": owner,
                },
            )
            Deal.all_objects.get_or_create(
                tenant=tenant,
                title=f"{slug.title()} Deal {i}",
                defaults={
                    "value": 1000 * i,
                    "stage": won_stage if i == 1 else new_stage,
                    "lead": lead,
                    "owner": owner,
                },
            )
        self.stdout.write(f"  + seeded pipeline, leads & deals for {slug}")
