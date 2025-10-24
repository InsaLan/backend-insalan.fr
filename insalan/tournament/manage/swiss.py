from math import ceil
from random import shuffle
from ..models import BaseTournament, SwissRound, SwissMatch, SwissSeeding, BestofType

def create_swiss_matchs(swiss: SwissRound, bo_type: BestofType = BestofType.BO1):
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
        matchs.append(SwissMatch.objects.create(
            round_number=1,
            index_in_round=match_idx + 1,
            swiss=swiss,
            score_group=0,
            bo_type=bo_type,
        ))

    matchs_per_score_group_per_round.append([nb_matchs])

    matchs += matchs[::-1]

    for i,team in enumerate(teams):
        if team is not None:
            matchs[i % (2 * nb_matchs)].teams.add(team)

    # next rounds
    for round_idx in range(1, swiss.min_score):
        match_idx = 0

        for idx in range(ceil(matchs_per_score_group_per_round[round_idx - 1][0] / 2)):
            SwissMatch.objects.create(
                round_number=round_idx + 1,
                index_in_round=idx + 1,
                swiss=swiss,
                score_group=0,
                bo_type=bo_type,
            )

        match_idx += idx + 1
        matchs_per_score_group_per_round.append([match_idx])

        for j in range(round_idx - 1):
            for idx in range(
                ceil(sum(matchs_per_score_group_per_round[round_idx - 1][j:j + 2]) / 2)
            ):
                SwissMatch.objects.create(
                    round_number=round_idx + 1,
                    index_in_round=match_idx + idx + 1,
                    swiss=swiss,
                    score_group=j + 1,
                    bo_type=bo_type,
                )

            matchs_per_score_group_per_round[-1].append(idx + 1)
            match_idx += idx + 1

        for idx in range(ceil(matchs_per_score_group_per_round[round_idx - 1][-1] / 2)):
            SwissMatch.objects.create(
                round_number=round_idx + 1,
                index_in_round=match_idx + idx + 1,
                swiss=swiss,
                score_group=round_idx,
                bo_type=bo_type,
            )

        matchs_per_score_group_per_round[-1].append(idx + 1)

    # last qualifying rounds
    for round_idx in range(swiss.min_score,2*swiss.min_score-1):
        matchs_per_score_group_per_round.append([])

        match_idx = 0

        for j in range(2 * swiss.min_score - round_idx - 1):
            for idx in range(
                ceil(sum(matchs_per_score_group_per_round[round_idx - 1][j:j + 2]) / 2)
            ):
                SwissMatch.objects.create(
                    round_number=round_idx + 1,
                    index_in_round=match_idx + idx + 1,
                    swiss=swiss,
                    score_group=j,
                    bo_type=bo_type,
                )

            matchs_per_score_group_per_round[-1].append(idx + 1)
            match_idx += idx + 1

def create_swiss_rounds(tournament: BaseTournament, min_score: int, use_seeding: bool,
                        bo_type: BestofType):
    teams = tournament.teams.filter(validated=True)
    swiss = SwissRound.objects.create(tournament=tournament, min_score=min_score)

    if use_seeding:
        for team in teams:
            if team is not None:
                SwissSeeding.objects.create(swiss=swiss, seeding=team.seed, team=team)
    else:
        for team in teams:
            if team is not None:
                SwissSeeding.objects.create(swiss=swiss, seeding=0, team=team)

    create_swiss_matchs(swiss, bo_type)

def get_winners_loosers_per_score_group(matchs_per_score_group):
    winners_per_score_group, loosers_per_score_group = [], []

    for idx, matchs in enumerate(matchs_per_score_group):
        winners_per_score_group.append([])
        loosers_per_score_group.append([])

        for match in matchs:
            winners, loosers = match.get_winners_loosers()
            winners_per_score_group[idx] += winners
            loosers_per_score_group[idx] += loosers

    return winners_per_score_group, loosers_per_score_group

def fill_matchs(matchs, teams, team_per_match):
    matchs = list(matchs)
    nb_matchs = len(matchs)

    # clear matchs
    for match in matchs:
        match.teams.clear()

    teams += [None] * (nb_matchs * team_per_match - len(teams))

    matchs += matchs[::-1]

    for i, team in enumerate(teams):
        if team is not None:
            matchs[i % (2 * nb_matchs)].teams.add(team)

def generate_swiss_round_round(swiss: SwissRound, round_idx: int):
    team_per_match = swiss.tournament.get_game().get_team_per_match()
    # before qualifying rounds
    if round_idx <= swiss.min_score:
        matchs_per_score_group = [SwissMatch.objects.filter(
            swiss=swiss,
            round_number=round_idx - 1,
            score_group=sg,
        ) for sg in range(round_idx - 1)]

        winners_per_score_group, loosers_per_score_group = get_winners_loosers_per_score_group(
            matchs_per_score_group,
        )

        matchs = SwissMatch.objects.filter(swiss=swiss, round_number=round_idx, score_group=0)

        teams = winners_per_score_group[0]
        shuffle(teams)

        fill_matchs(matchs, teams, team_per_match)

        for score_group in range(1,round_idx-1):
            matchs = SwissMatch.objects.filter(swiss=swiss, round_number=round_idx,
                                               score_group=score_group)

            teams = loosers_per_score_group[score_group-1] + winners_per_score_group[score_group]
            shuffle(teams)

            fill_matchs(matchs, teams, team_per_match)

        matchs = SwissMatch.objects.filter(swiss=swiss, round_number=round_idx,
                                           score_group=round_idx - 1)

        teams = loosers_per_score_group[round_idx-2]
        shuffle(teams)

        fill_matchs(matchs, teams, team_per_match)

    # qualifying rounds
    else:
        score_group_count = 2*swiss.min_score - round_idx
        matchs_per_score_group = [SwissMatch.objects.filter(
            swiss=swiss,
            round_number=round_idx - 1,
            score_group=sg,
        ) for sg in range(score_group_count + 1)]

        winners_per_score_group, loosers_per_score_group = get_winners_loosers_per_score_group(
            matchs_per_score_group
        )

        for score_group in range(score_group_count):
            matchs = SwissMatch.objects.filter(swiss=swiss, round_number=round_idx,
                                               score_group=score_group)

            teams = loosers_per_score_group[score_group] + winners_per_score_group[score_group + 1]
            shuffle(teams)

            fill_matchs(matchs, teams, team_per_match)

    return SwissMatch.objects.filter(swiss=swiss, round_number=round_idx)
