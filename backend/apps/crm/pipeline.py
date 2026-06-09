"""Default deal pipeline created for every new tenant."""
from .models import Stage

DEFAULT_STAGES = [
    {"name": "New", "order": 1},
    {"name": "Qualified", "order": 2},
    {"name": "Proposal", "order": 3},
    {"name": "Negotiation", "order": 4},
    {"name": "Won", "order": 5, "is_won": True},
    {"name": "Lost", "order": 6, "is_lost": True},
]


def create_default_pipeline(tenant):
    """Idempotently create the standard stages for ``tenant``."""
    for spec in DEFAULT_STAGES:
        Stage.all_objects.get_or_create(
            tenant=tenant, name=spec["name"], defaults=spec
        )
