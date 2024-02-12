from ..models import Bracket, KnockoutMatch, BracketType, BracketSet
from math import ceil

def create_empty_knockout_matchs(bracket: Bracket):
    depth = bracket.get_depth()

    for match in KnockoutMatch.objects.filter(bracket=bracket):
        match.delete()

    for roundIdx in range(1,depth+1):
        matchCount = min(2**(roundIdx-1),ceil(bracket.get_max_match_count()/2**(depth-roundIdx)))
        for matchId in range(1,matchCount+1):
            KnockoutMatch.objects.create(round_number=roundIdx,index_in_round=matchId,bracket=bracket)
    if bracket.bracket_type == BracketType.DOUBLE:
        for roundIdx in range(1,2*depth-1):
            matchCount = min(2**((roundIdx-1)//2),ceil((bracket.get_max_match_count()//2)/2**(depth-(roundIdx+1)//2 - 1)))
            for matchId in range(1,matchCount+1):
                KnockoutMatch.objects.create(round_number=roundIdx,index_in_round=matchId,bracket=bracket,bracket_set=BracketSet.LOOSER)
        KnockoutMatch.objects.create(round_number=0,index_in_round=1,bracket=bracket)

# def fill_knockout_matchs(bracket: Bracket):

def update_next_knockout_match(match: KnockoutMatch):
    if match.bracket_set == BracketSet.WINNER:
        if len(match.get_teams()) > 2:
            pass

        winner,looser = match.get_winners_loosers()

        new_index_in_round = ceil(match.index_in_round/2)

        next_match_winner = KnockoutMatch.objects.get(bracket=match.bracket,bracket_set=match.bracket_set,round_number=match.round_number-1,index_in_round=new_index_in_round)

        next_match_winner.teams.add(*winner)

        if match.round_number == match.bracket.get_depth():
            next_match_looser = KnockoutMatch.objects.get(bracket=match.bracket,bracket_set=BracketSet.LOOSER,round_number=2*(match.round_number-1),index_in_round=new_index_in_round)
        else:
            next_match_looser = KnockoutMatch.objects.get(bracket=match.bracket,bracket_set=BracketSet.LOOSER,round_number=2*match.round_number-1,index_in_round=new_index_in_round)
        
        next_match_looser.teams.add(*looser)
    elif match.bracket_set == BracketSet.LOOSER:
        if len(match.get_teams()) > 2:
            pass

        winner, _ = match.get_winners_loosers()

        if match.round_number == 1:
            next_match = KnockoutMatch.objects.get(bracket=match.bracket,bracket_set=BracketSet.WINNER,round_number=0,index_in_round=1)
        elif match.round_number%2:
            next_match = KnockoutMatch.objects.get(bracket=match.bracket,bracket_set=match.bracket_set,round_number=match.round_number-1,index_in_round=ceil(match.index_in_round/2))
        else:
            next_match = KnockoutMatch.objects.get(bracket=match.bracket,bracket_set=match.bracket_set,round_number=match.round_number-1,index_in_round=match.index_in_round)

        next_match.teams.add(*winner)
