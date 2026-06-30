from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("leads", views.LeadViewSet, basename="lead")
router.register("stages", views.StageViewSet, basename="stage")
router.register("deals", views.DealViewSet, basename="deal")
router.register("tasks", views.TaskViewSet, basename="task")
# Phase 8
router.register("tags", views.TagViewSet, basename="tag")
router.register("notes", views.NoteViewSet, basename="note")
router.register("attachments", views.AttachmentViewSet, basename="attachment")
router.register(
    "custom-fields", views.CustomFieldDefinitionViewSet, basename="customfield"
)
router.register("saved-views", views.SavedViewViewSet, basename="savedview")

urlpatterns = router.urls
