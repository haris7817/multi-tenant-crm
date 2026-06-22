from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("webhooks", views.WebhookEndpointViewSet, basename="webhook")
router.register(
    "webhook-deliveries", views.WebhookDeliveryViewSet, basename="webhook-delivery"
)
router.register(
    "inbound-endpoints", views.InboundEndpointViewSet, basename="inbound-endpoint"
)

urlpatterns = router.urls
