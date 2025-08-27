# events/serializers.py
from rest_framework import serializers


class OrganizerDashboardSerializer(serializers.Serializer):
    total_events = serializers.IntegerField()
    total_attendees = serializers.IntegerField()
    monthly_stats = serializers.ListField()   # [{month, year, events, attendees}]
    yearly_stats = serializers.ListField()    # [{year, events, attendees}]
