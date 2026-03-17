"""
Custom permissions for dashboard admin endpoints.
All dashboard views require staff or superuser access.
"""
from rest_framework.permissions import BasePermission


class IsStaffOrAdmin(BasePermission):
    """
    Permission class to restrict access to staff and superuser only.
    Used on all admin dashboard endpoints.
    """
    message = "This endpoint is restricted to staff and admin users only."
    
    def has_permission(self, request, view):
        """
        Check if user is authenticated and either staff or superuser.
        """
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_staff or request.user.is_superuser)
        )
