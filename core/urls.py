from django.urls import path

from core import views


urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("", views.dashboard, name="dashboard"),
    path("api/availability/", views.availability, name="availability"),
    path("api/requests/create/", views.create_request_view, name="create_request"),
    path("api/requests/<int:booking_id>/decide/", views.decide_request_view, name="decide_request"),
]
