"""Tournament Group Module Tests"""

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
    Group,
    Seeding,
    GroupMatch,
    GroupTiebreakScore
)
from insalan.user.models import User

class GroupEndpointTestCase(APITestCase):
    """Group Endpoint Unit Test Class"""

    def setUp(self) -> None:
        """Setup method for Player Unit Tests"""

        # Basic setup for a one-tournamnent game event
        event = Event.objects.create(
            name="InsaLan Test", date_start=date(2023,8,1), date_end=date(2023,8,2), description=""
        )
        game = Game.objects.create(name="Test Game")
        trnm = EventTournament.objects.create(game=game, event=event)
        stg = Stage.objects.create(name="Test Stage", tournament=trnm, index=1)
        group = Group.objects.create(name="Test Bracket", stage=stg, round_count=1, tournament=trnm)
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

    def test_list_groups(self) -> None:
        """
        Get groups details from the API endpoint
        """
        # get /v1/tournament/group/{id}
        raise NotImplementedError()

    def test_create_groups(self) -> None:
        """
        Add a list of groups from the API endpoint
        """
        # post /v1/tournament/group/{id}
        raise NotImplementedError()

    def test_group_details(self) -> None:
        """
        Get group details from the API endpoint
        """
        # get /v1/tournament/group/{id}
        raise NotImplementedError()

    def test_update_group_match(self) -> None:
        """
        Change information on a group match from the API
        """
        # patch /v1/tournament/group/{group_id}/match/{match_id}
        raise NotImplementedError()

    def test_delete_group_with_ongoing_match(self) -> None:
        """
        Try to delete group with ongoing matchs in it
        """
        # delete /v1/tournament/group/{id}
        raise NotImplementedError()

    def test_delete_group(self) -> None:
        """
        Delete group from the API
        """
        # delete /v1/tournament/group/{id}
        raise NotImplementedError()

    def test_create_group_match(self) -> None:
        """
        Create a match from the API endpoint
        """
        # patch /v1/tournament/groups/matchs/create
        raise NotImplementedError()

    def test_launch_group_match(self) -> None:
        """
        Launch matches from the API endpoint
        """
        # patch /v1/tournament/groups/matchs/launch
        raise NotImplementedError()

    def test_delete_group_match_ongoing(self) -> None:
        """
        Try to delete ongoing matches from the API endpoint
        """
        # post /v1/tournament/groups/matchs/delete
        raise NotImplementedError()

    def test_delete_group_match(self) -> None:
        """
        Delete matches from the API endpoint
        """
        # post /v1/tournament/groups/matchs/delete
        raise NotImplementedError()

    def test_update_group_match_score_not_ongoing(self) -> None:
        """
        Try to update match score while said match is scheduled or already over
        """
        # patch /v1/tournament/group/{group_id}/match/{match_id}/score
        raise NotImplementedError()

    def test_update_group_match_score_not_in_match(self) -> None:
        """
        Try to update match score while user is not in the match
        """
        # patch /v1/tournament/group/{group_id}/match/{match_id}/score
        raise NotImplementedError()

    def test_update_group_match_score(self) -> None:
        """
        Update group match score from the API endpoint
        """
        # patch /v1/tournament/group/{group_id}/match/{match_id}/score
        raise NotImplementedError()

    def test_update_group_match_results(self) -> None:
        """
        Test the result API endpoint
        """
        # post /v1/tournament/group/{group_id}/match/{match_id}/result
        raise NotImplementedError()

    def test_update_group_match_results_no_processor(self) -> None:
        """
        Try to use the result API endpoint on a group with no game processor
        """
        # post /v1/tournament/group/{group_id}/match/{match_id}/result
        raise NotImplementedError()
