from django.urls import path
from .views import UserDashboardView, OrganizerDashboardView, AdminDashboardView, OrganizerRequestCreateView
from .views import OrganizerRequestUpdateView, OrganizerRequestListView, OrganizerRequestStatusView, OrganizerRequestDetailView

urlpatterns = [
    path("user/", UserDashboardView.as_view(), name="user-dashboard"),
    path("organizer", OrganizerDashboardView.as_view(), name="organizer-dashboard"),
    path("admin", AdminDashboardView.as_view(), name="admin-dashboard"),
    path('request-organizer/', OrganizerRequestCreateView.as_view(), name='request-organizer'),
    path("request-organizer/<int:id>/", OrganizerRequestDetailView.as_view(), name="organizer-request-detail"),
    path('request-organizer/list/', OrganizerRequestListView.as_view(), name='list-organizer-requests'),
    path('request-organizer/<int:pk>/update/', OrganizerRequestUpdateView.as_view(), name='approve-organizer-request'),
    path("request-organizer/status/", OrganizerRequestStatusView.as_view(), name="request-organizer-status"),

]
