from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import action, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from .models import User, UserProfile
from .serializers import UserSerializer, UserProfileSerializer, RoleUpdateSerializer
from rest_framework.views import APIView
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_str
from rest_framework import filters


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Admin/staff can see all users.
    Regular users can only see their own.
    """
    # queryset = User.objects.select_related('profile').all()
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['email', 'first_name', 'last_name']
    

    def get_queryset(self):
        user = self.request.user
        if not (user.is_staff or user.is_superuser):
            # Non-admins only see themselves
            return self.queryset.filter(id=user.id)
        return self.queryset

    def get_filter_backends(self):
        """Only apply SearchFilter for admins."""
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return self.filter_backends
        return []


    
    @action(detail=False, methods=["get"])
    def me(self, request):
        return Response(self.get_serializer(request.user).data)

    @action(
    detail=True,
    methods=['patch'],
    permission_classes=[IsAdminUser],
    serializer_class=RoleUpdateSerializer
    )
    def set_role(self, request, pk=None):
        """
        Admin-only: Change a user's role.
        """
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_role = serializer.validated_data['role']
        user.role = new_role
        user.is_staff = (new_role == 'admin')
        user.save(update_fields=['role', 'is_staff'])

        # Return the updated user with the default serializer
        from .serializers import UserSerializer
        return Response(UserSerializer(user).data)
    

    def destroy(self, request, *args, **kwargs):
        """Allow only admin to delete a user (and their profile)."""
        if not request.user.is_staff and not request.user.is_superuser:
            return Response(
                {"detail": "You do not have permission to delete users."},
                status=status.HTTP_403_FORBIDDEN
            )

        user = self.get_object()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



class UserProfileViewSet(viewsets.ModelViewSet):
    """
    Manage user profiles.
    - Admins can view/delete any profile.
    - Authenticated users can only view/update their own profile via `me`.
    - Direct profile creation is not allowed.
    """
    queryset = UserProfile.objects.select_related("user")
    serializer_class = UserProfileSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve", "destroy"]:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        return Response(
            {"detail": "Creating profile directly is not allowed."},
            status=status.HTTP_403_FORBIDDEN
        )

    @action(detail=False, methods=["get", "put", "patch"])
    @parser_classes([MultiPartParser, FormParser])
    def me(self, request):
        """
        Allows the authenticated user to view or update their own profile.
        """
        profile = getattr(request.user, 'profile', None)
        if not profile:
            return Response(
                {"detail": "Profile does not exist."},
                status=status.HTTP_404_NOT_FOUND
            )

        if request.method in ["PUT", "PATCH"]:

            serializer = self.get_serializer(profile, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        else:
            serializer = self.get_serializer(profile)

        return Response(serializer.data)
    

class ActivateUserView(APIView):
    permission_classes = []

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({'detail': 'Invalid activation link.'}, status=status.HTTP_400_BAD_REQUEST)

        if user.is_active:
            return Response({'detail': 'Account already activated.'}, status=status.HTTP_200_OK)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({'detail': 'Account successfully activated.'}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
