from django.urls import path

from . import views

urlpatterns = [
    path("tenant/", views.current_tenant, name="current-tenant"),
]
