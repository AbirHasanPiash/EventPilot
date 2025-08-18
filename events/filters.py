import django_filters
from django.utils import timezone
from django.db.models import Q
from .models import Event

class EventFilter(django_filters.FilterSet):
    DATE_CHOICES = (
        ('archived', 'Archived'),
        ('today', 'Today'),
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
    )
    
    date_filter = django_filters.ChoiceFilter(choices=DATE_CHOICES, method='filter_by_date')

    class Meta:
        model = Event
        fields = ['date_filter']

    def filter_by_date(self, queryset, name, value):
        now = timezone.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start.replace(hour=23, minute=59, second=59, microsecond=999999)

        if value == 'archived':
            # Events fully ended before today
            return queryset.filter(end_time__lt=today_start)

        elif value == 'today':
            # Events that:
            # 1️⃣ Start today
            # 2️⃣ End today
            # 3️⃣ Or are ongoing during any time today
            return queryset.filter(
                Q(start_time__date=today_start.date()) |
                Q(end_time__date=today_start.date()) |
                Q(start_time__lte=now, end_time__gte=now)
            )

        elif value == 'upcoming':
            # Events starting after today ends
            return queryset.filter(start_time__gt=today_end)

        elif value == 'ongoing':
            # Events that started but not yet ended
            return queryset.filter(start_time__lte=now, end_time__gte=now)

        return queryset
