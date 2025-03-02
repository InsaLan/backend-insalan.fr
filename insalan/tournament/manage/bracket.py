from math import ceil
from ..models import Bracket, KnockoutMatch, BracketType, BracketSet, BestofType

def create_empty_knockout_matchs(bracket: Bracket, bo_type: BestofType = BestofType.BO1):
    depth = bracket.get_depth()

    for match in KnockoutMatch.objects.filter(bracket=bracket):
        match.delete()

    for round_idx in range(1,depth+1):
        match_count = min(
            2**(round_idx-1),
            ceil(bracket.get_max_match_count()/2**(depth-round_idx))
        )
        for match_id in range(1,match_count+1):
            KnockoutMatch.objects.create(round_number=round_idx,index_in_round=match_id,bracket=bracket,bo_type=bo_type)

    if bracket.bracket_type == BracketType.DOUBLE:
        for round_idx in range(1,2*depth-1):
            match_count = min(
                2**((round_idx-1)//2),
                ceil(bracket.get_max_match_count()/2**(depth-(round_idx+1)//2))
            )
            for match_id in range(1,match_count+1):
                KnockoutMatch.objects.create(round_number=round_idx,index_in_round=match_id,bracket=bracket,bracket_set=BracketSet.LOOSER,bo_type=bo_type)
        KnockoutMatch.objects.create(round_number=0,index_in_round=1,bracket=bracket,bo_type=bo_type)

def update_next_knockout_match(match):
    winners, loosers = match.get_winners_loosers()
    winners_count = len(winners)
    depth = match.bracket.get_depth()

    # winner bracket
    if match.bracket_set == BracketSet.WINNER:
        for i, winner in enumerate(winners):
            # regular new index
            new_index_in_round = ceil(match.index_in_round / 2) - 1
            # correction if more than one winner per match
            if match.round_number > 2:
                new_index_in_round = (new_index_in_round // winners_count)*winners_count + (new_index_in_round%winners_count - i)%winners_count + 1
            else:
                new_index_in_round += 1

            next_match_winner = KnockoutMatch.objects.get(bracket=match.bracket,bracket_set=match.bracket_set,round_number=match.round_number-1,index_in_round=new_index_in_round)

            next_match_winner.teams.add(winner)

        if match.bracket.bracket_type == BracketType.DOUBLE:
            for i, looser in enumerate(loosers):
                # regular new index
                if match.round_number == depth:
                    looser_round = 2*(match.round_number - 1)
                    new_index_in_round = ceil(match.index_in_round / 2) - 1
                else:
                    looser_round = 2*match.round_number - 1
                    new_index_in_round = match.index_in_round - 1
                # reverse order if odd round
                if (depth - match.round_number) % 2:
                    matchs_count = ceil(match.bracket.get_max_match_count() / 2**(depth - match.round_number))
                    new_index_in_round = matchs_count - new_index_in_round - 1
                # correction if more than one winner per match
                if match.round_number > 2:
                    new_index_in_round = (new_index_in_round // winners_count)*winners_count + (new_index_in_round%winners_count - i)%winners_count + 1
                else:
                    new_index_in_round += 1

                next_match_looser = KnockoutMatch.objects.get(bracket=match.bracket,bracket_set=BracketSet.LOOSER,round_number=looser_round,index_in_round=new_index_in_round)

                next_match_looser.teams.add(looser)

    # looser bracket winners
    else:
        if match.round_number == 1:
            next_match = KnockoutMatch.objects.get(bracket=match.bracket,bracket_set=BracketSet.WINNER,round_number=0,index_in_round=1)
            next_match.teams.add(*winners)
        else:
            if match.round_number%2:
                base_index_in_round = ceil(match.index_in_round / 2) - 1
            else:
                base_index_in_round = match.index_in_round - 1

            for i, winner in enumerate(winners):
                if match.round_number > 3:
                    new_index_in_round = (base_index_in_round // winners_count)*winners_count + (base_index_in_round%winners_count - i)%winners_count + 1
                else:
                    new_index_in_round = base_index_in_round + 1

                next_match = KnockoutMatch.objects.get(bracket=match.bracket,bracket_set=match.bracket_set,round_number=match.round_number-1,index_in_round=new_index_in_round)

                next_match.teams.add(winner)
