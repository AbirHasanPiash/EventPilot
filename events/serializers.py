from rest_framework import serializers
from .models import Event, EventCategory


class EventCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EventCategory
        fields = ['id', 'name', 'description']


class EventSerializer(serializers.ModelSerializer):
    organizer_name = serializers.CharField(source='organizer.get_full_name', read_only=True)
    category = EventCategorySerializer(read_only=True)
    attending_count = serializers.IntegerField(read_only=True)
    interested_count = serializers.IntegerField(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source='category',
        queryset=EventCategory.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Event
        fields = [
            'id', 'organizer', 'organizer_name',
            'title', 'description',
            'category', 'category_id',
            'tags', 'image',
            'start_time', 'end_time',
            'venue', 'location_map_url',
            'visibility', 'status',
            'capacity', 'allow_waitlist',
            'attending_count', 'interested_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'organizer', 'created_at', 'updated_at']
