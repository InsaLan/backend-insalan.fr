from ..models import Team, Tournament, SwissRound, SwissMatch, SwissSeeding
from math import ceil

def create_swiss_matchs(swiss: SwissRound):
    teams = swiss.get_sorted_teams()
    team_per_match = swiss.tournament.get_game().get_team_per_match()
    nb_matchs = ceil(len(teams)/team_per_match)

    teams += [None]*(nb_matchs*team_per_match-len(teams))

    matchs_per_score_group_per_round = []

    for match in SwissMatch.objects.filter(swiss=swiss):
        match.delete()

    # first round
    matchs = []
    for match_idx in range(nb_matchs):
        matchs.append(SwissMatch.objects.create(round_number=1,index_in_round=match_idx+1,swiss=swiss,score_group=0))

    matchs_per_score_group_per_round.append([nb_matchs])

    matchs += matchs[::-1]

    for i,team in enumerate(teams):
        if team != None:
            matchs[i%(2*nb_matchs)].teams.add(team)

    # next rounds
    for round_idx in range(1, swiss.min_score):
        match_idx = 0

        for idx in range(ceil(matchs_per_score_group_per_round[round_idx - 1][0] / 2)):
            SwissMatch.objects.create(round_number=round_idx+1,index_in_round=idx + 1,swiss=swiss,score_group=0)

        match_idx += idx + 1
        matchs_per_score_group_per_round.append([match_idx])

        for j in range(round_idx - 1):
            for idx in range(ceil(sum(matchs_per_score_group_per_round[round_idx - 1][j:j+2]) / 2)):
                SwissMatch.objects.create(round_number=round_idx+1,index_in_round=match_idx + idx + 1,swiss=swiss,score_group=j+1)

            matchs_per_score_group_per_round[-1].append(idx+1)
            match_idx += idx + 1

        for idx in range(ceil(matchs_per_score_group_per_round[round_idx - 1][-1] / 2)):
            SwissMatch.objects.create(round_number=round_idx+1,index_in_round=match_idx + idx + 1,swiss=swiss,score_group=round_idx)

        matchs_per_score_group_per_round[-1].append(idx+1)

    # last qualifying rounds
    for round_idx in range(swiss.min_score,2*swiss.min_score-1):
        matchs_per_score_group_per_round.append([])

        match_idx = 0

        for j in range(2*swiss.min_score - round_idx - 1):
            for idx in range(ceil(sum(matchs_per_score_group_per_round[round_idx - 1][j:j+2]) / 2)):
                SwissMatch.objects.create(round_number=round_idx+1,index_in_round=match_idx + idx + 1,swiss=swiss,score_group=j)

            matchs_per_score_group_per_round[-1].append(idx+1)
            match_idx += idx + 1

def create_swiss_rounds(tournament: Tournament, min_score: int, use_seeding: bool):
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