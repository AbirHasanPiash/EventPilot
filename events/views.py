from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied
from .models import Event, EventCategory
from .serializers import EventSerializer, EventCategorySerializer
from django_filters.rest_framework import DjangoFilterBackend
from .filters import EventFilter


class EventCategoryViewSet(viewsets.ModelViewSet):
    queryset = EventCategory.objects.all()
    serializer_class = EventCategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['name', 'description']
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        user = self.request.user
        if user.role not in ['organizer', 'admin'] and not user.is_staff:
            raise PermissionDenied("Only organizers and admins can create categories.")
        serializer.save()

    def perform_update(self, serializer):
        user = self.request.user
        if user.role not in ['organizer', 'admin'] and not user.is_staff:
            raise PermissionDenied("Only organizers and admins can update categories.")
        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user
        if user.role not in ['organizer', 'admin'] and not user.is_staff:
            raise PermissionDenied("Only organizers and admins can delete categories.")
        instance.delete()



class EventViewSet(viewsets.ModelViewSet):
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filterset_class = EventFilter
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    search_fields = ['title', 'venue', 'tags']
   
    def get_queryset(self):
        return Event.objects.select_related('organizer', 'category')
        
    def perform_create(self, serializer):
        if self.request.user.role != 'organizer' and not self.request.user.is_staff:
            raise PermissionDenied("Only organizers and staff can create events.")
        serializer.save(organizer=self.request.user)

    def perform_update(self, serializer):
        event = self.get_object()
        if self.request.user != event.organizer and not self.request.user.is_staff:
            raise PermissionDenied("You can only update your own events.")
        serializer.save()

    def perform_destroy(self, instance):
        if self.request.user != instance.organizer and not self.request.user.is_staff:
            raise PermissionDenied("You can only delete your own events.")
        instance.delete()
