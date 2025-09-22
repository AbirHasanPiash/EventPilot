from django.urls import path
from . import views

urlpatterns = [
    path("overview/", views.eventpilot_overview, name="eventpilot-overview"),
]
