from rest_framework.permissions import BasePermission, SAFE_METHODS

class ReadOnly(BasePermission):
    """Read-Only permissions"""

    def has_permission(self, request, _view):
        """Define the permissions for this class"""
        return request.method in SAFE_METHODS

class Patch(BasePermission):
    """Is the request using HTTP Method PATCH"""

    def has_permission(self, request, _view):
        """Define the permissions for this class"""
        return request.method == "PATCH"