from ..models import Bracket, KnockoutMatch, BracketType, BracketSet
from math import ceil

def create_empty_knockout_matchs(bracket: Bracket):
    depth = bracket.get_depth()

    for match in KnockoutMatch.objects.filter(bracket=bracket):
        match.delete()

    for round_idx in range(1,depth+1):
        match_count = min(2**(round_idx-1),ceil(bracket.get_max_match_count()/2**(depth-round_idx)))
        for match_id in range(1,match_count+1):
            KnockoutMatch.objects.create(round_number=round_idx,index_in_round=match_id,bracket=bracket)
    if bracket.bracket_type == BracketType.DOUBLE:
        for round_idx in range(1,2*depth-1):
            match_count = min(2**((round_idx-1)//2),ceil((bracket.get_max_match_count()//2)/2**(depth-(round_idx+1)//2 - 1)))
            for match_id in range(1,match_count+1):
                KnockoutMatch.objects.create(round_number=round_idx,index_in_round=match_id,bracket=bracket,bracket_set=BracketSet.LOOSER)
        KnockoutMatch.objects.create(round_number=0,index_in_round=1,bracket=bracket)

# def fill_knockout_matchs(bracket: Bracket):

def update_next_knockout_match(match: KnockoutMatch):
    if match.bracket_set == BracketSet.WINNER:
        winners, loosers = match.get_winners_loosers()
        match_count = KnockoutMatch.objects.filter(bracket=match.bracket,bracket_set=match.bracket_set,round_number=match.round_number-1).count()

        for i,winner in enumerate(winners):
            new_index_in_round = (ceil(match.index_in_round/2) + i)%(match_count+ 1)

            next_match_winner = KnockoutMatch.objects.get(bracket=match.bracket,bracket_set=match.bracket_set,round_number=match.round_number-1,index_in_round=new_index_in_round)

            next_match_winner.teams.add(winner)

        for i, looser in enumerate(loosers):
            new_index_in_round = (ceil(match.index_in_round/2) + i)%(match_count+ 1)

            if match.round_number == match.bracket.get_depth():
                looser_round = 2*(match.round_number-1)
            else:
                looser_round = 2*match.round_number-1

            next_match_looser = KnockoutMatch.objects.get(bracket=match.bracket,bracket_set=BracketSet.LOOSER,round_number=looser_round,index_in_round=new_index_in_round)

            next_match_looser.teams.add(looser)

    elif match.bracket_set == BracketSet.LOOSER:

        winners, _ = match.get_winners_loosers()
        match_count = KnockoutMatch.objects.filter(bracket=match.bracket,bracket_set=match.bracket_set,round_number=match.round_number-1).count()

        if match.round_number == 1:
            next_match = KnockoutMatch.objects.get(bracket=match.bracket,bracket_set=BracketSet.WINNER,round_number=0,index_in_round=1)
            next_match.teams.add(*winners)
        else:
            if match.round_number%2:
                base_index_in_round = ceil(match.index_in_round/2)
            else:
                base_index_in_round = match.index_in_round
            for i, winner in enumerate(winners):
                new_index_in_round = (base_index_in_round + i)%(match_count + 1)

                next_match = KnockoutMatch.objects.get(bracket=match.bracket,bracket_set=match.bracket_set,round_number=match.round_number-1,index_in_round=new_index_in_round)

                next_match.teams.add(winner)

