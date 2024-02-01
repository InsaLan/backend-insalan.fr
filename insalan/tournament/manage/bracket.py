from ..models import Bracket, KnockoutMatch, BracketType, BracketSet

def create_empty_knockout_matchs(bracket: Bracket):
    depth = bracket.depth

    for match in KnockoutMatch.objects.filter(bracket=bracket):
        match.delete()

    for round_n in range(1,depth+1):
        for match_id in range(1,2**(round_n-1)+1):
            KnockoutMatch.objects.create(round_number=round_n,index_in_round=match_id,bracket=bracket)
    if bracket.bracket_type == BracketType.DOUBLE:
        for round_n in range(1,2*depth-1):
            for match_id in range(1,2**((round_n-1)//2)+1):
                KnockoutMatch.objects.create(round_number=round_n,index_in_round=match_id,bracket=bracket,bracket_set=BracketSet.LOOSER)
        KnockoutMatch.objects.create(round_number=0,index_in_round=1,bracket=bracket)