import csv
import io

from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.accounts.models import ROLE_LEVEL, Role
from apps.activity.models import AuditLog
from apps.common.viewsets import TenantModelViewSet

from .filters import DealFilter, LeadFilter, TaskFilter
from .models import (
    Attachment,
    CustomFieldDefinition,
    Deal,
    Lead,
    Note,
    SavedView,
    Stage,
    Tag,
    Task,
)
from .serializers import (
    AttachmentSerializer,
    BulkActionSerializer,
    CustomFieldDefinitionSerializer,
    DealMoveSerializer,
    DealSerializer,
    LeadImportSerializer,
    LeadSerializer,
    NoteSerializer,
    SavedViewSerializer,
    StageSerializer,
    TagSerializer,
    TaskSerializer,
)
from .targets import TARGET_MODELS, resolve_target


class LeadViewSet(TenantModelViewSet):
    # Use the UNSCOPED manager here; TenantModelViewSet.get_queryset applies the
    # tenant filter per request (see note there).
    queryset = Lead.all_objects.all().prefetch_related("tags")
    serializer_class = LeadSerializer
    filterset_class = LeadFilter
    search_fields = ["name", "email", "company"]
    ordering_fields = ["created_at", "name", "status"]

    def get_queryset(self):
        qs = super().get_queryset()
        # 8.3 — Postgres full-text search across the lead's key text fields.
        q = self.request.query_params.get("q")
        if q:
            qs = qs.annotate(
                search=SearchVector("name", "company", "email", "notes")
            ).filter(search=SearchQuery(q))
        # 8.8 — filter by tag id.
        tag = self.request.query_params.get("tag")
        if tag:
            qs = qs.filter(tags__id=tag)
        return qs

    @extend_schema(request=LeadImportSerializer)
    @action(detail=False, methods=["post"], parser_classes=[MultiPartParser, FormParser])
    def import_csv(self, request):
        """8.4 — bulk import leads from a CSV with columns name,email,company,status."""
        serializer = LeadImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        text = serializer.validated_data["file"].read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        created, errors = 0, []
        valid_status = set(Lead.Status.values)
        for line, row in enumerate(reader, start=2):
            name = (row.get("name") or "").strip()
            if not name:
                errors.append({"row": line, "error": "missing name"})
                continue
            status = (row.get("status") or "new").strip().lower()
            Lead.all_objects.create(
                tenant=request.tenant,
                name=name,
                email=(row.get("email") or "").strip(),
                company=(row.get("company") or "").strip(),
                status=status if status in valid_status else Lead.Status.NEW,
                owner=request.user,
            )
            created += 1
        return Response({"created": created, "errors": errors})

    @action(detail=False, methods=["get"])
    def export(self, request):
        """8.4 — export the (filtered) lead list as CSV."""
        qs = self.filter_queryset(self.get_queryset())
        resp = HttpResponse(content_type="text/csv")
        resp["Content-Disposition"] = 'attachment; filename="leads.csv"'
        writer = csv.writer(resp)
        writer.writerow(["name", "email", "company", "status", "owner"])
        for lead in qs:
            writer.writerow(
                [lead.name, lead.email, lead.company, lead.status,
                 lead.owner.email if lead.owner else ""]
            )
        return resp

    @extend_schema(request=BulkActionSerializer)
    @action(detail=False, methods=["post"])
    def bulk(self, request):
        """8.5 — apply one action to many leads at once (tenant-scoped)."""
        serializer = BulkActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        qs = self.get_queryset().filter(id__in=data["ids"])  # already tenant-scoped
        op = data["action"]

        if op == "delete":
            if ROLE_LEVEL[request.role] < ROLE_LEVEL[Role.MANAGER]:
                return Response({"detail": "Delete requires Manager+."}, status=403)
            count = qs.count()
            qs.delete()
            return Response({"deleted": count})
        if op == "set_status":
            n = qs.update(status=data["status"])
            return Response({"updated": n})
        if op == "set_owner":
            n = qs.update(owner_id=data.get("owner"))
            return Response({"updated": n})
        if op == "add_tag":
            tag = Tag.all_objects.filter(pk=data.get("tag"), tenant=request.tenant).first()
            if not tag:
                return Response({"detail": "Unknown tag."}, status=400)
            for lead in qs:
                lead.tags.add(tag)
            return Response({"tagged": qs.count()})
        return Response({"detail": "Unknown action."}, status=400)


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


# --- Phase 8 viewsets -------------------------------------------------------


class TagViewSet(TenantModelViewSet):
    """8.8 — manage tags (Sales Rep+ to create)."""

    queryset = Tag.all_objects.all()
    serializer_class = TagSerializer
    ordering_fields = ["name"]


class _TargetScopedViewSet(TenantModelViewSet):
    """Shared base for Note/Attachment — filtered by ?target_model=&target_id=."""

    def get_queryset(self):
        qs = super().get_queryset()
        tm = self.request.query_params.get("target_model")
        tid = self.request.query_params.get("target_id")
        if tm and tid:
            model = TARGET_MODELS.get(tm.lower())
            if model:
                ct = ContentType.objects.get_for_model(model)
                qs = qs.filter(target_type=ct, target_id=tid)
        return qs

    def _save_with_target(self, serializer, **extra):
        target_id = self.request.data.get("target_id")
        ct, obj = resolve_target(
            self.request.tenant, self.request.data.get("target_model"), target_id
        )
        instance = serializer.save(
            tenant=self.request.tenant,
            target_type=ct,
            target_id=obj.pk,
            **extra,
        )
        self._audit(AuditLog.Action.CREATED, instance)
        return instance


class NoteViewSet(_TargetScopedViewSet):
    """8.1 — notes/comments on a Lead or Deal."""

    queryset = Note.all_objects.select_related("author", "target_type")
    serializer_class = NoteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        note = self._save_with_target(serializer, author=request.user)
        return Response(self.get_serializer(note).data, status=201)


class AttachmentViewSet(_TargetScopedViewSet):
    """8.2 — file attachments on a Lead or Deal."""

    queryset = Attachment.all_objects.select_related("target_type")
    serializer_class = AttachmentSerializer
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        upload = serializer.validated_data["file"]
        att = self._save_with_target(
            serializer, uploaded_by=request.user, filename=upload.name
        )
        return Response(self.get_serializer(att).data, status=201)


class CustomFieldDefinitionViewSet(TenantModelViewSet):
    """8.7 — tenant admins define extra fields per entity."""

    queryset = CustomFieldDefinition.all_objects.all()
    serializer_class = CustomFieldDefinitionSerializer
    write_role = Role.ADMIN
    delete_role = Role.ADMIN
    filterset_fields = ["entity"]


class SavedViewViewSet(TenantModelViewSet):
    """8.6 — a user's saved filters. Personal: any member manages their own."""

    queryset = SavedView.all_objects.all()
    serializer_class = SavedViewSerializer
    write_role = Role.VIEWER
    delete_role = Role.VIEWER
    audit = False
    filterset_fields = ["entity"]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant, user=self.request.user)
