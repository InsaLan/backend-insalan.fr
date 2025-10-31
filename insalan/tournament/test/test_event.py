"""Tournament Event Module Tests"""

from io import BytesIO

from django.utils import timezone
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase

from rest_framework.test import APITestCase

from insalan.tournament.models import (
    EventTournament,
    Event,
    Game,
)

class EventTestCase(TransactionTestCase):
    """Tests for the Event class"""

    def test_simple_event(self) -> None:
        """Test that we can create a simple event"""
        Event.objects.create(name="Insalan Test", year=2023, month=2, description="")

    def test_name_minimum_length(self) -> None:
        """Test that an Event cannot have too short a name"""
        eobj = Event(name="Ins", year=2023, month=2)
        self.assertRaises(ValidationError, eobj.full_clean)

    def test_earlierst_event_year(self) -> None:
        """Check that we can't have too early an event"""
        eobj = Event(name="InsaLan", year=2002, month=2)
        self.assertRaises(ValidationError, eobj.full_clean)

    def test_low_event_month(self) -> None:
        """Check that we cannot use too low an event month"""
        eobj = Event(name="InsaLan", year=2023, month=0)
        self.assertRaises(ValidationError, eobj.full_clean)

        eobj.month = -1
        self.assertRaises(ValidationError, eobj.full_clean)

        eobj.month = -1000
        self.assertRaises(ValidationError, eobj.full_clean)

        eobj.month = 1
        eobj.full_clean()

    def test_high_event_month(self) -> None:
        """Check that we cannot use too high an event month"""
        eobj = Event(name="InsaLan", year=2023, month=13)
        self.assertRaises(ValidationError, eobj.full_clean)

        eobj.month = 839
        self.assertRaises(ValidationError, eobj.full_clean)

        eobj.month = 12
        eobj.full_clean()

    def test_ongoing_events(self) -> None:
        """Test that we can find events that are ongoing"""
        Event.objects.create(name="InsaLan", year=2023, month=8)
        evobj_one = Event.objects.create(
            name="InsaLan", year=2023, month=9, ongoing=True
        )
        Event.objects.create(name="InsaLan", year=2023, month=10)
        evobj_two = Event.objects.create(
            name="InsaLan", year=2023, month=11, ongoing=True
        )

        query_ongoing = Event.objects.filter(ongoing=True)
        self.assertEqual(2, len(query_ongoing))

        self.assertTrue(evobj_one in query_ongoing)
        self.assertTrue(evobj_two in query_ongoing)

    def test_non_null_fields(self) -> None:
        """Test that all non-nullable fields should raise errors"""
        self.assertRaises(
            IntegrityError,
            Event.objects.create,
            name=None,
            year=2023,
            month=2,
            description="",
        )
        self.assertRaises(
            IntegrityError,
            Event.objects.create,
            name="",
            year=None,
            month=2,
            description="",
        )
        self.assertRaises(
            IntegrityError,
            Event.objects.create,
            name="",
            year=2023,
            month=None,
            description="",
        )
        self.assertRaises(
            IntegrityError,
            Event.objects.create,
            name="",
            year=2023,
            month=2,
            description=None,
        )

    def test_get_tournaments(self) -> None:
        """Get tournaments for an event"""
        event = Event.objects.create(name="Test", year=2023, month=3, description="")
        event_two = Event.objects.create(
            name="Test Two", year=2023, month=2, description=""
        )
        game_one = Game.objects.create(name="Test Game One")
        game_two = Game.objects.create(name="Test Game Two")
        game_three = Game.objects.create(name="Test Game Three")
        trnm_one = EventTournament.objects.create(game=game_one, event=event)
        trnm_two = EventTournament.objects.create(game=game_two, event=event)
        trnm_three = EventTournament.objects.create(game=game_three, event=event)
        trnm_four = EventTournament.objects.create(game=game_three, event=event_two)

        trnms_found = event.get_tournaments()
        self.assertEqual(3, len(trnms_found))
        self.assertTrue(trnm_one in trnms_found)
        self.assertTrue(trnm_two in trnms_found)
        self.assertTrue(trnm_three in trnms_found)
        self.assertFalse(trnm_four in trnms_found)

    @staticmethod
    def create_event_logo(file_name: str = "event-test.png") -> SimpleUploadedFile:
        """Create a logo for event tests"""
        test_img = BytesIO(f"test-image called {file_name}".encode("utf-8"))
        test_img.name = file_name
        return SimpleUploadedFile(test_img.name, test_img.getvalue())

    def test_logo_extension_enforcement(self) -> None:
        """Verify that we only accept logos as PNG, JPG, JPEG and SVG"""
        ev_obj = Event.objects.create(
            name="Insalan Test", year=2023, month=2, description=""
        )

        # PNGs work
        test_png = EventTestCase.create_event_logo("event-test.png")
        ev_obj.logo = test_png
        ev_obj.full_clean()

        # JPGs work
        test_jpg = EventTestCase.create_event_logo("event-test.jpg")
        ev_obj.logo = test_jpg
        ev_obj.full_clean()

        # JPEGs work
        test_jpeg = EventTestCase.create_event_logo("event-test.jpeg")
        ev_obj.logo = test_jpeg
        ev_obj.full_clean()

        # SVGs work
        test_svg = EventTestCase.create_event_logo("event-test.svg")
        ev_obj.logo = test_svg
        ev_obj.full_clean()

        # Others won't
        for ext in ["mkv", "txt", "md", "php", "exe", "zip", "7z"]:
            test_icon = EventTestCase.create_event_logo(f"event-test.{ext}")
            ev_obj.logo = test_icon
            self.assertRaises(ValidationError, ev_obj.full_clean)


class EventDerefAndGroupingEndpoints(APITestCase):
    """Test endpoints for dereferencing/fetching grouped events"""

    @staticmethod
    def create_multiple_events() -> None:
        """Create some of events"""
        Event.objects.create(name="Event 1", year=2018, month=8)
        Event.objects.create(name="Event 2", year=2019, month=3)
        Event.objects.create(name="Event 3", year=2019, month=7)
        Event.objects.create(name="Event 4", year=2021, month=11)

    def test_year_group_empty(self) -> None:
        """Test what happens when events are in the database but we query an empty year"""
        self.create_multiple_events()

        request = self.client.get("/v1/tournament/event/year/2020/", format="json")

        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.data), 0)

    def test_year_one_found(self) -> None:
        """Test what happens when one event is found"""
        self.create_multiple_events()

        request = self.client.get("/v1/tournament/event/year/2018/", format="json")

        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.data), 1)

    def test_year_two_found(self) -> None:
        """Test what happens when multiple events are found"""
        self.create_multiple_events()

        request = self.client.get("/v1/tournament/event/year/2019/", format="json")
        self.assertEqual(request.status_code, 200)
        self.assertEqual(len(request.data), 2)

    def test_year_garbage(self) -> None:
        """Test that if you put anything but a year it's not recognized"""
        self.create_multiple_events()

        request = self.client.get("/v1/tournament/event/year/00d1686a/", format="json")
        self.assertEqual(request.status_code, 404)

    def test_deref_not_found(self) -> None:
        """Test what happens on a not found event"""
        not_assigned_list = list(Event.objects.all().values_list("id", flat=True))
        if len(not_assigned_list) == 0:
            not_assigned_list = [1]
        not_assigned = max(not_assigned_list) + 1
        request = self.client.get(
            f"/v1/tournament/event/{not_assigned}/tournaments/", format="json"
        )

        self.assertEqual(request.status_code, 404)

    def test_deref_not_announced(self) -> None:
        """Test a simple example of a dereference"""
        evobj = Event.objects.create(name="Test", year=2023, month=3, ongoing=True)
        gobj = Game.objects.create(name="Test Game", short_name="TG")
        tourney = EventTournament.objects.create(
            name="Test Tournament",
            game=gobj,
            event=evobj,
            rules="have fun!",
            is_announced=False,
        )

        request = self.client.get(
            f"/v1/tournament/event/{evobj.id}/tournaments/", format="json"
        )

        self.assertEqual(request.status_code, 200)

        model = {
            "id": evobj.id,
            "name": "Test",
            "description": "",
            "year": 2023,
            "month": 3,
            "ongoing": True,
            "tournaments": [
                {
                    "id": tourney.id,
                    "is_announced": False,
                }
            ],
            "logo": None,
            "poster": None,
            "planning_file": None,
        }
        self.assertEqual(request.data, model)

    def test_deref(self) -> None:
        """Test a simple example of a dereference"""
        evobj = Event.objects.create(name="Test", year=2023, month=3, ongoing=True)
        gobj = Game.objects.create(name="Test Game", short_name="TG")
        tourney = EventTournament.objects.create(
            name="Test Tournament",
            game=gobj,
            event=evobj,
            rules="have fun!",
            is_announced=True,
        )

        request = self.client.get(
            f"/v1/tournament/event/{evobj.id}/tournaments/", format="json"
        )

        self.assertEqual(request.status_code, 200)

        assert tourney.manager_online_product is not None
        assert tourney.player_online_product is not None
        assert tourney.substitute_online_product is not None

        model = {
            "id": evobj.id,
            "name": "Test",
            "description": "",
            "year": 2023,
            "month": 3,
            "ongoing": True,
            "tournaments": [
                {
                    "id": tourney.id,
                    "teams": [],
                    "validated_teams": 0,
                    "name": "Test Tournament",
                    "is_announced": True,
                    "maxTeam": tourney.maxTeam,
                    "rules": "have fun!",
                    "registration_open": timezone.make_aware(
                        timezone.make_naive(tourney.registration_open)
                    ).isoformat(),
                    "registration_close": timezone.make_aware(
                        timezone.make_naive(tourney.registration_close)
                    ).isoformat(),
                    "logo": None,
                    "player_price_online": "0.00",
                    "player_price_onsite": "0.00",
                    "manager_price_online": "0.00",
                    "manager_price_onsite": "0.00",
                    "substitute_price_online": "0.00",
                    "substitute_price_onsite": "0.00",
                    "cashprizes": [],
                    "game": gobj.id,
                    "manager_online_product": tourney.manager_online_product.id,
                    "substitute_online_product": tourney.substitute_online_product.id,
                    "player_online_product": tourney.player_online_product.id,
                    "description": "",
                    "description_bottom": "",
                    "casters": [],
                    "planning_file": None,
                    "groups" : [],
                    "brackets" : [],
                    "swissRounds" : []
                }
            ],
            "logo": None,
            "poster": None,
            "planning_file": None,
        }
        self.assertEqual(request.data, model)
