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
    Stage
)


def generate_groups(
    tournament: BaseTournament,
    count: int,
    team_per_group: int,
    names: list[str],
    use_seeding: bool,
    stage: Stage,
    round_count: int
) -> None:
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
        group = Group.objects.create(
            tournament=tournament,
            name=names[i],
            round_count=round_count,
            stage=stage
        )

        for j in range(team_per_group):
            team = teams[i + count * j]
            if team is not None:
                Seeding.objects.create(group=group, team=team, seeding=j + 1)
                GroupTiebreakScore.objects.create(group=group, team=team)


def create_group_matchs(
    group: Group,
    bo_type: BestofType = BestofType.BO1,
    play_all: bool = False
) -> None:
    teams: list[int | None] = cast(list[int | None], group.get_sorted_teams())
    team_per_match = group.get_tournament().get_game().get_team_per_match()
    nb_matchs = math.ceil(len(teams)/team_per_match)
    nb_rounds = group.get_round_count()

    teams += [None] * (nb_matchs * team_per_match - len(teams))

    for gmatch in GroupMatch.objects.filter(group=group):
        gmatch.delete()

    # Get game processor for match creation
    processor_class = group.get_tournament().game.get_game_processor()

    for round_idx in range(nb_rounds):
        matchs = []
        for match_idx in range(nb_matchs):
            match = GroupMatch.objects.create(
                round_number=round_idx + 1,
                index_in_round=match_idx + 1,
                group=group,
                bo_type=bo_type,
                play_all=play_all
            )

            # Call game processor for match creation
            if processor_class is not None:
                api_data = processor_class.create_match(match)
                if api_data is not None:
                    match.api_data = api_data
                    match.save(update_fields=['api_data'])

            matchs.append(match)

        matchs += matchs[::-1]

        for i, team in enumerate(teams):
            if team is not None:
                matchs[i % (nb_matchs * 2)].teams.add(team)

        if len(teams) > 2:
            teams.insert(1, teams.pop())
