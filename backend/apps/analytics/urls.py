from django.urls import path

from . import views

urlpatterns = [
    path("analytics/summary/", views.summary, name="analytics-summary"),
    path("analytics/deals-by-stage/", views.deals_by_stage, name="analytics-deals-by-stage"),
    path("analytics/leads-by-status/", views.leads_by_status, name="analytics-leads-by-status"),
    path("analytics/leads-over-time/", views.leads_over_time, name="analytics-leads-over-time"),
    path("analytics/revenue-forecast/", views.revenue_forecast, name="analytics-revenue-forecast"),
]
