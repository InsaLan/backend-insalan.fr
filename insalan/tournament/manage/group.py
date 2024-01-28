import math
from typing import List
from ..models import Group, GroupMatch, Team

def create_group_matchs(group: Group):
    teams = group.get_sorted_teams()
    team_per_match = group.get_tournament().get_game().get_team_per_match()
    nb_matchs = math.ceil(len(teams)/team_per_match)
    nb_rounds = group.get_nb_rounds()

    for gmatch in GroupMatch.objects.filter(group=group):
        gmatch.delete()

    def index(k,n_match):
        if k%2 == 0:
            return k + n_match*team_per_match
        else:
            return -(k+1)//2 + n_match*team_per_match

    for round in range(1,nb_rounds+1):
        if nb_matchs == 1:
            gmatch = GroupMatch.objects.create(round_number=round,index_in_round=1,group=group)
            for team in teams:
                gmatch.teams.add(team)
        else:
            for n_match in range(nb_matchs):
                match_teams = [teams[index(k,n_match)] for k in range(team_per_match) if k == 1 or (abs(index(k,n_match))+abs(index(k-1,n_match)) + 1) <= len(teams)]
                gmatch = GroupMatch.objects.create(round_number=round,index_in_round=n_match+1,group=group)
                for team in match_teams:
                    gmatch.teams.add(team)
            
            if len(teams) > 2:
                teams = [teams[0]] + teams[2:] + [teams[1]]