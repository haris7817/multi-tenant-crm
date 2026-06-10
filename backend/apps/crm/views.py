from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import Role
from apps.activity.models import AuditLog
from apps.common.viewsets import TenantModelViewSet

from .filters import DealFilter, LeadFilter, TaskFilter
from .models import Deal, Lead, Stage, Task
from .serializers import (
    DealMoveSerializer,
    DealSerializer,
    LeadSerializer,
    StageSerializer,
    TaskSerializer,
)


class LeadViewSet(TenantModelViewSet):
    # Use the UNSCOPED manager here; TenantModelViewSet.get_queryset applies the
    # tenant filter per request (see note there).
    queryset = Lead.all_objects.all()
    serializer_class = LeadSerializer
    filterset_class = LeadFilter
    search_fields = ["name", "email", "company"]
    ordering_fields = ["created_at", "name", "status"]


class StageViewSet(TenantModelViewSet):
    """Pipeline configuration — managing stages is a Manager+ action."""

    queryset = Stage.all_objects.all()
    serializer_class = StageSerializer
    write_role = Role.MANAGER
    ordering_fields = ["order", "name"]


class DealViewSet(TenantModelViewSet):
    queryset = Deal.all_objects.select_related("stage", "lead", "owner").all()
    serializer_class = DealSerializer
    filterset_class = DealFilter
    search_fields = ["title"]
    ordering_fields = ["created_at", "value", "expected_close_date"]

    @extend_schema(request=DealMoveSerializer, responses=DealSerializer)
    @action(detail=True, methods=["post"])
    def move(self, request, pk=None):
        """Move a deal to a stage; stamp closed_at when it enters a won/lost stage."""
        deal = self.get_object()
        serializer = DealMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stage = serializer.validated_data["stage"]
        if stage.tenant_id != request.tenant.id:
            return Response({"detail": "Stage not in this tenant."}, status=400)

        deal.stage = stage
        deal.closed_at = timezone.now() if (stage.is_won or stage.is_lost) else None
        deal.save()
        self._audit(AuditLog.Action.UPDATED, deal, changes={"stage": [None, stage.name]})

        if stage.is_won:
            # Notify the owner once the change is durably committed.
            from apps.emails.tasks import send_deal_won_email

            transaction.on_commit(lambda: send_deal_won_email.delay(deal.id))

        return Response(DealSerializer(deal, context=self.get_serializer_context()).data)

    @extend_schema(responses=DealSerializer(many=True))
    @action(detail=False, methods=["get"])
    def pipeline(self, request):
        """Deals grouped by stage — the data behind a kanban board."""
        stages = Stage.objects.all()
        ctx = self.get_serializer_context()
        board = [
            {
                "stage": StageSerializer(stage).data,
                "deals": DealSerializer(stage.deals.all(), many=True, context=ctx).data,
            }
            for stage in stages
        ]
        return Response(board)


class TaskViewSet(TenantModelViewSet):
    queryset = Task.all_objects.all()
    serializer_class = TaskSerializer
    filterset_class = TaskFilter
    search_fields = ["title", "description"]
    ordering_fields = ["due_date", "created_at", "priority"]
