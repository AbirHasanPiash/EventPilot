from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Prefetch
from django.db import transaction

from .models import Event, EventCategory, EventReaction
from .serializers import EventSerializer, EventCategorySerializer
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
        qs = Event.objects.select_related('organizer', 'category')

        # Annotate counts
        qs = qs.annotate(
            attending_count=Count(
                "reactions",
                filter=Q(reactions__status=EventReaction.ATTENDING),
                distinct=True,
            ),
            interested_count=Count(
                "reactions",
                filter=Q(reactions__status=EventReaction.INTERESTED),
                distinct=True,
            ),
        )

        # Prefetch current user's reaction
        user = getattr(self.request, "user", None)
        if user and user.is_authenticated:
            qs = qs.prefetch_related(
                Prefetch(
                    "reactions",
                    queryset=EventReaction.objects.filter(user=user),
                    to_attr="my_reaction_list",
                )
            )

        return qs

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

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticatedOrReadOnly])
    def react(self, request, pk=None):
        """
        POST /api/events/{id}/react/
        Body: {"status": "interested" | "attending" | "none"}
        """
        event = self.get_object()
        status_in = (request.data or {}).get("status")

        if status_in not in ["interested", "attending", "none"]:
            return Response({"detail": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

        if status_in == "attending" and event.is_full():
            return Response(
                {"detail": "Event is full; cannot mark as attending."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            if status_in == "none":
                EventReaction.objects.filter(event=event, user=request.user).delete()
            else:
                EventReaction.objects.update_or_create(
                    event=event,
                    user=request.user,
                    defaults={"status": status_in},
                )

        # Re-fetch event so counts + reaction are fresh
        refreshed = self.get_queryset().filter(pk=event.pk).first()
        serializer = self.get_serializer(refreshed)
        return Response(serializer.data, status=status.HTTP_200_OK)
