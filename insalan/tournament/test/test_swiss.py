"""Tournament Swiss Round Module Tests"""

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
    SwissRound,
    SwissSeeding,
    SwissMatch,
)
from insalan.user.models import User

class SwissRoundEndpointTestCase(APITestCase):
    """Swiss Round Endpoint Unit Test Class"""

    def setUp(self) -> None:
        """Setup method for Unit Tests"""

        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", date_start=date(2023,8,1), date_end=date(2023,8,2), description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = EventTournament.objects.create(game=game, event=event)
        stg = Stage.objects.create(name="Test Stage", tournament=trnm, index=1)
        group = Group.objects.create(name="Test Group", stage=stg, round_count=1, tournament=trnm)
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

    def test_change_swiss_not_admin(self) -> None:
        """
        Check that the requests on APIs are refused to non admins
        """
        # * except get /v1/tournament/swiss/{id}/*
        raise NotImplementedError()

    def test_update_swiss_match(self) -> None:
        """
        Change information on a swiss match from the API
        """
        # patch /v1/tournament/swiss/{swiss_id}/match/{match_id}
        raise NotImplementedError()

    def test_delete_swiss_with_ongoing_match(self) -> None:
        """
        Try to delete swiss round with ongoing matchs in it
        """
        # delete /v1/tournament/swiss/{id}
        raise NotImplementedError()

    def test_delete_swiss(self) -> None:
        """
        Delete swiss round from the API
        """
        # delete /v1/tournament/swiss/{id}
        raise NotImplementedError()

    def test_fill_swiss_match(self) -> None:
        """
        Fill matches on a swiss round from the API endpoint
        """
        # patch /v1/tournament/swiss/matchs/launch
        raise NotImplementedError()

    def test_launch_swiss_match(self) -> None:
        """
        Launch matches from the API endpoint
        """
        # patch /v1/tournament/swiss/matchs/launch
        raise NotImplementedError()

    def test_update_swiss_match_score_not_ongoing(self) -> None:
        """
        Try to update match score while said match is scheduled or already over
        """
        # patch /v1/tournament/swiss/{swiss_id}/match/{match_id}/score
        raise NotImplementedError()

    def test_update_swiss_match_score_not_in_match(self) -> None:
        """
        Try to update match score while user is not in the match
        """
        # patch /v1/tournament/swiss/{swiss_id}/match/{match_id}/score
        raise NotImplementedError()

    def test_update_swiss_match_score(self) -> None:
        """
        Update swiss match score from the API endpoint
        """
        # patch /v1/tournament/swiss/{swiss_id}/match/{match_id}/score
        raise NotImplementedError()

    def test_update_swiss_match_results(self) -> None:
        """
        Test the result API endpoint
        """
        # post /v1/tournament/swiss/{swiss_id}/match/{match_id}/result
        raise NotImplementedError()

    def test_update_swiss_match_results_no_processor(self) -> None:
        """
        Try to use the result API endpoint on a swiss round with no game processor
        """
        # post /v1/tournament/swiss/{swiss_id}/match/{match_id}/result
        raise NotImplementedError()

class SwissRoundTestCase(TestCase):
    """SwissRound Unit Test Class"""

    def setUp(self) -> None:
        """Setup method for Unit Tests"""

        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", date_start=date(2023,8,1), date_end=date(2023,8,2), description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = EventTournament.objects.create(game=game, event=event)
        stg = Stage.objects.create(name="Test Stage", tournament=trnm, index=1)
        group = Group.objects.create(name="Test Group", stage=stg, round_count=1, tournament=trnm)
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

    def test_swiss_round_no_round_count_no_min_score_constraint(self) -> None:
        """
        Try to create a swiss round without providing either round count or min score
        Verify that providing either one of those properly create the swiss round.
        """
        raise NotImplementedError()

    def test_get_swiss_round_infos(self) -> None:
        """
        Get general infos
        check tournament and match functions
        """
        # get_name, get_teams, get_teams_id, get_teams_seeding, get_teams_seeding_by_id
        # get_sorted_teams, get_tournament, SwissMatch.get_tournament
        raise NotImplementedError()

    def test_get_swiss_round_round_infos(self) -> None:
        """
        Get round infos on the match
        """
        # get_round_count, get_leaderboad, get_qualifying_round_idx, get_matchs
        raise NotImplementedError()

    def test_get_match_winner_not_complete(self) -> None:
        """
        Test result of winners/loosers when there are no completed matchs
        Should result in an empty list ?
        """
        raise NotImplementedError()

    def test_get_swiss_round_winners_loosers(self) -> None:
        """
        Get swiss round winners/loosers with the manage script
        """
        raise NotImplementedError()

    def test_create_empty_matchs(self) -> None:
        """
        Create empty swiss rounds matchs with the manage script
        """
        raise NotImplementedError()

    def test_autofill_first_round(self) -> None:
        """
        Use the manage script first round autofill function
        """
        raise NotImplementedError()

    def test_fill_matchs(self) -> None:
        """
        Fill matchs and ensure correct teams have been added
        """
        raise NotImplementedError()

    def test_create_matchs_game_processor(self) -> None:
        """
        Create empty swiss rounds matchs with the manage script
        """
        raise NotImplementedError()

    def test_generate_swiss_round_not_qualifying(self) -> None:
        """
        Generate non-qualifying matchs with the manage script
        """
        raise NotImplementedError()

    def test_generate_swiss_round_qualifying(self) -> None:
        """
        Generate qualifying matchs with the manage script
        """
        raise NotImplementedError()
