import math
from typing import cast

from ..models import (
    BaseTournament,
    BestofType,
    Group,
    GroupMatch,
    GroupTiebreakScore,
    Team,
    Seeding,
)


def generate_groups(tournament: BaseTournament, count: int, team_per_group: int,
                    names: list[str], use_seeding: bool) -> None:
    teams: list[Team | None]
    if use_seeding:
        teams = cast(list[Team | None], list(Team.objects.filter(
            tournament=tournament,
            validated=True,
            seed__gt=0,
        ).order_by("seed")) + list(Team.objects.filter(
            tournament=tournament,
            validated=True,
            seed=0,
        )))
    else:
        teams = list(Team.objects.filter(tournament=tournament, validated=True))
    teams += [None] * (tournament.get_max_team() - len(teams))

    for i in range(count):
        group = Group.objects.create(tournament=tournament, name=names[i],
                                     round_count=team_per_group - 1)

        for j in range(team_per_group):
            team = teams[i + count * j]
            if team is not None:
                Seeding.objects.create(group=group, team=team, seeding=j + 1)
                GroupTiebreakScore.objects.create(group=group, team=team)


def create_group_matchs(group: Group, bo_type: BestofType = BestofType.BO1) -> None:
    teams: list[int | None] = cast(list[int | None], group.get_sorted_teams())
    team_per_match = group.get_tournament().get_game().get_team_per_match()
    nb_matchs = math.ceil(len(teams)/team_per_match)
    nb_rounds = group.get_round_count()

    teams += [None] * (nb_matchs * team_per_match - len(teams))

    for gmatch in GroupMatch.objects.filter(group=group):
        gmatch.delete()

    for round_idx in range(nb_rounds):
        matchs = []
        for match_idx in range(nb_matchs):
            matchs.append(GroupMatch.objects.create(
                round_number=round_idx + 1,
                index_in_round=match_idx + 1,
                group=group,
                bo_type=bo_type,
            ))

        matchs += matchs[::-1]

        for i, team in enumerate(teams):
            if team is not None:
                matchs[i % (nb_matchs * 2)].teams.add(team)

        if len(teams) > 2:
            teams.insert(1, teams.pop())
