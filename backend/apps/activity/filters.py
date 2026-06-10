from django_filters import rest_framework as filters

from .models import AuditLog


class AuditLogFilter(filters.FilterSet):
    # Filter a record's timeline by model name, e.g. ?target_model=lead&target_id=5
    target_model = filters.CharFilter(
        field_name="target_type__model", lookup_expr="iexact"
    )

    class Meta:
        model = AuditLog
        fields = {
            "action": ["exact"],
            "actor": ["exact"],
            "target_id": ["exact"],
        }
