from django_filters import rest_framework as filters

from .models import Deal, Lead, Task


class LeadFilter(filters.FilterSet):
    class Meta:
        model = Lead
        fields = {
            "status": ["exact"],
            "owner": ["exact"],
            "source": ["exact"],
        }


class DealFilter(filters.FilterSet):
    min_value = filters.NumberFilter(field_name="value", lookup_expr="gte")
    max_value = filters.NumberFilter(field_name="value", lookup_expr="lte")

    class Meta:
        model = Deal
        fields = {
            "stage": ["exact"],
            "owner": ["exact"],
            "lead": ["exact"],
        }


class TaskFilter(filters.FilterSet):
    class Meta:
        model = Task
        fields = {
            "is_done": ["exact"],
            "priority": ["exact"],
            "assigned_to": ["exact"],
            "lead": ["exact"],
            "deal": ["exact"],
        }
