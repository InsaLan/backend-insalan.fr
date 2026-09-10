"""Tournament Match Module Tests"""

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
    Match,
)
from insalan.user.models import User

class MatchTestCase(TestCase):
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

    def test_create_match(self) -> None:
        """
        Create a match and check some of its data
        """
        # functions to tests get_max_score, get_total_max_score, get_teams, 
        # get_teams_id, get_team_count, 
        raise NotImplementedError()

    def test_launch_match(self) -> None:
        """
        Launch a match, check that it is set on ongoing by default
        Check that the status is set to completed when one player is left
        """
        raise NotImplementedError()

    def test_update_match_score(self) -> None:
        """
        Check score updates through the manage.update_match_score call
        """
        raise NotImplementedError()

    def test_match_scores(self) -> None:
        """
        Check scores on a match
        """
        # check function get_scores, get_scores_list
        raise NotImplementedError()

    def test_get_winners_loser_BO(self) -> None:
        """
        Get looser and winners in BO match
        """
        raise NotImplementedError()

    def test_get_winners_loser_ranking(self) -> None:
        """
        Get looser and winners in ranking match
        """
        raise NotImplementedError()

    def test_multiple_scores_same_team_same_tournament(self) -> None:
        """
        Try to set multiple scores on the same team and tournament
        """
        raise NotImplementedError()

    def test_score_higher_than_max(self) -> None:
        """
        Try to set a score higher than the tournament max score
        """
        raise NotImplementedError()

    def test_users_in_match(self) -> None:
        """
        Check that users are correctly reported as in the match
        """
        raise NotImplementedError()
