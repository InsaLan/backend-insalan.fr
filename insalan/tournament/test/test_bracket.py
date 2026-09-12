"""Tournament Bracket Module Tests"""

from datetime import date
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

from rest_framework.test import APITestCase
from django.test import TestCase


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

class BracketEndpointTestCase(APITestCase):
    """Bracket Endpoint Unit Test Class"""

    def setUp(self) -> None:
        """Setup method for Player Unit Tests"""

        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", date_start=date(2023,8,1), date_end=date(2023,8,2), description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = EventTournament.objects.create(game=game, event=event)
        stg = Stage.objects.create(name="Test Stage", tournament=trnm, index=1)
        bracket = Bracket.objects.create(name="Test Bracket", stage=stg, bracket_type = BracketType.SINGLE, tournament=trnm)
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

        user_admin = User.objects.create_superuser(
            username="adminuser",
            email="admin.user.test@insalan.fr",
            password="^ThisIsAnAdminPassword42$",
            first_name="Iam",
            last_name="Staff",
        )

        user_one = User.objects.create_user(
            username="testplayer",
            email="player.user.test@insalan.fr",
            password="^ARandomPassword1$",
            first_name="Iam",
            last_name="Player",
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

    def test_change_match_not_admin(self) -> None:
        """
        Check that the requests on APIs are refused to non admins
        """
        # * except get /v1/tournament/bracket/{id}/*
        raise NotImplementedError()

    def test_bracket_details(self) -> None:
        """
        Get backets details from the API endpoint
        """
        # get /v1/tournament/bracket/{id}
        raise NotImplementedError()

    def test_update_bracket_match(self) -> None:
        """
        Change information on a bracket match from the API
        """
        # patch /v1/tournament/bracket/{bracket_id}/match/{match_id}
        raise NotImplementedError()

    def test_delete_bracket_match_ongoing(self) -> None:
        """
        Try to delete bracket with ongoing matchs in it
        """
        # delete /v1/tournament/bracket/{id}
        raise NotImplementedError()

    def test_delete_bracket_match(self) -> None:
        """
        Delete brackets from the API
        """
        # delete /v1/tournament/bracket/{id}
        raise NotImplementedError()

    def test_launch_bracket_match(self) -> None:
        """
        Launch matches from the API endpoint
        """
        # patch /v1/tournament/brackets/matchs/launch
        raise NotImplementedError()

    def test_update_bracket_match_score(self) -> None:
        """
        Update brackets score from the API endpoint
        """
        # patch /v1/tournament/bracket/{id}/score
        raise NotImplementedError()

    def test_update_bracket_match_results(self) -> None:
        """
        Test the result API endpoint
        """
        # post /v1/tournament/bracket/{id}/result
        raise NotImplementedError()

    def test_update_bracket_match_results_no_processor(self) -> None:
        """
        Try to use the result API endpoint on a bracket with no game processor
        """
        # post /v1/tournament/bracket/{id}/result
        raise NotImplementedError()

class BracketTestCase(TestCase):
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
        bracket = Bracket.objects.create(name="Test Bracket", stage=stg, bracket_type = BracketType.SINGLE, tournament=trnm)
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

        user_admin = User.objects.create_superuser(
            username="adminuser",
            email="admin.user.test@insalan.fr",
            password="^ThisIsAnAdminPassword42$",
            first_name="Iam",
            last_name="Staff",
        )

        user_one = User.objects.create_user(
            username="testplayer",
            email="player.user.test@insalan.fr",
            password="^ARandomPassword1$",
            first_name="Iam",
            last_name="Player",
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

    def test_create_simple_matchs(self) -> None:
        """
        Create simple brackets matchs with the manage script
        """
        raise NotImplementedError()

    def test_create_double_matchs(self) -> None:
        """
        Create double brackets matchs with the manage script
        """
        raise NotImplementedError()

    def test_create_matchs_game_processor(self) -> None:
        """
        Create double brackets matchs with the manage script
        """
        raise NotImplementedError()

    def test_update_match_winner_bracket(self) -> None:
        """
        Update matchs with the manage script
        """
        raise NotImplementedError()

    def test_update_match_looser_bracket(self) -> None:
        """
        Create double brackets matchs with the manage script
        """
        raise NotImplementedError()

    def test_update_match_looser_bracket_simple_match(self) -> None:
        """
        Try to update a looser bracket in a simple bracket match
        Idk what's the result or if it's supposed to happen tbh but ig it should stay consistent
        """
        raise NotImplementedError()
