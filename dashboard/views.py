# views.py
from django.utils import timezone
from django.db.models import Prefetch
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from events.models import EventReaction, Event, EventCategory
from events.serializers import EventSerializer
from .serializers import OrganizerDashboardSerializer
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Count, Q, F
from django.db.models.functions import TruncMonth, TruncYear
import calendar
from collections import OrderedDict
from users.models import User
from .serializers import OrganizerRequestSerializer
from rest_framework import generics, permissions
from .models import OrganizerRequest
from rest_framework import serializers



class UserDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        now = timezone.now()
        # day bounds
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59, microsecond=999999)
        today_date = today_start.date()

        # Prefetch only THIS user's reaction into `my_reaction_list`.
        user_reactions = EventReaction.objects.filter(user=user)

        # 1 query for events (with organizer+category joined), plus 1 prefetch for reactions.
        user_events_qs = (
            Event.objects.filter(reactions__user=user)
            .select_related("organizer", "category")
            .prefetch_related(
                Prefetch("reactions", queryset=user_reactions, to_attr="my_reaction_list")
            )
            .distinct()
        )

        # Evaluate ONCE and bucket in Python (prevents repeated prefetch queries).
        user_events = list(user_events_qs)

        # Buckets
        today_attending = []
        today_interested = []
        ongoing = []
        upcoming_attending = []
        upcoming_interested = []
        archived = []

        # Helper to read user's reaction status without hitting DB
        def status_of(ev):
            # my_reaction_list exists (prefetched); either [] or [EventReaction]
            return ev.my_reaction_list[0].status if getattr(ev, "my_reaction_list", []) else None

        for ev in user_events:
            s = status_of(ev)

            is_ongoing = ev.start_time <= now <= ev.end_time
            if is_ongoing:
                ongoing.append(ev)
                continue  # exclusive buckets

            # today but NOT ongoing
            is_today = (ev.start_time.date() == today_date) or (ev.end_time.date() == today_date)
            if is_today:
                if s == EventReaction.ATTENDING:
                    today_attending.append(ev)
                elif s == EventReaction.INTERESTED:
                    today_interested.append(ev)
                # if no status, skip (shouldn't happen because base qs filters by reactions__user)
                continue

            # upcoming after today end
            if ev.start_time > today_end:
                if s == EventReaction.ATTENDING:
                    upcoming_attending.append(ev)
                elif s == EventReaction.INTERESTED:
                    upcoming_interested.append(ev)
                continue

            # archived before today start
            if ev.end_time < today_start:
                archived.append(ev)
                continue
            # Any leftovers are neither today/upcoming/archived; they’re multi-day in the past-but-not-before-today_start,
            # but we already handled ongoing==False; usually this means ended earlier today (caught by 'today')
            # or spans earlier days but ends today (also 'today'). So typically no leftovers.

        return Response({
            "today": {
                "attending": EventSerializer(today_attending, many=True, context={"request": request}).data,
                "interested": EventSerializer(today_interested, many=True, context={"request": request}).data,
            },
            "ongoing": EventSerializer(ongoing, many=True, context={"request": request}).data,
            "upcoming": {
                "attending": EventSerializer(upcoming_attending, many=True, context={"request": request}).data,
                "interested": EventSerializer(upcoming_interested, many=True, context={"request": request}).data,
            },
            "archived": EventSerializer(archived, many=True, context={"request": request}).data,
        })




class OrganizerDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != "organizer":
            return Response({"detail": "Only organizers can access this endpoint."}, status=403)

        events_qs = Event.objects.filter(organizer=user)

        # ---- All-time totals ----
        total_events = events_qs.filter(start_time__lte=now()).count()
        total_attendees = EventReaction.objects.filter(
            event__organizer=user,
            event__start_time__lte=now(),
            status=EventReaction.ATTENDING
        ).count()

        # ---- Last 12 months timeline ----
        one_year_ago = now() - timedelta(days=365)
        monthly_data = (
            events_qs.filter(start_time__gte=one_year_ago, start_time__lte=now())
            .annotate(month=TruncMonth("start_time"))
            .values("month")
            .annotate(
                events_count=Count("id"),
                attendees_count=Count(
                    "reactions",
                    filter=Q(reactions__status=EventReaction.ATTENDING),
                ),
            )
            .order_by("month")
        )

        # Build skeleton for last 12 months
        monthly_results = OrderedDict()
        for i in range(12):
            dt = (now().replace(day=1) - timedelta(days=30 * i))
            key = (dt.year, dt.month)
            monthly_results[key] = {
                "month": calendar.month_name[dt.month],
                "year": dt.year,
                "events": 0,
                "attendees": 0,
            }

        for row in monthly_data:
            key = (row["month"].year, row["month"].month)
            if key in monthly_results:
                monthly_results[key].update({
                    "events": row["events_count"],
                    "attendees": row["attendees_count"],
                })

        final_monthly_stats = list(monthly_results.values())[::-1]  # chronological order

        # ---- Last 5 years timeline ----
        five_years_ago = now() - timedelta(days=365 * 5)
        yearly_data = (
            events_qs.filter(start_time__gte=five_years_ago, start_time__lte=now())
            .annotate(year=TruncYear("start_time"))
            .values("year")
            .annotate(
                events_count=Count("id"),
                attendees_count=Count(
                    "reactions",
                    filter=Q(reactions__status=EventReaction.ATTENDING),
                ),
            )
            .order_by("year")
        )

        # Build skeleton for last 5 years
        current_year = now().year
        yearly_results = {
            y: {"year": y, "events": 0, "attendees": 0}
            for y in range(current_year - 4, current_year + 1)
        }

        for row in yearly_data:
            y = row["year"].year
            if y in yearly_results:
                yearly_results[y].update({
                    "events": row["events_count"],
                    "attendees": row["attendees_count"],
                })

        final_yearly_stats = list(yearly_results.values())

        # ---- Final response ----
        data = {
            "total_events": total_events,
            "total_attendees": total_attendees,
            "monthly_stats": final_monthly_stats,
            "yearly_stats": final_yearly_stats,
        }

        serializer = OrganizerDashboardSerializer(data)
        return Response(serializer.data)



class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != "admin":
            return Response({"detail": "Only admins can access this endpoint."}, status=403)

        # --- Totals ---
        total_users = User.objects.count()
        total_events = Event.objects.count()
        total_attendees = EventReaction.objects.filter(
            status=EventReaction.ATTENDING
        ).count()

        # --- Breakdown ---
        users_by_role = User.objects.values("role").annotate(count=Count("id"))
        events_by_status = Event.objects.values("status").annotate(count=Count("id"))
        events_by_category = (
            EventCategory.objects.annotate(count=Count("events"))
            .values("name", "count")
        )

        # --- Time ranges ---
        one_year_ago = now() - timedelta(days=365)
        five_years_ago = now() - timedelta(days=365 * 5)

        # --- Trends: Users ---
        monthly_users = (
            User.objects.filter(date_joined__gte=one_year_ago)
            .annotate(month=TruncMonth("date_joined"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        yearly_users = (
            User.objects.filter(date_joined__gte=five_years_ago)
            .annotate(year=TruncYear("date_joined"))
            .values("year")
            .annotate(count=Count("id"))
            .order_by("year")
        )

        # --- Trends: Events ---
        monthly_events = (
            Event.objects.filter(start_time__gte=one_year_ago)
            .annotate(month=TruncMonth("start_time"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        yearly_events = (
            Event.objects.filter(start_time__gte=five_years_ago)
            .annotate(year=TruncYear("start_time"))
            .values("year")
            .annotate(count=Count("id"))
            .order_by("year")
        )

        # --- Trends: Attendees ---
        monthly_attendees = (
            EventReaction.objects.filter(
                status=EventReaction.ATTENDING, created_at__gte=one_year_ago
            )
            .annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by("month")
        )
        yearly_attendees = (
            EventReaction.objects.filter(
                status=EventReaction.ATTENDING, created_at__gte=five_years_ago
            )
            .annotate(year=TruncYear("created_at"))
            .values("year")
            .annotate(count=Count("id"))
            .order_by("year")
        )

        # --- Top 5 Rankings ---
        top_events = (
            Event.objects.annotate(
                attendee_count=Count(
                    "reactions", filter=Q(reactions__status=EventReaction.ATTENDING)
                )
            )
            .order_by("-attendee_count")[:5]
            .values("id", "title", "attendee_count")
        )
        top_organizers_by_events = (
            User.objects.filter(role="organizer")
            .annotate(events_count=Count("organized_events"))
            .order_by("-events_count")[:5]
            .values("id", "first_name", "last_name", "events_count")
        )
        top_organizers_by_attendees = (
            User.objects.filter(role="organizer")
            .annotate(
                attendee_count=Count(
                    "organized_events__reactions",
                    filter=Q(organized_events__reactions__status=EventReaction.ATTENDING),
                )
            )
            .order_by("-attendee_count")[:5]
            .values("id", "first_name", "last_name", "attendee_count")
        )

        # --- Organizer performance table ---
        organizer_performance = (
            User.objects.filter(role="organizer")
            .annotate(
                events_count=Count("organized_events", distinct=True),
                attendees_count=Count(
                    "organized_events__reactions",
                    filter=Q(
                        organized_events__reactions__status=EventReaction.ATTENDING
                    ),
                    distinct=True,
                ),
            )
            .values("id", "first_name", "last_name", "events_count", "attendees_count")
            .order_by("-events_count")
        )

        # --- System health ---
        system_health = Event.objects.aggregate(
            draft_events=Count("id", filter=Q(status="draft")),
            cancelled_events=Count("id", filter=Q(status="cancelled")),
            waitlist_enabled=Count("id", filter=Q(allow_waitlist=True)),
        )
        full_events = (
            Event.objects.annotate(
                attendee_count=Count(
                    "reactions", filter=Q(reactions__status=EventReaction.ATTENDING)
                )
            )
            .filter(attendee_count__gte=F("capacity"))
            .count()
        )

        # --- Format response ---
        data = {
            "totals": {
                "users": total_users,
                "events": total_events,
                "attendees": total_attendees,
            },
            "breakdowns": {
                "users_by_role": list(users_by_role),
                "events_by_status": list(events_by_status),
                "events_by_category": list(events_by_category),
            },
            "trends": {
                "monthly": {
                    "users": [
                        {
                            "month": d["month"].strftime("%B"),
                            "year": d["month"].year,
                            "count": d["count"],
                        }
                        for d in monthly_users
                    ],
                    "events": [
                        {
                            "month": d["month"].strftime("%B"),
                            "year": d["month"].year,
                            "count": d["count"],
                        }
                        for d in monthly_events
                    ],
                    "attendees": [
                        {
                            "month": d["month"].strftime("%B"),
                            "year": d["month"].year,
                            "count": d["count"],
                        }
                        for d in monthly_attendees
                    ],
                },
                "yearly": {
                    "users": [
                        {"year": d["year"].year, "count": d["count"]}
                        for d in yearly_users
                    ],
                    "events": [
                        {"year": d["year"].year, "count": d["count"]}
                        for d in yearly_events
                    ],
                    "attendees": [
                        {"year": d["year"].year, "count": d["count"]}
                        for d in yearly_attendees
                    ],
                },
            },
            "rankings": {
                "top_events_by_attendance": list(top_events),
                "top_organizers_by_events": list(top_organizers_by_events),
                "top_organizers_by_attendees": list(top_organizers_by_attendees),
            },
            "organizer_performance": list(organizer_performance),
            "system_health": {
                **system_health,
                "full_events": full_events,
            },
        }

        return Response(data)


class OrganizerRequestCreateView(generics.CreateAPIView):
    queryset = OrganizerRequest.objects.all()
    serializer_class = OrganizerRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        # Check if already has pending
        if OrganizerRequest.objects.filter(user=user, status='pending').exists():
            raise serializers.ValidationError({"detail": "You already have a pending request."})

        # Check if previously rejected within 90 days
        last_rejected = OrganizerRequest.objects.filter(user=user, status='rejected').order_by('-reviewed_at').first()
        if last_rejected and not last_rejected.can_request_again()[0]:
            remaining = last_rejected.can_request_again()[1]
            raise serializers.ValidationError({"detail": f"You must wait {remaining} more days before requesting again."})

        serializer.save(user=user)


class OrganizerRequestListView(generics.ListAPIView):
    serializer_class = OrganizerRequestSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        # join user and the user's profile in one query
        qs = OrganizerRequest.objects.select_related('user', 'user__profile')

        status_param = self.request.query_params.get("status")
        if status_param in ["pending", "approved", "rejected"]:
            return qs.filter(status=status_param)
        return qs.filter(status="pending")



class OrganizerRequestUpdateView(generics.UpdateAPIView):
    queryset = OrganizerRequest.objects.select_related('user').all()
    serializer_class = OrganizerRequestSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_update(self, serializer):
        instance = serializer.save(reviewed_at=now())
        if instance.status == 'approved':
            instance.user.role = 'organizer'
            instance.user.save()

class OrganizerRequestDetailView(generics.RetrieveAPIView):
    queryset = OrganizerRequest.objects.select_related("user", "user__profile")
    serializer_class = OrganizerRequestSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = "id" 


class OrganizerRequestStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user_id = request.user.id

        # Single query with user prefetched
        request_obj = (
            OrganizerRequest.objects.filter(user_id=user_id)
            .select_related("user")
            .order_by("-created_at")
            .first()
        )

        if not request_obj:
            return Response({"status": "none"}, status=200)

        serializer = OrganizerRequestSerializer(request_obj)
        data = serializer.data

        if request_obj.status == "rejected":
            can_request, remaining_days = request_obj.can_request_again()
            data["can_request_again"] = can_request
            data["remaining_days"] = remaining_days if not can_request else 0
        else:
            data["can_request_again"] = True
            data["remaining_days"] = 0

        return Response(data, status=200)