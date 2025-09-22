from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from users.views import UserProfileViewSet, UserViewSet
from events.views import EventViewSet, EventCategoryViewSet, EventScheduleViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'events', EventViewSet, basename='event')
router.register(r'categories', EventCategoryViewSet, basename='event-category')

events_router = NestedDefaultRouter(router, r"events", lookup="event")
events_router.register(r"schedules", EventScheduleViewSet, basename="event-schedules")


urlpatterns = [
    path('', include(router.urls)),
    path('', include(events_router.urls)),
    path("", include("overview.urls")),
    path("events/", include("events.urls")),
    path("dashboard/", include("dashboard.urls")),
]
