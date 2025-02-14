import math
from typing import List
from ..models import Group, GroupMatch, Team, Tournament, Seeding, GroupTiebreakScore, BestofType

def generate_groups(tournament: Tournament, count: int, team_per_group: int, names: list[str], use_seeding: bool):
    if use_seeding:
        teams = list(Team.objects.filter(tournament=tournament, validated=True).order_by("seed").reverse())
    else:
        teams = list(Team.objects.filter(tournament=tournament, validated=True))
    teams += [None]*(tournament.maxTeam - len(teams))

    for i in range(count):
        group = Group.objects.create(tournament=tournament, name=names[i], round_count=team_per_group-1)

        for j in range(team_per_group):
            team = teams[i+count*j]
            if team != None:
                Seeding.objects.create(group=group, team=team, seeding=j+1)
                GroupTiebreakScore.objects.create(group=group, team=team)

def create_group_matchs(group: Group, bo_type: BestofType):
    teams = group.get_sorted_teams()
    team_per_match = group.get_tournament().get_game().get_team_per_match()
    nb_matchs = math.ceil(len(teams)/team_per_match)
    nb_rounds = group.get_round_count()

    teams += [None]*(nb_matchs*team_per_match-len(teams))

    for gmatch in GroupMatch.objects.filter(group=group):
        gmatch.delete()

    for round_idx in range(nb_rounds):
        matchs = []
        for match_idx in range(nb_matchs):
            matchs.append(GroupMatch.objects.create(round_number=round_idx+1,index_in_round=match_idx+1,group=group, bo_type=bo_type))
        
        matchs += matchs[::-1]

        for i,team in enumerate(teams):
            if team != None:
                matchs[i%(nb_matchs*2)].teams.add(team)

        if len(teams) > 2:
            teams.insert(1,teams.pop())