from ..models import Match, Score, MatchStatus


def update_match_score(match: Match, data):
    match.times = data["times"]

    for score in match.get_scores_list():
        score.score = data["score"][str(score.team.id)]
        score.save()

    match.status = MatchStatus.COMPLETED

    match.save()


def launch_match(match: Match):
    if len(match.get_teams()) == 1:
        match.status = MatchStatus.COMPLETED
        score = Score.objects.get(team=match.get_teams()[0], match=match)
        score.score = match.get_winning_score()
        score.save()
    else:
        match.status = MatchStatus.ONGOING

    match.save()
