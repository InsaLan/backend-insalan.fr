"""Tournament Bracket Module Tests"""

from datetime import date
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

from rest_framework.test import APITestCase

from insalan.tournament.models import (
    Player,
    Team,
    EventTournament,
    Event,
    Game,
    Stage,
    Bracket,
    BracketType
)
from insalan.user.models import User

class BracketTestCase(APITestCase):
    """Bracket Unit Test Class"""

    def setUp(self) -> None:
        """Setup method for Player Unit Tests"""

        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", date_start=date(2023,8,1), date_end=date(2023,8,2), description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = EventTournament.objects.create(game=game, event=event)
        stg = Stage.objects.create(name="Test Stage", tournament=trnm, index=1)
        bracket = Bracket.objects.create(name="Test Bracket", stage=stg, bracket_type = BracketType.SINGLE)
        team_one: Team = Team.objects.create(
            name="La Team Test",
            tournament=trnm,
            password=make_password("password"),
        )

        # Second edition
        event_two = Event.objects.create(
            name="InsaLan Test (Past)",
            date_start=date(2023,3,1),
            date_end=date(2023,3,2),
            description=""
        )
        trnm_two = EventTournament.objects.create(game=game, event=event_two)
        team_two: Team = Team.objects.create(
            name="La Team Test Passée", tournament=trnm_two, password=make_password("password2")
        )

        # Now the users
        user_one = User.objects.create_user(
            username="testplayer",
            email="player.user.test@insalan.fr",
            password="^ThisIsAnAdminPassword42$",
            first_name="Iam",
            last_name="Staff",
        )

        User.objects.create_user(
            username="randomplayer",
            email="randomplayer@gmail.com",
            password="IUseAVerySecurePassword",
            first_name="Random",
            last_name="Player",
        )

        another_player = User.objects.create_user(
            username="anotherplayer",
            password="ThisIsPassword",
        )

        # Now, registrations
        Player.objects.create(team=team_one, user=user_one, name_in_game="playerOne")
        Player.objects.create(team=team_one, user=another_player, name_in_game="PlayerTwo")
        Player.objects.create(team=team_two, user=another_player, name_in_game="RandomKiller")

    def test_add_stage_not_admin(self) -> None:
        self.assertTrue(False)

    def test_add_stage(self) -> None:
        self.assertTrue(False)

    def test_update_stage_not_admin(self) -> None:
        self.assertTrue(False)

    def test_update_stage(self) -> None:
        self.assertTrue(False)

    def test_delete_stage_not_admin(self) -> None:
        self.assertTrue(False)

    def test_delete_stage(self) -> None:
        self.assertTrue(False)

    def test_add_groups_not_admin(self) -> None:
        self.assertTrue(False)

    def test_add_groups(self) -> None:
        self.assertTrue(False)

    def test_add_groups_autofill(self) -> None:
        self.assertTrue(False)

    def test_add_brackets_not_admin(self) -> None:
        self.assertTrue(False)

    def test_add_brackets(self) -> None:
        self.assertTrue(False)

    def test_add_swiss_not_admin(self) -> None:
        self.assertTrue(False)

    def test_add_swiss(self) -> None:
        self.assertTrue(False)
