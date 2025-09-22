# events/serializers.py
from rest_framework import serializers
from dashboard.models import OrganizerRequest


class OrganizerDashboardSerializer(serializers.Serializer):
    total_events = serializers.IntegerField()
    total_attendees = serializers.IntegerField()
    monthly_stats = serializers.ListField()   # [{month, year, events, attendees}]
    yearly_stats = serializers.ListField()    # [{year, events, attendees}]




class OrganizerRequestSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    profile_image = serializers.ImageField(source='user.profile.profile_image', read_only=True)
    

    class Meta:
        model = OrganizerRequest
        fields = ['id', 'user', 'first_name', 'last_name', 'profile_image', 'user_email', 'status', 'created_at', 'reviewed_at']
        read_only_fields = ['user', 'created_at', 'reviewed_at']

    def create(self, validated_data):
        user = self.context['request'].user

        if user.role == 'organizer':
            raise serializers.ValidationError("You are already an organizer.")
        if OrganizerRequest.objects.filter(user=user, status='pending').exists():
            raise serializers.ValidationError("You already have a pending request.")

        return OrganizerRequest.objects.create(user=user)
