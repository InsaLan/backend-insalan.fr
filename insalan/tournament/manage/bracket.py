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
