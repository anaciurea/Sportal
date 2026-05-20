from django.urls import path

from core import views


urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("", views.dashboard, name="dashboard"),
    path("resources/<int:resource_id>/", views.resource_detail, name="resource_detail"),
    path("stats/", views.stats_view, name="stats"),
    path("api/availability/", views.availability, name="availability"),
    path("api/calendar/", views.calendar_api, name="calendar_api"),
    path("api/requests/create/", views.create_request_view, name="create_request"),
    path("api/requests/<int:booking_id>/decide/", views.decide_request_view, name="decide_request"),
    path("api/requests/<int:booking_id>/review/", views.submit_review_view, name="submit_review"),
    path("api/resources/<int:resource_id>/reviews/", views.resource_reviews_api, name="resource_reviews"),
]
