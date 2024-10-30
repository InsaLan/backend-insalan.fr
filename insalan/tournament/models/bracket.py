import math
from typing import List

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator


from . import match, team

class BracketType(models.TextChoices):
    """Information about the type of a bracket, single or double elimination"""

    SINGLE = "SINGLE", _("Simple élimination")
    DOUBLE = "DOUBLE", _("Double élimination")

class BracketSet(models.TextChoices):
    """Information on the bracket set, winner or looser"""

    WINNER = "WINNER", _("Gagnant")
    LOOSER = "LOOSER", _("Perdant")

class Bracket(models.Model):
    name = models.CharField(
        max_length=40,
        verbose_name=_("Nom de l'arbre")
    )
    tournament = models.ForeignKey(
        "Tournament",
        verbose_name=_("Tournoi"),
        on_delete=models.CASCADE
    )
    bracket_type = models.CharField(
        default=BracketType.SINGLE,
        choices=BracketType.choices,
        max_length=10
    )
    team_count = models.IntegerField(
        default=2,
        verbose_name=_("Nombre d'équipes"),
        validators=[MinValueValidator(2)]
    )

    class Meta:
        verbose_name = _("Arbre de tournoi")
        verbose_name_plural = _("Arbres de tournoi")
        indexes = [
            models.Index(fields=["tournament"])
        ]

    def __str__(self):
        return self.name

    def get_depth(self) -> int:
        return math.ceil(math.log2(self.team_count/self.tournament.get_game().get_team_per_match())) + 1

    def get_max_match_count(self) -> int:
        return math.ceil(self.team_count/self.tournament.get_game().get_team_per_match())

    def get_teams(self) -> List["Team"]:
        # return [match.get_teams() for match in KnockoutMatch.objects.filter(bracket=self)]
        return team.Team.objects.filter(pk__in=KnockoutMatch.objects.filter(bracket=self).values("teams"))

    def get_teams_id(self) -> List[int]:
        return self.get_teams().values_list("id", flat=True)

    def get_matchs(self) -> List["KnockoutMatch"]:
        return KnockoutMatch.objects.filter(bracket=self)

    def get_winner(self) -> int:
        if self.bracket_type == BracketType.SINGLE:
            final = KnockoutMatch.objects.filter(round_number=1,index_in_round=1,bracket=self,bracket_set=BracketSet.WINNER,status=match.MatchStatus.COMPLETED)
        else:
            final = KnockoutMatch.objects.filter(round_number=0,index_in_round=1,bracket=self,bracket_set=BracketSet.WINNER,status=match.MatchStatus.COMPLETED)

        if len(final) != 1:
            return None

        winners, _ = final[0].get_winners_loosers()
        if len(winners):
            return winners[0]

        return None


class KnockoutMatch(match.Match):
    bracket = models.ForeignKey(
        "Bracket",
        verbose_name=_("Arbre de tournoi"),
        on_delete=models.CASCADE
    )
    bracket_set = models.CharField(
        max_length=10,
        default=BracketSet.WINNER,
        choices=BracketSet.choices,
        verbose_name=_("Type de tableau, gagnant ou perdant")
    )

    class Meta:
        verbose_name = _("Match d'arbre")
        verbose_name_plural = _("Matchs d'arbre")

    def get_tournament(self):
        return self.bracket.tournament
