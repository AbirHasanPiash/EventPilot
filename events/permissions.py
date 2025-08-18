from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOrganizerOrReadOnly(BasePermission):
    """
    - Allows read-only access to all authenticated users.
    - Write access is restricted to organizers or admins.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and (
            request.user.role == 'organizer' or request.user.is_staff
        )
    
