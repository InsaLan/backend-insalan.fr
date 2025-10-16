"""EventTournament Module Tests"""

from decimal import Decimal

from django.db.utils import IntegrityError
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from insalan.tournament.models import (
    PaymentStatus,
    Player,
    Manager,
    Substitute,
    Team,
    EventTournament,
    Event,
    Game,
    SeatSlot,
    Seat
)
from insalan.user.models import User

class EventTournamentTestCase(TestCase):
    """
        This class tests the EventTournament class and its methods.
        It verifies that the class can be created, that it has the correct
        attributes, and that it can be saved to the database.
        
        For fields that are related to BaseTournament, see the
        BaseTournamentTestCase class.
    """

    def setUp(self):
        """Set up the Tournaments"""
        event = Event.objects.create(name="Test", year=2023, month=3, description="")
        event_two = Event.objects.create(
            name="Test Two", year=2023, month=2, description=""
        )
        game_one = Game.objects.create(name="Test Game One")
        game_two = Game.objects.create(name="Test Game Two")
        game_three = Game.objects.create(name="Test Game Three")
        EventTournament.objects.create(name="Tourney 1", game=game_one, event=event)
        EventTournament.objects.create(name="Tourney 2", game=game_two, event=event)
        EventTournament.objects.create(name="Tourney 3", game=game_three, event=event)
        EventTournament.objects.create(name="Tourney 4", game=game_three, event=event_two)

    def test_tournament_null_event(self):
        """Test failure of creation of a Tournament with no event"""
        game = Game.objects.create(name="Test")
        self.assertRaises(
            IntegrityError, EventTournament.objects.create, event=None, game=game
        )

    def test_get_event(self):
        """Get the event for a tournament"""
        event = Event.objects.get(year=2023, month=3)
        game = Game.objects.get(name="Test Game One")
        tourney = EventTournament.objects.get(game=game)

        self.assertEqual(event, tourney.get_event())

    def test_default_cashprizes(self):
        """Test that the default for cashprizes is an empty list"""
        tourney = EventTournament.objects.all()[0]
        self.assertEqual([], tourney.cashprizes)

    def test_get_set_cashprizes(self):
        """Verify that getting and setting cashprizes is possible"""
        tourney = EventTournament.objects.all()[0]

        # One price
        tourney.cashprizes = [Decimal(28)]
        tourney.save()
        self.assertEqual(1, len(tourney.cashprizes))
        self.assertEqual(Decimal(28), tourney.cashprizes[0])

        # Many prices
        tourney.cashprizes = [Decimal(18), Decimal(22), Decimal(89)]
        tourney.save()
        self.assertEqual(3, len(tourney.cashprizes))
        self.assertEqual(Decimal(18), tourney.cashprizes[0])
        self.assertEqual(Decimal(22), tourney.cashprizes[1])
        self.assertEqual(Decimal(89), tourney.cashprizes[2])

        # Back to zero
        tourney.cashprizes = []
        tourney.save()
        self.assertEqual(0, len(tourney.cashprizes))

    def test_cashprizes_cannot_be_strictly_negative(self):
        """Test that a cashprize cannot be strictly negative"""
        tourney = EventTournament.objects.all()[0]

        tourney.cashprizes = [Decimal(278), Decimal(-1), Decimal(0)]
        self.assertRaises(ValidationError, tourney.full_clean)

        tourney.cashprizes = [Decimal(278), Decimal(0), Decimal(0)]
        tourney.full_clean()

    def test_event_deletion_cascade(self):
        """Verify that a tournament is deleted when its event is"""
        tourney = EventTournament.objects.all()[0]
        ev_obj = tourney.game

        EventTournament.objects.get(id=tourney.id)

        # Delete and verify
        ev_obj.delete()

        self.assertRaises(
            EventTournament.DoesNotExist, EventTournament.objects.get, id=tourney.id
        )

    def test_product_creation(self):
        """
        Verify that a product is created for a tournament
        """
        event_one = Event.objects.create(
            name="Insalan Test One", year=2023, month=2, description=""
        )

        game = Game.objects.create(name="Fortnite")

        trnm_one = EventTournament.objects.create(
            event=event_one, game=game, player_price_online=23.3, manager_price_online=3, substitute_price_online=3
        )
        self.assertEqual(trnm_one.player_price_online, 23.3)

        self.assertEqual(trnm_one.manager_price_online, 3)

        self.assertEqual(trnm_one.substitute_price_online, 3)

class TournamentFullDerefEndpoint(TestCase):
    """Test the endpoint that fully dereferences everything about a tournament"""

    def test_not_found(self):
        """Test what happens on a tournament not found"""
        candidates = EventTournament.objects.all().values_list("id", flat=True)
        if len(candidates) == 0:
            candidates = [1]
        not_used = max(candidates) + 1

        request = self.client.get(
            f"/v1/tournament/tournament/{not_used}/full/", format="sjon"
        )
        self.assertEqual(request.status_code, 404)

    def test_example(self):
        """Test a simple example"""
        uobj_one = User.objects.create(
            username="test_user_one", email="one@example.com"
        )
        uobj_two = User.objects.create(
            username="test_user_two", email="two@example.com"
        )
        uobj_three = User.objects.create(
            username="test_user_three", email="three@example.com"
        )
        uobj_four = User.objects.create(
            username="test_user_four", email="four@example.com"
        )
        uobj_five = User.objects.create(
            username="test_user_five", email="five@example.com"
        )

        admin = User.objects.create(
            username="admin", email="admin@example.com", is_staff=True
        )

        game_obj = Game.objects.create(name="Test Game", short_name="TFG")

        evobj = Event.objects.create(
            name="Test Event",
            description="This is a test",
            year=2021,
            month=12,
            ongoing=False,
        )
        tourneyobj_one = EventTournament.objects.create(
            event=evobj,
            name="Test Tournament",
            rules="have fun!",
            game=game_obj,
            is_announced=True,
        )
        team_one = Team.objects.create(name="Team One", tournament=tourneyobj_one)
        first = Player.objects.create(user=uobj_one, team=team_one, name_in_game="playerone")
        second = Player.objects.create(user=uobj_two, team=team_one, name_in_game="playertwo")
        Manager.objects.create(user=uobj_three, team=team_one)
        sub = Substitute.objects.create(user=uobj_four, team=team_one, name_in_game="substitute")
        team_one.save()

        seat_one = Seat.objects.create(
            event=evobj,
            x=1,
            y=1,
        )
        seat_one.save()

        seat_two = Seat.objects.create(
            event=evobj,
            x=2,
            y=1,
        )
        seat_two.save()

        seatslot_one = SeatSlot.objects.create(
            tournament=tourneyobj_one,
            team=team_one
        )
        seatslot_one.seats.set([seat_one, seat_two])
        seatslot_one.save()

        request = self.client.get(
            reverse("tournament/details-full", args=[tourneyobj_one.id]), format="json"
        )
        self.assertEqual(request.status_code, 200)
        model = {
            "id": tourneyobj_one.id,
            "event": {
                "id": evobj.id,
                "name": "Test Event",
                "description": "This is a test",
                "year": 2021,
                "month": 12,
                "ongoing": False,
                "logo": None,
                "poster": None,
                "seats": [
                    (
                        seat_one.x,
                        seat_one.y,
                    ),
                    (
                        seat_two.x,
                        seat_two.y,
                    )
                ],
                "planning_file": None,
            },
            "game": {
                "id": game_obj.id,
                "name": "Test Game",
                "short_name": "TFG",
                "players_per_team": 1,
                "substitute_players_per_team": 0,
                "team_per_match": 2
            },
            "name": "Test Tournament",
            "rules": "have fun!",
            "is_announced": True,
            "maxTeam": tourneyobj_one.maxTeam,
            # I don't know what's happenin with timezones here
            "registration_open": timezone.make_aware(
                timezone.make_naive(tourneyobj_one.registration_open)
            ).isoformat(),
            "registration_close": timezone.make_aware(
                timezone.make_naive(tourneyobj_one.registration_close)
            ).isoformat(),
            "player_price_online": "0.00",
            "player_price_onsite": "0.00",
            "manager_price_online": "0.00",
            "manager_price_onsite": "0.00",
            "substitute_price_online": "0.00",
            "substitute_price_onsite": "0.00",
            "cashprizes": [],
            "player_online_product": tourneyobj_one.player_online_product.id,
            "manager_online_product": tourneyobj_one.manager_online_product.id,
            "substitute_online_product": tourneyobj_one.substitute_online_product.id,
            "teams": [
                {
                    "id": team_one.id,
                    "name": "Team One",
                    "players": [
                        {"name_in_game": "playerone", "payment_status": None},
                        {"name_in_game": "playertwo", "payment_status": None},
                    ],
                    "managers": [
                        "test_user_three",
                    ],
                    "substitutes": [
                        {"name_in_game": "substitute", "payment_status": None},
                    ],
                    "captain": first.name_in_game,
                    "validated": team_one.validated,
                    "seat_slot": None,
                }
            ],
            "logo": None,
            "validated_teams": 0,
            "description": "",
            "description_bottom": "",
            "casters": [],
            "planning_file": None,
            "groups" : [],
            "brackets" : [],
            "swissRounds" : [],
            "seatslots": [
                {
                    "id": seatslot_one.id,
                    "seats": [
                        {
                            "id": seat_one.id,
                            "x": seat_one.x,
                            "y": seat_one.y
                        },
                        {
                            "id": seat_two.id,
                            "x": seat_two.x,
                            "y": seat_two.y
                        },
                    ]
                }
            ]
        }

        self.assertEqual(request.data["teams"], model["teams"])
        self.assertEqual(request.data, model)

        self.client.force_login(user=uobj_five)
        request = self.client.get(
            reverse("tournament/details-full", args=[tourneyobj_one.id]), format="json"
        )
        self.assertEqual(request.status_code, 200)

        self.assertEqual(request.data["teams"], model["teams"])
        self.assertEqual(request.data, model)

        self.client.force_login(user=uobj_one)
        request = self.client.get(
            reverse("tournament/details-full", args=[tourneyobj_one.id]), format="json"
        )
        self.assertEqual(request.status_code, 200)

        model["teams"][0]["players"][0]["payment_status"] = PaymentStatus.NOT_PAID
        model["teams"][0]["players"][1]["payment_status"] = PaymentStatus.NOT_PAID
        model["teams"][0]["substitutes"][0]["payment_status"] = PaymentStatus.NOT_PAID

        model["teams"][0]["players"][0]["id"] = first.id
        model["teams"][0]["players"][1]["id"] = second.id
        model["teams"][0]["substitutes"][0]["id"] = sub.id

        self.assertEqual(request.data["teams"], model["teams"])
        self.assertEqual(request.data, model)

        self.client.force_login(user=uobj_three)
        request = self.client.get(
            reverse("tournament/details-full", args=[tourneyobj_one.id]), format="json"
        )
        self.assertEqual(request.status_code, 200)

        self.assertEqual(request.data["teams"], model["teams"])
        self.assertEqual(request.data, model)


        self.client.force_login(user=uobj_four)
        request = self.client.get(
            reverse("tournament/details-full", args=[tourneyobj_one.id]), format="json"
        )
        self.assertEqual(request.status_code, 200)

        self.assertEqual(request.data["teams"], model["teams"])
        self.assertEqual(request.data, model)

        self.client.force_login(user=admin)

        request = self.client.get(
            reverse("tournament/details-full", args=[tourneyobj_one.id]), format="json"
        )
        self.assertEqual(request.status_code, 200)

        model["teams"][0]["seed"] = 0

        self.assertEqual(request.data["teams"], model["teams"])
        self.assertEqual(request.data, model)

    def test_not_announced(self):
        """Test if a tournament hasn't been yet announced"""
        uobj_one = User.objects.create(
            username="test_user_one", email="one@example.com"
        )
        uobj_two = User.objects.create(
            username="test_user_two", email="two@example.com"
        )
        uobj_three = User.objects.create(
            username="test_user_three", email="three@example.com"
        )

        game_obj = Game.objects.create(name="Test Game", short_name="TFG")

        evobj = Event.objects.create(
            name="Test Event",
            description="This is a test",
            year=2021,
            month=12,
            ongoing=False,
        )
        tourneyobj_one = EventTournament.objects.create(
            event=evobj,
            name="Test Tournament",
            rules="have fun!",
            game=game_obj,
            is_announced=False,
        )
        team_one = Team.objects.create(name="Team One", tournament=tourneyobj_one, password=make_password("strongpwd"))
        Player.objects.create(user=uobj_one, team=team_one)
        Player.objects.create(user=uobj_two, team=team_one)
        Manager.objects.create(user=uobj_three, team=team_one)
        Substitute.objects.create(user=uobj_three, team=team_one)

        request = self.client.get(
            reverse("tournament/details-full", args=[tourneyobj_one.id]), format="json"
        )
        self.assertEqual(request.status_code, 200)
        self.assertEqual(
            request.data,
            {
                "id": tourneyobj_one.id,
                "is_announced": False,
            },
        )
