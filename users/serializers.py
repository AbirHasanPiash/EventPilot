from rest_framework import serializers
from .models import User, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    profile_image = serializers.ImageField(required=False, allow_null=True, use_url=True)

    class Meta:
        model = UserProfile
        fields = ['bio', 'phone', 'address', 'organization', 'profile_image']

    def update(self, instance, validated_data):
        if 'profile_image' in validated_data and validated_data['profile_image'] is None:
            instance.profile_image = None
        return super().update(instance, validated_data)



class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'email',
            'role', 'is_active'
        ]
        read_only_fields = ['id', 'email', 'is_active', 'role']


# Admin-only serializer to validate role changes
class RoleUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)
