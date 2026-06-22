from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("connections", views.ConnectionViewSet, basename="connection")

urlpatterns = router.urls
