from rest_framework import serializers
from django.db.models import Count, Q
from .models import Event, EventCategory, EventReaction


class EventCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = EventCategory
        fields = ['id', 'name', 'description']


class EventSerializer(serializers.ModelSerializer):
    organizer_name = serializers.CharField(source='organizer.get_full_name', read_only=True)
    category = EventCategorySerializer(read_only=True)

    # counts from queryset annotations
    attending_count = serializers.IntegerField(read_only=True)
    interested_count = serializers.IntegerField(read_only=True)

    # ID field for creating/updating category
    category_id = serializers.PrimaryKeyRelatedField(
        source='category',
        queryset=EventCategory.objects.all(),
        write_only=True,
        required=False,
        allow_null=True
    )

    image = serializers.ImageField(required=False, allow_null=True)

    # dynamic field: user’s own reaction
    reaction_status = serializers.SerializerMethodField()

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
            'reaction_status',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'organizer', 'created_at', 'updated_at']

    def get_reaction_status(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        # Use only the prefetched data to avoid N+1 queries
        if hasattr(obj, "my_reaction_list") and obj.my_reaction_list:
            return obj.my_reaction_list[0].status

        return None
