from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("leads", views.LeadViewSet, basename="lead")
router.register("stages", views.StageViewSet, basename="stage")
router.register("deals", views.DealViewSet, basename="deal")
router.register("tasks", views.TaskViewSet, basename="task")

urlpatterns = router.urls
