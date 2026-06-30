"""
Core CRM domain: Leads, a configurable Deal pipeline (Stage), Deals, and Tasks.

Every model inherits ``TenantBaseModel`` so it carries a ``tenant`` FK and is
auto-scoped by ``TenantManager``. ``owner``/``assigned_to`` reference the global
User; they're expected to be members of the same tenant (kept simple here).
"""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models

from apps.tenants.models import TenantBaseModel


class Lead(TenantBaseModel):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        QUALIFIED = "qualified", "Qualified"
        UNQUALIFIED = "unqualified", "Unqualified"
        CONVERTED = "converted", "Converted"

    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    company = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=100, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.NEW
    )
    notes = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_leads",
    )
    # Set by the scheduled flag_stale_leads task when a lead goes cold.
    is_stale = models.BooleanField(default=False)
    # Phase 8: tags (8.8) and per-tenant custom field values (8.7).
    tags = models.ManyToManyField("Tag", blank=True, related_name="leads")
    custom = models.JSONField(default=dict, blank=True)
    notes_rel = GenericRelation(
        "Note", content_type_field="target_type", object_id_field="target_id"
    )
    attachments = GenericRelation(
        "Attachment", content_type_field="target_type", object_id_field="target_id"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class Stage(TenantBaseModel):
    """A column in the tenant's deal pipeline (e.g. Qualification → Won)."""

    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    is_won = models.BooleanField(default=False)
    is_lost = models.BooleanField(default=False)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class Deal(TenantBaseModel):
    title = models.CharField(max_length=255)
    value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    stage = models.ForeignKey(
        Stage, on_delete=models.PROTECT, related_name="deals"
    )
    lead = models.ForeignKey(
        Lead,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="deals",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_deals",
    )
    expected_close_date = models.DateField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField("Tag", blank=True, related_name="deals")
    custom = models.JSONField(default=dict, blank=True)
    notes_rel = GenericRelation(
        "Note", content_type_field="target_type", object_id_field="target_id"
    )
    attachments = GenericRelation(
        "Attachment", content_type_field="target_type", object_id_field="target_id"
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def is_closed(self):
        return self.stage.is_won or self.stage.is_lost


class Task(TenantBaseModel):
    class Priority(models.TextChoices):
        LOW = "low", "Low"
        MEDIUM = "medium", "Medium"
        HIGH = "high", "High"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    is_done = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_tasks",
    )
    lead = models.ForeignKey(
        Lead, null=True, blank=True, on_delete=models.CASCADE, related_name="tasks"
    )
    deal = models.ForeignKey(
        Deal, null=True, blank=True, on_delete=models.CASCADE, related_name="tasks"
    )

    class Meta:
        ordering = ["is_done", "due_date", "-created_at"]

    def __str__(self):
        return self.title


# --- Phase 8: CRM feature depth ---------------------------------------------


class Tag(TenantBaseModel):
    """A colored label that can be attached to leads/deals (8.8)."""

    name = models.CharField(max_length=50)
    color = models.CharField(max_length=20, default="slate")

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"], name="uniq_tag_per_tenant"
            )
        ]

    def __str__(self):
        return self.name


class Note(TenantBaseModel):
    """A free-text note/comment on a record (8.1)."""

    target_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_id = models.PositiveBigIntegerField()
    target = GenericForeignKey("target_type", "target_id")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="notes",
    )
    body = models.TextField()

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["target_type", "target_id"])]

    def __str__(self):
        return f"Note on {self.target_type.model}#{self.target_id}"


class Attachment(TenantBaseModel):
    """A file attached to a record (8.2). Local storage now; S3 later."""

    target_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    target_id = models.PositiveBigIntegerField()
    target = GenericForeignKey("target_type", "target_id")
    file = models.FileField(upload_to="attachments/%Y/%m/")
    filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="attachments",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["target_type", "target_id"])]

    def __str__(self):
        return self.filename


class CustomFieldDefinition(TenantBaseModel):
    """A tenant-defined extra field for a CRM entity (8.7)."""

    class Entity(models.TextChoices):
        LEAD = "lead", "Lead"
        DEAL = "deal", "Deal"

    class FieldType(models.TextChoices):
        TEXT = "text", "Text"
        NUMBER = "number", "Number"
        DATE = "date", "Date"
        SELECT = "select", "Select"

    entity = models.CharField(max_length=10, choices=Entity.choices)
    key = models.SlugField()
    label = models.CharField(max_length=100)
    field_type = models.CharField(
        max_length=10, choices=FieldType.choices, default=FieldType.TEXT
    )
    options = models.JSONField(default=list, blank=True)  # for SELECT

    class Meta:
        ordering = ["entity", "label"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "entity", "key"], name="uniq_customfield_per_tenant"
            )
        ]

    def __str__(self):
        return f"{self.entity}.{self.key}"


class SavedView(TenantBaseModel):
    """A user's saved filter/search/sort for an entity list (8.6)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_views"
    )
    entity = models.CharField(max_length=20)  # e.g. "lead"
    name = models.CharField(max_length=100)
    params = models.JSONField(default=dict, blank=True)  # query params snapshot

    class Meta:
        ordering = ["entity", "name"]

    def __str__(self):
        return f"{self.entity}: {self.name}"
