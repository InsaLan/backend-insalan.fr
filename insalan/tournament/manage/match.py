from typing import Any

from ..models import Match, MatchStatus, Score


def update_match_score(match: Match, data: dict[str, Any]) -> None:
    match.times = data["times"]

    for score in match.get_scores_list():
        score.score = data["score"][str(score.team.id)]
        score.save()

    match.status = MatchStatus.COMPLETED

    match.save()


def launch_match(match: Match) -> None:
    if len(match.get_teams()) == 1:
        match.status = MatchStatus.COMPLETED
        score = Score.objects.get(team=match.get_teams()[0], match=match)
        score.score = match.get_winning_score()
        score.save()
    else:
        match.status = MatchStatus.ONGOING
        
        # Call game processor for match start
        from ..models.bracket import KnockoutMatch
        from ..models.group import GroupMatch
        from ..models.swiss import SwissMatch
        
        # Get the tournament from the match
        tournament = None
        if hasattr(match, 'knockoutmatch'):
            tournament = KnockoutMatch.objects.get(id=match.id).bracket.tournament
        elif hasattr(match, 'groupmatch'):
            tournament = GroupMatch.objects.get(id=match.id).group.tournament
        elif hasattr(match, 'swissmatch'):
            tournament = SwissMatch.objects.get(id=match.id).round.tournament
        
        if tournament is not None:
            processor_class = tournament.game.get_game_processor()
            if processor_class is not None:
                api_data = processor_class.start_match(match)
                if api_data is not None:
                    match.api_data = api_data

    match.save()
