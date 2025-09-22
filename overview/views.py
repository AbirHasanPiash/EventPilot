from django.utils.timezone import now
from django.db.models import Count, Avg, Q, F
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import ExpressionWrapper, FloatField

from events.models import Event, EventCategory, EventReaction
from users.models import User


@api_view(["GET"])
@permission_classes([AllowAny])
def eventpilot_overview(request):
    # Stats
    total_events = Event.objects.filter(status="published").count()
    upcoming_events = Event.objects.filter(status="published", start_time__gte=now()).count()
    registered_users = User.objects.count()
    total_attendees = EventReaction.objects.filter(status=EventReaction.ATTENDING).count()

    # Active organizers
    active_organizers = (
        User.objects.filter(role="organizer", organized_events__status="published")
        .distinct()
        .count()
    )

    # Popular categories
    popular_categories = (
        EventCategory.objects.annotate(event_count=Count("events", filter=Q(events__status="published")))
        .filter(event_count__gt=0)
        .order_by("-event_count")[:5]
        .values("name", "event_count")
    )

    # Featured organizers (by event count)
    featured_organizers = (
        User.objects.filter(role="organizer")
        .annotate(event_count=Count("organized_events", filter=Q(organized_events__status="published")))
        .filter(event_count__gt=0)
        .order_by("-event_count")[:3]
        .values("id", "first_name", "last_name", "email", "event_count")
    )

    # Latest events
    latest_events = (
        Event.objects.filter(status="published")
        .order_by("-created_at")[:5]
        .values("id", "title", "start_time", "end_time", "venue", "capacity")
    )

    # Attendance rate & average capacity
    capacity_stats = (
    Event.objects.filter(status="published", capacity__gt=0)
    .annotate(
        attendee_count=Count("reactions", filter=Q(reactions__status=EventReaction.ATTENDING)),
        attendance_rate=ExpressionWrapper(
            F("attendee_count") * 1.0 / F("capacity"),
            output_field=FloatField(),
        ),
    )
    .aggregate(
        avg_capacity=Avg("capacity"),
        avg_attendance_rate=Avg("attendance_rate"),
    )
)

    response = {
        "stats": {
            "total_events": total_events,
            "upcoming_events": upcoming_events,
            "registered_users": registered_users,
            "total_attendees": total_attendees,
            "active_organizers": active_organizers,
            "avg_event_capacity": capacity_stats.get("avg_capacity") or 0,
            "avg_attendance_rate": round(capacity_stats.get("avg_attendance_rate") or 0, 2),
        },
        "popular_categories": list(popular_categories),
        "latest_events": list(latest_events),
        "featured_organizers": list(featured_organizers),
    }

    return Response(response)
