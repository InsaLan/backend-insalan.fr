import math
from typing import List
from ..models import Group, GroupMatch, Team

def create_group_matchs(group: Group):
    teams = group.get_sorted_teams()
    team_per_match = group.get_tournament().get_game().get_team_per_match()
    nb_matchs = math.ceil(len(teams)/team_per_match)
    nb_rounds = group.get_nb_rounds()

    teams += [None]*(nb_matchs*team_per_match-len(teams))

    for gmatch in GroupMatch.objects.filter(group=group):
        gmatch.delete()

    for round_idx in range(nb_rounds):
        matchs = []
        for match_idx in range(nb_matchs):
            matchs.append(GroupMatch.objects.create(round_number=round_idx+1,index_in_round=match_idx+1,group=group))
        
        matchs += matchs[::-1]

        for i,team in enumerate(teams):
            if team != None:
                matchs[i%(nb_matchs*2)].teams.add(team)

        if len(teams) > 2:
            teams.insert(1,teams.pop())