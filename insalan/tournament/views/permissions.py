from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.request import Request
from rest_framework.views import APIView

class ReadOnly(BasePermission):
    """Read-Only permissions"""

    def has_permission(self, request: Request, _view: APIView) -> bool:
        """Define the permissions for this class"""
        return request.method in SAFE_METHODS

class Patch(BasePermission):
    """Is the request using HTTP Method PATCH"""

    def has_permission(self, request: Request, _view: APIView) -> bool:
        """Define the permissions for this class"""
        return request.method == "PATCH"
