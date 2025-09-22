from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Prefetch
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Event, EventCategory, EventReaction, EventSchedule
from .serializers import EventSerializer, EventCategorySerializer, EventScheduleSerializer
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


class EventScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = EventScheduleSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        event_id = self.kwargs.get("event_pk")
        return EventSchedule.objects.filter(event_id=event_id).select_related("event")

    def perform_create(self, serializer):
        event_id = self.kwargs.get("event_pk")
        event = Event.objects.get(pk=event_id)

        user = self.request.user
        if user != event.organizer and not user.is_staff:
            raise PermissionDenied("You can only add schedules to your own events.")

        serializer.save(event=event)

    @action(detail=False, methods=["post"], url_path="bulk")
    def bulk_create(self, request, event_pk=None):
        """
        Create multiple schedules in one request.
        Expecting request body: {"schedules": [ {start_datetime, end_datetime, title, agenda}, ... ]}
        """
        event = get_object_or_404(Event, pk=event_pk)
        user = request.user
        if user != event.organizer and not user.is_staff:
            raise PermissionDenied("You can only add schedules to your own events.")

        schedules_data = request.data.get("schedules")
        if not isinstance(schedules_data, list) or not schedules_data:
            return Response({"detail": "schedules must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)

        # Inject event id into each incoming dict so serializer validation succeeds
        for item in schedules_data:
            # Make sure we don't override if the frontend included it
            item.setdefault("event", event.pk)

        serializer = self.get_serializer(data=schedules_data, many=True)
        serializer.is_valid(raise_exception=True)

        created_instances = []
        with transaction.atomic():
            # Create each item (use create() so auto_now fields, signals, and DB constraints run)
            for validated in serializer.validated_data:
                # validated may contain 'event' as an Event instance (if serializer resolved it)
                validated.pop("event", None)  # we'll pass event explicitly
                created = EventSchedule.objects.create(event=event, **validated)
                created_instances.append(created)

        out_serializer = EventScheduleSerializer(created_instances, many=True, context={"request": request})
        return Response(out_serializer.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        schedule = self.get_object()
        user = self.request.user

        if user != schedule.event.organizer and not user.is_staff:
            raise PermissionDenied("You can only update schedules for your own events.")

        serializer.save()

    def perform_destroy(self, instance):
        user = self.request.user

        if user != instance.event.organizer and not user.is_staff:
            raise PermissionDenied("You can only delete schedules for your own events.")

        instance.delete()