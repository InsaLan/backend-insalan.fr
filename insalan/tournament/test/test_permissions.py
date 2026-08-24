"""Permission Module Tests"""

from django.test.client import RequestFactory

from rest_framework.test import APITestCase
from insalan.tournament.views.permissions import ReadOnly, Patch
from insalan.tournament.views.tournament import TournamentDetails

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
        request_get = self.fact.get("/get")
        request_post = self.fact.post("/post")
        request_put = self.fact.put("/put")
        request_patch = self.fact.patch("/patch")
        request_delete = self.fact.delete("/delete")

        self.assertTrue(perm.has_permission(request_get, TournamentDetails))
        self.assertFalse(perm.has_permission(request_post, TournamentDetails))
        self.assertFalse(perm.has_permission(request_put, TournamentDetails))
        self.assertFalse(perm.has_permission(request_patch, TournamentDetails))
        self.assertFalse(perm.has_permission(request_delete, TournamentDetails))

    def test_patch_permission(self) -> None:
        """
        Check the result of patch permission
        """
        perm = Patch()
        request_get = self.fact.get("/get")
        request_post = self.fact.post("/post")
        request_put = self.fact.put("/put")
        request_patch = self.fact.patch("/patch")
        request_delete = self.fact.delete("/delete")

        self.assertFalse(perm.has_permission(request_get, TournamentDetails))
        self.assertFalse(perm.has_permission(request_post, TournamentDetails))
        self.assertFalse(perm.has_permission(request_put, TournamentDetails))
        self.assertTrue(perm.has_permission(request_patch, TournamentDetails))
        self.assertFalse(perm.has_permission(request_delete, TournamentDetails))
