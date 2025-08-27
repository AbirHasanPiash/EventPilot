from django.urls import path
from .views import UserDashboardView, OrganizerDashboardView, AdminDashboardView

urlpatterns = [
    path("user/", UserDashboardView.as_view(), name="user-dashboard"),
    path("organizer", OrganizerDashboardView.as_view(), name="organizer-dashboard"),
    path("admin", AdminDashboardView.as_view(), name="admin-dashboard"),
]
