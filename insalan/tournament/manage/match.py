from ..models import Match, Score, MatchStatus

def update_match_score(match: Match, data):
    match.times = data["times"]
    
    for score in match.get_Scores():
        score.score = data["score"][str(score.team.id)]
        score.save()

    match.status = MatchStatus.COMPLETED

    match.save()
