"""Phase 8 — notes, attachments, search, import/export, bulk, saved views, tags."""
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.accounts.models import Membership, Role, User
from apps.activity.models import AuditLog
from apps.crm.models import CustomFieldDefinition, Lead, Note, SavedView, Tag

pytestmark = pytest.mark.django_db


@pytest.fixture
def acme(make_tenant, make_member):
    tenant = make_tenant("acme")
    for role in (Role.VIEWER, Role.SALES_REP, Role.MANAGER, Role.ADMIN):
        make_member(tenant, role=role)
    return tenant


@pytest.fixture
def globex(make_tenant, make_member):
    tenant = make_tenant("globex")
    make_member(tenant, role=Role.SALES_REP)
    return tenant


# --- 8.8 Tags ----------------------------------------------------------------

def test_create_and_attach_tag(client_for, acme):
    api = client_for(acme, role=Role.SALES_REP)
    tag_id = api.post("/api/tags/", {"name": "VIP", "color": "amber"}).json()["id"]
    lead_id = api.post("/api/leads/", {"name": "Jane", "tags": [tag_id]}).json()["id"]
    detail = api.get(f"/api/leads/{lead_id}/").json()
    assert detail["tags"] == [tag_id]
    assert detail["tags_detail"][0]["name"] == "VIP"


def test_filter_leads_by_tag(client_for, acme):
    api = client_for(acme, role=Role.SALES_REP)
    tag_id = api.post("/api/tags/", {"name": "Hot"}).json()["id"]
    api.post("/api/leads/", {"name": "Tagged", "tags": [tag_id]})
    api.post("/api/leads/", {"name": "Untagged"})
    rows = api.get(f"/api/leads/?tag={tag_id}").json()["results"]
    assert [r["name"] for r in rows] == ["Tagged"]


def test_cannot_use_another_tenants_tag(client_for, acme, globex):
    g_tag = Tag.all_objects.create(tenant=globex, name="Foreign")
    api = client_for(acme, role=Role.SALES_REP)
    resp = api.post("/api/leads/", {"name": "X", "tags": [g_tag.id]})
    assert resp.status_code == 400


# --- 8.1 Notes ---------------------------------------------------------------

def test_add_note_to_lead_sets_author_and_audits(client_for, acme):
    api = client_for(acme, role=Role.SALES_REP)
    lead_id = api.post("/api/leads/", {"name": "Jane"}).json()["id"]
    resp = api.post(
        "/api/notes/",
        {"body": "Called, will follow up", "target_model": "lead", "target_id": lead_id},
    )
    assert resp.status_code == 201
    assert resp.json()["author_email"] == f"{Role.SALES_REP}@acme.crm.local"
    assert AuditLog.objects.filter(tenant=acme, target_type__model="note").exists()


def test_notes_listed_by_target(client_for, acme):
    api = client_for(acme, role=Role.SALES_REP)
    l1 = api.post("/api/leads/", {"name": "A"}).json()["id"]
    l2 = api.post("/api/leads/", {"name": "B"}).json()["id"]
    api.post("/api/notes/", {"body": "n1", "target_model": "lead", "target_id": l1})
    api.post("/api/notes/", {"body": "n2", "target_model": "lead", "target_id": l2})
    rows = api.get(f"/api/notes/?target_model=lead&target_id={l1}").json()["results"]
    assert [n["body"] for n in rows] == ["n1"]


def test_cannot_note_another_tenants_record(client_for, acme, globex):
    other = Lead.all_objects.create(tenant=globex, name="G")
    api = client_for(acme, role=Role.SALES_REP)
    resp = api.post(
        "/api/notes/", {"body": "x", "target_model": "lead", "target_id": other.id}
    )
    assert resp.status_code == 400


# --- 8.2 Attachments ---------------------------------------------------------

def test_upload_attachment_to_lead(client_for, acme):
    api = client_for(acme, role=Role.SALES_REP)
    lead_id = api.post("/api/leads/", {"name": "Jane"}).json()["id"]
    upload = SimpleUploadedFile("contract.txt", b"hello", content_type="text/plain")
    resp = api.post(
        "/api/attachments/",
        {"file": upload, "target_model": "lead", "target_id": lead_id},
        format="multipart",
    )
    assert resp.status_code == 201
    assert resp.json()["filename"] == "contract.txt"


# --- 8.3 Full-text search ----------------------------------------------------

def test_full_text_search(client_for, acme):
    api = client_for(acme, role=Role.SALES_REP)
    api.post("/api/leads/", {"name": "Acme Widgets", "company": "Globex"})
    api.post("/api/leads/", {"name": "Other", "company": "Initech"})
    rows = api.get("/api/leads/?q=globex").json()["results"]
    assert [r["name"] for r in rows] == ["Acme Widgets"]


# --- 8.4 CSV import / export -------------------------------------------------

def test_csv_import(client_for, acme):
    api = client_for(acme, role=Role.SALES_REP)
    csv_bytes = b"name,email,company,status\nAlice,a@x.com,Aing,new\n,,,\nBob,b@x.com,Bing,qualified\n"
    upload = SimpleUploadedFile("leads.csv", csv_bytes, content_type="text/csv")
    resp = api.post("/api/leads/import_csv/", {"file": upload}, format="multipart")
    assert resp.status_code == 200
    assert resp.json()["created"] == 2
    assert len(resp.json()["errors"]) == 1  # the blank row
    assert Lead.all_objects.filter(tenant=acme, name="Alice").exists()


def test_csv_export(client_for, acme):
    api = client_for(acme, role=Role.VIEWER)
    Lead.all_objects.create(tenant=acme, name="Exported", company="Co")
    resp = api.get("/api/leads/export/")
    assert resp.status_code == 200
    assert resp["Content-Type"] == "text/csv"
    assert b"Exported" in resp.content


# --- 8.5 Bulk actions --------------------------------------------------------

def test_bulk_set_status(client_for, acme):
    api = client_for(acme, role=Role.SALES_REP)
    ids = [
        Lead.all_objects.create(tenant=acme, name=f"L{i}").id for i in range(3)
    ]
    resp = api.post(
        "/api/leads/bulk/",
        {"ids": ids, "action": "set_status", "status": "qualified"},
        format="json",
    )
    assert resp.json()["updated"] == 3
    assert Lead.all_objects.filter(tenant=acme, status="qualified").count() == 3


def test_bulk_delete_requires_manager(client_for, acme):
    lead = Lead.all_objects.create(tenant=acme, name="Doomed")
    rep = client_for(acme, role=Role.SALES_REP)
    assert rep.post(
        "/api/leads/bulk/", {"ids": [lead.id], "action": "delete"}, format="json"
    ).status_code == 403
    mgr = client_for(acme, role=Role.MANAGER)
    assert mgr.post(
        "/api/leads/bulk/", {"ids": [lead.id], "action": "delete"}, format="json"
    ).json() == {"deleted": 1}


# --- 8.6 Saved views ---------------------------------------------------------

def test_saved_views_are_per_user(client_for, acme):
    rep = client_for(acme, role=Role.SALES_REP)
    rep.post(
        "/api/saved-views/",
        {"entity": "lead", "name": "My hot leads", "params": {"status": "qualified"}},
        format="json",
    )
    # Another user doesn't see it.
    mgr = client_for(acme, role=Role.MANAGER)
    assert mgr.get("/api/saved-views/").json()["count"] == 0
    assert rep.get("/api/saved-views/").json()["count"] == 1


# --- 8.7 Custom fields -------------------------------------------------------

def test_admin_defines_custom_field_and_lead_stores_value(client_for, acme):
    admin = client_for(acme, role=Role.ADMIN)
    resp = admin.post(
        "/api/custom-fields/",
        {"entity": "lead", "key": "industry", "label": "Industry", "field_type": "text"},
        format="json",
    )
    assert resp.status_code == 201
    lead_id = admin.post(
        "/api/leads/", {"name": "Jane", "custom": {"industry": "tech"}}, format="json"
    ).json()["id"]
    assert admin.get(f"/api/leads/{lead_id}/").json()["custom"]["industry"] == "tech"


def test_sales_rep_cannot_define_custom_field(client_for, acme):
    rep = client_for(acme, role=Role.SALES_REP)
    resp = rep.post(
        "/api/custom-fields/",
        {"entity": "lead", "key": "x", "label": "X"},
        format="json",
    )
    assert resp.status_code == 403
