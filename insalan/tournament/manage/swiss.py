from ..models import Team, Tournament, SwissRound, SwissMatch, SwissSeeding
import math


def create_swiss_matchs(swiss: SwissRound):
    teams = swiss.get_sorted_teams()
    team_per_match = swiss.tournament.get_game().get_team_per_match()
    nb_matchs = math.ceil(len(teams)/team_per_match)

    teams += [None]*(nb_matchs*team_per_match-len(teams))

    for match in SwissMatch.objects.filter(swiss=swiss):
        match.delete()

    for round_idx in range(swiss.min_score):
        matchs = []
        for match_idx in range(nb_matchs):
            matchs.append(SwissMatch.objects.create(round_number=round_idx+1,index_in_round=match_idx+1,swiss=swiss))

        matchs += matchs[::-1]

        if round_idx == 0:
            for i,team in enumerate(teams):
                if team != None:
                    matchs[i%(2*nb_matchs)].teams.add(team)
    
    nb_matchs -= math.ceil(nb_matchs/2**(swiss.min_score-1))
    for round_idx in range(swiss.min_score,2*swiss.min_score-1):
        matchs = []
        for match_idx in range(nb_matchs):
            matchs.append(SwissMatch.objects.create(round_number=round_idx+1,index_in_round=match_idx+1,swiss=swiss))

        nb_matchs = math.ceil(nb_matchs/2)

def generate_swiss_round(tournament: Tournament, min_score: int, use_seeding: bool):
    teams = tournament.teams.filter(validated=True)
    swiss = SwissRound.objects.create(tournament=tournament, min_score=min_score)

    if use_seeding:
        for team in teams:
            if team != None:
                SwissSeeding.objects.create(swiss=swiss, seeding=team.seed, team=team)
    else:
        for team in teams:
            if team != None:
                SwissSeeding.objects.create(swiss=swiss, seeding=0, team=team)

    create_swiss_matchs(swiss)