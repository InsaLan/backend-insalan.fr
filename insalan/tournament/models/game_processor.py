"""
GameProcessor class
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Type, TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import requests

from insalan.settings import RIOT_API_KEY, WEBSITE_HOST, PROTOCOL
from . import bracket, group, swiss
from .match import MatchStatus

if TYPE_CHECKING:
    from django_stubs_ext import StrPromise

    from .tournament import BaseTournament
    from .match import Match


REQUESTS_TIMEOUT_SECONDS: int = 5
RIOT_TOURNAMENT_API_BASE: str = "https://americas.api.riotgames.com"
RIOT_MATCH_API_BASE: str = "https://europe.api.riotgames.com"


class GameProcessor(ABC):
    """
    Abstract base class for game-specific processors.
    Each game that supports automatic match handling should implement this class.
    """
    short: ClassVar[str]
    name: ClassVar[StrPromise]

    # Default game parameters that will be used if not overridden
    default_game_parameters: ClassVar[dict[str, Any]] = {}

    # Schema defining available parameters and their possible values
    # Format: {
    #   "parameter_name": {"type": "choice|string|int|bool", "choices": [...], "label": "..."}
    # }
    game_parameters_schema: ClassVar[dict[str, dict[str, Any]]] = {}

    @staticmethod
    @abstractmethod
    def initialize_tournament(tournament: BaseTournament) -> dict[str, Any] | None:
        """
        Make the required API calls and return the data to save in the ApiData field of tournament.
        Will be called when tournament is created.
        
        Args:
            tournament: The tournament to initialize
            
        Returns:
            Dictionary containing API data to store, or None if initialization failed
        """

    @staticmethod
    @abstractmethod
    def update_tournament(tournament: BaseTournament) -> dict[str, Any] | None:
        """
        Make the required API calls and return the data to save in the ApiData field of tournament.
        Will be called with tournament action.
        
        Args:
            tournament: The tournament to update
            
        Returns:
            Dictionary containing updated API data to store, or None if update failed
        """

    @staticmethod
    @abstractmethod
    def create_match(match: Match) -> dict[str, Any] | None:
        """
        Make the required API calls and return the data to save in the ApiData field of match.
        Will be called when match is created.
        
        Args:
            match: The match to create
            
        Returns:
            Dictionary containing API data to store, or None if creation failed
        """

    @staticmethod
    @abstractmethod
    def start_match(match: Match) -> dict[str, Any] | None:
        """
        Make the required API calls and return the data to save in the ApiData field of match.
        Will be called when match status is set to started.
        
        Args:
            match: The match to start
            
        Returns:
            Dictionary containing updated API data to store, or None if start failed
        """

    @staticmethod
    @abstractmethod
    def process_result_match(match: Match, payload: dict[str, Any]) -> dict[str, Any] | None:
        """
        Make the required API calls and return the data to save in the ApiData field of match.
        Will be called upon match callback (if API).
        
        Args:
            match: The match to process results for
            payload: Data received from the callback
            
        Returns:
            Dictionary containing updated API data to store, or None if processing failed
        """

    @staticmethod
    @abstractmethod
    def delete_match(match: Match) -> None:
        """
        Make the required API calls to clean up match data.
        Will be called upon match destruction.
        
        Args:
            match: The match being deleted
        """


class EmptyGameProcessor(GameProcessor):
    """
    Default game processor that performs no automatic match handling.
    """
    short = "None"
    name = _("Pas de gestion automatique")

    default_game_parameters: ClassVar[dict[str, Any]] = {}
    game_parameters_schema: ClassVar[dict[str, dict[str, Any]]] = {}

    @staticmethod
    def initialize_tournament(tournament: BaseTournament) -> dict[str, Any] | None:
        return {}

    @staticmethod
    def update_tournament(tournament: BaseTournament) -> dict[str, Any] | None:
        return {}

    @staticmethod
    def create_match(match: Match) -> dict[str, Any] | None:
        return {}

    @staticmethod
    def start_match(match: Match) -> dict[str, Any] | None:
        return {}

    @staticmethod
    def process_result_match(match: Match, payload: dict[str, Any]) -> dict[str, Any] | None:
        return {}

    @staticmethod
    def delete_match(match: Match) -> None:
        pass


class LeagueOfLegendsGameProcessor(GameProcessor):
    """
    Game processor for League of Legends automatic match handling.
    Uses Riot's Tournament API v5 to create and manage tournament codes.
    """
    short = "LoL"
    name = _("League of Legends")

    default_game_parameters: ClassVar[dict[str, Any]] = {
        "mapType": "SUMMONERS_RIFT",
        "pickType": "TOURNAMENT_DRAFT",
        "spectatorType": "ALL",
    }

    game_parameters_schema: ClassVar[dict[str, dict[str, Any]]] = {
        "pickType": {
            "type": "choice",
            "label": _("Type de sélection"),
            "choices": [
                ("BLIND_PICK", _("Sélection aveugle")),
                ("DRAFT_MODE", _("Mode draft")),
                ("ALL_RANDOM", _("Tout aléatoire")),
                ("TOURNAMENT_DRAFT", _("Draft tournoi")),
            ],
            "help_text": _("Le mode de sélection des champions")
        },
        "mapType": {
            "type": "choice",
            "label": _("Type de carte"),
            "choices": [
                ("SUMMONERS_RIFT", _("Faille de l'invocateur")),
                ("HOWLING_ABYSS", _("Abîme hurlant")),
            ],
            "help_text": _("La carte sur laquelle se déroulera le match")
        },
        "spectatorType": {
            "type": "choice",
            "label": _("Type de spectateur"),
            "choices": [
                ("NONE", _("Aucun")),
                ("LOBBYONLY", _("Lobby uniquement")),
                ("ALL", _("Tous")),
            ],
            "help_text": _("Qui peut observer le match")
        }
    }

    @staticmethod
    def initialize_tournament(tournament: BaseTournament) -> dict[str, Any] | None:
        """
        Initialize a League of Legends tournament by creating a provider and tournament ID.
        
        Steps:
        1. Create a provider via POST /lol/tournament/v5/providers
        2. Create a tournament via POST /lol/tournament/v5/tournaments
        3. Save both IDs in tournament ApiData
        """
        api_data: dict[str, Any] = {}

        # Step 1: Create provider
        provider_response = requests.post(
            f"{RIOT_TOURNAMENT_API_BASE}/lol/tournament/v5/providers",
            headers={"X-Riot-Token": RIOT_API_KEY},
            json={
            "region": "EUW",  # Europe West region
            "url": (
                f"{PROTOCOL}://api.{WEBSITE_HOST}/v1/tournament/"
                f"tournament/{tournament.id}/result/"
            )
            },
            timeout=REQUESTS_TIMEOUT_SECONDS,
        )

        if provider_response.status_code != 200:
            return None

        provider_id = provider_response.json()
        api_data["providerID"] = provider_id

        # Step 2: Create tournament
        tournament_response = requests.post(
            f"{RIOT_TOURNAMENT_API_BASE}/lol/tournament/v5/tournaments",
            headers={"X-Riot-Token": RIOT_API_KEY},
            json={
                "providerId": provider_id,
                "name": tournament.name,
            },
            timeout=REQUESTS_TIMEOUT_SECONDS,
        )

        if tournament_response.status_code != 200:
            return None

        tournament_id = tournament_response.json()
        api_data["tournamentID"] = tournament_id

        return api_data

    @staticmethod
    def update_tournament(tournament: BaseTournament) -> dict[str, Any] | None:
        """
        Refresh tournament data. For LoL, this can only be done if no matches were created.
        If matches exist, raise an exception to inform the admin.
        If no matches exist, reinitialize the tournament.
        """
        # Check if any matches exist for this tournament
        has_matches = False

        # Check brackets
        for bracketmatch in bracket.Bracket.objects.filter(tournament=tournament):
            if bracketmatch.get_matchs().exists():
                has_matches = True
                break

        # Check groups
        if not has_matches:
            for groupmatch in group.Group.objects.filter(tournament=tournament):
                if groupmatch.get_matchs().exists():
                    has_matches = True
                    break

        # Check swiss rounds
        if not has_matches:
            for swiss_round in swiss.SwissRound.objects.filter(tournament=tournament):
                if swiss_round.get_matchs().exists():
                    has_matches = True
                    break

        if has_matches:
            raise ValidationError(
                _("Impossible de rafraîchir le tournoi : des matchs ont déjà été créés. "
                  "Pour League of Legends, le rafraîchissement ne peut être effectué "
                  "qu'avant la création des matchs.")
            )

        # No matches exist, we can reinitialize
        return LeagueOfLegendsGameProcessor.initialize_tournament(tournament)

    @staticmethod
    def create_match(match: Match) -> dict[str, Any] | None:
        """
        Create tournament codes for a League of Legends match.
        
        The match needs access to its tournament to get the tournamentID.
        Creates N codes where N = best-of games (e.g., BO3 = 3 codes).
        """
        tournament = None
        match_type = ""

        # Determine which type of match this is and get its tournament
        if hasattr(match, 'knockoutmatch'):
            knockout_match = bracket.KnockoutMatch.objects.get(id=match.id)
            tournament = knockout_match.bracket.tournament
            match_type = "knockout"
        elif hasattr(match, 'groupmatch'):
            group_match = group.GroupMatch.objects.get(id=match.id)
            tournament = group_match.group.tournament
            match_type = "group"
        elif hasattr(match, 'swissmatch'):
            swiss_match = swiss.SwissMatch.objects.get(id=match.id)
            tournament = swiss_match.swiss.tournament
            match_type = "swiss"
        else:
            import sys  # pylint: disable=import-outside-toplevel
            print(f"Unknown match type for match ID {match.id}", file=sys.stderr)
            return None

        # Check if tournament has provider data
        if not tournament.api_data or "tournamentID" not in tournament.api_data:
            # No provider configured, do nothing
            return {}

        tournament_id = tournament.api_data["tournamentID"]

        # Get games parameters from the game model
        game_parameters = tournament.game.games_parameters or {}
        game_parameters["teamSize"] = tournament.game.get_players_per_team()
        metadata = (
            f'{{"title":"{tournament.name} - Match {match.id}",'
            f'"tournament":"{tournament.id}","match":"{match.id}",'
            f'"match_type":"{match_type}"}}'
        )
        game_parameters["metadata"] = metadata

        # Determine the number of codes needed based on best-of type
        from .match import BestofType  # pylint: disable=import-outside-toplevel
        if match.bo_type == BestofType.RANKING:
            # For ranking matches, we don't create codes
            return {}

        code_count = match.bo_type

        # Create tournament codes
        codes_response = requests.post(
            f"{RIOT_TOURNAMENT_API_BASE}/lol/tournament/v5/codes",
            headers={"X-Riot-Token": RIOT_API_KEY},
            params={
                "tournamentId": tournament_id,
                "count": code_count,
            },
            json=game_parameters,
            timeout=REQUESTS_TIMEOUT_SECONDS,
        )

        if codes_response.status_code != 200:
            return None

        codes = codes_response.json()

        return {
            "pregame": codes,
            "postgame": {}
        }

    @staticmethod
    def start_match(match: Match) -> dict[str, Any] | None:
        """
        Start a match. For League of Legends, nothing needs to be done.
        """
        return match.api_data if isinstance(match.api_data, dict) else None

    @staticmethod
    def process_result_match(match: Match, payload: dict[str, Any]) -> dict[str, Any] | None:
        """
        Process match results from a callback.
        
        Payload example:
        {
          "startTime": 1234567890000,
          "shortCode": "NA1234a-1a23b456-a1b2-1abc-ab12-1234567890ab",
          "metaData": "{\\"title\\":\\"Game 42 - Finals\\"}",
          "gameId": 1234567890,
          "gameName": "a123bc45-ab1c-1a23-ab12-12345a67b89c",
          "gameType": "Practice",
          "gameMap": 11,
          "gameMode": "CLASSIC",
          "region": "NA1"
        }
        
        Steps:
        1. Extract match PUUID from payload (gameName field)
        2. Fetch match details from Riot API
        3. Process and save statistics to match.api_data.postgame[shortCode]
        4. Check if all games have finished, mark match as completed if so
        """
        if not match.api_data:
            match.api_data = {"pregame": [], "postgame": {}}

        if "postgame" not in match.api_data:
            match.api_data["postgame"] = {}

        # Extract data from payload
        short_code = payload.get("shortCode")
        game_id_raw = payload.get("gameId")

        if not short_code or not game_id_raw:
            return None

        game_id = f"EUW1_{game_id_raw}"

        # Fetch match details from Riot API
        match_response = requests.get(
            f"{RIOT_MATCH_API_BASE}/lol/match/v5/matches/{game_id}",
            headers={"X-Riot-Token": RIOT_API_KEY},
            timeout=REQUESTS_TIMEOUT_SECONDS,
        )

        if match_response.status_code != 200:
            return None

        match_data = match_response.json()

        # TODO: Extract relevant statistics
        # Store essential match information
        game_stats = {
            "gameId": game_id,
            "startTime": payload.get("startTime"),
            "gameDuration": match_data.get("info", {}).get("gameDuration"),
            "teams": match_data.get("info", {}).get("teams", []),
            "participants": match_data.get("info", {}).get("participants", []),
        }

        # Save to postgame data keyed by tournament code
        match.api_data["postgame"][short_code] = game_stats

        # Check if all games have finished
        pregame_codes = match.api_data.get("pregame", [])
        postgame_codes = match.api_data.get("postgame", {})

        if len(postgame_codes) >= len(pregame_codes) and match.status != MatchStatus.COMPLETED:
            # All games finished, extract winners and determine final score
            from ..manage.match import update_match_score  # pylint: disable=import-outside-toplevel
            from ..manage.bracket import update_next_knockout_match  # pylint: disable=import-outside-toplevel
            from .bracket import KnockoutMatch  # pylint: disable=import-outside-toplevel

            # Initialize score dict for each team
            team_scores: dict[str, int] = {}
            for team in match.get_teams():
                team_scores[str(team.id)] = 0

            # Count wins for each team by analyzing postgame data
            for game_data in postgame_codes.values():
                participants = game_data.get("participants", [])
                teams_data = game_data.get("teams", [])

                # Find winning team ID from teams data
                winning_team_id = None
                for team_info in teams_data:
                    if team_info.get("win"):
                        winning_team_id = team_info.get("teamId")
                        break

                if winning_team_id is None:
                    continue

                # Get PUUIDs of players in the winning team
                winning_puuids = set()
                for participant in participants:
                    if participant.get("teamId") == winning_team_id:
                        puuid = participant.get("puuid")
                        if puuid:
                            winning_puuids.add(puuid)

                # Match PUUIDs to our teams via Player.validator_data
                for team in match.get_teams():
                    team_players = team.get_players()
                    team_puuids = set()
                    for player in team_players:
                        player_puuid = player.validator_data.get("puuid")
                        if player_puuid:
                            team_puuids.add(player_puuid)

                    # Check if this team's PUUIDs overlap with winning PUUIDs
                    # If at least one player matches, this team won the game
                    if team_puuids & winning_puuids:
                        team_scores[str(team.id)] += 1
                        break

            # Extract game durations
            times = []
            for game_data in postgame_codes.values():
                duration = game_data.get("gameDuration", 0)
                # Convert from seconds to minutes
                times.append(duration // 60 if duration else 0)

            # Update match with final scores
            score_data = {
                "score": {str(team_id): score for team_id, score in team_scores.items()},
                "times": times
            }

            update_match_score(match, score_data)

            # Propagate results if this is a bracket match
            if isinstance(match, KnockoutMatch) and not match.is_last_match():
                update_next_knockout_match(match)

        return match.api_data if isinstance(match.api_data, dict) else None

    @staticmethod
    def delete_match(match: Match) -> None:
        """
        Clean up match data. For League of Legends, no cleanup is required.
        Tournament codes remain valid but unused.
        """


processors: list[Type[GameProcessor]] = [
    EmptyGameProcessor,
    LeagueOfLegendsGameProcessor,
]


def get_processor_choices() -> list[tuple[str, StrPromise]]:
    """
    Get the choices for the game processors
    """
    return [(processor.short, processor.name) for processor in processors]


def get_processor(name: str) -> Type[GameProcessor] | None:
    """
    Get the game processor from a name
    """
    for processor in processors:
        if processor.short == name:
            return processor
    return None


def get_processor_default_parameters(processor_name: str) -> dict[str, Any]:
    """
    Get the default game parameters for a processor
    """
    processor = get_processor(processor_name)
    if processor is None:
        return {}
    return processor.default_game_parameters.copy()


def get_processor_parameters_schema(processor_name: str) -> dict[str, dict[str, Any]]:
    """
    Get the game parameters schema for a processor
    """
    processor = get_processor(processor_name)
    if processor is None:
        return {}
    return processor.game_parameters_schema.copy()
