from django.urls import path

from . import views

urlpatterns = [
    path("billing/", views.billing_status, name="billing-status"),
    path("billing/plans/", views.plans_view, name="billing-plans"),
    path("billing/checkout/", views.checkout, name="billing-checkout"),
    path("billing/stripe/webhook/", views.stripe_webhook, name="billing-stripe-webhook"),
]
