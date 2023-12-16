"""
Langate unit tests
"""

from django.db import models
from django.test import TestCase
from django.utils.translation import gettext_lazy as _
from rest_framework.test import APIClient

from insalan.tournament.models import Event, Game, Tournament, Player, Team, Manager, PaymentStatus
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
        self.assertEqual(ser["username"], "limefox")
        self.assertEqual(ser["email"], "test@insalan.fr")
        self.assertEqual(ser["name"], "Test User")

    # There are no field size checks because the only direction for
    # conversion will be db -> json, and you can only do validation when
    # going the opposite way

    def test_successful_reply(self):
        """
        Tests what the serialization of a successful reply looks like
        """
        user = User.objects.create_user(
            username="limefox",
            email="test@example.com",
            password="test",
            first_name="One",
            last_name="Two",
        )
        rep = LangateReply.new(user)
        rep.err = LangateReply.RegistrationStatus.NOT_REGISTERED

        ser = ReplySerializer(rep).data

        self.assertEqual(ser["err"], LangateReply.RegistrationStatus.NOT_REGISTERED)

        user_dc = ser["user"]
        self.assertEqual(user_dc["username"], "limefox")
        self.assertEqual(user_dc["email"], "test@example.com")
        self.assertEqual(user_dc["name"], "One Two")

        self.assertEqual(len(ser["tournaments"]), 0)


class EndpointTests(TestCase):
    """
    Endpoint tests
    """

    def test_unauthenticated_user(self):
        """
        Tests that the API endpoint refuses to give information without auth
        """
        request = self.client.post("/v1/langate/authenticate", format="json")
        self.assertEqual(request.status_code, 403)

    def test_authenticated_user(self):
        """Verify result on an authenticated user"""
        Event.objects.create(name="InsaLan", year=2023, month=3, ongoing=True)
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate')
        self.assertEqual(reply.status_code, 404)

        ser = reply.data
        self.assertEqual(ser["err"], LangateReply.RegistrationStatus.NOT_REGISTERED)

        user_dc = ser["user"]
        self.assertEqual(user_dc["username"], "limefox")
        self.assertEqual(user_dc["email"], "test@example.com")
        self.assertEqual(user_dc["name"], "Lux Amelia Phifollen")

        self.assertEqual(len(ser["tournaments"]), 0)

    def test_no_ongoing_event(self):
        """
        Verify what happens when no event is happening
        """
        Event.objects.create(name="Insalan XV", year=2020, month=2, ongoing=False)
        Event.objects.create(name="Insalan XVI", year=2022, month=3, ongoing=False)
        Event.objects.create(name="InsaLan XVII", year=2023, month=2, ongoing=False)
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate')
        # No ongoing event triggers a 500
        self.assertEqual(reply.status_code, 500)

    def test_no_ongoing_event_with_id(self):
        """
        Verify what happens when no event is happening
        """
        Event.objects.create(name="Insalan XV", year=2020, month=2, ongoing=False)
        evobj = Event.objects.create(name="Insalan XVI", year=2022, month=3, ongoing=False)
        Event.objects.create(name="InsaLan XVII", year=2023, month=2, ongoing=False)
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate', data={"event_id": evobj.id})
        # No ongoing event triggers a 500
        self.assertEqual(reply.status_code, 500)

    def test_one_ongoing_event_no_id(self):
        """
        Verify what happens with only one ongoing event and no ID in the POST
        """
        Event.objects.create(name="Insalan XV", year=2020, month=2, ongoing=False)
        evobj = Event.objects.create(name="Insalan XVI", year=2022, month=3, ongoing=True)
        Event.objects.create(name="InsaLan XVII", year=2023, month=2, ongoing=False)
        game_obj = Game.objects.create(name="Test Game", short_name="TG")
        tourney = Tournament.objects.create(name="Tourney", game=game_obj, event=evobj)
        team = Team.objects.create(name="Bloop", tournament=tourney)
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()
        Player.objects.create(user=user, team=team)

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate')
        self.assertEqual(reply.status_code, 200)

        ser = reply.data
        self.assertEqual(ser["err"], LangateReply.RegistrationStatus.NOT_PAID)

        self.assertEqual(len(ser["tournaments"]), 1)

        tourney_reg = ser["tournaments"][0]
        self.assertEqual(tourney_reg["shortname"], "TG")
        self.assertEqual(tourney_reg["game_name"], "Test Game")
        self.assertEqual(tourney_reg["team"], "Bloop")
        self.assertFalse(tourney_reg["manager"])
        self.assertFalse(tourney_reg["has_paid"])

    def test_one_ongoing_event_correct_id(self):
        """
        Verify what happens with only one ongoing event and the right ID in the POST
        """
        Event.objects.create(name="Insalan XV", year=2020, month=2, ongoing=False)
        evobj = Event.objects.create(name="Insalan XVI", year=2022, month=3, ongoing=True)
        Event.objects.create(name="InsaLan XVII", year=2023, month=2, ongoing=False)
        game_obj = Game.objects.create(name="Test Game", short_name="TG")
        tourney = Tournament.objects.create(name="Tourney", game=game_obj, event=evobj)
        team = Team.objects.create(name="Bloop", tournament=tourney)
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()
        Player.objects.create(user=user, team=team)

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate', {"event_id": evobj.id})
        self.assertEqual(reply.status_code, 200)

        ser = reply.data
        self.assertEqual(ser["err"], LangateReply.RegistrationStatus.NOT_PAID)

        self.assertEqual(len(ser["tournaments"]), 1)

        tourney_reg = ser["tournaments"][0]
        self.assertEqual(tourney_reg["shortname"], "TG")
        self.assertEqual(tourney_reg["game_name"], "Test Game")
        self.assertEqual(tourney_reg["team"], "Bloop")
        self.assertFalse(tourney_reg["manager"])
        self.assertFalse(tourney_reg["has_paid"])

    def test_one_ongoing_event_wrong_id(self):
        """
        Verify what happens with only one ongoing event and the wrong ID in the POST
        """
        Event.objects.create(name="Insalan XV", year=2020, month=2, ongoing=False)
        evobj = Event.objects.create(name="Insalan XVI", year=2022, month=3, ongoing=True)
        Event.objects.create(name="InsaLan XVII", year=2023, month=2, ongoing=False)
        game_obj = Game.objects.create(name="Test Game", short_name="TG")
        tourney = Tournament.objects.create(name="Tourney", game=game_obj, event=evobj)
        team = Team.objects.create(name="Bloop", tournament=tourney)
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()
        Player.objects.create(user=user, team=team)

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate', {"event_id": evobj.id+1})
        self.assertEqual(reply.status_code, 400)

        self.assertEqual(reply.data["err"], _("Évènement demandé incompatible"))


    def test_many_ongoing_events_no_id(self):
        """
        Verify what happens multiple ongoing event and no ID in the POST
        """
        Event.objects.create(name="Insalan XV", year=2020, month=2, ongoing=False)
        Event.objects.create(name="Insalan XVI", year=2022, month=3, ongoing=True)
        evobj = Event.objects.create(name="InsaLan XVII", year=2023, month=2, ongoing=True)
        game_obj = Game.objects.create(name="Test Game", short_name="TG")
        tourney = Tournament.objects.create(name="Tourney", game=game_obj, event=evobj)
        team = Team.objects.create(name="Bloop", tournament=tourney)
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()
        Player.objects.create(user=user, team=team)

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate')
        self.assertEqual(reply.status_code, 400)

        self.assertEqual(reply.data["err"], _("Identifiant manquant"))

    def test_many_ongoing_events_wrong_id(self):
        """
        Verify what happens with many ongoing events and the wrong ID in the POST
        """
        evobj_get = Event.objects.create(name="Insalan XV", year=2020, month=2, ongoing=False)
        evobj = Event.objects.create(name="Insalan XVI", year=2022, month=3, ongoing=True)
        Event.objects.create(name="InsaLan XVII", year=2023, month=2, ongoing=True)
        game_obj = Game.objects.create(name="Test Game", short_name="TG")
        tourney = Tournament.objects.create(name="Tourney", game=game_obj, event=evobj)
        team = Team.objects.create(name="Bloop", tournament=tourney)
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()
        Player.objects.create(user=user, team=team)

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate', {"event_id": evobj_get.id})
        self.assertEqual(reply.status_code, 400)

        self.assertEqual(reply.data["err"], _("Évènement non en cours"))

    def test_many_ongoing_events_correct_id_with_registration(self):
        """
        Verify what happens with many ongoing events and the right ID in the POST
        """
        Event.objects.create(name="Insalan XV", year=2020, month=2, ongoing=True)
        evobj = Event.objects.create(name="Insalan XVI", year=2022, month=3, ongoing=True)
        Event.objects.create(name="InsaLan XVII", year=2023, month=2, ongoing=False)
        game_obj = Game.objects.create(name="Test Game", short_name="TG")
        tourney = Tournament.objects.create(name="Tourney", game=game_obj, event=evobj)
        team = Team.objects.create(name="Bloop", tournament=tourney)
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()
        Player.objects.create(user=user, team=team)

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate', {"event_id": evobj.id})
        self.assertEqual(reply.status_code, 200)

        ser = reply.data
        self.assertEqual(ser["err"], LangateReply.RegistrationStatus.NOT_PAID)

        self.assertEqual(len(ser["tournaments"]), 1)

        tourney_reg = ser["tournaments"][0]
        self.assertEqual(tourney_reg["shortname"], "TG")
        self.assertEqual(tourney_reg["game_name"], "Test Game")
        self.assertEqual(tourney_reg["team"], "Bloop")
        self.assertFalse(tourney_reg["manager"])
        self.assertFalse(tourney_reg["has_paid"])

    def test_many_ongoing_events_correct_id_disjointed_player(self):
        """
        Verify that disjointed player registrations are not both pulled
        """
        evobj_old = Event.objects.create(name="Insalan XV", year=2020, month=2, ongoing=True)
        evobj = Event.objects.create(name="Insalan XVI", year=2022, month=3, ongoing=True)
        Event.objects.create(name="InsaLan XVII", year=2023, month=2, ongoing=False)
        game_obj = Game.objects.create(name="Test Game", short_name="TG")
        tourney_old = Tournament.objects.create(name="Tourney Old", game=game_obj, event=evobj_old)
        tourney = Tournament.objects.create(name="Tourney", game=game_obj, event=evobj)
        team_old = Team.objects.create(name="Bloop Old", tournament=tourney_old)
        team = Team.objects.create(name="Bloop", tournament=tourney)
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()
        Player.objects.create(user=user, team=team_old)
        Player.objects.create(user=user, team=team)

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate', {"event_id": evobj.id})
        self.assertEqual(reply.status_code, 200)

        ser = reply.data
        self.assertEqual(ser["err"], LangateReply.RegistrationStatus.NOT_PAID)

        self.assertEqual(len(ser["tournaments"]), 1)

        tourney_reg = ser["tournaments"][0]
        self.assertEqual(tourney_reg["shortname"], "TG")
        self.assertEqual(tourney_reg["game_name"], "Test Game")
        self.assertEqual(tourney_reg["team"], "Bloop")
        self.assertFalse(tourney_reg["manager"])
        self.assertFalse(tourney_reg["has_paid"])

    def test_many_ongoing_events_correct_id_disjointed_player_manager(self):
        """
        Verify that disjointed player and manager registrations are not both pulled
        """
        evobj_old = Event.objects.create(name="Insalan XV", year=2020, month=2, ongoing=True)
        evobj = Event.objects.create(name="Insalan XVI", year=2022, month=3, ongoing=True)
        Event.objects.create(name="InsaLan XVII", year=2023, month=2, ongoing=False)
        game_obj = Game.objects.create(name="Test Game", short_name="TG")
        tourney_old = Tournament.objects.create(name="Tourney Old", game=game_obj, event=evobj_old)
        tourney = Tournament.objects.create(name="Tourney", game=game_obj, event=evobj)
        team_old = Team.objects.create(name="Bloop Old", tournament=tourney_old)
        team = Team.objects.create(name="Bloop", tournament=tourney)
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()
        Player.objects.create(user=user, team=team_old)
        Manager.objects.create(user=user, team=team)

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate', {"event_id": evobj.id})
        self.assertEqual(reply.status_code, 200)

        ser = reply.data
        self.assertEqual(ser["err"], LangateReply.RegistrationStatus.NOT_PAID)

        self.assertEqual(len(ser["tournaments"]), 1)

        tourney_reg = ser["tournaments"][0]
        self.assertEqual(tourney_reg["shortname"], "TG")
        self.assertEqual(tourney_reg["game_name"], "Test Game")
        self.assertEqual(tourney_reg["team"], "Bloop")
        self.assertTrue(tourney_reg["manager"])
        self.assertFalse(tourney_reg["has_paid"])

    def test_many_ongoing_events_correct_id_common_player_manager(self):
        """
        Verify that disjointed player and manager registrations are not both pulled
        """
        Event.objects.create(name="Insalan XV", year=2020, month=2, ongoing=True)
        evobj = Event.objects.create(name="Insalan XVI", year=2022, month=3, ongoing=True)
        Event.objects.create(name="InsaLan XVII", year=2023, month=2, ongoing=False)
        game_obj = Game.objects.create(name="Test Game", short_name="TG")
        tourney = Tournament.objects.create(name="Tourney", game=game_obj, event=evobj)
        team = Team.objects.create(name="Bloop", tournament=tourney)
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()
        Player.objects.create(user=user, team=team)
        Manager.objects.create(user=user, team=team)

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate', {"event_id": evobj.id})
        self.assertEqual(reply.status_code, 200)

        ser = reply.data
        self.assertEqual(ser["err"], LangateReply.RegistrationStatus.NOT_PAID)

        self.assertEqual(len(ser["tournaments"]), 2)

        # Player registrations are pulled first
        tourney_reg = ser["tournaments"][0]
        self.assertEqual(tourney_reg["shortname"], "TG")
        self.assertEqual(tourney_reg["game_name"], "Test Game")
        self.assertEqual(tourney_reg["team"], "Bloop")
        self.assertFalse(tourney_reg["manager"])
        self.assertFalse(tourney_reg["has_paid"])

        tourney_reg = ser["tournaments"][1]
        self.assertEqual(tourney_reg["shortname"], "TG")
        self.assertEqual(tourney_reg["game_name"], "Test Game")
        self.assertEqual(tourney_reg["team"], "Bloop")
        self.assertTrue(tourney_reg["manager"])
        self.assertFalse(tourney_reg["has_paid"])

    def test_payment_status_paid(self):
        """
        Verify that payment is correctly updated when payed
        """
        Event.objects.create(name="Insalan XV", year=2020, month=2, ongoing=False)
        evobj = Event.objects.create(name="Insalan XVI", year=2022, month=3, ongoing=True)
        Event.objects.create(name="InsaLan XVII", year=2023, month=2, ongoing=False)
        game_obj = Game.objects.create(name="Test Game", short_name="TG")
        tourney = Tournament.objects.create(name="Tourney", game=game_obj, event=evobj)
        team = Team.objects.create(name="Bloop", tournament=tourney)
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()
        Player.objects.create(user=user, team=team, payment_status=PaymentStatus.PAID)

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate')
        self.assertEqual(reply.status_code, 200)

        ser = reply.data
        self.assertEqual(ser["err"], None)

        self.assertEqual(len(ser["tournaments"]), 1)

        tourney_reg = ser["tournaments"][0]
        self.assertEqual(tourney_reg["shortname"], "TG")
        self.assertEqual(tourney_reg["game_name"], "Test Game")
        self.assertEqual(tourney_reg["team"], "Bloop")
        self.assertFalse(tourney_reg["manager"])
        self.assertTrue(tourney_reg["has_paid"])

    def test_payment_status_pay_later(self):
        """
        Verify that payment is correctly updated when payed
        """
        Event.objects.create(name="Insalan XV", year=2020, month=2, ongoing=False)
        evobj = Event.objects.create(name="Insalan XVI", year=2022, month=3, ongoing=True)
        Event.objects.create(name="InsaLan XVII", year=2023, month=2, ongoing=False)
        game_obj = Game.objects.create(name="Test Game", short_name="TG")
        tourney = Tournament.objects.create(name="Tourney", game=game_obj, event=evobj)
        team = Team.objects.create(name="Bloop", tournament=tourney)
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()
        Player.objects.create(user=user, team=team, payment_status=PaymentStatus.PAY_LATER)

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate')
        self.assertEqual(reply.status_code, 200)

        ser = reply.data
        self.assertEqual(ser["err"], LangateReply.RegistrationStatus.NOT_PAID)

        self.assertEqual(len(ser["tournaments"]), 1)

        tourney_reg = ser["tournaments"][0]
        self.assertEqual(tourney_reg["shortname"], "TG")
        self.assertEqual(tourney_reg["game_name"], "Test Game")
        self.assertEqual(tourney_reg["team"], "Bloop")
        self.assertFalse(tourney_reg["manager"])
        self.assertFalse(tourney_reg["has_paid"])

    def test_payment_status_contamination(self):
        """
        Verify that payment status is contaminated by a single not paid ticket
        """
        Event.objects.create(name="Insalan XV", year=2020, month=2, ongoing=False)
        evobj = Event.objects.create(name="Insalan XVI", year=2022, month=3, ongoing=True)
        Event.objects.create(name="InsaLan XVII", year=2023, month=2, ongoing=False)
        game_obj = Game.objects.create(name="Test Game", short_name="TG")
        tourney = Tournament.objects.create(name="Tourney", game=game_obj, event=evobj)
        team = Team.objects.create(name="Bloop", tournament=tourney)
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()
        Player.objects.create(user=user, team=team, payment_status=PaymentStatus.PAID)
        Manager.objects.create(user=user, team=team, payment_status=PaymentStatus.NOT_PAID)

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate')
        self.assertEqual(reply.status_code, 200)

        ser = reply.data
        self.assertEqual(ser["err"], LangateReply.RegistrationStatus.NOT_PAID)

        self.assertEqual(len(ser["tournaments"]), 2)

        tourney_reg = ser["tournaments"][0]
        self.assertEqual(tourney_reg["shortname"], "TG")
        self.assertEqual(tourney_reg["game_name"], "Test Game")
        self.assertEqual(tourney_reg["team"], "Bloop")
        self.assertFalse(tourney_reg["manager"])
        self.assertTrue(tourney_reg["has_paid"])

        tourney_reg = ser["tournaments"][1]
        self.assertEqual(tourney_reg["shortname"], "TG")
        self.assertEqual(tourney_reg["game_name"], "Test Game")
        self.assertEqual(tourney_reg["team"], "Bloop")
        self.assertTrue(tourney_reg["manager"])
        self.assertFalse(tourney_reg["has_paid"])

    def test_payment_status_fully_paid(self):
        """
        Verify that payment status is null when all is paid
        """
        Event.objects.create(name="Insalan XV", year=2020, month=2, ongoing=False)
        evobj = Event.objects.create(name="Insalan XVI", year=2022, month=3, ongoing=True)
        Event.objects.create(name="InsaLan XVII", year=2023, month=2, ongoing=False)
        game_obj = Game.objects.create(name="Test Game", short_name="TG")
        tourney = Tournament.objects.create(name="Tourney", game=game_obj, event=evobj)
        team = Team.objects.create(name="Bloop", tournament=tourney)
        user = User.objects.create_user(username="limefox",
                                        email="test@example.com",
                                        first_name="Lux Amelia",
                                        last_name="Phifollen",
                                        password="bad_pass"
                                        )
        user.save()
        Player.objects.create(user=user, team=team, payment_status=PaymentStatus.PAID)
        Manager.objects.create(user=user, team=team, payment_status=PaymentStatus.PAID)

        self.client.login(username="limefox", password="bad_pass")
        reply = self.client.post('/v1/langate/authenticate')
        self.assertEqual(reply.status_code, 200)

        ser = reply.data
        self.assertEqual(ser["err"], None)

        self.assertEqual(len(ser["tournaments"]), 2)

        tourney_reg = ser["tournaments"][0]
        self.assertEqual(tourney_reg["shortname"], "TG")
        self.assertEqual(tourney_reg["game_name"], "Test Game")
        self.assertEqual(tourney_reg["team"], "Bloop")
        self.assertFalse(tourney_reg["manager"])
        self.assertTrue(tourney_reg["has_paid"])

        tourney_reg = ser["tournaments"][1]
        self.assertEqual(tourney_reg["shortname"], "TG")
        self.assertEqual(tourney_reg["game_name"], "Test Game")
        self.assertEqual(tourney_reg["team"], "Bloop")
        self.assertTrue(tourney_reg["manager"])
        self.assertTrue(tourney_reg["has_paid"])
