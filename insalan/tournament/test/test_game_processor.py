"""GameProcessor Module Tests"""

from datetime import date
from unittest.mock import Mock, patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from insalan.tournament.models import (
    Event,
    EventTournament,
    Game,
    Team,
    Player,
    BestofType,
    MatchStatus,
)
from insalan.tournament.models.bracket import Bracket, KnockoutMatch
from insalan.tournament.models.group import Group, GroupMatch
from insalan.tournament.models.swiss import SwissRound, SwissMatch
from insalan.tournament.models.game_processor import (
    EmptyGameProcessor,
    LeagueOfLegendsGameProcessor,
    get_processor,
    get_processor_choices,
    get_processor_default_parameters,
    get_processor_parameters_schema,
)
from insalan.user.models import User


class EmptyGameProcessorTestCase(TestCase):
    """Test the EmptyGameProcessor class"""

    def setUp(self) -> None:
        """Set up test data"""

        event = Event.objects.create(
            name="Test Event",
            date_start=date(2023, 3, 1),
            date_end=date(2023, 3, 2),
            description="Test Description"
        )
        game = Game.objects.create(
            name="Test Game",
            game_processor="None"
        )
        with patch('insalan.tournament.models.game_processor.requests.post') as mock_post:
            # Mock API responses to prevent actual calls during tournament creation
            mock_response = Mock()
            mock_response.status_code = 500  # Simulate failure so no api_data is set
            mock_post.return_value = mock_response
            self.tournament = EventTournament.objects.create(
                name="Test Tournament",
                game=game,
                event=event,
                max_team_thresholds=[8, 16, 32]
            )
        self.bracket = Bracket.objects.create(
            tournament=self.tournament,
            name="Test Bracket"
        )
        self.match = KnockoutMatch.objects.create(
            bracket=self.bracket,
            bo_type=BestofType.BO3,
            round_number=1,
            index_in_round=1
        )

    def test_empty_processor_exists(self) -> None:
        """Test that the EmptyGameProcessor is registered"""
        choices = get_processor_choices()
        self.assertIn(("None", "Pas de gestion automatique"), choices)

    def test_empty_processor_initialize_tournament(self) -> None:
        """Test that initialize_tournament returns empty dict"""
        result = EmptyGameProcessor.initialize_tournament(self.tournament)
        self.assertEqual(result, {})

    def test_empty_processor_update_tournament(self) -> None:
        """Test that update_tournament returns empty dict"""
        result = EmptyGameProcessor.update_tournament(self.tournament)
        self.assertEqual(result, {})

    def test_empty_processor_create_match(self) -> None:
        """Test that create_match returns empty dict"""
        result = EmptyGameProcessor.create_match(self.match)
        self.assertEqual(result, {})

    def test_empty_processor_start_match(self) -> None:
        """Test that start_match returns empty dict"""
        result = EmptyGameProcessor.start_match(self.match)
        self.assertEqual(result, {})

    def test_empty_processor_process_result_match(self) -> None:
        """Test that process_result_match returns empty dict"""
        result = EmptyGameProcessor.process_result_match(self.match, {})
        self.assertEqual(result, {})

    def test_empty_processor_delete_match(self) -> None:
        """Test that delete_match doesn't raise errors"""
        EmptyGameProcessor.delete_match(self.match)


class LeagueOfLegendsGameProcessorTestCase(TestCase):
    """Test the LeagueOfLegendsGameProcessor class"""

    def setUp(self) -> None:
        """Set up test data"""

        event = Event.objects.create(
            name="Test Event",
            date_start=date(2023, 3, 1),
            date_end=date(2023, 3, 2),
            description="Test Description"
        )
        self.game = Game.objects.create(
            name="League of Legends",
            game_processor="LoL",
            players_per_team=5,
            games_parameters={
                "mapType": "SUMMONERS_RIFT",
                "pickType": "TOURNAMENT_DRAFT",
                "spectatorType": "ALL",
            }
        )
        with patch('insalan.tournament.models.game_processor.requests.post') as mock_post:
            # Mock API responses to prevent actual calls during tournament creation
            mock_response = Mock()
            mock_response.status_code = 500  # Simulate failure so no api_data is set
            mock_post.return_value = mock_response
            self.tournament = EventTournament.objects.create(
                name="LoL Tournament",
                game=self.game,
                event=event,
                max_team_thresholds=[8, 16, 32]
            )

        # Create teams with players
        self.team1 = Team.objects.create(
            name="Team 1",
            tournament=self.tournament
        )
        self.team2 = Team.objects.create(
            name="Team 2",
            tournament=self.tournament
        )

        # Create users and players for team 1
        for i in range(5):
            user = User.objects.create(
                username=f"player1_{i}",
                email=f"player1_{i}@example.com"
            )
            Player.objects.create(
                user=user,
                team=self.team1,
                name_in_game=f"Player1_{i}",
                validator_data={"puuid": f"puuid_team1_{i}"}
            )

        # Create users and players for team 2
        for i in range(5):
            user = User.objects.create(
                username=f"player2_{i}",
                email=f"player2_{i}@example.com"
            )
            Player.objects.create(
                user=user,
                team=self.team2,
                name_in_game=f"Player2_{i}",
                validator_data={"puuid": f"puuid_team2_{i}"}
            )

        self.bracket = Bracket.objects.create(
            tournament=self.tournament,
            name="Test Bracket"
        )
        self.match = KnockoutMatch.objects.create(
            bracket=self.bracket,
            bo_type=BestofType.BO3,
            round_number=1,
            index_in_round=1
        )
        self.match.teams.add(self.team1, self.team2)

    def test_lol_processor_exists(self) -> None:
        """Test that the LeagueOfLegendsGameProcessor is registered"""
        choices = get_processor_choices()
        self.assertIn(("LoL", "League of Legends"), choices)

    def test_lol_processor_default_parameters(self) -> None:
        """Test that default parameters are correctly defined"""
        defaults = get_processor_default_parameters("LoL")
        self.assertEqual(defaults["mapType"], "SUMMONERS_RIFT")
        self.assertEqual(defaults["pickType"], "TOURNAMENT_DRAFT")
        self.assertEqual(defaults["spectatorType"], "ALL")

    def test_lol_processor_parameters_schema(self) -> None:
        """Test that parameters schema is correctly defined"""
        schema = get_processor_parameters_schema("LoL")
        self.assertIn("pickType", schema)
        self.assertIn("mapType", schema)
        self.assertIn("spectatorType", schema)
        self.assertEqual(schema["pickType"]["type"], "choice")

    @patch('insalan.tournament.models.game_processor.requests.post')
    def test_initialize_tournament_success(self, mock_post: Mock) -> None:
        """Test successful tournament initialization"""
        # Mock provider creation
        mock_provider_response = Mock()
        mock_provider_response.status_code = 200
        mock_provider_response.json.return_value = 12345

        # Mock tournament creation
        mock_tournament_response = Mock()
        mock_tournament_response.status_code = 200
        mock_tournament_response.json.return_value = 67890

        mock_post.side_effect = [mock_provider_response, mock_tournament_response]

        result = LeagueOfLegendsGameProcessor.initialize_tournament(self.tournament)

        self.assertIsNotNone(result)
        assert result is not None  # Type narrowing for mypy
        self.assertEqual(result["providerID"], 12345)
        self.assertEqual(result["tournamentID"], 67890)
        self.assertEqual(mock_post.call_count, 2)

    @patch('insalan.tournament.models.game_processor.requests.post')
    def test_initialize_tournament_provider_failure(self, mock_post: Mock) -> None:
        """Test tournament initialization failure on provider creation"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        result = LeagueOfLegendsGameProcessor.initialize_tournament(self.tournament)

        self.assertIsNone(result)

    @patch('insalan.tournament.models.game_processor.requests.post')
    def test_initialize_tournament_tournament_failure(self, mock_post: Mock) -> None:
        """Test tournament initialization failure on tournament creation"""
        mock_provider_response = Mock()
        mock_provider_response.status_code = 200
        mock_provider_response.json.return_value = 12345

        mock_tournament_response = Mock()
        mock_tournament_response.status_code = 500

        mock_post.side_effect = [mock_provider_response, mock_tournament_response]

        result = LeagueOfLegendsGameProcessor.initialize_tournament(self.tournament)

        self.assertIsNone(result)

    # pylint: disable=line-too-long
    @patch('insalan.tournament.models.game_processor.LeagueOfLegendsGameProcessor.initialize_tournament')
    def test_update_tournament_no_matches(self, mock_initialize: Mock) -> None:
        """Test tournament update when no matches exist"""
        # Delete the match created in setUp to test the "no matches" scenario
        self.match.delete()

        mock_initialize.return_value = {"providerID": 12345, "tournamentID": 67890}

        result = LeagueOfLegendsGameProcessor.update_tournament(self.tournament)

        self.assertIsNotNone(result)
        mock_initialize.assert_called_once_with(self.tournament)

    def test_update_tournament_with_bracket_matches(self) -> None:
        """Test tournament update fails when bracket matches exist"""
        # Match already exists from setUp
        with self.assertRaises(ValidationError):
            LeagueOfLegendsGameProcessor.update_tournament(self.tournament)

    def test_update_tournament_with_group_matches(self) -> None:
        """Test tournament update fails when group matches exist"""
        group = Group.objects.create(
            tournament=self.tournament,
            name="Test Group"
        )
        GroupMatch.objects.create(
            group=group,
            bo_type=BestofType.BO3,
            round_number=1,
            index_in_round=1
        )

        with self.assertRaises(ValidationError):
            LeagueOfLegendsGameProcessor.update_tournament(self.tournament)

    def test_update_tournament_with_swiss_matches(self) -> None:
        """Test tournament update fails when swiss matches exist"""
        swiss_round = SwissRound.objects.create(
            tournament=self.tournament,
            min_score=3
        )
        SwissMatch.objects.create(
            swiss=swiss_round,
            bo_type=BestofType.BO3,
            round_number=1,
            index_in_round=1
        )

        with self.assertRaises(ValidationError):
            LeagueOfLegendsGameProcessor.update_tournament(self.tournament)

    @patch('insalan.tournament.models.game_processor.requests.post')
    def test_create_match_knockout(self, mock_post: Mock) -> None:
        """Test creating a knockout match with tournament codes"""
        self.tournament.api_data = {
            "providerID": 12345,
            "tournamentID": 67890
        }
        self.tournament.save()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["CODE1", "CODE2", "CODE3"]
        mock_post.return_value = mock_response

        result = LeagueOfLegendsGameProcessor.create_match(self.match)

        self.assertIsNotNone(result)
        assert result is not None  # Type narrowing for mypy
        self.assertIn("pregame", result)
        self.assertIn("postgame", result)
        self.assertEqual(result["pregame"], ["CODE1", "CODE2", "CODE3"])
        self.assertEqual(result["postgame"], {})

    def test_create_match_no_tournament_data(self) -> None:
        """Test creating match when tournament has no API data"""
        # Ensure tournament has no api_data or has api_data without tournamentID
        self.tournament.api_data = {}
        self.tournament.save()

        result = LeagueOfLegendsGameProcessor.create_match(self.match)

        self.assertEqual(result, {})

    def test_create_match_ranking(self) -> None:
        """Test creating a ranking match (no codes needed)"""
        self.match.bo_type = BestofType.RANKING
        self.match.save()

        result = LeagueOfLegendsGameProcessor.create_match(self.match)

        self.assertEqual(result, {})

    @patch('insalan.tournament.models.game_processor.requests.post')
    def test_create_match_group(self, mock_post: Mock) -> None:
        """Test creating a group match"""
        group = Group.objects.create(
            tournament=self.tournament,
            name="Test Group"
        )
        group_match = GroupMatch.objects.create(
            group=group,
            bo_type=BestofType.BO5,
            round_number=1,
            index_in_round=1
        )
        group_match.teams.add(self.team1, self.team2)

        self.tournament.api_data = {
            "providerID": 12345,
            "tournamentID": 67890
        }
        self.tournament.save()

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["CODE1", "CODE2", "CODE3", "CODE4", "CODE5"]
        mock_post.return_value = mock_response

        result = LeagueOfLegendsGameProcessor.create_match(group_match)

        self.assertIsNotNone(result)
        assert result is not None  # Type narrowing for mypy
        self.assertEqual(len(result["pregame"]), 5)

    def test_start_match(self) -> None:
        """Test starting a match"""
        self.match.api_data = {"pregame": ["CODE1", "CODE2", "CODE3"], "postgame": {}}
        self.match.save()

        result = LeagueOfLegendsGameProcessor.start_match(self.match)

        self.assertEqual(result, self.match.api_data)

    @patch('insalan.tournament.models.game_processor.requests.get')
    def test_process_result_match_single_game(self, mock_get: Mock) -> None:
        """Test processing a single game result"""
        self.match.api_data = {
            "pregame": ["CODE1", "CODE2", "CODE3"],
            "postgame": {}
        }
        self.match.save()

        # Mock Riot API match details response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "info": {
                "gameDuration": 1800,
                "teams": [
                    {"teamId": 100, "win": True},
                    {"teamId": 200, "win": False}
                ],
                "participants": [
                    {"teamId": 100, "puuid": "puuid_team1_0"},
                    {"teamId": 100, "puuid": "puuid_team1_1"},
                    {"teamId": 100, "puuid": "puuid_team1_2"},
                    {"teamId": 100, "puuid": "puuid_team1_3"},
                    {"teamId": 100, "puuid": "puuid_team1_4"},
                    {"teamId": 200, "puuid": "puuid_team2_0"},
                    {"teamId": 200, "puuid": "puuid_team2_1"},
                    {"teamId": 200, "puuid": "puuid_team2_2"},
                    {"teamId": 200, "puuid": "puuid_team2_3"},
                    {"teamId": 200, "puuid": "puuid_team2_4"},
                ]
            }
        }
        mock_get.return_value = mock_response

        payload = {
            "shortCode": "CODE1",
            "gameId": 1234567890,
            "startTime": 1234567890000
        }

        result = LeagueOfLegendsGameProcessor.process_result_match(self.match, payload)

        self.assertIsNotNone(result)
        assert result is not None  # Type narrowing for mypy
        self.assertIn("CODE1", result["postgame"])
        self.assertEqual(result["postgame"]["CODE1"]["gameId"], "EUW1_1234567890")

    @patch('insalan.tournament.models.game_processor.requests.get')
    @patch('insalan.tournament.manage.match.update_match_score')
    def test_process_result_match_all_games_finished(
        self,
        mock_update_score: Mock,
        mock_get: Mock
    ) -> None:
        """Test processing results when all games are finished"""
        self.match.api_data = {
            "pregame": ["CODE1", "CODE2", "CODE3"],
            "postgame": {
                "CODE1": {
                    "gameId": "EUW1_1",
                    "gameDuration": 1800,
                    "teams": [
                        {"teamId": 100, "win": True},
                        {"teamId": 200, "win": False}
                    ],
                    "participants": [
                        {"teamId": 100, "puuid": "puuid_team1_0"},
                        {"teamId": 100, "puuid": "puuid_team1_1"},
                        {"teamId": 100, "puuid": "puuid_team1_2"},
                        {"teamId": 100, "puuid": "puuid_team1_3"},
                        {"teamId": 100, "puuid": "puuid_team1_4"},
                        {"teamId": 200, "puuid": "puuid_team2_0"},
                        {"teamId": 200, "puuid": "puuid_team2_1"},
                        {"teamId": 200, "puuid": "puuid_team2_2"},
                        {"teamId": 200, "puuid": "puuid_team2_3"},
                        {"teamId": 200, "puuid": "puuid_team2_4"},
                    ]
                },
                "CODE2": {
                    "gameId": "EUW1_2",
                    "gameDuration": 2100,
                    "teams": [
                        {"teamId": 100, "win": True},
                        {"teamId": 200, "win": False}
                    ],
                    "participants": [
                        {"teamId": 100, "puuid": "puuid_team1_0"},
                        {"teamId": 100, "puuid": "puuid_team1_1"},
                        {"teamId": 100, "puuid": "puuid_team1_2"},
                        {"teamId": 100, "puuid": "puuid_team1_3"},
                        {"teamId": 100, "puuid": "puuid_team1_4"},
                        {"teamId": 200, "puuid": "puuid_team2_0"},
                        {"teamId": 200, "puuid": "puuid_team2_1"},
                        {"teamId": 200, "puuid": "puuid_team2_2"},
                        {"teamId": 200, "puuid": "puuid_team2_3"},
                        {"teamId": 200, "puuid": "puuid_team2_4"},
                    ]
                }
            }
        }
        self.match.status = MatchStatus.ONGOING
        self.match.save()

        # Mock the final game result
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "info": {
                "gameDuration": 1500,
                "teams": [
                    {"teamId": 100, "win": False},
                    {"teamId": 200, "win": True}
                ],
                "participants": [
                    {"teamId": 100, "puuid": "puuid_team1_0"},
                    {"teamId": 100, "puuid": "puuid_team1_1"},
                    {"teamId": 100, "puuid": "puuid_team1_2"},
                    {"teamId": 100, "puuid": "puuid_team1_3"},
                    {"teamId": 100, "puuid": "puuid_team1_4"},
                    {"teamId": 200, "puuid": "puuid_team2_0"},
                    {"teamId": 200, "puuid": "puuid_team2_1"},
                    {"teamId": 200, "puuid": "puuid_team2_2"},
                    {"teamId": 200, "puuid": "puuid_team2_3"},
                    {"teamId": 200, "puuid": "puuid_team2_4"},
                ]
            }
        }
        mock_get.return_value = mock_response

        payload = {
            "shortCode": "CODE3",
            "gameId": 3,
            "startTime": 1234567890000
        }

        result = LeagueOfLegendsGameProcessor.process_result_match(self.match, payload)

        self.assertIsNotNone(result)
        # Verify that update_match_score was called
        mock_update_score.assert_called_once()
        call_args = mock_update_score.call_args
        self.assertEqual(call_args[0][0], self.match)
        score_data = call_args[0][1]
        self.assertIn("score", score_data)
        self.assertIn("times", score_data)

    def test_process_result_match_no_short_code(self) -> None:
        """Test processing result with missing shortCode"""
        self.match.api_data = {"pregame": ["CODE1"], "postgame": {}}
        self.match.save()

        result = LeagueOfLegendsGameProcessor.process_result_match(
            self.match,
            {"gameId": 123}
        )

        self.assertIsNone(result)

    @patch('insalan.tournament.models.game_processor.requests.get')
    def test_process_result_match_api_failure(self, mock_get: Mock) -> None:
        """Test processing result when Riot API fails"""
        self.match.api_data = {"pregame": ["CODE1"], "postgame": {}}
        self.match.save()

        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = LeagueOfLegendsGameProcessor.process_result_match(
            self.match,
            {"shortCode": "CODE1", "gameId": 123}
        )

        self.assertIsNone(result)

    def test_delete_match(self) -> None:
        """Test deleting a match"""
        # Should not raise any errors
        LeagueOfLegendsGameProcessor.delete_match(self.match)


class ProcessorUtilityFunctionsTestCase(TestCase):
    """Test utility functions for game processors"""

    def test_get_processor_choices(self) -> None:
        """Test getting processor choices"""
        choices = get_processor_choices()
        self.assertIsInstance(choices, list)
        self.assertGreaterEqual(len(choices), 2)
        self.assertIn(("None", "Pas de gestion automatique"), choices)
        self.assertIn(("LoL", "League of Legends"), choices)

    def test_get_processor_existing(self) -> None:
        """Test getting an existing processor"""
        processor = get_processor("LoL")
        self.assertIsNotNone(processor)
        self.assertEqual(processor, LeagueOfLegendsGameProcessor)

    def test_get_processor_non_existing(self) -> None:
        """Test getting a non-existing processor"""
        processor = get_processor("InvalidProcessor")
        self.assertIsNone(processor)

    def test_get_processor_default_parameters_existing(self) -> None:
        """Test getting default parameters for existing processor"""
        params = get_processor_default_parameters("LoL")
        self.assertIsInstance(params, dict)
        self.assertIn("mapType", params)
        self.assertIn("pickType", params)
        self.assertIn("spectatorType", params)

    def test_get_processor_default_parameters_non_existing(self) -> None:
        """Test getting default parameters for non-existing processor"""
        params = get_processor_default_parameters("InvalidProcessor")
        self.assertEqual(params, {})

    def test_get_processor_parameters_schema_existing(self) -> None:
        """Test getting parameters schema for existing processor"""
        schema = get_processor_parameters_schema("LoL")
        self.assertIsInstance(schema, dict)
        self.assertIn("mapType", schema)
        self.assertIn("pickType", schema)
        self.assertIn("spectatorType", schema)

    def test_get_processor_parameters_schema_non_existing(self) -> None:
        """Test getting parameters schema for non-existing processor"""
        schema = get_processor_parameters_schema("InvalidProcessor")
        self.assertEqual(schema, {})
