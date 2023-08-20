"""
Langate unit tests
"""

from django.db import models
from django.test import TestCase
from rest_framework.test import APIClient

from insalan.user.models import User

from .models import SimplifiedUserData, LangateReply
from .serializers import SimplifiedUserDataSerializer, ReplySerializer

class SerializationTests(TestCase):
    """
    Class for serialization tests
    """
    def test_successful_user(self):
        """
        Tests what the successful serialization of simplified user data looks like
        """
        sud = SimplifiedUserData()
        sud.username = "limefox"
        sud.email = "test@insalan.fr"
        sud.name = "Test User"

        ser = SimplifiedUserDataSerializer(sud).data
        self.assertEquals(ser["username"], "limefox")
        self.assertEquals(ser["email"], "test@insalan.fr")
        self.assertEquals(ser["name"], "Test User")

    # There are no field size checks because the only direction for
    # conversion will be db -> json, and you can only do validation when
    # going the opposite way

    def test_successful_reply(self):
        """
        Tests what the serialization of a successful reply looks like
        """
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        password="test",
                                        first_name="One",
                                        last_name="Two"
                                        )
        rep = LangateReply.new(user)

        ser = ReplySerializer(rep).data

        # FIXME: Change these when we have tournaments up
        self.assertEquals(ser["err"], "registration_not_found")

        user_dc = ser["user"]
        self.assertEquals(user_dc["username"], "limefox")
        self.assertEquals(user_dc["email"], "test@example.com")
        self.assertEquals(user_dc["name"], "One Two")

        self.assertEquals(len(ser["tournaments"]), 1)
        user_tnm = ser["tournaments"][0]
        self.assertEquals(user_tnm["shortname"], "cs")
        self.assertEquals(user_tnm["game_name"], "CS:GO")
        self.assertEquals(user_tnm["team"], "la team chiante là")
        self.assertEquals(user_tnm["manager"], False)
        self.assertEquals(user_tnm["has_paid"], False)

class EndpointTests(TestCase):
    """
    Endpoint tests
    """
    client: APIClient

    def setUp(self):
        """
        Method called before every test
        """
        self.client = APIClient()

    def test_unauthenticated_user(self):
        """
        Tests that the API endpoint refuses to give information without auth
        """
        request = self.client.post('/v1/langate/authenticate', format='json')
        self.assertEquals(request.status_code, 403)

    def test_authenticated_user(self):
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate')
        self.assertEquals(reply.status_code, 200)

        ser = reply.data
        # FIXME: Change these when we have tournaments up
        self.assertEquals(ser["err"], "registration_not_found")

        user_dc = ser["user"]
        self.assertEquals(user_dc["username"], "limefox")
        self.assertEquals(user_dc["email"], "test@example.com")
        self.assertEquals(user_dc["name"], "Lux Amelia Phifollen")

        self.assertEquals(len(ser["tournaments"]), 1)
        user_tnm = ser["tournaments"][0]
        self.assertEquals(user_tnm["shortname"], "cs")
        self.assertEquals(user_tnm["game_name"], "CS:GO")
        self.assertEquals(user_tnm["team"], "la team chiante là")
        self.assertEquals(user_tnm["manager"], False)
        self.assertEquals(user_tnm["has_paid"], False)
