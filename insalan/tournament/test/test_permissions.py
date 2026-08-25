"""Permission Module Tests"""

from typing import cast
from django.test.client import RequestFactory

from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.test import APITestCase
from insalan.tournament.views.permissions import ReadOnly, Patch

class PermissionTestCase(APITestCase):
    """Permission Unit Test Class"""
    def setUp(self) -> None:
        """Setup method for Permission Unit Tests"""
        self.fact = RequestFactory()

    def test_readonly_permission(self) -> None:
        """
        Check the result of readonly permission
        """
        perm = ReadOnly()
        request_get = cast(Request, self.fact.get("/get"))
        request_post = cast(Request, self.fact.post("/post"))
        request_put = cast(Request, self.fact.put("/put"))
        request_patch = cast(Request, self.fact.patch("/patch"))
        request_delete = cast(Request, self.fact.delete("/delete"))
        view = APIView()

        self.assertTrue(perm.has_permission(request_get, view))
        self.assertFalse(perm.has_permission(request_post, view))
        self.assertFalse(perm.has_permission(request_put, view))
        self.assertFalse(perm.has_permission(request_patch, view))
        self.assertFalse(perm.has_permission(request_delete, view))

    def test_patch_permission(self) -> None:
        """
        Check the result of patch permission
        """
        perm = Patch()
        request_get = cast(Request, self.fact.get("/get"))
        request_post = cast(Request, self.fact.post("/post"))
        request_put = cast(Request, self.fact.put("/put"))
        request_patch = cast(Request, self.fact.patch("/patch"))
        request_delete = cast(Request, self.fact.delete("/delete"))
        view = APIView()

        self.assertFalse(perm.has_permission(request_get, view))
        self.assertFalse(perm.has_permission(request_post, view))
        self.assertFalse(perm.has_permission(request_put, view))
        self.assertTrue(perm.has_permission(request_patch, view))
        self.assertFalse(perm.has_permission(request_delete, view))
