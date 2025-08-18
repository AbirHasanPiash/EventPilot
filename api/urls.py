from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import UserProfileViewSet, UserViewSet
from events.views import EventViewSet, EventCategoryViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'profile', UserProfileViewSet, basename='profile')
router.register(r'events', EventViewSet, basename='event')
router.register(r'categories', EventCategoryViewSet, basename='event-category')

urlpatterns = [
    path('', include(router.urls)),
    path("events/", include("events.urls")),
]
